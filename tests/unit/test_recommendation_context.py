"""Unit tests for Stage 13 recommendation context builder."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import (
    Base,
    ClusterAssignment,
    ClusterLabel,
    CompetitorProfile,
    FinalScore,
    Gig,
    Keyword,
    KeywordScore,
    Niche,
    Recommendation,
    SearchResult,
)
from src.recommendations import context_builder
from src.recommendations.context_builder import (
    build_recommendation_context,
    get_confidence_modifier,
)
from src.recommendations.storage import write_recommendation


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)()


def _seed_keyword_and_score(db: Session, *, confidence_modifier: float | None = 0.8, tag: str = "STRONG_GO") -> None:
    niche = Niche(id=1, slug="automation", name="Automation", category_path="programming-tech/automation")
    keyword = Keyword(
        id=101,
        niche_id=1,
        keyword="python automation",
        normalized_keyword="python automation",
    )
    keyword_score = KeywordScore(
        keyword_id=101,
        scoring_profile="default",
        score_depth="standard",
        demand_score=75.0,
        competition_score=40.0,
        opportunity_score=82.0,
        feasibility_score=64.0,
        saturation_score=33.0,
        final_score=82.0,
        confidence_modifier=confidence_modifier,
        tag=tag,
    )
    db.add_all([niche, keyword, keyword_score])
    db.commit()


def test_build_context_returns_populated_object() -> None:
    db = _session()
    _seed_keyword_and_score(db)
    db.add_all(
        [
            ClusterAssignment(keyword_id=101, niche_id="1", cluster_id=4, run_id="run-1"),
            ClusterLabel(
                niche_id="1",
                cluster_id=4,
                run_id="run-1",
                label_text="Workflow Automation",
                keyword_count=12,
            ),
            CompetitorProfile(
                niche_id="1",
                run_id="run-1",
                top_gig_count=5,
                new_seller_gap={
                    "top_competitor_weaknesses": [
                        {
                            "gig_title": "I will automate your tasks",
                            "weaknesses": [{"weakness": "slow delivery", "severity": "HIGH"}],
                        }
                    ]
                },
            ),
        ]
    )
    db.commit()

    context = build_recommendation_context(keyword_id=101, niche_id="1", run_id="run-1", db=db)

    assert context is not None
    assert context.keyword_id == 101
    assert context.keyword_text == "python automation"
    assert context.tag == "STRONG GO"
    assert context.final_score == 82.0
    assert context.niche_name == "Automation"
    assert context.top_competitor_weaknesses[0]["gig_title"] == "I will automate your tasks"
    db.close()


def test_build_context_returns_none_when_no_score() -> None:
    db = _session()
    db.add(Niche(id=1, slug="automation", name="Automation", category_path="programming-tech/automation"))
    db.add(Keyword(id=101, niche_id=1, keyword="python automation", normalized_keyword="python automation"))
    db.commit()

    context = build_recommendation_context(keyword_id=101, niche_id="1", run_id="run-1", db=db)

    assert context is None
    db.close()


def test_build_context_falls_back_to_final_score_when_keyword_score_missing() -> None:
    db = _session()
    db.add(Niche(id=1, slug="automation", name="Automation", category_path="programming-tech/automation"))
    db.add(Keyword(id=101, niche_id=1, keyword="python automation", normalized_keyword="python automation"))
    db.add(
        FinalScore(
            run_id=1,
            keyword_id=101,
            gig_id=None,
            final_score=77.0,
            raw_json={
                "tag": "CONDITIONAL GO",
                "demand_score": 61.0,
                "competition_score": 42.0,
                "opportunity_score": 70.0,
                "feasibility_score": 59.0,
                "saturation_score": 33.0,
                "confidence_modifier": 0.66,
            },
        )
    )
    db.commit()

    context = build_recommendation_context(keyword_id=101, niche_id="1", run_id="1", db=db)

    assert context is not None
    assert context.tag == "CONDITIONAL GO"
    assert context.final_score == 77.0
    assert context.demand_score == 61.0
    assert context.competition_score == 42.0
    assert context.opportunity_score == 70.0
    assert context.feasibility_score == 59.0
    assert context.saturation_score == 33.0
    assert context.confidence_modifier == 0.66
    db.close()


def test_extract_tag_from_final_score_returns_none_for_non_mapping_raw_json() -> None:
    row = type("FinalScoreRow", (), {"raw_json": "not-a-dict"})()
    assert context_builder._extract_tag_from_final_score(row) is None


def test_resolve_score_metric_returns_none_without_final_score_data() -> None:
    row = type("FinalScoreRow", (), {"raw_json": "invalid"})()
    assert context_builder._resolve_score_metric(None, None, "demand_score") is None
    assert context_builder._resolve_score_metric(None, row, "demand_score") is None


def test_build_context_includes_cluster_data() -> None:
    db = _session()
    _seed_keyword_and_score(db)
    db.add(ClusterAssignment(keyword_id=101, niche_id="1", cluster_id=9, run_id="run-1"))
    db.add(
        ClusterLabel(
            niche_id="1",
            cluster_id=9,
            run_id="run-1",
            label_text="Niche Positioning",
            keyword_count=7,
        )
    )
    db.commit()

    context = build_recommendation_context(keyword_id=101, niche_id="1", run_id="run-1", db=db)

    assert context is not None
    assert context.cluster_label == "Niche Positioning"
    assert context.cluster_size == 7
    db.close()


def test_build_context_handles_missing_competitor_profile() -> None:
    db = _session()
    _seed_keyword_and_score(db)

    context = build_recommendation_context(keyword_id=101, niche_id="1", run_id="run-1", db=db)

    assert context is not None
    assert context.top_competitor_weaknesses == []
    db.close()


def test_get_confidence_modifier_defaults_when_missing() -> None:
    db = _session()
    _seed_keyword_and_score(db, confidence_modifier=None)

    confidence = get_confidence_modifier(101, db)

    assert confidence == 0.5
    db.close()


def test_build_context_uses_search_result_titles_when_profile_missing() -> None:
    db = _session()
    _seed_keyword_and_score(db)
    gig = Gig(id=1, gig_url="https://fiverr.com/gigs/1", seller_username="seller_a", title="I will build automations")
    result = SearchResult(keyword_id=101, run_id="run-1", rank=1, gig_id=1, title="Search title fallback")
    db.add_all([gig, result])
    db.commit()

    context = build_recommendation_context(keyword_id=101, niche_id="1", run_id="run-1", db=db)

    assert context is not None
    assert context.top_competitor_weaknesses
    assert context.top_competitor_weaknesses[0]["gig_title"] == "I will build automations"
    db.close()


def test_build_context_falls_back_to_search_result_title() -> None:
    db = _session()
    _seed_keyword_and_score(db)
    result = SearchResult(
        keyword_id=101,
        run_id="run-1",
        rank=1,
        gig_id=None,
        title="Fallback search title",
    )
    db.add(result)
    db.commit()

    context = build_recommendation_context(keyword_id=101, niche_id="1", run_id="run-1", db=db)

    assert context is not None
    assert context.top_competitor_weaknesses[0]["gig_title"] == "Fallback search title"
    db.close()


def test_get_confidence_modifier_clamps_to_one() -> None:
    db = _session()
    _seed_keyword_and_score(db, confidence_modifier=1.8)

    confidence = get_confidence_modifier(101, db)

    assert confidence == 1.0
    db.close()


def test_get_confidence_modifier_clamps_to_zero() -> None:
    db = _session()
    _seed_keyword_and_score(db, confidence_modifier=-0.2)

    confidence = get_confidence_modifier(101, db)

    assert confidence == 0.0
    db.close()


def test_build_context_uses_niche_argument_when_lookup_missing() -> None:
    db = _session()
    _seed_keyword_and_score(db)
    db.query(Niche).delete()
    db.commit()

    context = build_recommendation_context(keyword_id=101, niche_id="custom-niche", run_id="run-1", db=db)

    assert context is not None
    assert context.niche_name == "custom-niche"
    db.close()


def test_recommendation_model() -> None:
    db = _session()
    _seed_keyword_and_score(db)
    row = Recommendation(
        keyword_id=101,
        run_id_text="run-ctx",
        recommendation_type="keyword_recommendation",
        recommendation_text="Recommend this keyword",
        generation_complete=True,
        final_score=81.0,
        llm_cost_usd=0.12,
        gig_titles=[{"title": "I will automate your workflows"}],
    )
    db.add(row)
    db.commit()

    persisted = db.query(Recommendation).filter(Recommendation.keyword_id == 101).first()
    assert persisted is not None
    assert persisted.run_id_text == "run-ctx"
    assert persisted.generation_complete is True
    assert persisted.final_score == 81.0
    assert isinstance(persisted.gig_titles, list)
    db.close()


def test_write_recommendation() -> None:
    db = _session()
    _seed_keyword_and_score(db)
    context = build_recommendation_context(keyword_id=101, niche_id="1", run_id="run-ctx", db=db)
    assert context is not None

    payload = {
        "generation_complete": True,
        "llm_cost_usd": 0.07,
        "gig_titles": [{"title": "I will automate your workflows"}],
        "tag_sets": [["python automation", "workflow automation", "api integration", "task scripts", "ops"]],
        "niche_viability": {"blunt_recommendation": "enter now"},
    }
    wrote = write_recommendation(101, "run-ctx", context, payload, db)
    assert wrote is True

    persisted = db.query(Recommendation).filter(Recommendation.keyword_id == 101).first()
    assert persisted is not None
    assert persisted.run_id_text == "run-ctx"
    assert persisted.generation_complete is True
    assert persisted.llm_cost_usd == 0.07
    assert persisted.niche_viability == {"blunt_recommendation": "enter now"}
    db.close()
