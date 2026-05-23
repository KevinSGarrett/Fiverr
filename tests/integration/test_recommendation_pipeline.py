"""Integration test for Stage 13 context + gate flow."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.models import (
    Base,
    ClusterAssignment,
    ClusterLabel,
    CompetitorProfile,
    GigQualityScore,
    Keyword,
    KeywordScore,
    Niche,
)
from src.recommendations.context_builder import build_recommendation_context
from src.recommendations.eligibility import passes_recommendation_gates


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)()


def test_recommendation_pipeline_context_and_gate_pass() -> None:
    db = _session()
    db.add(Niche(id=1, slug="automation", name="Automation", category_path="programming-tech/automation"))
    db.add(
        Keyword(
            id=101,
            niche_id=1,
            keyword="python automation",
            normalized_keyword="python automation",
        )
    )
    db.add(
        KeywordScore(
            keyword_id=101,
            scoring_profile="default",
            score_depth="standard",
            demand_score=75.0,
            competition_score=40.0,
            opportunity_score=70.0,
            feasibility_score=66.0,
            saturation_score=35.0,
            final_score=82.0,
            confidence_modifier=0.88,
            tag="STRONG GO",
        )
    )
    db.add(ClusterAssignment(keyword_id=101, niche_id="1", cluster_id=3, run_id="run-int-1"))
    db.add(
        ClusterLabel(
            niche_id="1",
            cluster_id=3,
            run_id="run-int-1",
            label_text="Automation Workflows",
            keyword_count=9,
        )
    )
    db.add(
        CompetitorProfile(
            niche_id="1",
            run_id="run-int-1",
            top_gig_count=5,
            new_seller_gap={
                "top_competitor_weaknesses": [
                    {"gig_title": "I will automate business workflows", "weaknesses": [{"weakness": "slow turnaround"}]}
                ]
            },
        )
    )
    db.add(
        GigQualityScore(
            keyword_id=101,
            gig_url="https://fiverr.com/gig/1",
            run_id="run-int-1",
            analysis_complete=True,
        )
    )
    db.commit()

    context = build_recommendation_context(keyword_id=101, niche_id="1", run_id="run-int-1", db=db)
    assert context is not None
    assert context.keyword_text == "python automation"
    assert context.cluster_label == "Automation Workflows"
    assert context.cluster_size == 9
    assert context.top_competitor_weaknesses

    passes, reason = passes_recommendation_gates(
        {
            "keyword_id": context.keyword_id,
            "confidence_modifier": context.confidence_modifier,
            "demand_score": context.demand_score,
        },
        db,
    )
    assert passes is True
    assert reason == "All gates passed"
    db.close()
