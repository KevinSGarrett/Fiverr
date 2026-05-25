"""Integration tests for SQLAlchemy-backed scoring calculator paths."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import (
    Base,
    ExternalSignal,
    Gig,
    GigVisualAnalysis,
    Keyword,
    Niche,
    SaturationScore,
    SearchResult,
    Seller,
)
from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.confidence import ConfidenceScoreModifier
from src.scoring.demand import DemandScoreCalculator
from src.scoring.feasibility import NewSellerFeasibilityCalculator
from src.scoring.intent import ConversionIntentScoreCalculator
from src.scoring.opportunity import OpportunityScoreCalculator
from src.scoring.orchestrator import ScoringOrchestrator
from src.scoring.pipeline import SCORING_PROFILES, calculate_weighted_composite
from src.scoring.profitability import ProfitabilityScoreCalculator
from src.scoring.saturation_score import SaturationScoreCalculator, get_saturation_signal
from src.scoring.trend import TrendScoreCalculator
from src.scoring.weakness import GigQualityWeaknessScoreCalculator


def _session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def _seed_keyword_data(session: Session) -> int:
    niche = Niche(slug="automation", name="Automation", category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automation",
        normalized_keyword="python automation",
        metadata_json={"autocomplete_position": 2, "intent_classification": "HIGH_INTENT"},
    )
    session.add(keyword)
    session.flush()

    for rank in range(1, 11):
        seller = Seller(
            seller_handle=f"seller_{rank}",
            level="Level 1" if rank <= 5 else "Level 2",
            metadata_json={"is_pro": rank in {1, 2}},
        )
        session.add(seller)
        session.flush()
        gig = Gig(
            seller_id=seller.id,
            title=f"I will automate task {rank}",
            normalized_title=f"automate task {rank if rank <= 8 else 8}",
            starting_price=30.0 + rank,
            review_count=50 + (rank * 20),
            metadata_json={
                "premium_price": 120.0 + rank,
                "delivery_time_days": 1 + (rank % 3),
                "extras": [{"name": "fast_delivery"}] if rank % 2 == 0 else [],
                "has_portfolio": rank % 3 != 0,
            },
        )
        session.add(gig)
        session.flush()
        search_result = SearchResult(
            keyword_id=keyword.id,
            rank=rank,
            gig_id=gig.id,
            title=gig.title,
        )
        session.add(search_result)
        if rank <= 6:
            session.add(GigVisualAnalysis(gig_id=gig.id, has_video=(rank % 2 == 0)))

    session.add(
        ExternalSignal(
            source_name="google",
            signal_type="google_trends",
            keyword_id=keyword.id,
            raw_value_json={
                "trends_12mo_score": 64,
                "trends_3mo_score": 70,
                "trends_3mo_avg": 68,
                "trends_12mo_avg": 60,
                "google_trends_12mo_series": [45, 48, 50, 54, 58, 62, 64, 66, 67, 68, 69, 70],
                "google_trends_3mo_series": [66, 68, 70],
            },
            normalized_value=64.0,
        )
    )
    session.add(
        ExternalSignal(
            source_name="reddit",
            signal_type="reddit_demand",
            keyword_id=keyword.id,
            raw_value_json={
                "reddit_demand_intent_score": 7.5,
                "reddit_recent_post_volume": 20,
                "reddit_historical_post_volume": 15,
                "reddit_activity_trend_score": 62,
            },
            normalized_value=7.5,
        )
    )
    session.commit()
    return keyword.id


def _seed_keyword_data_without_search_links(session: Session) -> int:
    niche = Niche(slug="automation-fallback", name="Automation Fallback", category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automation fallback",
        normalized_keyword="python automation fallback",
    )
    session.add(keyword)
    session.flush()

    for rank in range(1, 4):
        seller = Seller(
            seller_handle=f"fallback_seller_{rank}",
            level="Level 1",
            metadata_json={"is_pro": False},
        )
        session.add(seller)
        session.flush()
        session.add(
            Gig(
                gig_url=f"https://www.fiverr.com/fallback/{rank}",
                keyword_id=keyword.id,
                run_id="fallback-run",
                seller_id=seller.id,
                seller_username=seller.seller_handle,
                title=f"Fallback gig {rank}",
                normalized_title=f"fallback gig {rank}",
                position=rank,
                starting_price=75.0 + rank,
                review_count=20 + rank,
                metadata_json={
                    "premium_price": 150.0 + rank,
                    "delivery_time_days": float(rank),
                    "extras": [{"name": "fast_delivery"}],
                    "has_video": rank % 2 == 0,
                    "has_portfolio": rank % 2 == 1,
                },
            )
        )

    session.commit()
    return keyword.id


def _seed_keyword_data_without_search_links_mixed_runs(session: Session) -> int:
    niche = Niche(
        slug="automation-fallback-mixed",
        name="Automation Fallback Mixed",
        category_path="Programming & Tech > AI",
    )
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automation run scoped fallback",
        normalized_keyword="python automation run scoped fallback",
    )
    session.add(keyword)
    session.flush()

    for rank in range(1, 3):
        stale_seller = Seller(
            seller_handle=f"stale_run_seller_{rank}",
            level="Level 2",
            metadata_json={"is_pro": True},
        )
        session.add(stale_seller)
        session.flush()
        session.add(
            Gig(
                gig_url=f"https://www.fiverr.com/stale/{rank}",
                keyword_id=keyword.id,
                run_id="stale-run",
                seller_id=stale_seller.id,
                seller_username=stale_seller.seller_handle,
                title=f"Stale run gig {rank}",
                normalized_title=f"stale run gig {rank}",
                position=rank,
                starting_price=800.0 + rank,
                review_count=500 + rank,
                metadata_json={
                    "premium_price": 1200.0 + rank,
                    "delivery_time_days": 30.0,
                    "extras": [],
                    "has_video": False,
                    "has_portfolio": False,
                },
            )
        )

        active_seller = Seller(
            seller_handle=f"active_run_seller_{rank}",
            level="Level 1",
            metadata_json={"is_pro": False},
        )
        session.add(active_seller)
        session.flush()
        session.add(
            Gig(
                gig_url=f"https://www.fiverr.com/active/{rank}",
                keyword_id=keyword.id,
                run_id="active-run",
                seller_id=active_seller.id,
                seller_username=active_seller.seller_handle,
                title=f"Active run gig {rank}",
                normalized_title=f"active run gig {rank}",
                position=rank,
                starting_price=20.0 + rank,
                review_count=10 + rank,
                metadata_json={
                    "premium_price": 40.0 + rank,
                    "delivery_time_days": 2.0,
                    "extras": [{"name": "extra"}],
                    "has_video": True,
                    "has_portfolio": True,
                },
            )
        )

    for rank in range(1, 3):
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id="active-run",
                rank=rank,
                title=f"Active unlinked result {rank}",
                gig_id=None,
            )
        )

    session.commit()
    return keyword.id


def test_demand_calculator_sqlalchemy_path_returns_score() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    result = DemandScoreCalculator().calculate(keyword_id, session)
    assert result.score_value is not None
    session.close()


def test_competition_calculator_sqlalchemy_path_returns_score() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    result = CompetitionScoreCalculator().calculate(keyword_id, session)
    assert result.score_value is not None
    session.close()


def test_opportunity_calculator_sqlalchemy_path_returns_score() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    result = OpportunityScoreCalculator().calculate(keyword_id, session)
    assert result.score_value is not None
    session.close()


def test_feasibility_calculator_sqlalchemy_path_returns_score() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    result = NewSellerFeasibilityCalculator().calculate(keyword_id, session)
    assert result.score_value is not None
    session.close()


def test_profitability_calculator_sqlalchemy_path_returns_score() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    result = ProfitabilityScoreCalculator().calculate(keyword_id, session)
    assert result.score_value is not None
    session.close()


def test_intent_saturation_weakness_trend_sqlalchemy_paths_return_scores() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    assert ConversionIntentScoreCalculator().calculate(keyword_id, session).score_value is not None
    assert SaturationScoreCalculator().calculate(keyword_id, session).score_value is not None
    assert GigQualityWeaknessScoreCalculator().calculate(keyword_id, session).score_value is not None
    assert TrendScoreCalculator().calculate(keyword_id, session).score_value is not None
    session.close()


def test_scoring_calculators_fallback_to_keyword_gigs_without_search_result_links() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_without_search_links(session)

    feasibility_result = NewSellerFeasibilityCalculator().calculate(keyword_id, session)
    profitability_result = ProfitabilityScoreCalculator().calculate(keyword_id, session)
    weakness_result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)

    assert feasibility_result.score_value is not None
    assert profitability_result.score_value is not None
    assert weakness_result.score_value is not None
    session.close()


# pylint: disable=protected-access
def test_scoring_fallback_queries_scope_to_active_run_id() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_without_search_links_mixed_runs(session)

    feasibility_signals = NewSellerFeasibilityCalculator()._load_signals_from_db(keyword_id, session)
    profitability_signals = ProfitabilityScoreCalculator()._load_signals_from_db(keyword_id, session)
    weakness_signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)

    assert feasibility_signals["top10_prices"] == [21.0, 22.0]
    assert profitability_signals["avg_starting_price_top10"] == 21.5
    assert weakness_signals["top10_has_video"] == [True, True]
    assert weakness_signals["top10_has_portfolio"] == [True, True]
    session.close()


def test_confidence_modifier_sqlalchemy_context_returns_clamped_value() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    modifier = ConfidenceScoreModifier().calculate(keyword_id, None, session)
    assert 0.0 <= modifier <= 1.0
    session.close()


def test_orchestrator_run_with_sqlalchemy_session_returns_result() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    run_result = ScoringOrchestrator().run([keyword_id], session)
    assert run_result.keyword_results
    assert run_result.keyword_results[0]["final_payload"]["final_score"] >= 0.0
    session.close()


def test_dict_proxy_path_still_works_after_sqlalchemy_changes() -> None:
    keyword_id = 999
    db_proxy = {
        keyword_id: {
            "total_result_count": 800,
            "autocomplete_position": 1,
            "trends_12mo_score": 60,
            "reddit_demand_intent_score": 7.0,
        }
    }
    result = DemandScoreCalculator().calculate(keyword_id, db_proxy)
    assert result.score_value is not None


def test_missing_keyword_id_returns_none_score_gracefully() -> None:
    session = next(_session())
    result = DemandScoreCalculator().calculate(123456, session)
    assert result.score_value is None
    session.close()


def test_saturation_signal_reads_from_analysis_table() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    session.add(
        SaturationScore(
            keyword_id=keyword_id,
            niche_id="automation",
            run_id="legacy",
            saturation_score=77.5,
            count_score=80.0,
            title_dup_score=75.0,
            price_score=70.0,
            overlap_score=65.0,
            llm_class_score=60.0,
            title_duplication_rate=0.75,
            price_compression_rate=0.7,
            seller_overlap_rate=0.65,
            explanation_text="integration test",
        )
    )
    session.commit()

    assert get_saturation_signal(keyword_id, "legacy", session) == 77.5
    session.close()


def test_saturation_signal_none_when_no_row() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    assert get_saturation_signal(keyword_id, "legacy", session) is None
    session.close()


def test_saturation_signal_does_not_fallback_to_different_run() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    session.add(
        SaturationScore(
            keyword_id=keyword_id,
            niche_id="automation",
            run_id="old-run",
            saturation_score=81.0,
            count_score=80.0,
            title_dup_score=75.0,
            price_score=70.0,
            overlap_score=65.0,
            llm_class_score=60.0,
            title_duplication_rate=0.75,
            price_compression_rate=0.7,
            seller_overlap_rate=0.65,
            explanation_text="old run only",
        )
    )
    session.commit()

    assert get_saturation_signal(keyword_id, "current-run", session) is None
    assert get_saturation_signal(keyword_id, "", session) == 81.0
    session.close()


def test_saturation_signal_non_session_paths_handle_valid_and_invalid_values() -> None:
    class _SignalProvider:
        @staticmethod
        def get_saturation_signal(_keyword_id: int, _run_id: str) -> str:
            return "66.5"

    class _BadSignalProvider:
        @staticmethod
        def get_saturation_signal(_keyword_id: int, _run_id: str) -> str:
            return "not-a-number"

    class _InputsProvider:
        @staticmethod
        def get_saturation_inputs(_keyword_id: int) -> dict[str, float]:
            return {"saturation_score": 72.0}

    assert get_saturation_signal(101, "run-a", _SignalProvider()) == 66.5
    assert get_saturation_signal(101, "run-a", _BadSignalProvider()) is None
    assert get_saturation_signal(101, "run-a", _InputsProvider()) == 72.0
    assert get_saturation_signal(101, "run-a", {101: {"saturation_score": 55.0}}) == 55.0


def test_saturation_calculator_uses_mapping_run_id_for_analysis_output() -> None:
    db_proxy = {
        701: {
            "run_id": "run-map-701",
            "saturation_score": 73.4,
        }
    }
    result = SaturationScoreCalculator().calculate(
        701,
        db_proxy,
        config={"scoring": {"saturation": {"use_analysis_output": True}}},
    )
    assert result.score_value == 73.4
    assert "saturation_scores.saturation_score[run-map-701]" in result.source_evidence


def test_saturation_score_resolver_fallback_paths() -> None:
    calculator = SaturationScoreCalculator()
    assert calculator._resolve_title_duplication_score({"duplicate_title_count_top30": 12.0}) == 40.0
    assert calculator._resolve_price_compression_score({"price_diversity_top30": 0.25}) == 75.0
    assert calculator._resolve_llm_saturation_assessment({"llm_saturation_assessment": 6.4}) == 6.4


def test_saturation_normalization_and_price_compression_helpers() -> None:
    assert SaturationScoreCalculator._normalize_total_gig_count(0) == 0.0
    assert SaturationScoreCalculator._normalize_ratio_or_score(0.5) == 50.0
    assert SaturationScoreCalculator._normalize_ratio_or_score(6.0) == 60.0
    assert SaturationScoreCalculator._normalize_ratio_or_score(140.0) == 100.0
    assert SaturationScoreCalculator._price_compression_ratio([20.0, 20.0]) == 1.0
    assert SaturationScoreCalculator._price_compression_ratio([10.0]) is None


def test_saturation_score_inverted_correctly_in_composite() -> None:
    common_scores = {
        "demand_score": 70.0,
        "competition_score": 40.0,
        "opportunity_score": 65.0,
        "feasibility_score": 60.0,
        "profitability_score": 55.0,
        "intent_score": 50.0,
        "weakness_score": 45.0,
        "trend_score": 60.0,
    }
    low_saturation_scores = {**common_scores, "saturation_score": 10.0}
    high_saturation_scores = {**common_scores, "saturation_score": 90.0}

    low_value, _ = calculate_weighted_composite(low_saturation_scores, SCORING_PROFILES["default"])
    high_value, _ = calculate_weighted_composite(high_saturation_scores, SCORING_PROFILES["default"])
    assert low_value > high_value
