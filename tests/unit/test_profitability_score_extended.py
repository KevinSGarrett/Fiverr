"""Additional Cycle 049 Agent F profitability coverage."""

from __future__ import annotations

from typing import Any

from src.scoring.profitability import ProfitabilityScoreCalculator


class _FakeScoringDB:
    def __init__(self, profitability_inputs: dict[str, Any]) -> None:
        self._profitability_inputs = profitability_inputs

    def get_profitability_inputs(self, _keyword_id: int) -> dict[str, Any]:
        return self._profitability_inputs


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


def _calculate(inputs: dict[str, Any]) -> Any:
    return ProfitabilityScoreCalculator().calculate(110, _FakeScoringDB(inputs))


def test_profitability_with_premium_price_populated() -> None:
    inputs = _base_profitability_inputs()
    inputs["avg_premium_package_price_top10"] = 420.0
    result = _calculate(inputs)
    assert result.score_value is not None
    assert result.score_components["avg_premium_price"].value > 0.0


def test_profitability_with_starting_price_populated() -> None:
    inputs = _base_profitability_inputs()
    inputs["avg_starting_price_top10"] = 150.0
    result = _calculate(inputs)
    assert result.score_value is not None
    assert result.score_components["avg_starting_price"].value > 0.0


def test_profitability_extras_presence_ratio_nonzero() -> None:
    inputs = _base_profitability_inputs()
    inputs["extras_presence_ratio"] = 0.4
    inputs["avg_extras_price"] = 28.0
    result = _calculate(inputs)
    assert result.score_value is not None
    assert result.score_components["gig_extras_upsell"].value > 0.0


def test_profitability_all_three_tiers_present() -> None:
    inputs = _base_profitability_inputs()
    inputs["avg_starting_price_top10"] = 140.0
    inputs["avg_premium_package_price_top10"] = 380.0
    inputs["extras_presence_ratio"] = 0.9
    inputs["avg_extras_price"] = 45.0
    result = _calculate(inputs)
    assert result.score_value is not None
    assert "avg_starting_price" in result.score_components
    assert "avg_premium_price" in result.score_components
    assert "gig_extras_upsell" in result.score_components


def test_profitability_handles_null_premium_gracefully() -> None:
    inputs = _base_profitability_inputs()
    inputs["avg_premium_package_price_top10"] = None
    result = _calculate(inputs)
    assert result.score_value is not None
    assert "avg_premium_price" not in result.score_components


def test_profitability_handles_null_starting_price_gracefully() -> None:
    inputs = _base_profitability_inputs()
    inputs["avg_starting_price_top10"] = None
    result = _calculate(inputs)
    assert result.score_value is not None
    assert "avg_starting_price" not in result.score_components


def test_profitability_kw3_equivalent_low_price_path() -> None:
    inputs = _base_profitability_inputs()
    inputs["avg_starting_price_top10"] = 50.0
    inputs["avg_premium_package_price_top10"] = 50.0
    inputs["typical_delivery_days"] = 7
    inputs["extras_presence_ratio"] = 1.0
    inputs["avg_extras_price"] = 15.0
    result = _calculate(inputs)
    assert result.score_value is not None
    assert 15.0 <= result.score_value <= 40.0


def test_profitability_kw110_equivalent_medium_price_path() -> None:
    inputs = _base_profitability_inputs()
    inputs["avg_starting_price_top10"] = 80.0
    inputs["avg_premium_package_price_top10"] = 80.0
    inputs["typical_delivery_days"] = 5
    inputs["extras_presence_ratio"] = 1.0
    inputs["avg_extras_price"] = 25.0
    result = _calculate(inputs)
    assert result.score_value is not None
    assert 20.0 <= result.score_value <= 45.0
