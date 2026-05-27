"""Cycle 045 scoring math regressions for profitability and weakness helpers."""

from __future__ import annotations

import math

import pytest
from src.scoring.profitability import ProfitabilityScoreCalculator
from src.scoring.weakness import compute_weakness_penalty_from_flags

# pylint: disable=protected-access


_NORM_WITH_UNIVERSE_CASES: list[tuple[float, float | None, float | None]] = [
    (-10.0, None, None),
    (0.0, None, None),
    (20.0, None, None),
    (50.0, None, None),
    (120.0, None, None),
    (220.0, None, None),
    (300.0, None, None),
    (420.0, None, None),
    (0.0, 0.0, 100.0),
    (25.0, 0.0, 100.0),
    (50.0, 0.0, 100.0),
    (75.0, 0.0, 100.0),
    (100.0, 0.0, 100.0),
    (125.0, 0.0, 100.0),
    (10.0, 10.0, 10.0),
    (11.0, 10.0, 10.0),
    (9.0, 10.0, 10.0),
    (150.0, 100.0, 200.0),
    (100.0, 100.0, 200.0),
    (200.0, 100.0, 200.0),
    (250.0, 100.0, 200.0),
    (50.0, 100.0, 200.0),
    (180.0, 150.0, 450.0),
    (450.0, 150.0, 450.0),
]


@pytest.mark.parametrize(("value", "universe_min", "universe_max"), _NORM_WITH_UNIVERSE_CASES)
def test_profitability_normalize_with_universe_regression(
    value: float,
    universe_min: float | None,
    universe_max: float | None,
) -> None:
    """Guard normalization logic, default bounds, and clamp behavior."""
    if universe_min is None:
        min_bound = 20.0
    else:
        min_bound = universe_min
    if universe_max is None:
        max_bound = 300.0
    else:
        max_bound = universe_max

    if max_bound <= min_bound:
        expected = max(0.0, min(100.0, value))
    else:
        expected = max(0.0, min(100.0, ((value - min_bound) / (max_bound - min_bound)) * 100.0))

    actual = ProfitabilityScoreCalculator._normalize_with_universe(value, universe_min, universe_max)
    assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-9)


_DELIVERY_DAYS_CASES: list[float] = [
    -1.0,
    0.0,
    0.25,
    0.5,
    1.0,
    1.5,
    2.0,
    3.0,
    4.0,
    5.0,
    7.0,
    10.0,
    12.0,
    14.0,
    21.0,
    30.0,
    45.0,
    60.0,
    90.0,
    120.0,
]


@pytest.mark.parametrize("delivery_days", _DELIVERY_DAYS_CASES)
def test_profitability_normalize_delivery_days_regression(delivery_days: float) -> None:
    """Lock delivery-day scoring curve and clamps across common ranges."""
    if delivery_days <= 0:
        expected = 100.0
    else:
        expected = max(0.0, min(100.0, 100.0 - ((math.log10(delivery_days + 1.0) / 2.0) * 100.0)))

    actual = ProfitabilityScoreCalculator._normalize_delivery_days(delivery_days)
    assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-9)


_WEAKNESS_FLAG_CASES: list[tuple[list[str], float]] = [
    ([], 0.0),
    (["NO_VIDEO"], 25.0),
    (["NO_PORTFOLIO"], 20.0),
    (["THIN_DESCRIPTION"], 35.0),
    (["NO_FAQ"], 20.0),
    (["NO_VIDEO", "NO_PORTFOLIO"], 45.0),
    (["NO_VIDEO", "THIN_DESCRIPTION"], 60.0),
    (["NO_VIDEO", "NO_FAQ"], 45.0),
    (["NO_PORTFOLIO", "THIN_DESCRIPTION"], 55.0),
    (["NO_PORTFOLIO", "NO_FAQ"], 40.0),
    (["THIN_DESCRIPTION", "NO_FAQ"], 55.0),
    (["NO_VIDEO", "NO_PORTFOLIO", "THIN_DESCRIPTION"], 80.0),
    (["NO_VIDEO", "NO_PORTFOLIO", "NO_FAQ"], 65.0),
    (["NO_VIDEO", "THIN_DESCRIPTION", "NO_FAQ"], 80.0),
    (["NO_PORTFOLIO", "THIN_DESCRIPTION", "NO_FAQ"], 75.0),
    (["NO_VIDEO", "NO_PORTFOLIO", "THIN_DESCRIPTION", "NO_FAQ"], 100.0),
    (["video absent"], 25.0),
    (["portfolio_missing"], 20.0),
    (["description-thin"], 35.0),
    (["faq absent"], 20.0),
]


@pytest.mark.parametrize(("flags", "expected_penalty"), _WEAKNESS_FLAG_CASES)
def test_weakness_flag_penalty_regression(flags: list[str], expected_penalty: float) -> None:
    """Ensure flag aliasing and additive penalty math remain stable."""
    assert compute_weakness_penalty_from_flags(flags) == expected_penalty
