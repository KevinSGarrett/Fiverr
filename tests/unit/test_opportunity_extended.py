"""Extended opportunity qualifier tests."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest
from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.demand import DemandScoreCalculator
from src.scoring.opportunity import (
    OpportunityScoreCalculator,
    _opportunity_config,
    _opportunity_relevance_qualifier,
)


class _FakeDB:
    def __init__(self, payload: dict[int, dict[str, Any]]) -> None:
        self._payload = payload

    def get_demand_inputs(self, keyword_id: int) -> dict[str, Any]:
        return dict(self._payload.get(keyword_id, {}))

    def get_competition_inputs(self, keyword_id: int) -> dict[str, Any]:
        return dict(self._payload.get(keyword_id, {}))

    def get_opportunity_inputs(self, keyword_id: int) -> dict[str, Any]:
        return dict(self._payload.get(keyword_id, {}))

    def get_intent_inputs(self, keyword_id: int) -> dict[str, Any]:
        return dict(self._payload.get(keyword_id, {}))


def _demand() -> Any:
    return replace(
        DemandScoreCalculator().calculate(1, _FakeDB({1: {"total_result_count": 1000, "autocomplete_position": 2}})),
        score_value=80.0,
    )


def _competition() -> Any:
    return replace(
        CompetitionScoreCalculator().calculate(
            1,
            _FakeDB(
                {
                    1: {
                        "total_result_count": 1000,
                        "avg_review_count_top10": 120.0,
                        "avg_seller_level_top10": "Level 2",
                        "proportion_with_100_plus_reviews": 0.4,
                        "pro_verified_presence_ratio": 0.2,
                        "avg_starting_price_top10": 40.0,
                        "llm_competitor_strength_rating": 5.0,
                    }
                }
            ),
        ),
        score_value=40.0,
    )


def _competition_for_raw_80() -> Any:
    # raw opportunity = (80 * 1.2) - (20 * 0.8) = 80
    return replace(_competition(), score_value=20.0)


def _competition_for_negative_raw() -> Any:
    # raw opportunity = (80 * 1.2) - (140 * 0.8) = -16
    return replace(_competition(), score_value=140.0)


def _expected_normalized(raw_value: float) -> float:
    return pytest.approx(round(min(100.0, max(0.0, ((raw_value + 80.0) / 200.0) * 100.0)), 2))


def test_opportunity_scaled_by_rsv() -> None:
    # RSV=0.60 is below the R4.7 threshold (0.70) and matches the spec's own
    # worked example: multiplier = 0.50 + 0.50*0.60 = 0.80.
    baseline = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {}}),
        demand_result=_demand(),
        competition_result=_competition_for_raw_80(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": False}}},
    )
    qualified = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {"rsv_relevance": 0.60}}),
        demand_result=_demand(),
        competition_result=_competition_for_raw_80(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": True}}},
    )
    assert baseline.score_value == _expected_normalized(80.0)
    assert qualified.score_value == _expected_normalized(64.0)
    assert qualified.opportunity_relevance_factor == pytest.approx(0.80)


def test_opportunity_qualified_by_relevance() -> None:
    result = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {"rsv_relevance": 0.60, "query_intent_class": "TRANSACTIONAL", "service_intent_class": "TRANSACTIONAL"}}),
        demand_result=_demand(),
        competition_result=_competition_for_raw_80(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": True}}},
    )
    assert result.score_value == _expected_normalized(64.0)
    assert result.opportunity_relevance_factor == pytest.approx(0.80)


def test_opportunity_relevance_at_or_above_threshold_unchanged() -> None:
    """R4.7: RSV >= 0.70 must leave the opportunity score unchanged (only
    contaminated result sets, RSV < 0.70, are qualified/penalized)."""
    baseline = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {}}),
        demand_result=_demand(),
        competition_result=_competition_for_raw_80(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": False}}},
    )
    at_threshold = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {"rsv_relevance": 0.70}}),
        demand_result=_demand(),
        competition_result=_competition_for_raw_80(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": True}}},
    )
    assert at_threshold.opportunity_relevance_factor == pytest.approx(1.0)
    assert at_threshold.score_value == baseline.score_value


def test_relevance_does_not_boost_negative_opportunity() -> None:
    baseline = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {"query_intent_class": "TRANSACTIONAL", "service_intent_class": "TRANSACTIONAL"}}),
        demand_result=_demand(),
        competition_result=_competition_for_negative_raw(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": False}}},
    )
    high_rel = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {"rsv_relevance": 0.9, "query_intent_class": "TRANSACTIONAL", "service_intent_class": "TRANSACTIONAL"}}),
        demand_result=_demand(),
        competition_result=_competition_for_negative_raw(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": True}}},
    )
    low_rel = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {"rsv_relevance": 0.3, "query_intent_class": "TRANSACTIONAL", "service_intent_class": "TRANSACTIONAL"}}),
        demand_result=_demand(),
        competition_result=_competition_for_negative_raw(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": True}}},
    )
    assert baseline.score_value is not None
    assert high_rel.score_value is not None
    assert low_rel.score_value is not None
    assert low_rel.score_value <= high_rel.score_value
    assert low_rel.score_value <= baseline.score_value


def test_opportunity_relevance_none_no_change() -> None:
    result = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {}}),
        demand_result=_demand(),
        competition_result=_competition(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": True}}},
    )
    assert result.opportunity_relevance_factor == 1.0
    assert result.score_value == pytest.approx(72.0)


def test_opportunity_relevance_factor_recorded() -> None:
    result = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {"rsv_relevance": 0.60}}),
        demand_result=_demand(),
        competition_result=_competition(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": True}}},
    )
    assert result.opportunity_relevance_factor == pytest.approx(0.80)


def test_opportunity_qualifier_toggle_off_matches_legacy() -> None:
    legacy = OpportunityScoreCalculator().calculate(1, _FakeDB({1: {}}), demand_result=_demand(), competition_result=_competition())
    off = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {"rsv_relevance": 0.3}}),
        demand_result=_demand(),
        competition_result=_competition(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": False}}},
    )
    assert off.score_value == legacy.score_value


def test_opportunity_relevance_qualifier_clamps() -> None:
    assert _opportunity_relevance_qualifier(None) == 1.0
    assert _opportunity_relevance_qualifier(1.5) == 1.0
    # Below threshold: 0.50 + 0.50*clamp01(rsv). -0.5 clamps to 0.0 -> factor 0.50.
    assert _opportunity_relevance_qualifier(-0.5) == 0.50


def test_opportunity_relevance_qualifier_matches_spec_worked_examples() -> None:
    """OPPORTUNITY_SCORE.md SRDI ADDENDUM effect-examples table (threshold-gated
    reading: unchanged at/above 0.70, else 0.50 + 0.50*rsv)."""
    assert _opportunity_relevance_qualifier(1.00) == pytest.approx(1.0)
    assert _opportunity_relevance_qualifier(0.70) == pytest.approx(1.0)
    assert _opportunity_relevance_qualifier(0.60) == pytest.approx(0.80)
    assert _opportunity_relevance_qualifier(0.40) == pytest.approx(0.70)
    assert _opportunity_relevance_qualifier(0.20) == pytest.approx(0.60)


def test_opportunity_rsv_none_unchanged() -> None:
    baseline = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {}}),
        demand_result=_demand(),
        competition_result=_competition_for_raw_80(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": False}}},
    )
    unchanged = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {"rsv_relevance": None}}),
        demand_result=_demand(),
        competition_result=_competition_for_raw_80(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": True}}},
    )
    assert unchanged.opportunity_relevance_factor == pytest.approx(1.0)
    assert unchanged.score_value == baseline.score_value


def test_opportunity_rsv_clamped() -> None:
    clamped = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {"rsv_relevance": 1.3}}),
        demand_result=_demand(),
        competition_result=_competition_for_raw_80(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": True}}},
    )
    assert clamped.opportunity_relevance_factor == pytest.approx(1.0)
    assert clamped.score_value == _expected_normalized(80.0)


def test_opportunity_factor_recorded() -> None:
    result = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {"rsv_relevance": 0.60}}),
        demand_result=_demand(),
        competition_result=_competition_for_raw_80(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": True}}},
    )
    assert result.opportunity_relevance_factor == pytest.approx(0.80)


def test_opportunity_config_guard_paths() -> None:
    assert _opportunity_config(None) == {}
    assert _opportunity_config({"scoring": "bad"}) == {}
    assert _opportunity_config({"scoring": {"opportunity": "bad"}}) == {}
    assert _opportunity_config({"scoring": {"opportunity": {"qualify_by_relevance": True}}}) == {
        "qualify_by_relevance": True
    }


def test_opportunity_rsv_and_intent_loaded_from_mapping_db() -> None:
    payload = {
        1: {
            "rsv_relevance": 0.60,
            "query_intent_class": "INFORMATIONAL",
            "service_intent_class": "TRANSACTIONAL",
        }
    }
    result = OpportunityScoreCalculator().calculate(
        1,
        payload,
        demand_result=_demand(),
        competition_result=_competition_for_raw_80(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": True}}},
    )
    assert result.opportunity_relevance_factor == pytest.approx(0.80)
    assert result.score_value is not None
