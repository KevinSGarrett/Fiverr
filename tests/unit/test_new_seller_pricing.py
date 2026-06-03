from __future__ import annotations

from dataclasses import asdict
from types import SimpleNamespace

import pytest

from src.pricing.new_seller_pricing import (
    PricingRecommendation,
    _assess_pricing_confidence,
    _build_price_ladder,
    _calculate_moat_adjustment,
    _calculate_undercut,
    _find_gap_opportunity,
    _get_floor_price,
    calculate_new_seller_pricing,
    to_dict,
)


class _FakeQuery:
    def __init__(self, row: object | None) -> None:
        self._row = row

    def filter(self, *args: object, **kwargs: object) -> _FakeQuery:
        return self

    def first(self) -> object | None:
        return self._row


class _FakeDB:
    def __init__(self, keyword: object | None, niche: object | None = None) -> None:
        self._keyword = keyword
        self._niche = niche

    def query(self, model: object) -> _FakeQuery:
        name = getattr(model, "__name__", "")
        if name == "Niche":
            return _FakeQuery(self._niche)
        return _FakeQuery(self._keyword)


def _analysis(**overrides: object) -> SimpleNamespace:
    payload = {
        "market_type": "MODERATE_SPREAD",
        "moat_strength": "MEDIUM",
        "basic_n": 12,
        "basic_skewness": 0.1,
        "basic_median": 100.0,
        "standard_median": 180.0,
        "premium_median": 280.0,
        "basic_gaps": [],
    }
    payload.update(overrides)
    return SimpleNamespace(**payload)


def _config() -> dict[str, object]:
    return {"starter_prices": {"basic": 60, "standard": 120, "premium": 240}}


def test_calculate_new_seller_pricing_full_data() -> None:
    db = _FakeDB(SimpleNamespace(id=1, keyword="kw", niche_id=11), SimpleNamespace(slug="python_automation"))
    rec = calculate_new_seller_pricing(1, _analysis(), _config(), db)
    assert rec.entry_basic > 0 and rec.target_premium >= rec.entry_premium


def test_entry_prices_maintain_ordering() -> None:
    db = _FakeDB(SimpleNamespace(id=1, keyword="kw", niche_id=11), SimpleNamespace(slug="python_automation"))
    rec = calculate_new_seller_pricing(1, _analysis(), _config(), db)
    assert rec.entry_basic < rec.entry_standard < rec.entry_premium


def test_entry_prices_never_below_floor() -> None:
    db = _FakeDB(SimpleNamespace(id=1, keyword="kw", niche_id=11), SimpleNamespace(slug="python_automation"))
    rec = calculate_new_seller_pricing(1, _analysis(basic_median=1, standard_median=2, premium_median=3), _config(), db)
    assert rec.entry_basic >= 60


def test_acquisition_prices_le_entry_basic() -> None:
    db = _FakeDB(SimpleNamespace(id=1, keyword="kw", niche_id=11), SimpleNamespace(slug="python_automation"))
    rec = calculate_new_seller_pricing(1, _analysis(), _config(), db)
    assert rec.acquisition_basic <= rec.entry_basic


def test_price_ladder_exactly_5_milestones() -> None:
    ladder = _build_price_ladder(60, 120, 240, 100, 180, 300)
    assert [step["milestone"] for step in ladder] == [5, 10, 25, 50, 100]


def test_price_ladder_monotonic_increase() -> None:
    ladder = _build_price_ladder(60, 120, 240, 100, 180, 300)
    assert ladder[0]["basic"] <= ladder[-1]["basic"]


def test_target_prices_at_or_above_median() -> None:
    db = _FakeDB(SimpleNamespace(id=1, keyword="kw", niche_id=11), SimpleNamespace(slug="python_automation"))
    analysis = _analysis(basic_median=100, standard_median=200, premium_median=300)
    rec = calculate_new_seller_pricing(1, analysis, _config(), db)
    assert rec.target_basic >= 100


def test_commodity_market_undercut() -> None:
    assert _calculate_undercut(_analysis(market_type="COMMODITY", basic_n=10, basic_skewness=0)) == 0.10


def test_wide_spread_market_undercut() -> None:
    assert _calculate_undercut(_analysis(market_type="WIDE_SPREAD", basic_n=10, basic_skewness=0)) == 0.25


def test_high_moat_extra_discount() -> None:
    assert _calculate_moat_adjustment(_analysis(moat_strength="HIGH")) == 0.10


def test_gap_target_used_when_lower_than_entry() -> None:
    db = _FakeDB(SimpleNamespace(id=1, keyword="kw", niche_id=11), SimpleNamespace(slug="python_automation"))
    analysis = _analysis(basic_gaps=[{"gap_midpoint": 50, "gap_width": 40, "pct_of_range": 30}], basic_median=100)
    rec = calculate_new_seller_pricing(1, analysis, _config(), db)
    assert rec.gap_pricing_used is True and rec.entry_basic == 60.0


def test_confidence_high_when_n_at_least_10() -> None:
    assert _assess_pricing_confidence(_analysis(basic_n=10)) == "HIGH"


def test_confidence_low_when_n_below_5() -> None:
    assert _assess_pricing_confidence(_analysis(basic_n=4)) == "LOW"


def test_calculate_undercut_clamped_range() -> None:
    value = _calculate_undercut(_analysis(market_type="WIDE_SPREAD", basic_n=99, basic_skewness=-2))
    assert 0.05 <= value <= 0.40


def test_get_floor_price_reads_starter_prices() -> None:
    assert _get_floor_price("basic", _config()) == 60


def test_pricing_recommendation_serializable_to_dict() -> None:
    rec = PricingRecommendation(1, "k", "n", 10, 20, 30, 8, 18, 28, [], 12, 24, 36, 10, 5, False, None, "COMMODITY", "LOW")
    assert isinstance(to_dict(rec), dict)


def test_dataclass_round_trip() -> None:
    rec = PricingRecommendation(1, "k", "n", 10, 20, 30, 8, 18, 28, [], 12, 24, 36, 10, 5, False, None, "COMMODITY", "LOW")
    clone = PricingRecommendation(**asdict(rec))
    assert clone.entry_standard == rec.entry_standard


def test_crowded_market_additional_undercut() -> None:
    assert _calculate_undercut(_analysis(market_type="MODERATE_SPREAD", basic_n=20, basic_skewness=0)) == 0.25


def test_right_skewed_market_less_undercut() -> None:
    assert _calculate_undercut(_analysis(market_type="MODERATE_SPREAD", basic_n=10, basic_skewness=0.8)) == 0.15000000000000002


def test_build_price_ladder_milestone_count_matches_expected() -> None:
    ladder = _build_price_ladder(70, 130, 250, 110, 190, 330)
    assert len(ladder) == 5


def test_find_gap_opportunity_returns_tuple() -> None:
    gap = _find_gap_opportunity(_analysis(basic_gaps=[{"gap_midpoint": 70, "gap_width": 30, "pct_of_range": 20}], basic_median=120))
    assert gap == (70.0, True)


def test_pricing_package_imports_exposed() -> None:
    from src.pricing import PriceDistribution as ImportedDistribution, PricingRecommendation as ImportedRecommendation

    assert ImportedDistribution is not None
    assert ImportedRecommendation is not None


@pytest.mark.parametrize(
    ("market_type", "basic_n", "skew"),
    [
        ("COMMODITY", 3, 0.0),
        ("COMMODITY", 6, 0.2),
        ("COMMODITY", 20, 0.1),
        ("MODERATE_SPREAD", 4, 0.0),
        ("MODERATE_SPREAD", 8, 0.0),
        ("MODERATE_SPREAD", 18, 0.0),
        ("MODERATE_SPREAD", 18, 0.8),
        ("MODERATE_SPREAD", 18, -0.6),
        ("WIDE_SPREAD", 4, 0.0),
        ("WIDE_SPREAD", 8, 0.0),
        ("WIDE_SPREAD", 18, 0.0),
        ("WIDE_SPREAD", 18, 0.9),
        ("WIDE_SPREAD", 18, -0.7),
        ("FRAGMENTED", 4, 0.0),
        ("FRAGMENTED", 8, 0.0),
        ("FRAGMENTED", 18, 0.0),
        ("FRAGMENTED", 18, 0.9),
        ("FRAGMENTED", 18, -0.7),
        ("UNKNOWN", 2, 0.0),
        ("UNKNOWN", 30, -1.0),
    ],
)
def test_undercut_matrix_is_clamped(market_type: str, basic_n: int, skew: float) -> None:
    value = _calculate_undercut(_analysis(market_type=market_type, basic_n=basic_n, basic_skewness=skew))
    assert 0.05 <= value <= 0.40
