"""Integration tests for R4 scoring integrity invariants."""
from __future__ import annotations

from src.models import ResultSetValidation
from src.scoring.pipeline import SCORING_PROFILES, calculate_weighted_composite
from src.scoring.result_set_relevance import apply_trc_adjustments


def test_weighted_composite_inverts_competition_and_saturation_axes() -> None:
    low_friction_scores: dict[str, float | None] = {
        "demand_score": 70.0,
        "competition_score": 20.0,
        "opportunity_score": 70.0,
        "feasibility_score": 65.0,
        "profitability_score": 60.0,
        "intent_score": 60.0,
        "saturation_score": 15.0,
        "weakness_score": 55.0,
        "trend_score": 58.0,
    }
    high_friction_scores: dict[str, float | None] = {
        **low_friction_scores,
        "competition_score": 85.0,
        "saturation_score": 90.0,
    }
    low_friction_value, low_components = calculate_weighted_composite(low_friction_scores, SCORING_PROFILES["default"])
    high_friction_value, high_components = calculate_weighted_composite(high_friction_scores, SCORING_PROFILES["default"])
    assert low_friction_value > high_friction_value
    assert low_components["competition_score"]["effective_value"] == 80.0
    assert high_components["competition_score"]["effective_value"] == 15.0
    assert low_components["saturation_score"]["effective_value"] == 85.0


def test_trc_adjustments_use_conservative_single_multiplier() -> None:
    rsv = ResultSetValidation()
    rsv.result_set_relevance_score = 0.55
    adjusted = apply_trc_adjustments(trc=1000.0, rsv=rsv, sponsored_fraction=0.35)
    r2_only = apply_trc_adjustments(trc=1000.0, rsv=rsv, sponsored_fraction=0.10)
    r3_only = apply_trc_adjustments(trc=1000.0, rsv=None, sponsored_fraction=0.35)
    assert adjusted == 550.0
    assert r2_only == 550.0
    assert r3_only == 650.0
    assert adjusted <= r2_only <= 1000.0


def test_weighted_composite_stays_clamped_and_components_are_present() -> None:
    extreme_scores: dict[str, float | None] = {
        "demand_score": 150.0,
        "competition_score": -10.0,
        "opportunity_score": 200.0,
        "feasibility_score": 130.0,
        "profitability_score": 140.0,
        "intent_score": 160.0,
        "saturation_score": -50.0,
        "weakness_score": 145.0,
        "trend_score": 170.0,
    }
    value, components = calculate_weighted_composite(extreme_scores, SCORING_PROFILES["default"])
    assert 0.0 <= value <= 100.0
    assert components["demand_score"]["contribution"] is not None
    assert components["competition_score"]["effective_value"] == 110.0
    assert components["saturation_score"]["effective_value"] == 150.0
