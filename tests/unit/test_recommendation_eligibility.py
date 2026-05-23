"""Unit tests for Stage 13 recommendation eligibility and gating."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base, GigQualityScore, Keyword, KeywordScore, Niche, Recommendation
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
