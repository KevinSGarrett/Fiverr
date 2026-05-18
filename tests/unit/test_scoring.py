"""Unit tests for S4.1/S4.2/S4.3 scoring calculators."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.demand import DemandScoreCalculator
from src.scoring.feasibility import NewSellerFeasibilityCalculator
from src.scoring.intent import ConversionIntentScoreCalculator
from src.scoring.opportunity import OpportunityScoreCalculator
from src.scoring.profitability import ProfitabilityScoreCalculator
from src.scoring.saturation_score import SaturationScoreCalculator


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
    ) -> None:
        self._demand_inputs = demand_inputs or {}
        self._competition_inputs = competition_inputs or {}
        self._feasibility_inputs = feasibility_inputs or {}
        self._profitability_inputs = profitability_inputs or {}
        self._intent_inputs = intent_inputs or {}
        self._saturation_inputs = saturation_inputs or {}

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
    keyword_id: int = 101,
) -> FakeScoringDB:
    return FakeScoringDB(
        demand_inputs={keyword_id: demand_inputs or {}},
        competition_inputs={keyword_id: competition_inputs or {}},
        feasibility_inputs={keyword_id: feasibility_inputs or {}},
        profitability_inputs={keyword_id: profitability_inputs or {}},
        intent_inputs={keyword_id: intent_inputs or {}},
        saturation_inputs={keyword_id: saturation_inputs or {}},
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
