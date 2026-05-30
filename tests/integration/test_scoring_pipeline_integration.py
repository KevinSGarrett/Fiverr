"""End-to-end scoring pipeline integration coverage for Cycle 047."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from src.migrations.srdi_r8.run_srdi_r8_migrations import run_srdi_r8_migrations
from src.models import (
    Base,
    CompetitorProfile,
    ExternalSignal,
    Gig,
    GigQualityAnalysis,
    GigQualityScore,
    Keyword,
    KeywordScore,
    Niche,
    SearchResult,
    Seller,
)
from src.recommendations.context_builder import build_recommendation_context
from src.recommendations.eligibility import get_eligible_keywords, passes_recommendation_gates
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


def test_scoring_pipeline_kw3_equivalent_gets_weakness_via_run_id_fallback(integration_db: Session) -> None:
    keyword_id = _seed_keyword(
        integration_db,
        keyword_text="kw3-equivalent fallback",
        run_id="active-run",
        gig_count=1,
        with_links=True,
        with_gqa=False,
        with_reddit=False,
        with_trends=True,
    )
    top_row = (
        integration_db.query(SearchResult)
        .filter(SearchResult.keyword_id == keyword_id, SearchResult.rank == 1)
        .first()
    )
    assert top_row is not None and top_row.gig is not None
    keyword = integration_db.query(Keyword).filter(Keyword.id == keyword_id).first()
    assert keyword is not None and keyword.niche is not None
    integration_db.add(
        GigQualityAnalysis(
            gig_url=top_row.gig.gig_url,
            niche_id=keyword.niche.slug,
            run_id="cycle_older",
            rubric_score=15.0,
            video_absent=True,
            portfolio_absent=True,
            description_thin=True,
            faq_absent=False,
            thumbnail_quality_flag=False,
            weakness_flags=["video_absent", "portfolio_absent", "description_thin"],
        )
    )
    integration_db.commit()

    weakness_result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, integration_db)
    assert weakness_result.score_value is not None
    assert weakness_result.score_value > 0.0


def test_scoring_pipeline_multiple_keywords_with_mixed_weakness_coverage(integration_db: Session) -> None:
    kw_with_gqa = _seed_keyword(
        integration_db,
        keyword_text="kw with gqa",
        run_id="mixed-gqa",
        gig_count=2,
        with_links=True,
        with_gqa=True,
        with_reddit=False,
        with_trends=True,
    )
    kw_without_gqa = _seed_keyword(
        integration_db,
        keyword_text="kw without gqa",
        run_id="mixed-no-gqa",
        gig_count=0,
        with_links=True,
        with_gqa=False,
        with_reddit=False,
        with_trends=True,
    )

    with_gqa_payload = _run_pipeline(integration_db, kw_with_gqa)
    without_gqa_payload = _run_pipeline(integration_db, kw_without_gqa)

    assert with_gqa_payload["final_score"] is not None
    assert without_gqa_payload["final_score"] is not None
    assert with_gqa_payload["weakness_score"] is not None
    assert without_gqa_payload["weakness_score"] is None


def test_full_scoring_with_reddit_signal_improves_cm(integration_db: Session) -> None:
    kw_with_reddit = _seed_keyword(
        integration_db,
        keyword_text="reddit cm keyword",
        run_id="reddit-cm",
        gig_count=2,
        with_links=True,
        with_gqa=True,
        with_reddit=True,
        with_trends=True,
    )
    kw_without_reddit = _seed_keyword(
        integration_db,
        keyword_text="no reddit cm keyword",
        run_id="no-reddit-cm",
        gig_count=2,
        with_links=True,
        with_gqa=True,
        with_reddit=False,
        with_trends=True,
    )

    with_reddit_cm, with_reddit_breakdown = ConfidenceScoreModifier().calculate_with_breakdown(
        kw_with_reddit,
        run_context={
            "data_completeness_ratio": 1.0,
            "data_freshness_score": 1.0,
            "source_diversity_score": 1.0,
            "llm_analysis_completion_ratio": 1.0,
            "google_trends_available": True,
            "gig_detail_collected": True,
            "seller_profiles_collected": True,
            "reddit_signals_available": True,
            "llm_gig_quality_incomplete_count": 0.0,
            "llm_competitor_synthesis_failed": False,
            "mode": "standard",
        },
        db=integration_db,
    )
    without_reddit_cm, without_reddit_breakdown = ConfidenceScoreModifier().calculate_with_breakdown(
        kw_without_reddit,
        run_context={
            "data_completeness_ratio": 1.0,
            "data_freshness_score": 1.0,
            "source_diversity_score": 1.0,
            "llm_analysis_completion_ratio": 1.0,
            "google_trends_available": True,
            "gig_detail_collected": True,
            "seller_profiles_collected": True,
            "reddit_signals_available": False,
            "llm_gig_quality_incomplete_count": 0.0,
            "llm_competitor_synthesis_failed": False,
            "mode": "standard",
        },
        db=integration_db,
    )

    assert "missing_reddit_signals" not in with_reddit_breakdown
    assert without_reddit_breakdown["missing_reddit_signals"] == -0.05
    assert with_reddit_cm > without_reddit_cm


def _seed_keyword_with_custom_ows(
    session: Session,
    *,
    keyword_text: str,
    active_run_id: str,
    fallback_run_id: str | None,
    rubric_scores: list[float],
) -> int:
    niche = Niche(
        slug=f"{active_run_id}-custom-niche",
        name=f"{active_run_id} custom niche",
        category_path="Programming & Tech > AI",
    )
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
    for rank, rubric_score in enumerate(rubric_scores, start=1):
        gig_url = f"https://www.fiverr.com/{active_run_id}/custom-{rank}"
        seller = Seller(seller_handle=f"{active_run_id}_custom_{rank}", level="Level 1")
        session.add(seller)
        session.flush()
        gig = Gig(
            gig_url=gig_url,
            keyword_id=keyword.id,
            run_id=active_run_id,
            seller_id=seller.id,
            seller_username=seller.seller_handle,
            title=f"{active_run_id} custom gig {rank}",
            normalized_title=f"{active_run_id} custom gig {rank}",
            position=rank,
            starting_price=75.0 + rank,
            review_count=rank,
            metadata_json={"has_video": True, "has_portfolio": True},
        )
        session.add(gig)
        session.flush()
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id=active_run_id,
                rank=rank,
                gig_id=gig.id,
                title=f"{active_run_id} custom result {rank}",
                gig_cards=[{"position": rank, "gig_url": gig_url}],
                total_result_count=1100 + rank,
            )
        )
        if fallback_run_id is not None:
            session.add(
                GigQualityAnalysis(
                    gig_url=gig_url,
                    niche_id=niche.slug,
                    run_id=fallback_run_id,
                    rubric_score=rubric_score,
                    video_absent=False,
                    portfolio_absent=False,
                    description_thin=False,
                    faq_absent=False,
                    thumbnail_quality_flag=False,
                    weakness_flags=[],
                )
            )
        else:
            session.add(
                GigQualityAnalysis(
                    gig_url=gig_url,
                    niche_id=niche.slug,
                    run_id=active_run_id,
                    rubric_score=rubric_score,
                    video_absent=False,
                    portfolio_absent=False,
                    description_thin=False,
                    faq_absent=False,
                    thumbnail_quality_flag=False,
                    weakness_flags=[],
                )
            )
    session.commit()
    return keyword.id


def test_weakness_combined_state_kw96_equivalent_is_consistent_with_isolation(integration_db: Session) -> None:
    keyword_id = _seed_keyword_with_custom_ows(
        integration_db,
        keyword_text="kw96 combined consistency",
        active_run_id="kw96-combined",
        fallback_run_id=None,
        rubric_scores=[50.0, 55.0, 0.0, 40.0],
    )
    weakness_result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, integration_db)
    assert weakness_result.score_value is not None
    assert weakness_result.score_value < 100.0
    overall = weakness_result.score_components["overall_weakness_score"].value
    assert abs(overall - 63.75) < 0.35


def test_weakness_multi_run_fallback_consistent_before_after_enrichment(integration_db: Session) -> None:
    keyword_id = _seed_keyword_with_custom_ows(
        integration_db,
        keyword_text="kw96 fallback consistency",
        active_run_id="kw96-active-empty",
        fallback_run_id="kw96-older-run",
        rubric_scores=[45.0, 0.0, 52.0],
    )
    weakness_result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, integration_db)
    assert weakness_result.score_value is not None
    overall = weakness_result.score_components["overall_weakness_score"].value
    assert weakness_result.score_value < 100.0
    assert 65.0 <= overall <= 70.0


def test_kw110_equivalent_conditional_go_keyword_is_eligible_for_recommendations(integration_db: Session) -> None:
    niche = Niche(id=999, slug="kw110-niche", name="kw110 niche", category_path="Programming & Tech > AI")
    keyword = Keyword(
        id=110,
        niche_id=999,
        keyword="AI chatbot handoff",
        normalized_keyword="AI chatbot handoff",
    )
    score = KeywordScore(
        keyword_id=110,
        scoring_profile="aggressive_new_seller",
        score_depth="standard",
        demand_score=41.69,
        competition_score=56.84,
        opportunity_score=42.28,
        feasibility_score=78.04,
        final_score=61.0,
        confidence_modifier=1.0,
        tag="CONDITIONAL GO",
    )
    integration_db.add_all([niche, keyword, score])
    integration_db.add(
        GigQualityScore(
            keyword_id=110,
            gig_url="https://fiverr.com/gig/110",
            run_id="run-110",
            analysis_complete=True,
        )
    )
    integration_db.commit()

    config = {
        "recommendations": {
            "min_tag": "CONDITIONAL GO",
            "niches": {"999": {"recommendation_generation": True}},
        }
    }
    eligible = get_eligible_keywords("run-110", integration_db, config)
    assert len(eligible) > 0
    gate_ok, gate_reason = passes_recommendation_gates(eligible[0], integration_db)
    assert gate_ok is True
    assert gate_reason == "All gates passed"


def test_first_recommendation_context_has_all_required_fields(integration_db: Session) -> None:
    niche = Niche(id=1001, slug="context-niche", name="context niche", category_path="Programming & Tech > AI")
    keyword = Keyword(
        id=2110,
        niche_id=1001,
        keyword="context keyword",
        normalized_keyword="context keyword",
    )
    score = KeywordScore(
        keyword_id=2110,
        scoring_profile="aggressive_new_seller",
        score_depth="standard",
        demand_score=44.0,
        competition_score=55.0,
        opportunity_score=48.0,
        feasibility_score=72.0,
        saturation_score=31.0,
        final_score=61.0,
        confidence_modifier=1.0,
        tag="CONDITIONAL GO",
    )
    integration_db.add_all([niche, keyword, score])
    integration_db.commit()

    context = build_recommendation_context(keyword_id=2110, niche_id=1001, run_id="context-run", db=integration_db)
    assert context is not None
    assert context.keyword_id == 2110
    assert context.keyword_text == "context keyword"
    assert context.niche_id == 1001
    assert context.tag in {"CONDITIONAL GO", "MONITOR"}
    assert context.final_score == 61.0
    assert context.confidence_modifier == 1.0
    assert context.demand_score == 44.0
    assert context.competition_score == 55.0
    assert context.opportunity_score == 48.0
    assert isinstance(context.top_competitor_weaknesses, list)
    assert context.cluster_label is None or isinstance(context.cluster_label, str)
    assert context.cluster_size is None or isinstance(context.cluster_size, int)
    assert context.saturation_score == 31.0
    assert context.feasibility_score == 72.0


def test_kw110_reaches_conditional_go_with_reddit_signal(integration_db: Session) -> None:
    keyword_id = _seed_keyword(
        integration_db,
        keyword_text="kw110 reddit signal uplift",
        run_id="kw110-reddit-signal",
        gig_count=1,
        with_links=True,
        with_gqa=False,
        with_reddit=False,
        with_trends=True,
    )
    integration_db.add(
        ExternalSignal(
            signal_type="reddit_demand",
            keyword_id=keyword_id,
            collection_method="reddit_devvit_bridge",
            signal_json={"post_count_90d": 3, "reddit_demand_intent_score": 8.0},
            signal_value=8.0,
            run_id="kw110-reddit-signal",
        )
    )
    integration_db.commit()

    cm = ConfidenceScoreModifier().calculate(keyword_id, run_context=None, db=integration_db)
    assert cm == 1.0
    scores = {
        "demand_score": 41.69,
        "competition_score": 56.84,
        "opportunity_score": 42.28,
        "feasibility_score": 78.04,
        "profitability_score": 36.13,
        "intent_score": 47.14,
        "saturation_score": None,
        "weakness_score": 100.0,
        "trend_score": None,
    }
    composite, _ = calculate_weighted_composite(scores, SCORING_PROFILES["aggressive_new_seller"])
    final_score = calculate_final_score(composite, cm)
    assert final_score >= 60.0
    assert assign_tag(final_score, cm) == "CONDITIONAL_GO"


def test_kw96_weakness_not_regressed_by_srdi_schema(integration_db: Session) -> None:
    run_srdi_r8_migrations(engine=cast(Engine, integration_db.get_bind()))
    keyword_id = _seed_keyword(
        integration_db,
        keyword_text="kw96 weakness fallback consistency",
        run_id="kw96-srdi-schema",
        gig_count=0,
        with_links=False,
        with_gqa=False,
        with_reddit=False,
        with_trends=False,
    )
    integration_db.add(
        KeywordScore(
            keyword_id=keyword_id,
            final_score=51.2,
            weakness_score=100.0,
            score_components={},
            tag="MONITOR",
            scored_at=datetime.now(UTC),
        )
    )
    integration_db.add(
        KeywordScore(
            keyword_id=keyword_id,
            final_score=51.2,
            weakness_score=53.52,
            score_components={},
            tag="MONITOR",
            scored_at=datetime.now(UTC) + timedelta(seconds=1),
        )
    )
    integration_db.commit()
    result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, integration_db)
    assert result.score_value is not None
    assert result.score_value == pytest.approx(53.52, abs=2.0)
