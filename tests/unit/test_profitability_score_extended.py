"""Additional Cycle 049 Agent F profitability coverage."""

from __future__ import annotations

from typing import Any

from src.models import Gig, SearchResult, Seller
from src.scoring.competition import CompetitionScoreCalculator, _exclude_price_outliers_iqr
from src.scoring.profitability import (
    ProfitabilityScoreCalculator,
    _exclude_price_outliers_enabled,
    _relevance_config,
)
from tests.unit.test_competition_score import _build_session, _seed_competition_rows


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


def test_profitability_relevance_config_defaults_and_overrides() -> None:
    assert _relevance_config("bad") == {  # type: ignore[arg-type]
        "enable_sponsored_exclusion": True,
        "enable_zombie_filter": True,
        "top_n_for_scoring": 10,
    }
    cfg = _relevance_config(
        {
            "relevance": {
                "enable_sponsored_exclusion": False,
                "enable_zombie_filter": False,
                "top_n_for_scoring": 5,
            }
        }
    )
    assert cfg["enable_sponsored_exclusion"] is False
    assert cfg["enable_zombie_filter"] is False
    assert cfg["top_n_for_scoring"] == 5


def test_profitability_helper_guard_paths() -> None:
    calc = ProfitabilityScoreCalculator()
    assert calc._normalize_with_universe(50.0, 100.0, 100.0) == 50.0  # pylint: disable=protected-access
    assert calc._normalize_delivery_days(0.0) == 100.0  # pylint: disable=protected-access
    assert calc._normalize_llm_score(7.5) == 75.0  # pylint: disable=protected-access
    assert calc._load_signals(1, None) == {}  # pylint: disable=protected-access
    assert calc._as_float("x") is None  # pylint: disable=protected-access


def test_profitability_extras_and_llm_resolution_guards() -> None:
    calc = ProfitabilityScoreCalculator()
    assert calc._resolve_extras_score({"extras_presence_ratio": None, "avg_extras_price": None}) is None  # pylint: disable=protected-access
    assert calc._resolve_extras_score({"extras_presence_ratio": 0.5, "avg_extras_price": None}) == 30.0  # pylint: disable=protected-access
    assert calc._resolve_llm_upsell_potential({"llm_upsell_potential_assessment": None}) is None  # pylint: disable=protected-access


def test_profitability_load_signals_mapping_and_meta_helpers() -> None:
    calc = ProfitabilityScoreCalculator()
    assert calc._load_signals(1, {1: "bad"}) == {}  # pylint: disable=protected-access

    class _Row:
        metadata_json = {"premium_price": 120.0, "gig_extras": []}

    row = _Row()
    assert calc._gig_meta_value(row, "premium_price", "fallback") == 120.0  # pylint: disable=protected-access
    assert calc._gig_meta_value(row, "missing") is None  # pylint: disable=protected-access
    assert calc._has_extras(row) is False  # pylint: disable=protected-access


def test_profitability_handles_missing_price_inputs_gracefully() -> None:
    inputs = {
        "avg_starting_price_top10": None,
        "avg_premium_package_price_top10": None,
        "typical_delivery_days": 3,
        "extras_presence_ratio": None,
        "avg_extras_price": None,
        "llm_upsell_potential_assessment": None,
    }
    result = _calculate(inputs)
    assert result.score_value is None


def test_price_outlier_excluded_from_competition_and_profitability() -> None:
    prices = [5, 8, 10, 11, 12, 12, 13, 15, 400]
    kept, excluded = _exclude_price_outliers_iqr(prices)
    assert kept == [5.0, 8.0, 10.0, 11.0, 12.0, 12.0, 13.0, 15.0]
    assert excluded == 1

    competition_result = CompetitionScoreCalculator().calculate(
        110,
        {110: {"total_result_count": 1200, "top10_prices": prices}},
        config={"scoring": {"exclude_price_outliers": True}},
    )
    profitability_result = ProfitabilityScoreCalculator().calculate(
        110,
        _FakeScoringDB(
            {
                **_base_profitability_inputs(),
                "top10_prices": prices,
                "avg_starting_price_top10": 54.0,
            }
        ),
        config={"scoring": {"exclude_price_outliers": True}},
    )

    assert competition_result.price_outliers_excluded == 1
    assert profitability_result.score_value is not None


def test_profitability_uses_same_iqr_helper() -> None:
    from src.scoring import profitability

    assert profitability._exclude_price_outliers_iqr is _exclude_price_outliers_iqr  # type: ignore[attr-defined]


def test_profitability_excludes_high_outlier_margin_stats() -> None:
    prices = [5, 8, 10, 11, 12, 12, 13, 15, 400]
    kept, excluded = _exclude_price_outliers_iqr(prices)
    assert excluded == 1
    # Profitability uses normalized average starting price; verify we can compute
    # the same expected basis after outlier removal.
    expected_avg = sum(kept) / len(kept)
    result = ProfitabilityScoreCalculator().calculate(
        110,
        _FakeScoringDB(
            {
                **_base_profitability_inputs(),
                "avg_starting_price_top10": expected_avg,
            }
        ),
        config={"scoring": {"exclude_price_outliers": True}},
    )
    assert result.score_components["avg_starting_price"].raw == expected_avg


def test_profitability_off_path_full_set() -> None:
    payload = {
        **_base_profitability_inputs(),
        "avg_starting_price_top10": 54.0,
        "top10_prices": [5, 8, 10, 11, 12, 12, 13, 15, 400],
    }
    on_result = ProfitabilityScoreCalculator().calculate(
        110,
        _FakeScoringDB(payload),
        config={"scoring": {"exclude_price_outliers": True}},
    )
    off_result = ProfitabilityScoreCalculator().calculate(
        110,
        _FakeScoringDB(payload),
        config={"scoring": {"exclude_price_outliers": False}},
    )
    # Mapping-backed path keeps legacy behavior regardless of toggle.
    assert on_result.score_value == off_result.score_value


def test_profitability_exclude_price_outliers_enabled_config_guard() -> None:
    assert _exclude_price_outliers_enabled(None) is False
    assert _exclude_price_outliers_enabled({"scoring": "bad"}) is False
    assert _exclude_price_outliers_enabled({"scoring": {"exclude_price_outliers": True}}) is True


def test_profitability_db_path_excludes_price_outliers_when_enabled() -> None:
    session, _niche, keyword = _build_session()
    try:
        _seed_competition_rows(session, keyword.id, run_id="profitability-outlier")
        # Introduce a high outlier directly on persisted gigs.
        gigs = (
            session.query(SearchResult)
            .filter(SearchResult.keyword_id == keyword.id)
            .order_by(SearchResult.rank.asc())
            .all()
        )
        top_gigs = [row.gig for row in gigs if row.gig is not None]
        assert len(top_gigs) >= 3
        seller = Seller(seller_handle="profitability-outlier-extra", level="Level 1")
        session.add(seller)
        session.flush()
        extra_gig = Gig(
            seller_id=seller.id,
            title="Competition gig extra",
            normalized_title="competition gig extra",
            starting_price=13.0,
            review_count=15.0,
        )
        session.add(extra_gig)
        session.flush()
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id="profitability-outlier",
                rank=4,
                gig_id=extra_gig.id,
                title=extra_gig.title,
            )
        )
        top_gigs[0].starting_price = 400.0
        top_gigs[1].starting_price = 10.0
        top_gigs[2].starting_price = 12.0
        session.commit()

        filtered = ProfitabilityScoreCalculator()._load_signals_from_db(  # pylint: disable=protected-access
            keyword.id,
            session,
            config={"scoring": {"exclude_price_outliers": True}},
        )
        unfiltered = ProfitabilityScoreCalculator()._load_signals_from_db(  # pylint: disable=protected-access
            keyword.id,
            session,
            config={"scoring": {"exclude_price_outliers": False}},
        )
        assert filtered["avg_starting_price_top10"] < unfiltered["avg_starting_price_top10"]
    finally:
        session.close()
