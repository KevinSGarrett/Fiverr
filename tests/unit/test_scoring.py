"""Unit tests for S4.1/S4.2/S4.3 scoring calculators."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest
from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.confidence import ConfidenceScoreModifier
from src.scoring.contracts import ScoringInput
from src.scoring.demand import DemandScoreCalculator
from src.scoring.feasibility import (
    NewSellerFeasibilityCalculator,
    _coerce_float,
    _extract_gap_flags_from_profile,
    _feasibility_config,
    _get_feasibility_gap_signal_details,
    _normalize_gap_flags,
    get_feasibility_gap_signal,
)
from src.scoring.final import FinalRecommendationScoreCalculator
from src.scoring.intent import ConversionIntentScoreCalculator
from src.scoring.opportunity import OpportunityScoreCalculator
from src.scoring.orchestrator import ScoringOrchestrator
from src.scoring.profitability import ProfitabilityScoreCalculator
from src.scoring.ranking import KeywordRanker
from src.scoring.saturation_score import SaturationScoreCalculator
from src.scoring.trend import TrendScoreCalculator
from src.scoring.weakness import GigQualityWeaknessScoreCalculator


class FakeScoringDB:
    """Simple in-memory signal source for scoring tests."""

    def __init__(
        self,
        demand_inputs: dict[int, dict[str, Any]] | None = None,
        competition_inputs: dict[int, dict[str, Any]] | None = None,
        feasibility_inputs: dict[int, dict[str, Any]] | None = None,
        profitability_inputs: dict[int, dict[str, Any]] | None = None,
        intent_inputs: dict[int, dict[str, Any]] | None = None,
        saturation_inputs: dict[int, dict[str, Any]] | None = None,
        weakness_inputs: dict[int, dict[str, Any]] | None = None,
        trend_inputs: dict[int, dict[str, Any]] | None = None,
        confidence_inputs: dict[int, dict[str, Any]] | None = None,
        final_inputs: dict[int, dict[str, Any]] | None = None,
    ) -> None:
        self._demand_inputs = demand_inputs or {}
        self._competition_inputs = competition_inputs or {}
        self._feasibility_inputs = feasibility_inputs or {}
        self._profitability_inputs = profitability_inputs or {}
        self._intent_inputs = intent_inputs or {}
        self._saturation_inputs = saturation_inputs or {}
        self._weakness_inputs = weakness_inputs or {}
        self._trend_inputs = trend_inputs or {}
        self._confidence_inputs = confidence_inputs or {}
        self._final_inputs = final_inputs or {}

    def get_demand_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._demand_inputs.get(keyword_id, {})

    def get_competition_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._competition_inputs.get(keyword_id, {})

    def get_feasibility_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._feasibility_inputs.get(keyword_id, {})

    def get_profitability_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._profitability_inputs.get(keyword_id, {})

    def get_intent_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._intent_inputs.get(keyword_id, {})

    def get_saturation_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._saturation_inputs.get(keyword_id, {})

    def get_weakness_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._weakness_inputs.get(keyword_id, {})

    def get_trend_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._trend_inputs.get(keyword_id, {})

    def get_confidence_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._confidence_inputs.get(keyword_id, {})

    def get_final_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._final_inputs.get(keyword_id, {})


def _base_demand_inputs() -> dict[str, Any]:
    return {
        "total_result_count": 1250,
        "autocomplete_position": 3,
        "trends_12mo_score": 58,
        "reddit_demand_intent_score": 7.2,
    }


def _base_competition_inputs() -> dict[str, Any]:
    return {
        "total_result_count": 3200,
        "avg_review_count_top10": 420,
        "avg_seller_level_top10": "Level 2",
        "proportion_with_100_plus_reviews": 0.8,
        "pro_verified_presence_ratio": 0.5,
        "avg_starting_price_top10": 55.0,
        "llm_competitor_strength_rating": 7.5,
    }


def _db_with_inputs(
    demand_inputs: dict[str, Any] | None = None,
    competition_inputs: dict[str, Any] | None = None,
    feasibility_inputs: dict[str, Any] | None = None,
    profitability_inputs: dict[str, Any] | None = None,
    intent_inputs: dict[str, Any] | None = None,
    saturation_inputs: dict[str, Any] | None = None,
    weakness_inputs: dict[str, Any] | None = None,
    trend_inputs: dict[str, Any] | None = None,
    confidence_inputs: dict[str, Any] | None = None,
    final_inputs: dict[str, Any] | None = None,
    keyword_id: int = 101,
) -> FakeScoringDB:
    return FakeScoringDB(
        demand_inputs={keyword_id: demand_inputs or {}},
        competition_inputs={keyword_id: competition_inputs or {}},
        feasibility_inputs={keyword_id: feasibility_inputs or {}},
        profitability_inputs={keyword_id: profitability_inputs or {}},
        intent_inputs={keyword_id: intent_inputs or {}},
        saturation_inputs={keyword_id: saturation_inputs or {}},
        weakness_inputs={keyword_id: weakness_inputs or {}},
        trend_inputs={keyword_id: trend_inputs or {}},
        confidence_inputs={keyword_id: confidence_inputs or {}},
        final_inputs={keyword_id: final_inputs or {}},
    )


def _base_feasibility_inputs() -> dict[str, Any]:
    return {
        "level1_or_new_ratio_top10": 0.6,
        "lowest_ranked_review_count_page1": 14,
        "price_diversity_top10": 0.65,
        "llm_gig_quality_weakness_avg_top10": 7.2,
        "llm_entry_gap_assessment": 6.8,
        "niche_name": "AI Agent",
    }


def _base_profitability_inputs() -> dict[str, Any]:
    return {
        "avg_starting_price_top10": 130.0,
        "keyword_universe_starting_price_min": 25.0,
        "keyword_universe_starting_price_max": 220.0,
        "avg_premium_package_price_top10": 360.0,
        "keyword_universe_premium_price_min": 90.0,
        "keyword_universe_premium_price_max": 600.0,
        "typical_delivery_days": 4,
        "extras_presence_ratio": 0.8,
        "avg_extras_price": 42.0,
        "llm_upsell_potential_assessment": 7.5,
    }


def _base_intent_inputs() -> dict[str, Any]:
    return {
        "keyword": "hire python automation expert",
        "commercial_modifier_score": None,
        "avg_review_count_top10": 220,
        "llm_buyer_intent_classification": "HIGH_INTENT",
        "reddit_demand_intent_score": 7.1,
    }


def _base_saturation_inputs() -> dict[str, Any]:
    return {
        "total_gig_count": 5600,
        "title_duplication_rate": 0.55,
        "price_compression_signal": 0.62,
        "seller_portfolio_overlap_ratio": 0.47,
        "llm_saturation_assessment": 6.9,
    }


def _base_weakness_inputs() -> dict[str, Any]:
    return {
        "video_absence_rate": 0.5,
        "portfolio_absence_rate": 0.4,
        "llm_description_quality_score": 6.0,
        "llm_weakness_count_per_gig": 4.0,
        "llm_thumbnail_quality_score": 7.0,
        "llm_faq_completeness_score": 6.0,
        "llm_package_differentiation_score": 5.0,
        "llm_niche_specificity_score": 6.5,
    }


def _base_trend_inputs() -> dict[str, Any]:
    return {
        "google_trends_slope": 10.0,
        "trends_3mo_avg": 72.0,
        "trends_12mo_avg": 60.0,
        "reddit_recent_post_volume": 30.0,
        "reddit_historical_post_volume": 20.0,
        "llm_trend_classification": "RISING",
    }


def _base_confidence_context() -> dict[str, Any]:
    return {
        "data_completeness_ratio": 0.95,
        "data_freshness_score": 0.90,
        "source_diversity_score": 0.85,
        "llm_analysis_completion_ratio": 0.95,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": True,
        "llm_gig_quality_incomplete_count": 0,
        "llm_competitor_synthesis_failed": False,
        "data_age_hours": 4.0,
        "data_ttl_hours": 24.0,
        "mode": "standard",
    }


def _base_final_inputs() -> dict[str, Any]:
    return {
        "demand_score": 80.0,
        "competition_score": 40.0,
        "opportunity_score": 70.0,
        "feasibility_score": 65.0,
        "profitability_score": 75.0,
        "intent_score": 60.0,
        "saturation_score": 30.0,
        "weakness_score": 68.0,
        "trend_score": 72.0,
        "confidence_modifier": 0.9,
    }


def test_demand_score_all_inputs_present() -> None:
    calculator = DemandScoreCalculator()
    result = calculator.calculate(101, _db_with_inputs(demand_inputs=_base_demand_inputs()))
    assert result.score_value is not None
    assert 0.0 <= result.score_value <= 100.0


def test_demand_score_missing_google_trends() -> None:
    inputs = _base_demand_inputs()
    inputs["trends_12mo_score"] = None
    calculator = DemandScoreCalculator()
    result = calculator.calculate(101, _db_with_inputs(demand_inputs=inputs))
    assert result.score_value is not None
    assert result.confidence_breakdown["missing_google_trends"] == -0.15


def test_demand_score_missing_reddit() -> None:
    inputs = _base_demand_inputs()
    inputs["reddit_demand_intent_score"] = None
    calculator = DemandScoreCalculator()
    result = calculator.calculate(101, _db_with_inputs(demand_inputs=inputs))
    assert result.score_value is not None
    assert result.confidence_breakdown["missing_reddit_intent"] == -0.05


def test_demand_score_no_autocomplete() -> None:
    inputs = _base_demand_inputs()
    inputs["autocomplete_position"] = None
    calculator = DemandScoreCalculator()
    result = calculator.calculate(101, _db_with_inputs(demand_inputs=inputs))
    assert result.score_components["autocomplete"].value == 0.0


def test_demand_score_zero_result_count() -> None:
    inputs = _base_demand_inputs()
    inputs["total_result_count"] = 0
    calculator = DemandScoreCalculator()
    result = calculator.calculate(101, _db_with_inputs(demand_inputs=inputs))
    assert result.score_components["fiverr_count"].value == 0.0


def test_demand_score_high_count() -> None:
    inputs = _base_demand_inputs()
    inputs["total_result_count"] = 10000
    calculator = DemandScoreCalculator()
    result = calculator.calculate(101, _db_with_inputs(demand_inputs=inputs))
    assert result.score_components["fiverr_count"].value == 100.0


def test_demand_score_insufficient_data() -> None:
    inputs = {
        "total_result_count": None,
        "autocomplete_position": None,
        "trends_12mo_score": None,
        "reddit_demand_intent_score": None,
    }
    calculator = DemandScoreCalculator()
    result = calculator.calculate(101, _db_with_inputs(demand_inputs=inputs))
    assert result.score_value is None


def test_demand_score_all_missing() -> None:
    calculator = DemandScoreCalculator()
    result = calculator.calculate(101, _db_with_inputs(demand_inputs={}))
    assert result.score_value is None


def test_demand_score_result_fields() -> None:
    calculator = DemandScoreCalculator()
    result = calculator.calculate(101, _db_with_inputs(demand_inputs=_base_demand_inputs()))
    assert result.score_components
    assert isinstance(result.confidence_modifier, float)
    assert isinstance(result.missing_data_warnings, list)
    assert isinstance(result.source_evidence, list)
    assert isinstance(result.explanation_text, str)


def test_demand_score_autocomplete_pos_1() -> None:
    inputs = _base_demand_inputs()
    inputs["autocomplete_position"] = 1
    calculator = DemandScoreCalculator()
    result = calculator.calculate(101, _db_with_inputs(demand_inputs=inputs))
    assert result.score_components["autocomplete"].value == 100.0


def test_demand_score_autocomplete_pos_10() -> None:
    inputs = _base_demand_inputs()
    inputs["autocomplete_position"] = 10
    calculator = DemandScoreCalculator()
    result = calculator.calculate(101, _db_with_inputs(demand_inputs=inputs))
    assert result.score_components["autocomplete"].value == 10.0


def test_demand_score_log_normalization() -> None:
    calculator = DemandScoreCalculator()
    base_inputs = _base_demand_inputs()
    result_100 = calculator.calculate(
        101,
        _db_with_inputs(demand_inputs={**base_inputs, "total_result_count": 100}),
    )
    result_1000 = calculator.calculate(
        101,
        _db_with_inputs(demand_inputs={**base_inputs, "total_result_count": 1000}),
    )
    result_5000 = calculator.calculate(
        101,
        _db_with_inputs(demand_inputs={**base_inputs, "total_result_count": 5000}),
    )
    assert round(result_100.score_components["fiverr_count"].value, 2) == 50.11
    assert round(result_1000.score_components["fiverr_count"].value, 2) == 75.01
    assert round(result_5000.score_components["fiverr_count"].value, 2) > 90.0


def test_competition_score_all_inputs() -> None:
    calculator = CompetitionScoreCalculator()
    result = calculator.calculate(201, _db_with_inputs(competition_inputs=_base_competition_inputs(), keyword_id=201))
    assert result.score_value is not None
    assert 0.0 <= result.score_value <= 100.0


def test_competition_score_no_gig_data() -> None:
    inputs = {"total_result_count": 500, "llm_competitor_strength_rating": 6.0}
    calculator = CompetitionScoreCalculator()
    result = calculator.calculate(201, _db_with_inputs(competition_inputs=inputs, keyword_id=201))
    assert result.confidence_breakdown["missing_gig_detail_dataset"] == -0.20


def test_competition_score_level_mapping() -> None:
    calculator = CompetitionScoreCalculator()
    inputs = _base_competition_inputs()
    inputs["avg_seller_level_top10"] = "TRS"
    result = calculator.calculate(201, _db_with_inputs(competition_inputs=inputs, keyword_id=201))
    assert result.score_components["seller_level"].value == 100.0


def test_competition_score_review_proportion() -> None:
    calculator = CompetitionScoreCalculator()
    inputs = _base_competition_inputs()
    inputs["proportion_with_100_plus_reviews"] = 0.42
    result = calculator.calculate(201, _db_with_inputs(competition_inputs=inputs, keyword_id=201))
    assert result.score_components["hundred_plus_review_ratio"].value == 42.0


def test_competition_score_pro_verified() -> None:
    calculator = CompetitionScoreCalculator()
    inputs = _base_competition_inputs()
    inputs["pro_verified_presence_ratio"] = 0.9
    result = calculator.calculate(201, _db_with_inputs(competition_inputs=inputs, keyword_id=201))
    assert result.score_components["pro_verified_presence"].value == 90.0


def test_competition_score_insufficient_data() -> None:
    inputs = {"llm_competitor_strength_rating": 4.0}
    calculator = CompetitionScoreCalculator()
    result = calculator.calculate(201, _db_with_inputs(competition_inputs=inputs, keyword_id=201))
    assert result.score_value is None


def test_competition_score_result_fields() -> None:
    calculator = CompetitionScoreCalculator()
    result = calculator.calculate(201, _db_with_inputs(competition_inputs=_base_competition_inputs(), keyword_id=201))
    assert isinstance(result.score_components, dict)
    assert isinstance(result.confidence_modifier, float)
    assert isinstance(result.explanation_text, str)


def test_competition_score_high_competition() -> None:
    calculator = CompetitionScoreCalculator()
    inputs = {
        "total_result_count": 100000,
        "avg_review_count_top10": 2500,
        "avg_seller_level_top10": "TRS",
        "proportion_with_100_plus_reviews": 1.0,
        "pro_verified_presence_ratio": 1.0,
        "avg_starting_price_top10": 200.0,
        "llm_competitor_strength_rating": 10.0,
    }
    result = calculator.calculate(201, _db_with_inputs(competition_inputs=inputs, keyword_id=201))
    assert result.score_value is not None
    assert result.score_value > 90.0


def test_competition_score_low_competition() -> None:
    calculator = CompetitionScoreCalculator()
    inputs = {
        "total_result_count": 10,
        "avg_review_count_top10": 2,
        "avg_seller_level_top10": "Level 1",
        "proportion_with_100_plus_reviews": 0.0,
        "pro_verified_presence_ratio": 0.0,
        "avg_starting_price_top10": 5.0,
        "llm_competitor_strength_rating": 1.0,
    }
    result = calculator.calculate(201, _db_with_inputs(competition_inputs=inputs, keyword_id=201))
    assert result.score_value is not None
    assert result.score_value < 30.0


def test_competition_score_missing_prices() -> None:
    calculator = CompetitionScoreCalculator()
    inputs = _base_competition_inputs()
    inputs["avg_starting_price_top10"] = None
    result = calculator.calculate(201, _db_with_inputs(competition_inputs=inputs, keyword_id=201))
    assert result.score_value is not None
    assert "Missing average starting price for top 10 gigs." in result.missing_data_warnings


def test_opportunity_score_formula() -> None:
    calculator = OpportunityScoreCalculator()
    result = calculator.calculate(
        301,
        _db_with_inputs(keyword_id=301),
        demand_result=replace(
            DemandScoreCalculator().calculate(101, _db_with_inputs(demand_inputs=_base_demand_inputs())),
            score_value=70.0,
        ),
        competition_result=replace(
            CompetitionScoreCalculator().calculate(
                201, _db_with_inputs(competition_inputs=_base_competition_inputs(), keyword_id=201)
            ),
            score_value=40.0,
        ),
    )
    assert result.score_value == 66.0


def test_opportunity_score_normalized() -> None:
    calculator = OpportunityScoreCalculator()
    demand_result = replace(
        DemandScoreCalculator().calculate(101, _db_with_inputs(demand_inputs=_base_demand_inputs())),
        score_value=0.0,
    )
    competition_result = replace(
        CompetitionScoreCalculator().calculate(
            201, _db_with_inputs(competition_inputs=_base_competition_inputs(), keyword_id=201)
        ),
        score_value=100.0,
    )
    low_result = calculator.calculate(
        301,
        _db_with_inputs(keyword_id=301),
        demand_result=demand_result,
        competition_result=competition_result,
    )
    high_result = calculator.calculate(
        301,
        _db_with_inputs(keyword_id=301),
        demand_result=replace(demand_result, score_value=100.0),
        competition_result=replace(competition_result, score_value=0.0),
    )
    assert low_result.score_value == 0.0
    assert high_result.score_value == 100.0


def test_opportunity_score_demand_none() -> None:
    calculator = OpportunityScoreCalculator()
    demand_result = replace(
        DemandScoreCalculator().calculate(101, _db_with_inputs(demand_inputs=_base_demand_inputs())),
        score_value=None,
    )
    comp_result = replace(
        CompetitionScoreCalculator().calculate(201, _db_with_inputs(competition_inputs=_base_competition_inputs(), keyword_id=201)),
        score_value=55.0,
    )
    result = calculator.calculate(301, _db_with_inputs(keyword_id=301), demand_result=demand_result, competition_result=comp_result)
    assert result.score_value is None


def test_opportunity_score_competition_none() -> None:
    calculator = OpportunityScoreCalculator()
    demand_result = replace(
        DemandScoreCalculator().calculate(101, _db_with_inputs(demand_inputs=_base_demand_inputs())),
        score_value=55.0,
    )
    comp_result = replace(
        CompetitionScoreCalculator().calculate(201, _db_with_inputs(competition_inputs=_base_competition_inputs(), keyword_id=201)),
        score_value=None,
    )
    result = calculator.calculate(301, _db_with_inputs(keyword_id=301), demand_result=demand_result, competition_result=comp_result)
    assert result.score_value is None


def test_opportunity_score_both_none() -> None:
    calculator = OpportunityScoreCalculator()
    demand_result = replace(
        DemandScoreCalculator().calculate(101, _db_with_inputs(demand_inputs=_base_demand_inputs())),
        score_value=None,
    )
    comp_result = replace(
        CompetitionScoreCalculator().calculate(201, _db_with_inputs(competition_inputs=_base_competition_inputs(), keyword_id=201)),
        score_value=None,
    )
    result = calculator.calculate(301, _db_with_inputs(keyword_id=301), demand_result=demand_result, competition_result=comp_result)
    assert result.score_value is None


def test_opportunity_score_high_demand_low_competition() -> None:
    calculator = OpportunityScoreCalculator()
    demand_result = replace(
        DemandScoreCalculator().calculate(101, _db_with_inputs(demand_inputs=_base_demand_inputs())),
        score_value=90.0,
    )
    comp_result = replace(
        CompetitionScoreCalculator().calculate(201, _db_with_inputs(competition_inputs=_base_competition_inputs(), keyword_id=201)),
        score_value=10.0,
    )
    result = calculator.calculate(301, _db_with_inputs(keyword_id=301), demand_result=demand_result, competition_result=comp_result)
    assert result.score_value is not None
    assert result.score_value > 70.0


def test_opportunity_score_low_demand_high_competition() -> None:
    calculator = OpportunityScoreCalculator()
    demand_result = replace(
        DemandScoreCalculator().calculate(101, _db_with_inputs(demand_inputs=_base_demand_inputs())),
        score_value=20.0,
    )
    comp_result = replace(
        CompetitionScoreCalculator().calculate(201, _db_with_inputs(competition_inputs=_base_competition_inputs(), keyword_id=201)),
        score_value=90.0,
    )
    result = calculator.calculate(301, _db_with_inputs(keyword_id=301), demand_result=demand_result, competition_result=comp_result)
    assert result.score_value is not None
    assert result.score_value < 30.0


def test_opportunity_score_result_fields() -> None:
    calculator = OpportunityScoreCalculator()
    demand_result = replace(
        DemandScoreCalculator().calculate(101, _db_with_inputs(demand_inputs=_base_demand_inputs())),
        score_value=65.0,
    )
    comp_result = replace(
        CompetitionScoreCalculator().calculate(201, _db_with_inputs(competition_inputs=_base_competition_inputs(), keyword_id=201)),
        score_value=45.0,
    )
    result = calculator.calculate(301, _db_with_inputs(keyword_id=301), demand_result=demand_result, competition_result=comp_result)
    assert isinstance(result.score_components, dict)
    assert result.default_weight == 0.25
    assert isinstance(result.explanation_text, str)


def test_feasibility_all_inputs() -> None:
    calculator = NewSellerFeasibilityCalculator()
    result = calculator.calculate(401, _db_with_inputs(feasibility_inputs=_base_feasibility_inputs(), keyword_id=401))
    assert result.score_value is not None
    assert 0.0 <= result.score_value <= 100.0


def test_feasibility_tier2_niche_context() -> None:
    calculator = NewSellerFeasibilityCalculator()
    result = calculator.calculate(401, _db_with_inputs(feasibility_inputs=_base_feasibility_inputs(), keyword_id=401))
    assert result.niche_tier == "tier2_standard"


def test_feasibility_level1_dominance() -> None:
    calculator = NewSellerFeasibilityCalculator()
    inputs = _base_feasibility_inputs()
    inputs["level1_or_new_ratio_top10"] = 1.0
    result = calculator.calculate(401, _db_with_inputs(feasibility_inputs=inputs, keyword_id=401))
    assert result.score_components["level1_or_new_ratio"].value == 100.0


def test_feasibility_high_entry_barrier() -> None:
    calculator = NewSellerFeasibilityCalculator()
    inputs = _base_feasibility_inputs()
    inputs["level1_or_new_ratio_top10"] = 0.0
    inputs["lowest_ranked_review_count_page1"] = 1500
    result = calculator.calculate(401, _db_with_inputs(feasibility_inputs=inputs, keyword_id=401))
    assert result.score_value is not None
    assert result.score_value < 50.0


def test_feasibility_low_review_threshold() -> None:
    calculator = NewSellerFeasibilityCalculator()
    low_inputs = _base_feasibility_inputs()
    low_inputs["lowest_ranked_review_count_page1"] = 3
    high_inputs = _base_feasibility_inputs()
    high_inputs["lowest_ranked_review_count_page1"] = 600
    low_result = calculator.calculate(401, _db_with_inputs(feasibility_inputs=low_inputs, keyword_id=401))
    high_result = calculator.calculate(401, _db_with_inputs(feasibility_inputs=high_inputs, keyword_id=401))
    assert low_result.score_components["lowest_ranked_review_barrier"].value > high_result.score_components["lowest_ranked_review_barrier"].value


def test_feasibility_price_diversity() -> None:
    calculator = NewSellerFeasibilityCalculator()
    inputs = _base_feasibility_inputs()
    inputs["price_diversity_top10"] = 0.85
    result = calculator.calculate(401, _db_with_inputs(feasibility_inputs=inputs, keyword_id=401))
    assert result.score_components["price_diversity"].value == 85.0


def test_feasibility_llm_stub() -> None:
    calculator = NewSellerFeasibilityCalculator()
    inputs = _base_feasibility_inputs()
    inputs["llm_entry_gap_assessment"] = None
    result = calculator.calculate(401, _db_with_inputs(feasibility_inputs=inputs, keyword_id=401))
    assert any("llm_not_implemented" in warning for warning in result.missing_data_warnings)
    assert result.score_value is not None


def test_feasibility_insufficient_data() -> None:
    calculator = NewSellerFeasibilityCalculator()
    inputs = {"lowest_ranked_review_count_page1": 40}
    result = calculator.calculate(401, _db_with_inputs(feasibility_inputs=inputs, keyword_id=401))
    assert result.score_value is None


def test_feasibility_result_fields() -> None:
    calculator = NewSellerFeasibilityCalculator()
    result = calculator.calculate(401, _db_with_inputs(feasibility_inputs=_base_feasibility_inputs(), keyword_id=401))
    assert isinstance(result.score_components, dict)
    assert isinstance(result.missing_data_warnings, list)
    assert isinstance(result.source_evidence, list)
    assert isinstance(result.explanation_text, str)
    assert result.default_weight == 0.15


def test_feasibility_niche_tier_tier2() -> None:
    calculator = NewSellerFeasibilityCalculator()
    inputs = _base_feasibility_inputs()
    inputs["niche_name"] = "Python Scraping"
    result = calculator.calculate(401, _db_with_inputs(feasibility_inputs=inputs, keyword_id=401))
    assert result.niche_tier == "tier2_standard"


def test_feasibility_zero_entry_barrier() -> None:
    calculator = NewSellerFeasibilityCalculator()
    inputs = _base_feasibility_inputs()
    inputs["level1_or_new_ratio_top10"] = 1.0
    inputs["lowest_ranked_review_count_page1"] = 0
    inputs["price_diversity_top10"] = 1.0
    inputs["llm_gig_quality_weakness_avg_top10"] = 10.0
    inputs["llm_entry_gap_assessment"] = 10.0
    result = calculator.calculate(401, _db_with_inputs(feasibility_inputs=inputs, keyword_id=401))
    assert result.score_value == 100.0


def test_feasibility_confidence_deductions() -> None:
    calculator = NewSellerFeasibilityCalculator()
    inputs = _base_feasibility_inputs()
    inputs["llm_gig_quality_weakness_avg_top10"] = None
    inputs["llm_entry_gap_assessment"] = None
    result = calculator.calculate(401, _db_with_inputs(feasibility_inputs=inputs, keyword_id=401))
    assert result.confidence_modifier < 1.0


@pytest.mark.parametrize(
    ("lower_reviews", "higher_reviews"),
    [(value, value + 1) for value in range(0, 60)],
)
def test_feasibility_entry_barrier_monotonic_grid(
    lower_reviews: int,
    higher_reviews: int,
) -> None:
    low_score = NewSellerFeasibilityCalculator._normalize_entry_review_barrier(float(lower_reviews))
    high_score = NewSellerFeasibilityCalculator._normalize_entry_review_barrier(float(higher_reviews))
    assert 0.0 <= low_score <= 100.0
    assert 0.0 <= high_score <= 100.0
    assert low_score >= high_score


def test_feasibility_helper_parsing_and_config_guards() -> None:
    assert _coerce_float("bad-number", 3.5) == 3.5
    assert _feasibility_config({"scoring": {"feasibility": "invalid"}}) == {}
    assert _normalize_gap_flags(["low video presence", 123, "HIGH-PRICE VARIANCE"]) == [
        "LOW_VIDEO_PRESENCE",
        "HIGH_PRICE_VARIANCE",
    ]
    assert _extract_gap_flags_from_profile({"gap_flags": ["low portfolio presence"]}) == [
        "LOW_PORTFOLIO_PRESENCE"
    ]


def test_feasibility_gap_signal_non_session_paths_and_guards() -> None:
    class _Provider:
        @staticmethod
        def get_competitor_profile_inputs(_niche_id: str, _run_id: str) -> dict[str, Any]:
            return {"gap_flags": ["low video presence", "unsupported"]}

    class _UnsupportedProvider:
        @staticmethod
        def get_competitor_profile_inputs(_niche_id: str, _run_id: str) -> dict[str, Any]:
            return {"gap_flags": ["unknown-flag"]}

    zero_boost, zero_flags = _get_feasibility_gap_signal_details(" ", "run-1", _Provider())
    assert zero_boost == 0.0
    assert zero_flags == []

    boost, flags = _get_feasibility_gap_signal_details(
        "automation",
        "run-1",
        _Provider(),
        config={"scoring": {"feasibility": {"gap_boost_per_flag": "12.5", "max_gap_boost": "20"}}},
    )
    assert boost == 12.5
    assert flags == ["LOW_VIDEO_PRESENCE"]

    unsupported_boost = get_feasibility_gap_signal("automation", "run-1", _UnsupportedProvider())
    assert unsupported_boost == 0.0
    assert _get_feasibility_gap_signal_details("automation", "run-1", object()) == (0.0, [])


# pylint: disable=protected-access
def test_feasibility_level_price_and_misc_private_fallbacks() -> None:
    calculator = NewSellerFeasibilityCalculator()

    assert calculator._resolve_level1_ratio({"top10_seller_levels": ["new seller", "Level 2", None]}) == (
        2 / 3
    )
    assert calculator._resolve_price_diversity_score({"price_diversity_top10": 120.0}) == 100.0
    assert calculator._resolve_price_diversity_score({"top10_prices": [100.0, 120.0, 140.0]}) is not None
    assert calculator._resolve_price_diversity_score({"top10_prices": [-10.0, -20.0]}) == 0.0

    assert calculator._resolve_niche_tier({"niche_tier": "  custom_tier  "}) == "custom_tier"
    assert calculator._normalize_llm_score(11.0) == 11.0
    assert calculator._as_float(object()) is None
    assert calculator._load_signals(401, None) == {}
    assert calculator._compute_price_diversity([10.0]) is None
    assert calculator._compute_price_diversity([0.0, 0.0]) == 0.0


def test_profitability_all_inputs() -> None:
    calculator = ProfitabilityScoreCalculator()
    result = calculator.calculate(501, _db_with_inputs(profitability_inputs=_base_profitability_inputs(), keyword_id=501))
    assert result.score_value is not None
    assert 0.0 <= result.score_value <= 100.0


def test_profitability_high_price_market() -> None:
    calculator = ProfitabilityScoreCalculator()
    inputs = _base_profitability_inputs()
    inputs["avg_starting_price_top10"] = 220.0
    inputs["avg_premium_package_price_top10"] = 620.0
    result = calculator.calculate(501, _db_with_inputs(profitability_inputs=inputs, keyword_id=501))
    assert result.score_value is not None
    assert result.score_value > 70.0


def test_profitability_low_price_market() -> None:
    calculator = ProfitabilityScoreCalculator()
    inputs = _base_profitability_inputs()
    inputs["avg_starting_price_top10"] = 20.0
    inputs["avg_premium_package_price_top10"] = 65.0
    inputs["extras_presence_ratio"] = 0.1
    result = calculator.calculate(501, _db_with_inputs(profitability_inputs=inputs, keyword_id=501))
    assert result.score_value is not None
    assert result.score_value < 40.0


def test_profitability_premium_package() -> None:
    calculator = ProfitabilityScoreCalculator()
    high_inputs = _base_profitability_inputs()
    high_inputs["avg_premium_package_price_top10"] = 500.0
    low_inputs = _base_profitability_inputs()
    low_inputs["avg_premium_package_price_top10"] = 120.0
    high_result = calculator.calculate(501, _db_with_inputs(profitability_inputs=high_inputs, keyword_id=501))
    low_result = calculator.calculate(501, _db_with_inputs(profitability_inputs=low_inputs, keyword_id=501))
    assert high_result.score_components["avg_premium_price"].value > low_result.score_components["avg_premium_price"].value


def test_profitability_aov_context_in_explanation() -> None:
    calculator = ProfitabilityScoreCalculator()
    result = calculator.calculate(501, _db_with_inputs(profitability_inputs=_base_profitability_inputs(), keyword_id=501))
    assert "Month 1-3 AOV typically $95-175. Month 6+ AOV can reach $300+" in result.explanation_text


def test_profitability_delivery_time_short() -> None:
    calculator = ProfitabilityScoreCalculator()
    fast_inputs = _base_profitability_inputs()
    fast_inputs["typical_delivery_days"] = 1
    slow_inputs = _base_profitability_inputs()
    slow_inputs["typical_delivery_days"] = 30
    fast_result = calculator.calculate(501, _db_with_inputs(profitability_inputs=fast_inputs, keyword_id=501))
    slow_result = calculator.calculate(501, _db_with_inputs(profitability_inputs=slow_inputs, keyword_id=501))
    assert fast_result.score_components["delivery_time_efficiency"].value > slow_result.score_components["delivery_time_efficiency"].value


def test_profitability_extras_present() -> None:
    calculator = ProfitabilityScoreCalculator()
    inputs = _base_profitability_inputs()
    inputs["extras_presence_ratio"] = 1.0
    inputs["avg_extras_price"] = 70.0
    result = calculator.calculate(501, _db_with_inputs(profitability_inputs=inputs, keyword_id=501))
    assert result.score_components["gig_extras_upsell"].value > 70.0


def test_profitability_llm_stub() -> None:
    calculator = ProfitabilityScoreCalculator()
    inputs = _base_profitability_inputs()
    inputs["llm_upsell_potential_assessment"] = None
    result = calculator.calculate(501, _db_with_inputs(profitability_inputs=inputs, keyword_id=501))
    assert result.score_value is not None
    assert any("llm_not_implemented" in warning for warning in result.missing_data_warnings)


def test_profitability_insufficient_data() -> None:
    calculator = ProfitabilityScoreCalculator()
    inputs = {"typical_delivery_days": 4}
    result = calculator.calculate(501, _db_with_inputs(profitability_inputs=inputs, keyword_id=501))
    assert result.score_value is None


def test_profitability_result_fields() -> None:
    calculator = ProfitabilityScoreCalculator()
    result = calculator.calculate(501, _db_with_inputs(profitability_inputs=_base_profitability_inputs(), keyword_id=501))
    assert isinstance(result.score_components, dict)
    assert isinstance(result.source_evidence, list)
    assert isinstance(result.missing_data_warnings, list)
    assert result.default_weight == 0.10


def test_intent_all_inputs() -> None:
    calculator = ConversionIntentScoreCalculator()
    result = calculator.calculate(601, _db_with_inputs(intent_inputs=_base_intent_inputs(), keyword_id=601))
    assert result.score_value is not None
    assert 0.0 <= result.score_value <= 100.0


def test_intent_long_tail_keyword() -> None:
    calculator = ConversionIntentScoreCalculator()
    inputs = _base_intent_inputs()
    inputs["keyword"] = "hire ai agent automation specialist"
    result = calculator.calculate(601, _db_with_inputs(intent_inputs=inputs, keyword_id=601))
    assert result.score_components["keyword_specificity"].value == 100.0


def test_intent_broad_keyword() -> None:
    calculator = ConversionIntentScoreCalculator()
    inputs = _base_intent_inputs()
    inputs["keyword"] = "python"
    result = calculator.calculate(601, _db_with_inputs(intent_inputs=inputs, keyword_id=601))
    assert result.score_components["keyword_specificity"].value == 20.0


def test_intent_commercial_modifier() -> None:
    calculator = ConversionIntentScoreCalculator()
    inputs = _base_intent_inputs()
    inputs["keyword"] = "hire python developer"
    result = calculator.calculate(601, _db_with_inputs(intent_inputs=inputs, keyword_id=601))
    assert result.score_components["commercial_modifier_presence"].value == 90.0


def test_intent_transactional_llm() -> None:
    calculator = ConversionIntentScoreCalculator()
    inputs = _base_intent_inputs()
    inputs["llm_buyer_intent_classification"] = "TRANSACTIONAL"
    result = calculator.calculate(601, _db_with_inputs(intent_inputs=inputs, keyword_id=601))
    assert result.score_components["llm_buyer_intent"].value == 100.0


def test_intent_informational_llm() -> None:
    calculator = ConversionIntentScoreCalculator()
    inputs = _base_intent_inputs()
    inputs["llm_buyer_intent_classification"] = "INFORMATIONAL"
    result = calculator.calculate(601, _db_with_inputs(intent_inputs=inputs, keyword_id=601))
    assert result.score_components["llm_buyer_intent"].value == 10.0


def test_intent_llm_default_stub() -> None:
    calculator = ConversionIntentScoreCalculator()
    inputs = _base_intent_inputs()
    inputs["llm_buyer_intent_classification"] = None
    result = calculator.calculate(601, _db_with_inputs(intent_inputs=inputs, keyword_id=601))
    assert result.score_components["llm_buyer_intent"].value == 40.0
    assert any("CONSIDERATION (40)" in warning for warning in result.missing_data_warnings)


def test_intent_high_review_count() -> None:
    calculator = ConversionIntentScoreCalculator()
    high_inputs = _base_intent_inputs()
    high_inputs["avg_review_count_top10"] = 600
    low_inputs = _base_intent_inputs()
    low_inputs["avg_review_count_top10"] = 3
    high_result = calculator.calculate(601, _db_with_inputs(intent_inputs=high_inputs, keyword_id=601))
    low_result = calculator.calculate(601, _db_with_inputs(intent_inputs=low_inputs, keyword_id=601))
    assert high_result.score_components["buyer_proof_reviews"].value > low_result.score_components["buyer_proof_reviews"].value


def test_intent_insufficient_data() -> None:
    calculator = ConversionIntentScoreCalculator()
    result = calculator.calculate(601, _db_with_inputs(intent_inputs={}, keyword_id=601))
    assert result.score_value is None


def test_intent_result_fields() -> None:
    calculator = ConversionIntentScoreCalculator()
    result = calculator.calculate(601, _db_with_inputs(intent_inputs=_base_intent_inputs(), keyword_id=601))
    assert isinstance(result.score_components, dict)
    assert isinstance(result.explanation_text, str)
    assert isinstance(result.confidence_breakdown, dict)
    assert result.default_weight == 0.10


def test_saturation_all_inputs() -> None:
    calculator = SaturationScoreCalculator()
    result = calculator.calculate(701, _db_with_inputs(saturation_inputs=_base_saturation_inputs(), keyword_id=701))
    assert result.score_value is not None
    assert 0.0 <= result.score_value <= 100.0


def test_saturation_is_inverted_flag() -> None:
    calculator = SaturationScoreCalculator()
    result = calculator.calculate(701, _db_with_inputs(saturation_inputs=_base_saturation_inputs(), keyword_id=701))
    assert result.is_inverted is True


def test_saturation_high_gig_count() -> None:
    calculator = SaturationScoreCalculator()
    high_inputs = _base_saturation_inputs()
    high_inputs["total_gig_count"] = 100000
    low_inputs = _base_saturation_inputs()
    low_inputs["total_gig_count"] = 30
    high_result = calculator.calculate(701, _db_with_inputs(saturation_inputs=high_inputs, keyword_id=701))
    low_result = calculator.calculate(701, _db_with_inputs(saturation_inputs=low_inputs, keyword_id=701))
    assert high_result.score_components["total_gig_count"].value > low_result.score_components["total_gig_count"].value


def test_saturation_low_gig_count() -> None:
    calculator = SaturationScoreCalculator()
    inputs = _base_saturation_inputs()
    inputs["total_gig_count"] = 10
    result = calculator.calculate(701, _db_with_inputs(saturation_inputs=inputs, keyword_id=701))
    assert result.score_components["total_gig_count"].value < 30.0


def test_saturation_title_duplication() -> None:
    calculator = SaturationScoreCalculator()
    inputs = _base_saturation_inputs()
    inputs["title_duplication_rate"] = 0.9
    result = calculator.calculate(701, _db_with_inputs(saturation_inputs=inputs, keyword_id=701))
    assert result.score_components["title_duplication"].value == 90.0


def test_saturation_price_compression() -> None:
    calculator = SaturationScoreCalculator()
    inputs = _base_saturation_inputs()
    inputs["price_compression_signal"] = 0.92
    result = calculator.calculate(701, _db_with_inputs(saturation_inputs=inputs, keyword_id=701))
    assert result.score_components["price_compression"].value == 92.0


def test_saturation_llm_stub() -> None:
    calculator = SaturationScoreCalculator()
    inputs = _base_saturation_inputs()
    inputs["llm_saturation_assessment"] = None
    result = calculator.calculate(701, _db_with_inputs(saturation_inputs=inputs, keyword_id=701))
    assert result.score_value is not None
    assert any("llm_not_implemented" in warning for warning in result.missing_data_warnings)


def test_saturation_insufficient_data() -> None:
    calculator = SaturationScoreCalculator()
    inputs = {"seller_portfolio_overlap_ratio": 0.3}
    result = calculator.calculate(701, _db_with_inputs(saturation_inputs=inputs, keyword_id=701))
    assert result.score_value is None


def test_saturation_result_fields() -> None:
    calculator = SaturationScoreCalculator()
    result = calculator.calculate(701, _db_with_inputs(saturation_inputs=_base_saturation_inputs(), keyword_id=701))
    assert isinstance(result.score_components, dict)
    assert isinstance(result.source_evidence, list)
    assert result.is_inverted is True


def test_saturation_inversion_note() -> None:
    calculator = SaturationScoreCalculator()
    result = calculator.calculate(701, _db_with_inputs(saturation_inputs=_base_saturation_inputs(), keyword_id=701))
    assert "(100 - saturation_score) * 0.05" in result.explanation_text


def test_weakness_collection_inputs_only() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    result = calculator.calculate(
        801,
        _db_with_inputs(
            weakness_inputs={"video_absence_rate": 0.8, "portfolio_absence_rate": 0.6},
            keyword_id=801,
        ),
    )
    assert result.score_value is not None


def test_weakness_video_absence() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    result = calculator.calculate(
        801,
        _db_with_inputs(
            weakness_inputs={"top10_has_video": [False] * 10, "portfolio_absence_rate": 0.2},
            keyword_id=801,
        ),
    )
    assert result.score_components["video_absence_rate"].value == 100.0


def test_weakness_portfolio_absence() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    result = calculator.calculate(
        801,
        _db_with_inputs(
            weakness_inputs={"video_absence_rate": 0.2, "top10_has_portfolio": [False] * 10},
            keyword_id=801,
        ),
    )
    assert result.score_components["portfolio_absence_rate"].value == 100.0


def test_weakness_all_llm_stubs() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    inputs = _base_weakness_inputs()
    for key in list(inputs.keys()):
        if key.startswith("llm_"):
            inputs[key] = None
    result = calculator.calculate(801, _db_with_inputs(weakness_inputs=inputs, keyword_id=801))
    assert result.score_value is not None


def test_weakness_high_weakness_count() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    inputs = _base_weakness_inputs()
    inputs["llm_weakness_count_per_gig"] = 12.0
    result = calculator.calculate(801, _db_with_inputs(weakness_inputs=inputs, keyword_id=801))
    assert result.score_components["weakness_count"].value == 100.0


def test_weakness_description_quality_inverted() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    high_quality = _base_weakness_inputs()
    low_quality = _base_weakness_inputs()
    high_quality["llm_description_quality_score"] = 9.0
    low_quality["llm_description_quality_score"] = 2.0
    high_result = calculator.calculate(801, _db_with_inputs(weakness_inputs=high_quality, keyword_id=801))
    low_result = calculator.calculate(801, _db_with_inputs(weakness_inputs=low_quality, keyword_id=801))
    assert (
        high_result.score_components["description_quality_inverted"].value
        < low_result.score_components["description_quality_inverted"].value
    )


def test_weakness_llm_warning_emission() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    result = calculator.calculate(
        801,
        _db_with_inputs(
            weakness_inputs={"video_absence_rate": 0.7, "portfolio_absence_rate": 0.5},
            keyword_id=801,
        ),
    )
    assert any("llm_not_implemented" in warning for warning in result.missing_data_warnings)


def test_weakness_insufficient_data() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    result = calculator.calculate(801, _db_with_inputs(weakness_inputs={"video_absence_rate": 0.5}, keyword_id=801))
    assert result.score_value is None


def test_weakness_result_fields() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    result = calculator.calculate(801, _db_with_inputs(weakness_inputs=_base_weakness_inputs(), keyword_id=801))
    assert isinstance(result.score_components, dict)
    assert isinstance(result.confidence_modifier, float)
    assert isinstance(result.source_evidence, list)


def test_weakness_score_range() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    result = calculator.calculate(801, _db_with_inputs(weakness_inputs=_base_weakness_inputs(), keyword_id=801))
    assert result.score_value is not None
    assert 0.0 <= result.score_value <= 100.0


def test_weakness_opportunity_interpretation() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    strong_inputs = _base_weakness_inputs()
    weak_inputs = _base_weakness_inputs()
    strong_inputs["video_absence_rate"] = 1.0
    strong_inputs["portfolio_absence_rate"] = 1.0
    weak_inputs["video_absence_rate"] = 0.0
    weak_inputs["portfolio_absence_rate"] = 0.0
    strong_result = calculator.calculate(801, _db_with_inputs(weakness_inputs=strong_inputs, keyword_id=801))
    weak_result = calculator.calculate(801, _db_with_inputs(weakness_inputs=weak_inputs, keyword_id=801))
    assert strong_result.score_value is not None
    assert weak_result.score_value is not None
    assert strong_result.score_value > weak_result.score_value


def test_weakness_deterministic() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    inputs = _base_weakness_inputs()
    first = calculator.calculate(801, _db_with_inputs(weakness_inputs=inputs, keyword_id=801))
    second = calculator.calculate(801, _db_with_inputs(weakness_inputs=inputs, keyword_id=801))
    assert first.score_value == second.score_value


def test_trend_all_inputs() -> None:
    calculator = TrendScoreCalculator()
    result = calculator.calculate(901, _db_with_inputs(trend_inputs=_base_trend_inputs(), keyword_id=901))
    assert result.score_value is not None
    assert 0.0 <= result.score_value <= 100.0


def test_trend_slope_calculation() -> None:
    calculator = TrendScoreCalculator()
    inputs = _base_trend_inputs()
    inputs["google_trends_slope"] = 22.0
    result = calculator.calculate(901, _db_with_inputs(trend_inputs=inputs, keyword_id=901))
    assert result.score_components["google_trends_slope"].value > 50.0


def test_trend_negative_slope() -> None:
    calculator = TrendScoreCalculator()
    inputs = _base_trend_inputs()
    inputs["google_trends_slope"] = -20.0
    result = calculator.calculate(901, _db_with_inputs(trend_inputs=inputs, keyword_id=901))
    assert result.score_components["google_trends_slope"].value < 50.0


def test_trend_acceleration_positive() -> None:
    calculator = TrendScoreCalculator()
    inputs = _base_trend_inputs()
    inputs["trends_3mo_avg"] = 80.0
    inputs["trends_12mo_avg"] = 60.0
    result = calculator.calculate(901, _db_with_inputs(trend_inputs=inputs, keyword_id=901))
    assert result.score_components["google_trends_acceleration"].value > 50.0


def test_trend_acceleration_negative() -> None:
    calculator = TrendScoreCalculator()
    inputs = _base_trend_inputs()
    inputs["trends_3mo_avg"] = 45.0
    inputs["trends_12mo_avg"] = 60.0
    result = calculator.calculate(901, _db_with_inputs(trend_inputs=inputs, keyword_id=901))
    assert result.score_components["google_trends_acceleration"].value < 50.0


def test_trend_strongly_rising_llm() -> None:
    calculator = TrendScoreCalculator()
    inputs = _base_trend_inputs()
    inputs["llm_trend_classification"] = "STRONGLY_RISING"
    result = calculator.calculate(901, _db_with_inputs(trend_inputs=inputs, keyword_id=901))
    assert result.score_components["llm_trend_classification"].value == 100.0


def test_trend_stable_default() -> None:
    calculator = TrendScoreCalculator()
    inputs = _base_trend_inputs()
    inputs["llm_trend_classification"] = None
    result = calculator.calculate(901, _db_with_inputs(trend_inputs=inputs, keyword_id=901))
    assert result.score_components["llm_trend_classification"].value == 50.0


def test_trend_insufficient_data() -> None:
    calculator = TrendScoreCalculator()
    result = calculator.calculate(901, _db_with_inputs(trend_inputs={"llm_trend_classification": None}, keyword_id=901))
    assert result.score_value is None


def test_trend_result_fields() -> None:
    calculator = TrendScoreCalculator()
    result = calculator.calculate(901, _db_with_inputs(trend_inputs=_base_trend_inputs(), keyword_id=901))
    assert isinstance(result.score_components, dict)
    assert isinstance(result.source_evidence, list)


def test_trend_no_google_trends() -> None:
    calculator = TrendScoreCalculator()
    inputs = _base_trend_inputs()
    inputs["google_trends_slope"] = None
    result = calculator.calculate(901, _db_with_inputs(trend_inputs=inputs, keyword_id=901))
    assert result.confidence_breakdown["missing_google_trends"] == -0.15


@pytest.mark.parametrize("raw_value", list(range(-50, 260, 10)))
def test_trend_percentage_normalization_clamps_and_is_monotonic(raw_value: int) -> None:
    score = TrendScoreCalculator._normalize_percentage_score(float(raw_value))
    assert 0.0 <= score <= 100.0

    next_value = float(raw_value + 5)
    next_score = TrendScoreCalculator._normalize_percentage_score(next_value)
    if (raw_value <= 1 and next_value <= 1) or (1 < raw_value <= 10 and 1 < next_value <= 10) or (raw_value > 10 and next_value > 10):
        assert next_score >= score


@pytest.mark.parametrize("slope", list(range(-150, 160, 10)))
def test_trend_slope_normalization_clamps_and_is_monotonic(slope: int) -> None:
    score = TrendScoreCalculator._normalize_slope_to_score(float(slope))
    assert 0.0 <= score <= 100.0

    next_score = TrendScoreCalculator._normalize_slope_to_score(float(slope + 1))
    assert next_score >= score


def test_confidence_full_data() -> None:
    modifier = ConfidenceScoreModifier()
    value = modifier.calculate(1001, _base_confidence_context(), None)
    assert value > 0.8


def test_confidence_missing_google_trends() -> None:
    modifier = ConfidenceScoreModifier()
    context = _base_confidence_context()
    context["google_trends_available"] = False
    modifier.calculate(1001, context, None)
    assert modifier.last_breakdown["missing_google_trends"] == -0.15


def test_confidence_no_gig_detail() -> None:
    modifier = ConfidenceScoreModifier()
    context = _base_confidence_context()
    context["gig_detail_collected"] = False
    modifier.calculate(1001, context, None)
    assert modifier.last_breakdown["missing_gig_detail"] == -0.20


def test_confidence_no_seller_profiles() -> None:
    modifier = ConfidenceScoreModifier()
    context = _base_confidence_context()
    context["seller_profiles_collected"] = False
    modifier.calculate(1001, context, None)
    assert modifier.last_breakdown["missing_seller_profiles"] == -0.10


def test_confidence_no_reddit() -> None:
    modifier = ConfidenceScoreModifier()
    context = _base_confidence_context()
    context["reddit_signals_available"] = False
    modifier.calculate(1001, context, None)
    assert modifier.last_breakdown["missing_reddit_signals"] == -0.05


def test_confidence_llm_gig_quality_incomplete() -> None:
    modifier = ConfidenceScoreModifier()
    context = _base_confidence_context()
    context["llm_gig_quality_incomplete_count"] = 4
    modifier.calculate(1001, context, None)
    assert modifier.last_breakdown["llm_gig_quality_incomplete"] == -0.2


def test_confidence_llm_competitor_failed() -> None:
    modifier = ConfidenceScoreModifier()
    context = _base_confidence_context()
    context["llm_competitor_synthesis_failed"] = True
    modifier.calculate(1001, context, None)
    assert modifier.last_breakdown["llm_competitor_synthesis_failed"] == -0.10


def test_confidence_stale_data() -> None:
    modifier = ConfidenceScoreModifier()
    context = _base_confidence_context()
    context["data_age_hours"] = 100.0
    context["data_ttl_hours"] = 20.0
    modifier.calculate(1001, context, None)
    assert modifier.last_breakdown["data_stale_over_2x_ttl"] == -0.15


def test_confidence_keyword_only_mode() -> None:
    modifier = ConfidenceScoreModifier()
    context = _base_confidence_context()
    context["mode"] = "keyword_only"
    modifier.calculate(1001, context, None)
    assert modifier.last_breakdown["partial_depth_mode"] == -0.25


def test_confidence_clamped_at_zero() -> None:
    modifier = ConfidenceScoreModifier()
    context = _base_confidence_context()
    context.update(
        {
            "data_completeness_ratio": 0.0,
            "data_freshness_score": 0.0,
            "source_diversity_score": 0.0,
            "llm_analysis_completion_ratio": 0.0,
            "google_trends_available": False,
            "gig_detail_collected": False,
            "seller_profiles_collected": False,
            "reddit_signals_available": False,
            "llm_gig_quality_incomplete_count": 10,
            "llm_competitor_synthesis_failed": True,
            "data_age_hours": 999.0,
            "data_ttl_hours": 1.0,
            "mode": "keyword_only",
        }
    )
    value = modifier.calculate(1001, context, None)
    assert value == 0.0


def test_confidence_clamped_at_one() -> None:
    modifier = ConfidenceScoreModifier()
    context = _base_confidence_context()
    context.update(
        {
            "data_completeness_ratio": 1.0,
            "data_freshness_score": 1.0,
            "source_diversity_score": 1.0,
            "llm_analysis_completion_ratio": 1.0,
        }
    )
    value = modifier.calculate(1001, context, None)
    assert 0.0 <= value <= 1.0


def test_confidence_breakdown_dict() -> None:
    modifier = ConfidenceScoreModifier()
    modifier.calculate(1001, _base_confidence_context(), None)
    assert "remaining_modifier" in modifier.last_breakdown


def test_final_score_default_profile() -> None:
    calculator = FinalRecommendationScoreCalculator()
    result = calculator.calculate(1101, "default", _db_with_inputs(final_inputs=_base_final_inputs(), keyword_id=1101))
    assert result["profile_used"] == "default"


def test_final_score_aggressive_profile() -> None:
    calculator = FinalRecommendationScoreCalculator()
    result = calculator.calculate(
        1101,
        "aggressive_new_seller",
        _db_with_inputs(final_inputs=_base_final_inputs(), keyword_id=1101),
    )
    assert result["weights_applied"]["feasibility"] == 0.25


def test_final_score_profitability_profile() -> None:
    calculator = FinalRecommendationScoreCalculator()
    result = calculator.calculate(
        1101,
        "profitability_focus",
        _db_with_inputs(final_inputs=_base_final_inputs(), keyword_id=1101),
    )
    assert result["weights_applied"]["profitability"] == 0.25


def test_final_score_trend_chaser_profile() -> None:
    calculator = FinalRecommendationScoreCalculator()
    result = calculator.calculate(
        1101,
        "trend_chaser",
        _db_with_inputs(final_inputs=_base_final_inputs(), keyword_id=1101),
    )
    assert result["weights_applied"]["trend"] == 0.25


def test_final_score_weights_sum_to_1() -> None:
    sums = FinalRecommendationScoreCalculator.validate_profile_weights()
    assert all(abs(total - 1.0) <= 0.001 for total in sums.values())


def test_final_score_strong_go_threshold() -> None:
    calculator = FinalRecommendationScoreCalculator()
    high = _base_final_inputs()
    for key in list(high.keys()):
        if key.endswith("_score"):
            high[key] = 100.0
    high["competition_score"] = 0.0
    high["saturation_score"] = 0.0
    high["confidence_modifier"] = 1.0
    result = calculator.calculate(1101, "default", _db_with_inputs(final_inputs=high, keyword_id=1101))
    assert result["tag"] == "STRONG_GO"


def test_final_score_pass_threshold() -> None:
    calculator = FinalRecommendationScoreCalculator()
    low = _base_final_inputs()
    for key in list(low.keys()):
        if key.endswith("_score"):
            low[key] = 0.0
    low["confidence_modifier"] = 0.5
    result = calculator.calculate(1101, "default", _db_with_inputs(final_inputs=low, keyword_id=1101))
    assert result["tag"] == "PASS"


def test_final_score_confidence_applied() -> None:
    calculator = FinalRecommendationScoreCalculator()
    inputs = _base_final_inputs()
    inputs["confidence_modifier"] = 0.5
    result = calculator.calculate(1101, "default", _db_with_inputs(final_inputs=inputs, keyword_id=1101))
    assert result["final_score"] < 60.0


def test_final_score_none_components() -> None:
    calculator = FinalRecommendationScoreCalculator()
    inputs = _base_final_inputs()
    inputs["trend_score"] = None
    inputs["weakness_score"] = None
    result = calculator.calculate(1101, "default", _db_with_inputs(final_inputs=inputs, keyword_id=1101))
    assert "trend_score" in result["missing_components"]
    assert "weakness_score" in result["missing_components"]


def test_final_score_competition_inverted() -> None:
    calculator = FinalRecommendationScoreCalculator()
    low_comp = _base_final_inputs()
    high_comp = _base_final_inputs()
    low_comp["competition_score"] = 20.0
    high_comp["competition_score"] = 80.0
    low_result = calculator.calculate(1101, "default", _db_with_inputs(final_inputs=low_comp, keyword_id=1101))
    high_result = calculator.calculate(1101, "default", _db_with_inputs(final_inputs=high_comp, keyword_id=1101))
    assert low_result["final_score"] > high_result["final_score"]


def test_final_score_saturation_inverted() -> None:
    calculator = FinalRecommendationScoreCalculator()
    low_sat = _base_final_inputs()
    high_sat = _base_final_inputs()
    low_sat["saturation_score"] = 10.0
    high_sat["saturation_score"] = 90.0
    low_result = calculator.calculate(1101, "default", _db_with_inputs(final_inputs=low_sat, keyword_id=1101))
    high_result = calculator.calculate(1101, "default", _db_with_inputs(final_inputs=high_sat, keyword_id=1101))
    assert low_result["final_score"] > high_result["final_score"]


def test_final_score_result_structure() -> None:
    calculator = FinalRecommendationScoreCalculator()
    result = calculator.calculate(1101, "default", _db_with_inputs(final_inputs=_base_final_inputs(), keyword_id=1101))
    for field in [
        "final_score",
        "tag",
        "profile_used",
        "weights_applied",
        "component_scores",
        "confidence_modifier",
        "missing_components",
        "explanation_text",
    ]:
        assert field in result


def test_ranker_sort_descending() -> None:
    ranker = KeywordRanker()
    ranked = ranker.rank(
        [
            {"keyword_id": 2, "final_score": 50.0, "tag": "MONITOR"},
            {"keyword_id": 1, "final_score": 75.0, "tag": "CONDITIONAL_GO"},
        ],
        profile="default",
    )
    assert ranked[0]["keyword_id"] == 1


def test_ranker_rank_field() -> None:
    ranker = KeywordRanker()
    ranked = ranker.rank(
        [{"keyword_id": 1, "final_score": 60.0, "tag": "MONITOR"}],
        profile="default",
    )
    assert ranked[0]["rank"] == 1


def test_ranker_percentile_field() -> None:
    ranker = KeywordRanker()
    ranked = ranker.rank(
        [
            {"keyword_id": 1, "final_score": 80.0, "tag": "STRONG_GO"},
            {"keyword_id": 2, "final_score": 60.0, "tag": "MONITOR"},
            {"keyword_id": 3, "final_score": 40.0, "tag": "CAUTION"},
        ],
        profile="default",
    )
    assert all(0.0 <= item["percentile"] <= 100.0 for item in ranked)


def test_ranker_delta_from_top() -> None:
    ranker = KeywordRanker()
    ranked = ranker.rank(
        [
            {"keyword_id": 1, "final_score": 90.0, "tag": "STRONG_GO"},
            {"keyword_id": 2, "final_score": 80.0, "tag": "CONDITIONAL_GO"},
        ],
        profile="default",
    )
    assert ranked[0]["delta_from_top"] == 0.0
    assert ranked[1]["delta_from_top"] == 10.0


def test_ranker_filter_by_tag() -> None:
    ranker = KeywordRanker()
    ranked = ranker.rank(
        [
            {"keyword_id": 1, "final_score": 90.0, "tag": "STRONG_GO"},
            {"keyword_id": 2, "final_score": 70.0, "tag": "CONDITIONAL_GO"},
        ],
        profile="default",
    )
    filtered = ranker.filter_by_tag(ranked, "STRONG_GO")
    assert len(filtered) == 1


def test_ranker_filter_by_niche() -> None:
    ranker = KeywordRanker()
    ranked = ranker.rank(
        [
            {"keyword_id": 1, "final_score": 90.0, "tag": "STRONG_GO", "niche_id": "A"},
            {"keyword_id": 2, "final_score": 70.0, "tag": "CONDITIONAL_GO", "niche_id": "B"},
        ],
        profile="default",
    )
    filtered = ranker.filter_by_niche(ranked, "A")
    assert len(filtered) == 1


def test_ranker_filter_by_min_score() -> None:
    ranker = KeywordRanker()
    ranked = ranker.rank(
        [
            {"keyword_id": 1, "final_score": 90.0, "tag": "STRONG_GO"},
            {"keyword_id": 2, "final_score": 50.0, "tag": "MONITOR"},
        ],
        profile="default",
    )
    filtered = ranker.filter_by_min_score(ranked, 60.0)
    assert len(filtered) == 1


def test_ranker_tie_breaking() -> None:
    ranker = KeywordRanker()
    ranked = ranker.rank(
        [
            {"keyword_id": 2, "final_score": 80.0, "tag": "CONDITIONAL_GO"},
            {"keyword_id": 1, "final_score": 80.0, "tag": "CONDITIONAL_GO"},
        ],
        profile="default",
    )
    assert ranked[0]["keyword_id"] == 1


def test_ranker_empty_input() -> None:
    ranker = KeywordRanker()
    assert ranker.rank([], profile="default") == []


def test_ranker_single_item() -> None:
    ranker = KeywordRanker()
    ranked = ranker.rank([{"keyword_id": 1, "final_score": 88.0, "tag": "STRONG_GO"}], profile="default")
    assert ranked[0]["rank"] == 1
    assert ranked[0]["percentile"] == 100.0
    assert ranked[0]["delta_from_top"] == 0.0


def test_orchestrator_runs_all_calculators() -> None:
    orchestrator = ScoringOrchestrator()
    db = _db_with_inputs(
        demand_inputs=_base_demand_inputs(),
        competition_inputs=_base_competition_inputs(),
        feasibility_inputs=_base_feasibility_inputs(),
        profitability_inputs=_base_profitability_inputs(),
        intent_inputs=_base_intent_inputs(),
        saturation_inputs=_base_saturation_inputs(),
        weakness_inputs=_base_weakness_inputs(),
        trend_inputs=_base_trend_inputs(),
        keyword_id=1201,
    )
    result = orchestrator.run([1201], db, profile="default")
    assert len(result.keyword_results) == 1
    assert "demand_score" in result.keyword_results[0]["scores"]
    assert "trend_score" in result.keyword_results[0]["scores"]


def test_orchestrator_returns_scoring_run_result() -> None:
    orchestrator = ScoringOrchestrator()
    result = orchestrator.run([], _db_with_inputs(keyword_id=1201), profile="default")
    assert hasattr(result, "run_id")
    assert hasattr(result, "keyword_results")


def test_orchestrator_handles_none_scores() -> None:
    orchestrator = ScoringOrchestrator()
    db = _db_with_inputs(
        demand_inputs={},
        competition_inputs={},
        feasibility_inputs={},
        profitability_inputs={},
        intent_inputs={},
        saturation_inputs={},
        weakness_inputs={"video_absence_rate": 0.6, "portfolio_absence_rate": 0.6},
        trend_inputs={"llm_trend_classification": None},
        keyword_id=1201,
    )
    result = orchestrator.run([1201], db, profile="default")
    assert result.keyword_results[0]["final_payload"]["final_score"] >= 0.0


def test_orchestrator_applies_profile() -> None:
    orchestrator = ScoringOrchestrator()
    db = _db_with_inputs(
        demand_inputs=_base_demand_inputs(),
        competition_inputs=_base_competition_inputs(),
        feasibility_inputs=_base_feasibility_inputs(),
        profitability_inputs=_base_profitability_inputs(),
        intent_inputs=_base_intent_inputs(),
        saturation_inputs=_base_saturation_inputs(),
        weakness_inputs=_base_weakness_inputs(),
        trend_inputs=_base_trend_inputs(),
        keyword_id=1201,
    )
    result = orchestrator.run([1201], db, profile="trend_chaser")
    assert result.profile_used == "trend_chaser"


def test_orchestrator_run_metadata() -> None:
    orchestrator = ScoringOrchestrator()
    result = orchestrator.run([], _db_with_inputs(keyword_id=1201), profile="default")
    assert result.run_id.startswith("score_run_")
    assert result.started_at <= result.completed_at


def test_orchestrator_empty_keyword_list() -> None:
    orchestrator = ScoringOrchestrator()
    result = orchestrator.run([], _db_with_inputs(keyword_id=1201), profile="default")
    assert result.keyword_count == 0
    assert result.ranked_keywords == []


def test_orchestrator_ranking_included() -> None:
    orchestrator = ScoringOrchestrator()
    db = _db_with_inputs(
        demand_inputs=_base_demand_inputs(),
        competition_inputs=_base_competition_inputs(),
        feasibility_inputs=_base_feasibility_inputs(),
        profitability_inputs=_base_profitability_inputs(),
        intent_inputs=_base_intent_inputs(),
        saturation_inputs=_base_saturation_inputs(),
        weakness_inputs=_base_weakness_inputs(),
        trend_inputs=_base_trend_inputs(),
        keyword_id=1201,
    )
    result = orchestrator.run([1201], db, profile="default")
    assert result.ranked_keywords[0]["rank"] == 1


def test_orchestrator_error_list() -> None:
    orchestrator = ScoringOrchestrator()
    db = _db_with_inputs(
        weakness_inputs={"video_absence_rate": 0.8, "portfolio_absence_rate": 0.9},
        trend_inputs={"llm_trend_classification": None},
        keyword_id=1201,
    )
    result = orchestrator.run([1201], db, profile="default")
    assert isinstance(result.errors, list)


def test_orchestrator_score_uses_scoring_input_signals() -> None:
    orchestrator = ScoringOrchestrator()
    rich_input = ScoringInput(
        run_id=1,
        keyword_id=1201,
        profile_name="default",
        demand_signals=_base_demand_inputs(),
        competition_signals=_base_competition_inputs(),
        feasibility_signals=_base_feasibility_inputs(),
        profitability_signals=_base_profitability_inputs(),
        intent_signals=_base_intent_inputs(),
        saturation_signals=_base_saturation_inputs(),
        weakness_signals=_base_weakness_inputs(),
        trend_signals=_base_trend_inputs(),
    )
    sparse_input = replace(
        rich_input,
        demand_signals={},
        competition_signals={},
        feasibility_signals={},
        profitability_signals={},
        intent_signals={},
        saturation_signals={},
        weakness_signals={},
        trend_signals={},
    )

    rich_output = orchestrator.score(rich_input)
    sparse_output = orchestrator.score(sparse_input)

    assert rich_output.composite_score > sparse_output.composite_score
    assert rich_output.raw_json.get("component_scores", {}).get("demand_score") is not None


def test_orchestrator_run_context_marks_missing_reddit_signals() -> None:
    orchestrator = ScoringOrchestrator()
    demand_inputs = _base_demand_inputs()
    demand_inputs["reddit_demand_intent_score"] = None
    intent_inputs = _base_intent_inputs()
    intent_inputs["reddit_demand_intent_score"] = None
    trend_inputs = _base_trend_inputs()
    trend_inputs["reddit_recent_post_volume"] = None
    trend_inputs["reddit_historical_post_volume"] = None

    db = _db_with_inputs(
        demand_inputs=demand_inputs,
        competition_inputs=_base_competition_inputs(),
        feasibility_inputs=_base_feasibility_inputs(),
        profitability_inputs=_base_profitability_inputs(),
        intent_inputs=intent_inputs,
        saturation_inputs=_base_saturation_inputs(),
        weakness_inputs=_base_weakness_inputs(),
        trend_inputs=trend_inputs,
        keyword_id=1201,
    )
    result = orchestrator.run([1201], db, profile="default")
    confidence_breakdown = result.keyword_results[0]["confidence_breakdown"]
    assert confidence_breakdown["missing_reddit_signals"] == -0.05


def test_trend_fabricated_llm_default_excluded_from_weight() -> None:
    """Rank-12 (gap-audit-2 P1, SCRUM-1100): with no llm_client (every real call site)
    and no pre-stored classification, the fabricated "STABLE" default must be excluded
    from the weighted average like any other missing signal - previously it was blended
    in at the full 20% weight, permanently propping every production trend score toward
    the neutral 50."""
    calculator = TrendScoreCalculator()
    inputs = _base_trend_inputs()
    del inputs["llm_trend_classification"]
    result = calculator.calculate(901, _db_with_inputs(trend_inputs=inputs, keyword_id=901))

    component = result.score_components["llm_trend_classification"]
    assert component.weight == 0.0
    assert component.raw is None
    assert result.total_weight_available == pytest.approx(0.80)  # slope+accel+reddit only
    assert "llm.trend_classification" not in result.source_evidence

    # The score must equal the weighted average of the REAL signals alone.
    real = [
        (result.score_components["google_trends_slope"], 0.40),
        (result.score_components["google_trends_acceleration"], 0.25),
        (result.score_components["reddit_activity_trend"], 0.15),
    ]
    expected = sum(c.value * w for c, w in real) / sum(w for _, w in real)
    assert result.score_value == pytest.approx(round(expected, 2))


def test_trend_prestored_llm_classification_still_counts_at_full_weight() -> None:
    """A REAL pre-stored classification signal keeps its full 20% weight."""
    calculator = TrendScoreCalculator()
    result = calculator.calculate(
        901, _db_with_inputs(trend_inputs=_base_trend_inputs(), keyword_id=901)
    )
    component = result.score_components["llm_trend_classification"]
    assert component.weight == pytest.approx(0.20)
    assert component.raw == "RISING"
    assert result.total_weight_available == pytest.approx(1.0)
    assert "llm.trend_classification" in result.source_evidence


def test_trend_fabricated_llm_cannot_rescue_insufficient_coverage() -> None:
    """Reddit alone is 0.15 weight (< 0.30 minimum). Previously the fabricated LLM
    default added 0.20 fake weight, pushing coverage to 0.35 and producing a score
    built almost entirely from an invented value; now this honestly returns None."""
    calculator = TrendScoreCalculator()
    inputs = {
        "reddit_recent_post_volume": 30.0,
        "reddit_historical_post_volume": 20.0,
    }
    result = calculator.calculate(901, _db_with_inputs(trend_inputs=inputs, keyword_id=901))
    assert result.score_value is None
    assert "Insufficient" in (result.confidence_reason or "")


def test_orchestrator_calculator_failure_produces_error_entry_not_fake_pass(monkeypatch) -> None:
    """Rank-12 (gap-audit-2 P1, SCRUM-1102): a crashed calculator previously produced a
    fabricated final_score=0.0 / tag="PASS" entry structurally indistinguishable from a
    legitimately-scored low keyword - silent data-quality regressions could ship to
    paying users as real "pass" verdicts. Failures must now be visibly machine-
    detectable ERROR entries."""
    orchestrator = ScoringOrchestrator()

    def _boom(*args, **kwargs):
        raise RuntimeError("calculator exploded")

    monkeypatch.setattr(orchestrator._demand_calculator, "calculate", _boom)  # noqa: SLF001
    db = _db_with_inputs(keyword_id=1301)
    result = orchestrator.run([1301], db, profile="default")

    entry = result.keyword_results[0]
    assert entry["tag"] == "ERROR"
    assert entry["scoring_failed"] is True
    assert entry["final_score"] is None
    assert "calculator exploded" in entry["error"]
    assert "calculator exploded" in entry["final_payload"]["explanation_text"]
    assert entry["final_payload"]["tag"] == "ERROR"
    # The failure is also recorded in the run-level error list.
    assert any("1301" in message for message in result.errors)


def test_orchestrator_error_entries_rank_below_real_results(monkeypatch) -> None:
    """ERROR entries sort to the bottom of rankings and group separately from every
    legitimate tag - never mixed into real PASS results."""
    orchestrator = ScoringOrchestrator()
    original_calculate = orchestrator._demand_calculator.calculate  # noqa: SLF001

    def _boom_only_1302(keyword_id, db, *args, **kwargs):
        if keyword_id == 1302:
            raise RuntimeError("calculator exploded")
        return original_calculate(keyword_id, db, *args, **kwargs)

    monkeypatch.setattr(orchestrator._demand_calculator, "calculate", _boom_only_1302)  # noqa: SLF001
    db = _db_with_inputs(
        demand_inputs=_base_demand_inputs(),
        competition_inputs=_base_competition_inputs(),
        feasibility_inputs=_base_feasibility_inputs(),
        profitability_inputs=_base_profitability_inputs(),
        intent_inputs=_base_intent_inputs(),
        saturation_inputs=_base_saturation_inputs(),
        weakness_inputs=_base_weakness_inputs(),
        trend_inputs=_base_trend_inputs(),
        keyword_id=1301,
    )
    result = orchestrator.run([1301, 1302], db, profile="default")

    assert result.ranked_keywords[-1]["keyword_id"] == 1302  # errored entry ranks last
    assert result.ranked_keywords[-1]["tag"] == "ERROR"
    grouped = result.grouped_rankings
    assert [kw["keyword_id"] for kw in grouped.get("ERROR", [])] == [1302]
    assert all(kw["keyword_id"] != 1302 for kw in grouped.get("PASS", []))
