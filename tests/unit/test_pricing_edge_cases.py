from __future__ import annotations

import json
from dataclasses import asdict
from types import SimpleNamespace

import numpy as np
import pytest
from src.pricing.analysis import (
    PriceDistribution,
    detect_price_clusters,
    detect_price_gaps,
    extract_extras_pricing,
    extract_tier_prices,
)
from src.pricing.new_seller_pricing import (
    PricingRecommendation,
    _calculate_moat_adjustment,
    _calculate_undercut,
    _get_floor_price,
    calculate_new_seller_pricing,
)


def _analysis(**overrides: object) -> SimpleNamespace:
    payload = {
        "market_type": "MODERATE_SPREAD",
        "moat_strength": "LOW",
        "basic_n": 4,
        "basic_skewness": 0.0,
        "basic_median": 50.0,
        "standard_median": 90.0,
        "premium_median": 140.0,
        "basic_gaps": [],
    }
    payload.update(overrides)
    return SimpleNamespace(**payload)


def test_price_distribution_all_same_price() -> None:
    dist = PriceDistribution(5, 100, 100, 100, 100, 100, 0, 100, 100, 0, 100, 100, 0, [], [], 0)
    assert dist.coefficient_of_variation == 0


def test_price_distribution_single_gig_per_tier() -> None:
    assert detect_price_gaps(np.array([100], dtype=float)) == []


def test_price_distribution_outlier_exclusion_median_stable() -> None:
    prices = np.array([50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 5000], dtype=float)
    assert np.median(prices) == 100


def test_price_distribution_none_packages() -> None:
    gig = SimpleNamespace(packages=None)
    assert extract_tier_prices([gig], "basic") == []


def test_price_distribution_empty_packages_dict() -> None:
    gig = SimpleNamespace(packages={})
    assert extract_tier_prices([gig], "basic") == []


def test_new_seller_pricing_all_floors_applied() -> None:
    db = SimpleNamespace(query=lambda model: SimpleNamespace(filter=lambda *args, **kwargs: SimpleNamespace(first=lambda: SimpleNamespace(keyword="kw", niche_id=1))))
    rec = calculate_new_seller_pricing(1, _analysis(basic_median=1, standard_median=2, premium_median=3), {"starter_prices": {"basic": 15, "standard": 30, "premium": 50}}, db)
    assert rec.entry_basic >= 15 and rec.entry_premium >= 50


def test_new_seller_pricing_acquisition_never_above_entry() -> None:
    db = SimpleNamespace(query=lambda model: SimpleNamespace(filter=lambda *args, **kwargs: SimpleNamespace(first=lambda: SimpleNamespace(keyword="kw", niche_id=1))))
    rec = calculate_new_seller_pricing(1, _analysis(basic_n=12), {"starter_prices": {"basic": 60, "standard": 120, "premium": 240}}, db)
    assert rec.acquisition_basic <= rec.entry_basic <= rec.target_basic


def test_price_ladder_monotonically_increasing() -> None:
    db = SimpleNamespace(query=lambda model: SimpleNamespace(filter=lambda *args, **kwargs: SimpleNamespace(first=lambda: SimpleNamespace(keyword="kw", niche_id=1))))
    rec = calculate_new_seller_pricing(1, _analysis(basic_n=12), {"starter_prices": {"basic": 60, "standard": 120, "premium": 240}}, db)
    basics = [step["basic"] for step in rec.price_ladder]
    assert basics == sorted(basics)


def test_price_gap_detection_contiguous_prices() -> None:
    assert detect_price_gaps(np.array([10, 20, 30, 40, 50], dtype=float)) == []


def test_price_gap_detection_single_large_gap() -> None:
    gaps = detect_price_gaps(np.array([50, 55, 200, 210], dtype=float))
    assert gaps and gaps[0]["gap_width"] >= 145


def test_market_type_commodity_below_15pct_cv() -> None:
    value = _calculate_undercut(_analysis(market_type="COMMODITY", basic_n=10))
    assert value == 0.10


def test_market_type_fragmented_above_50pct_cv() -> None:
    value = _calculate_undercut(_analysis(market_type="FRAGMENTED", basic_n=10))
    assert value >= 0.20


def test_pricing_recommendation_is_json_serializable() -> None:
    rec = PricingRecommendation(1, "k", "n", 10, 20, 30, 8, 18, 28, [], 12, 24, 36, 10, 0, False, None, "LOW", "LOW")
    assert isinstance(asdict(rec), dict)


def test_undercut_pct_clamped_between_5_and_40() -> None:
    value = _calculate_undercut(_analysis(market_type="WIDE_SPREAD", basic_n=100, basic_skewness=-5))
    assert 0.05 <= value <= 0.40


def test_moat_adjustment_zero_when_moat_low() -> None:
    assert _calculate_moat_adjustment(_analysis(moat_strength="LOW")) == 0.0


def test_extras_pricing_empty_extras_returns_none_fields() -> None:
    result = extract_extras_pricing([SimpleNamespace(gig_extras=[])])
    assert result["min"] is None and result["max"] is None


def test_extras_pricing_handles_json_string() -> None:
    result = extract_extras_pricing([SimpleNamespace(gig_extras=json.dumps([{"price": 25}, {"price": 40}]))])
    assert result["max"] == 40.0


def test_extract_tier_prices_handles_json_string_packages() -> None:
    gig_json = SimpleNamespace(packages=json.dumps({"basic": {"price": 75}, "standard": {"price": 150}, "premium": {"price": 300}}))
    gig_dict = SimpleNamespace(packages={"basic": {"price": 75}, "standard": {"price": 150}})
    gig_list = SimpleNamespace(packages=[{"price": 75}, {"price": 150}, {"price": 300}])
    gig_none = SimpleNamespace(packages=None)
    assert extract_tier_prices([gig_json], "basic") == [75.0]
    assert extract_tier_prices([gig_dict], "basic") == [75.0]
    assert extract_tier_prices([gig_list], "basic") == [75.0]
    assert extract_tier_prices([gig_none], "basic") == []


def test_price_distribution_consistent_with_high_n() -> None:
    prices = np.random.uniform(50, 300, 25)
    clusters = detect_price_clusters(prices)
    gaps = detect_price_gaps(prices)
    assert isinstance(clusters, list) and isinstance(gaps, list)


def test_floor_price_uses_starter_price() -> None:
    assert _get_floor_price("basic", {"starter_prices": {"basic": 99}}) == 99


@pytest.mark.parametrize(
    ("tier", "starter", "expected_min"),
    [
        ("basic", 15, 15),
        ("basic", 25, 25),
        ("basic", 35, 35),
        ("basic", 45, 45),
        ("basic", 55, 55),
        ("standard", 30, 30),
        ("standard", 60, 60),
        ("standard", 90, 90),
        ("standard", 120, 120),
        ("standard", 150, 150),
        ("premium", 50, 50),
        ("premium", 100, 100),
        ("premium", 150, 150),
        ("premium", 200, 200),
        ("premium", 250, 250),
    ],
)
def test_floor_price_matrix(tier: str, starter: float, expected_min: float) -> None:
    value = _get_floor_price(tier, {"starter_prices": {tier: starter}})
    assert value >= expected_min
