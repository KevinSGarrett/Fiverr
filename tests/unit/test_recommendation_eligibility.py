"""Unit tests for Stage 13 recommendation eligibility and gating."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import (
    Base,
    FinalScore,
    GigQualityScore,
    Keyword,
    KeywordScore,
    Niche,
    Recommendation,
)
from src.recommendations import eligibility


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)()


def _config(*, min_tag: str = "CONDITIONAL GO", recommendation_generation: bool = True) -> dict[str, object]:
    return {
        "recommendations": {
            "min_tag": min_tag,
            "niches": {"1": {"recommendation_generation": recommendation_generation}},
        }
    }


def _seed_keyword_with_score(
    db: Session,
    *,
    keyword_id: int = 101,
    niche_id: int = 1,
    demand_score: float | None = 75.0,
    tag: str = "STRONG GO",
    final_score: float = 82.0,
    confidence_modifier: float = 0.8,
) -> None:
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if niche is None:
        niche = Niche(
            id=niche_id,
            slug=f"niche-{niche_id}",
            name=f"Niche {niche_id}",
            category_path="programming-tech",
        )
        db.add(niche)
    keyword = Keyword(
        id=keyword_id,
        niche_id=niche_id,
        keyword=f"keyword-{keyword_id}",
        normalized_keyword=f"keyword-{keyword_id}",
    )
    score = KeywordScore(
        keyword_id=keyword_id,
        scoring_profile="default",
        score_depth="standard",
        demand_score=demand_score,
        competition_score=40.0,
        opportunity_score=80.0,
        feasibility_score=60.0,
        final_score=final_score,
        confidence_modifier=confidence_modifier,
        tag=tag,
    )
    db.add_all([niche, keyword, score])
    db.commit()


def _add_gig_quality(db: Session, *, keyword_id: int = 101, analysis_complete: bool = True) -> None:
    row = GigQualityScore(
        keyword_id=keyword_id,
        gig_url=f"https://fiverr.com/gig/{keyword_id}",
        run_id="run-1",
        analysis_complete=analysis_complete,
    )
    db.add(row)
    db.commit()


def test_tags_at_or_above_strong_go_returns_one() -> None:
    assert eligibility._tags_at_or_above("STRONG GO") == ["STRONG GO"]


def test_tags_at_or_above_conditional_go_returns_two() -> None:
    assert eligibility._tags_at_or_above("CONDITIONAL GO") == ["STRONG GO", "CONDITIONAL GO"]


def test_get_eligible_keywords_filters_by_tag() -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=101, tag="STRONG GO")
    _seed_keyword_with_score(db, keyword_id=102, tag="PASS", final_score=10.0)

    rows = eligibility.get_eligible_keywords("run-1", db, _config())

    assert [row["keyword_id"] for row in rows] == [101]
    db.close()


def test_get_eligible_keywords_with_mixed_tag_keywords() -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=111, tag="STRONG_GO")
    _seed_keyword_with_score(db, keyword_id=112, tag="CONDITIONAL GO")
    _seed_keyword_with_score(db, keyword_id=113, tag="MONITOR")

    rows = eligibility.get_eligible_keywords("run-1", db, _config(min_tag="CONDITIONAL GO"))

    assert {row["keyword_id"] for row in rows} == {111, 112}
    assert {row["tag"] for row in rows} == {"STRONG GO", "CONDITIONAL GO"}
    db.close()


def test_get_eligible_keywords_skips_disabled_niche() -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=101, niche_id=1, tag="STRONG GO")

    rows = eligibility.get_eligible_keywords(
        "run-1",
        db,
        _config(recommendation_generation=False),
    )

    assert rows == []
    db.close()


def test_get_eligible_keywords_skips_keyword_score_fallback_when_final_scores_exist_for_other_run() -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=101, tag="STRONG GO")
    db.add(
        FinalScore(
            run_id=999,
            keyword_id=101,
            gig_id=None,
            final_score=74.0,
            raw_json={"tag": "CONDITIONAL GO"},
        )
    )
    db.commit()

    rows = eligibility.get_eligible_keywords("1", db, _config())

    assert rows == []
    db.close()


def test_load_ranking_rows_prefers_run_scoped_opportunity_rows_when_present(monkeypatch) -> None:
    class _RunColumn:
        def __eq__(self, other: object) -> tuple[str, object]:
            return ("run_id_eq", other)

    class _RankingModel:
        run_id = _RunColumn()

    class _Query:
        def __init__(self) -> None:
            self.filters: list[tuple[str, object]] = []
            self.rows = [object()]

        def filter(self, predicate: tuple[str, object]) -> _Query:
            self.filters.append(predicate)
            return self

        def all(self) -> list[object]:
            return self.rows

    query = _Query()
    monkeypatch.setattr(
        eligibility,
        "_model_by_name",
        lambda name: _RankingModel if name == "OpportunityRanking" else None,
    )
    monkeypatch.setattr(
        eligibility,
        "_safe_query",
        lambda _db, model: query if model is _RankingModel else None,
    )

    rows = eligibility._load_ranking_rows("run-123", db=object())

    assert rows == query.rows
    assert query.filters == [("run_id_eq", "run-123")]


def test_load_ranking_rows_falls_back_to_latest_keyword_scores_when_no_final_scores() -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=121, final_score=81.0)
    _seed_keyword_with_score(db, keyword_id=122, final_score=77.0)

    rows = eligibility._load_ranking_rows("run-missing", db=db)

    assert len(rows) == 2
    assert {row.keyword_id for row in rows} == {121, 122}
    db.close()


def test_gate1_fails_low_confidence() -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=101, demand_score=60.0)
    _add_gig_quality(db, keyword_id=101)

    ok, reason = eligibility.passes_recommendation_gates(
        {"keyword_id": 101, "confidence_modifier": 0.39, "demand_score": 60.0},
        db,
    )

    assert ok is False
    assert "below 0.40" in reason
    db.close()


def test_gate2_fails_missing_demand_score() -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=101, demand_score=None)
    _add_gig_quality(db, keyword_id=101)

    ok, reason = eligibility.passes_recommendation_gates(
        {"keyword_id": 101, "confidence_modifier": 0.85},
        db,
    )

    assert ok is False
    assert "Demand score" in reason
    db.close()


def test_gate2_fails_low_demand_score() -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=101, demand_score=20.0)
    _add_gig_quality(db, keyword_id=101)

    ok, reason = eligibility.passes_recommendation_gates(
        {"keyword_id": 101, "confidence_modifier": 0.9, "demand_score": 20.0},
        db,
    )

    assert ok is False
    assert "Demand score" in reason
    db.close()


def test_gate3_fails_no_gig_quality_analysis() -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=101, demand_score=65.0)

    ok, reason = eligibility.passes_recommendation_gates(
        {"keyword_id": 101, "confidence_modifier": 0.9, "demand_score": 65.0},
        db,
    )

    assert ok is False
    assert "No gig quality analysis" in reason
    db.close()


def test_gate3_passes_when_any_gig_quality_row_is_complete() -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=131, demand_score=65.0)
    _add_gig_quality(db, keyword_id=131, analysis_complete=False)
    db.add(
        GigQualityScore(
            keyword_id=131,
            gig_url="https://fiverr.com/gig/131-alt",
            run_id="run-2",
            analysis_complete=True,
        )
    )
    db.commit()

    ok, reason = eligibility.passes_recommendation_gates(
        {"keyword_id": 131, "confidence_modifier": 0.9, "demand_score": 65.0},
        db,
    )

    assert ok is True
    assert reason == "All gates passed"
    db.close()


def test_gate4_user_override_bypasses_gates(monkeypatch) -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=101, demand_score=5.0)

    monkeypatch.setattr(eligibility, "is_keyword_force_recommended", lambda keyword_id, db: True)
    ok, reason = eligibility.passes_recommendation_gates(
        {"keyword_id": 101, "confidence_modifier": 0.0, "demand_score": 0.0},
        db,
    )

    assert ok is True
    assert "forced recommendation" in reason
    db.close()


def test_all_gates_pass_returns_true() -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=101, demand_score=65.0)
    _add_gig_quality(db, keyword_id=101)

    ok, reason = eligibility.passes_recommendation_gates(
        {"keyword_id": 101, "confidence_modifier": 0.9, "demand_score": 65.0},
        db,
    )

    assert ok is True
    assert reason == "All gates passed"
    db.close()


def test_regenerate_when_no_existing_recommendation() -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=101)

    assert eligibility.should_regenerate_recommendation(101, 82.0, db) is True
    db.close()


def test_skip_when_score_unchanged() -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=101)
    db.add(
        Recommendation(
            keyword_id=101,
            run_id=1,
            run_id_text="run-1",
            recommendation_type="keyword_recommendation",
            recommendation_text="Keep this approach",
            final_score=80.0,
            score_at_generation=80.0,
            generation_complete=True,
        )
    )
    db.commit()

    assert eligibility.should_regenerate_recommendation(101, 83.9, db) is False
    db.close()


def test_regenerate_when_score_changed_5_points() -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=101)
    db.add(
        Recommendation(
            keyword_id=101,
            run_id=1,
            run_id_text="run-1",
            recommendation_type="keyword_recommendation",
            recommendation_text="Previous recommendation",
            final_score=80.0,
            score_at_generation=80.0,
            generation_complete=True,
        )
    )
    db.commit()

    assert eligibility.should_regenerate_recommendation(101, 85.0, db) is True
    db.close()


def test_should_regenerate_when_latest_recommendation_is_incomplete() -> None:
    db = _session()
    _seed_keyword_with_score(db, keyword_id=141)
    db.add(
        Recommendation(
            keyword_id=141,
            run_id=1,
            run_id_text="run-1",
            recommendation_type="keyword_recommendation",
            recommendation_text="incomplete payload",
            final_score=82.0,
            score_at_generation=82.0,
            generation_complete=False,
        )
    )
    db.commit()

    assert eligibility.should_regenerate_recommendation(141, 82.1, db) is True
    db.close()
