"""End-to-end scoring pipeline integration coverage for Cycle 047."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import (
    Base,
    CompetitorProfile,
    ExternalSignal,
    Gig,
    GigQualityAnalysis,
    Keyword,
    Niche,
    SearchResult,
    Seller,
)
from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.confidence import ConfidenceScoreModifier
from src.scoring.demand import DemandScoreCalculator
from src.scoring.feasibility import NewSellerFeasibilityCalculator
from src.scoring.intent import ConversionIntentScoreCalculator
from src.scoring.opportunity import OpportunityScoreCalculator
from src.scoring.pipeline import (
    SCORING_PROFILES,
    assign_tag,
    calculate_final_score,
    calculate_weighted_composite,
)
from src.scoring.profitability import ProfitabilityScoreCalculator
from src.scoring.saturation_score import SaturationScoreCalculator
from src.scoring.trend import TrendScoreCalculator
from src.scoring.weakness import GigQualityWeaknessScoreCalculator


def _seed_keyword(
    session: Session,
    *,
    keyword_text: str,
    run_id: str,
    gig_count: int,
    with_links: bool,
    with_gqa: bool,
    with_reddit: bool,
    with_trends: bool,
) -> int:
    niche = Niche(slug=f"{run_id}-niche", name=f"{run_id} niche", category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword=keyword_text,
        normalized_keyword=keyword_text,
        metadata_json={"autocomplete_position": 2, "intent_classification": "HIGH_INTENT"},
    )
    session.add(keyword)
    session.flush()

    for rank in range(1, gig_count + 1):
        seller = Seller(seller_handle=f"{run_id}_seller_{rank}", level="Level 1")
        session.add(seller)
        session.flush()
        gig_url = f"https://www.fiverr.com/{run_id}/gig-{rank}"
        gig = Gig(
            gig_url=gig_url,
            keyword_id=keyword.id,
            run_id=run_id,
            seller_id=seller.id,
            seller_username=seller.seller_handle,
            title=f"{run_id} gig {rank}",
            normalized_title=f"{run_id} gig {rank}",
            position=rank,
            starting_price=100.0 + rank,
            review_count=rank,
            metadata_json={
                "premium_price": 160.0 + rank,
                "delivery_time_days": 3.0,
                "extras": [{"name": "fast_delivery"}],
                "has_video": False,
                "has_portfolio": False,
            },
        )
        session.add(gig)
        session.flush()
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id=run_id,
                rank=rank,
                gig_id=gig.id if with_links else None,
                title=f"{run_id} result {rank}",
                gig_cards=[{"position": rank, "gig_url": gig_url}] if not with_links else None,
                total_result_count=1200 + rank,
            )
        )
        if with_gqa:
            session.add(
                GigQualityAnalysis(
                    gig_url=gig_url,
                    niche_id=niche.slug,
                    run_id=run_id,
                    rubric_score=0.0,
                    video_absent=True,
                    portfolio_absent=True,
                    description_thin=True,
                    faq_absent=True,
                    thumbnail_quality_flag=False,
                    weakness_flags=["video_absent", "portfolio_absent", "description_thin", "faq_absent"],
                )
            )

    session.add(
        CompetitorProfile(
            niche_id=niche.slug,
            run_id=run_id,
            top_gig_count=max(1, gig_count),
            seller_level_distribution={"LEVEL_1": 1.0},
            new_seller_gap={
                "gap_flags": ["LOW_VIDEO_PRESENCE", "LOW_PORTFOLIO_PRESENCE", "HIGH_PRICE_VARIANCE"]
            },
        )
    )

    if with_trends:
        session.add(
            ExternalSignal(
                source_name="google",
                signal_type="google_trends",
                keyword_id=keyword.id,
                raw_value_json={"trends_12mo_score": 72, "trends_3mo_score": 75, "trends_3mo_avg": 70, "trends_12mo_avg": 60},
                normalized_value=72.0,
            )
        )
    if with_reddit:
        session.add(
            ExternalSignal(
                source_name="reddit",
                signal_type="reddit_demand",
                keyword_id=keyword.id,
                raw_value_json={"reddit_demand_intent_score": 7.5, "reddit_recent_post_volume": 30, "reddit_historical_post_volume": 20},
                normalized_value=7.5,
            )
        )

    session.commit()
    return keyword.id


def _run_pipeline(session: Session, keyword_id: int) -> dict[str, float | str | None]:
    demand = DemandScoreCalculator().calculate(keyword_id, session)
    competition = CompetitionScoreCalculator().calculate(keyword_id, session)
    opportunity = OpportunityScoreCalculator().calculate(keyword_id, session, demand_result=demand, competition_result=competition)
    feasibility = NewSellerFeasibilityCalculator().calculate(keyword_id, session)
    profitability = ProfitabilityScoreCalculator().calculate(keyword_id, session)
    intent = ConversionIntentScoreCalculator().calculate(keyword_id, session)
    saturation = SaturationScoreCalculator().calculate(keyword_id, session)
    weakness = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
    trend = TrendScoreCalculator().calculate(keyword_id, session)

    scores = {
        "demand_score": demand.score_value,
        "competition_score": competition.score_value,
        "opportunity_score": opportunity.score_value,
        "feasibility_score": feasibility.score_value,
        "profitability_score": profitability.score_value,
        "intent_score": intent.score_value,
        "saturation_score": saturation.score_value,
        "weakness_score": weakness.score_value,
        "trend_score": trend.score_value,
    }
    confidence_context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": scores["trend_score"] is not None,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": True,
        "llm_gig_quality_incomplete_count": 0,
        "llm_competitor_synthesis_failed": False,
        "data_age_hours": 0.0,
        "data_ttl_hours": 168.0,
        "mode": "standard",
    }
    cm = ConfidenceScoreModifier().calculate(keyword_id, confidence_context, session)
    composite, _ = calculate_weighted_composite(scores, SCORING_PROFILES["aggressive_new_seller"])
    final_score = calculate_final_score(composite, cm)
    tag = assign_tag(final_score, cm)
    return {
        "final_score": final_score,
        "feasibility_score": scores["feasibility_score"],
        "weakness_score": scores["weakness_score"],
        "confidence_modifier": cm,
        "tag": tag,
    }


@pytest.fixture
def integration_db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = factory()
    try:
        yield session
    finally:
        session.close()


def test_full_scoring_pipeline_produces_non_none_final_score(integration_db: Session) -> None:
    keyword_id = _seed_keyword(
        integration_db,
        keyword_text="full scoring keyword",
        run_id="full-pipeline",
        gig_count=5,
        with_links=True,
        with_gqa=True,
        with_reddit=True,
        with_trends=True,
    )
    payload = _run_pipeline(integration_db, keyword_id)
    assert payload["final_score"] is not None
    assert 0.0 <= float(payload["final_score"]) <= 100.0


def test_scoring_pipeline_feasibility_above_80_when_gig_fully_priced(integration_db: Session) -> None:
    keyword_id = _seed_keyword(
        integration_db,
        keyword_text="feasibility keyword",
        run_id="feasibility-pipeline",
        gig_count=5,
        with_links=True,
        with_gqa=True,
        with_reddit=True,
        with_trends=True,
    )
    payload = _run_pipeline(integration_db, keyword_id)
    assert float(payload["feasibility_score"]) >= 80.0


def test_scoring_pipeline_weakness_above_60_when_ows_high(integration_db: Session) -> None:
    keyword_id = _seed_keyword(
        integration_db,
        keyword_text="weakness keyword",
        run_id="weakness-pipeline",
        gig_count=5,
        with_links=True,
        with_gqa=True,
        with_reddit=True,
        with_trends=True,
    )
    payload = _run_pipeline(integration_db, keyword_id)
    assert float(payload["weakness_score"]) >= 60.0


def test_scoring_pipeline_cm_above_0_80_when_data_complete(integration_db: Session) -> None:
    keyword_id = _seed_keyword(
        integration_db,
        keyword_text="cm keyword",
        run_id="cm-pipeline",
        gig_count=5,
        with_links=True,
        with_gqa=True,
        with_reddit=True,
        with_trends=True,
    )
    payload = _run_pipeline(integration_db, keyword_id)
    assert float(payload["confidence_modifier"]) >= 0.80


def test_scoring_pipeline_tag_assigned_correctly(integration_db: Session) -> None:
    keyword_id = _seed_keyword(
        integration_db,
        keyword_text="tag keyword",
        run_id="tag-pipeline",
        gig_count=5,
        with_links=True,
        with_gqa=True,
        with_reddit=True,
        with_trends=True,
    )
    payload = _run_pipeline(integration_db, keyword_id)
    assert payload["tag"] in {"CONDITIONAL_GO", "STRONG_GO"}


def test_scoring_pipeline_does_not_crash_with_minimal_data(integration_db: Session) -> None:
    keyword_id = _seed_keyword(
        integration_db,
        keyword_text="minimal keyword",
        run_id="minimal-pipeline",
        gig_count=0,
        with_links=False,
        with_gqa=False,
        with_reddit=False,
        with_trends=False,
    )
    payload = _run_pipeline(integration_db, keyword_id)
    assert payload["final_score"] is not None
    assert isinstance(payload["final_score"], float)
