"""Unit tests for S4.1/S4.2/S4.3 scoring calculators."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.demand import DemandScoreCalculator
from src.scoring.opportunity import OpportunityScoreCalculator


class FakeScoringDB:
    """Simple in-memory signal source for scoring tests."""

    def __init__(
        self,
        demand_inputs: dict[int, dict[str, Any]] | None = None,
        competition_inputs: dict[int, dict[str, Any]] | None = None,
    ) -> None:
        self._demand_inputs = demand_inputs or {}
        self._competition_inputs = competition_inputs or {}

    def get_demand_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._demand_inputs.get(keyword_id, {})

    def get_competition_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._competition_inputs.get(keyword_id, {})


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
    keyword_id: int = 101,
) -> FakeScoringDB:
    return FakeScoringDB(
        demand_inputs={keyword_id: demand_inputs or {}},
        competition_inputs={keyword_id: competition_inputs or {}},
    )


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
