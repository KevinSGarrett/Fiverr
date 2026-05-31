"""Extended demand score tests for Cycle 048 Agent F."""

from __future__ import annotations

import pytest
from src.models import ClusterAssignment, ResultSetValidation, SearchResult
from src.scoring.demand import (
    DemandScoreCalculator,
    _classify_autocomplete_state,
    _compute_trc_reliability,
    _load_cluster_context_from_session,
    _relevance_factor,
    _sponsored_factor,
    _strictness_factor,
    _trends_platform_qualifier,
    trc_adjustment,
)
from src.scoring.result_set_relevance import apply_trc_adjustments
from tests.unit.test_demand_score import (
    KEYWORD_ID,
    FakeDemandDB,
    _base_demand_inputs,
    _build_demand_session,
    _cluster_config,
)


def test_demand_score_uses_trc_as_primary_signal_when_available() -> None:
    result = DemandScoreCalculator().calculate(
        KEYWORD_ID,
        FakeDemandDB(demand_inputs={KEYWORD_ID: _base_demand_inputs()}),
    )
    assert result.score_components["fiverr_count"].raw == 1250


def test_demand_score_normalizes_trc_correctly_at_threshold_values() -> None:
    calculator = DemandScoreCalculator()
    assert calculator._normalize_count(0.0) == 0.0  # pylint: disable=protected-access
    assert 0.0 < calculator._normalize_count(10.0) < calculator._normalize_count(1000.0)  # pylint: disable=protected-access


def test_demand_score_handles_null_trc_gracefully() -> None:
    result = DemandScoreCalculator().calculate(
        KEYWORD_ID,
        FakeDemandDB(demand_inputs={KEYWORD_ID: {"autocomplete_position": 2}}),
    )
    assert result.score_value is None
    assert "Missing Fiverr total result count." in result.missing_data_warnings


def test_demand_score_reddit_intent_component_when_signal_present() -> None:
    result = DemandScoreCalculator().calculate(
        KEYWORD_ID,
        FakeDemandDB(demand_inputs={KEYWORD_ID: _base_demand_inputs()}),
    )
    assert result.score_components["reddit_intent"].value == 72.0


def test_demand_score_reddit_intent_absent_falls_back_correctly() -> None:
    payload = dict(_base_demand_inputs())
    payload["reddit_demand_intent_score"] = None
    result = DemandScoreCalculator().calculate(KEYWORD_ID, FakeDemandDB(demand_inputs={KEYWORD_ID: payload}))
    assert "reddit_intent" not in result.score_components
    assert result.confidence_breakdown["missing_reddit_intent"] == -0.05


def test_demand_score_autocomplete_position_contribution() -> None:
    payload = dict(_base_demand_inputs())
    payload["autocomplete_position"] = 1
    result = DemandScoreCalculator().calculate(KEYWORD_ID, FakeDemandDB(demand_inputs={KEYWORD_ID: payload}))
    assert result.score_components["autocomplete"].value == 100.0


def test_demand_score_google_trends_component_weight() -> None:
    result = DemandScoreCalculator().calculate(
        KEYWORD_ID,
        FakeDemandDB(demand_inputs={KEYWORD_ID: _base_demand_inputs()}),
    )
    assert result.score_components["google_trends"].weight == 0.20


def test_demand_score_combined_signals_produce_higher_score() -> None:
    sparse = DemandScoreCalculator().calculate(
        KEYWORD_ID,
        FakeDemandDB(demand_inputs={KEYWORD_ID: {"total_result_count": 40, "autocomplete_position": 10}}),
    )
    rich = DemandScoreCalculator().calculate(
        KEYWORD_ID,
        FakeDemandDB(demand_inputs={KEYWORD_ID: _base_demand_inputs()}),
    )
    assert sparse.score_value is not None
    assert rich.score_value is not None
    assert rich.score_value > sparse.score_value


def test_demand_score_produces_valid_range_with_minimal_data() -> None:
    result = DemandScoreCalculator().calculate(
        KEYWORD_ID,
        FakeDemandDB(demand_inputs={KEYWORD_ID: {"total_result_count": 1}}),
        config=_cluster_config(use_cluster_boost=False),
    )
    assert result.score_value is not None
    assert 0.0 <= result.score_value <= 100.0


def test_demand_score_kw96_equivalent_fixture_matches_expected() -> None:
    kw96_like = {
        "total_result_count": 518,
        "autocomplete_position": None,
        "trends_12mo_score": 2.0,
        "reddit_demand_intent_score": None,
    }
    result = DemandScoreCalculator().calculate(KEYWORD_ID, FakeDemandDB(demand_inputs={KEYWORD_ID: kw96_like}))
    assert result.score_value is not None
    assert result.score_value < 45.0


def test_demand_cluster_context_negative_cluster_id_returns_zeroed_context() -> None:
    session, keyword = _build_demand_session()
    try:
        session.add(
            ClusterAssignment(
                keyword_id=keyword.id,
                niche_id="demand-niche",
                cluster_id=-1,
                run_id="negative-cluster-run",
                algorithm="kmeans",
            )
        )
        session.commit()
        context = _load_cluster_context_from_session(keyword.id, session)
        assert context is not None
        assert context["cluster_id"] == -1
        assert context["keyword_count"] == 0
    finally:
        session.close()


def test_demand_load_signals_returns_empty_for_none_db() -> None:
    assert DemandScoreCalculator()._load_signals(KEYWORD_ID, None) == {}  # pylint: disable=protected-access


def test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20_percent() -> None:
    assert trc_adjustment(3, 12, {"relevance": {"enable_sponsored_exclusion": True}}, "SUBCATEGORY") == 0.80


def test_trc_multiplier_bands() -> None:
    cfg = {"relevance": {"enable_sponsored_exclusion": True}}
    assert trc_adjustment(1, 10, cfg, "SUBCATEGORY") == 1.00
    assert trc_adjustment(2, 10, cfg, "SUBCATEGORY") == 0.90
    assert trc_adjustment(7, 20, cfg, "SUBCATEGORY") == 0.80
    assert trc_adjustment(8, 20, cfg, "SUBCATEGORY") == 0.70


def test_demand_legacy_when_toggle_off() -> None:
    cfg_on = {"relevance": {"enable_sponsored_exclusion": True}}
    cfg_off = {"relevance": {"enable_sponsored_exclusion": False}}
    on = trc_adjustment(3, 12, cfg_on, "SUBCATEGORY")
    off = trc_adjustment(3, 12, cfg_off, "SUBCATEGORY")
    assert on == 0.80
    assert off == 1.0


def test_demand_qualified_trc_when_rsv_below_080() -> None:
    session, keyword = _build_demand_session()
    try:
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id="r1",
                page_collected=1,
                total_result_count=100,
                sponsored_gig_count=0,
                organic_gig_count=10,
                search_strictness_used="SUBCATEGORY",
            )
        )
        session.add(
            ResultSetValidation(
                keyword_id=keyword.id,
                run_id="r1",
                result_set_relevance_score=0.60,
                relevance_deduction=-0.15,
            )
        )
        session.commit()
        result = DemandScoreCalculator().calculate(keyword.id, session)
        assert result.score_components["fiverr_count"].note
        assert "60.00" in result.score_components["fiverr_count"].note
    finally:
        session.close()


def test_trc_qualified_by_result_set_relevance_in_demand() -> None:
    """REG-16 alias: qualified TRC obeys RSV multiplier, baseline unchanged when absent."""
    assert apply_trc_adjustments(
        100.0,
        ResultSetValidation(result_set_relevance_score=0.60),
        sponsored_fraction=0.0,
    ) == pytest.approx(60.0)
    assert apply_trc_adjustments(
        100.0,
        None,
        sponsored_fraction=0.0,
    ) == pytest.approx(100.0)


def test_demand_no_stack_with_sponsored_multiplier() -> None:
    adjusted = apply_trc_adjustments(
        100.0,
        ResultSetValidation(result_set_relevance_score=0.60),
        sponsored_fraction=0.30,
    )
    assert adjusted == 60.0


def test_demand_no_rsv_is_baseline() -> None:
    baseline = DemandScoreCalculator().calculate(
        KEYWORD_ID,
        FakeDemandDB(demand_inputs={KEYWORD_ID: _base_demand_inputs()}),
    )
    assert baseline.score_value is not None


def test_demand_no_rsv_equals_baseline() -> None:
    baseline = DemandScoreCalculator().calculate(
        KEYWORD_ID,
        FakeDemandDB(demand_inputs={KEYWORD_ID: _base_demand_inputs()}),
    )
    assert baseline.score_value is not None
    assert baseline.score_components["fiverr_count"].raw == _base_demand_inputs()["total_result_count"]


def test_demand_uses_shared_rsv_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def _fake_get_result_set_validation(keyword_id: int, _db: object) -> None:  # type: ignore[no-untyped-def]
        calls.append(keyword_id)
        return None

    monkeypatch.setattr("src.scoring.demand.get_result_set_validation", _fake_get_result_set_validation)
    result = DemandScoreCalculator().calculate(
        KEYWORD_ID,
        FakeDemandDB(demand_inputs={KEYWORD_ID: _base_demand_inputs()}),
    )
    assert result.score_value is not None
    assert calls == [KEYWORD_ID]


def test_trc_reliability_uses_min_factor_not_product() -> None:
    factor = _compute_trc_reliability(0.60, 0.30, "SUBCATEGORY")
    assert factor == pytest.approx(0.60)
    assert (100.0 * factor) == pytest.approx(60.0)


def test_trc_reliability_equals_min_of_existing_component_factors() -> None:
    rsv = 0.63
    sponsored_fraction = 0.32
    strictness = "NONE"
    expected = min(
        _relevance_factor(rsv),
        _sponsored_factor(sponsored_fraction),
        _strictness_factor(strictness),
    )
    assert _compute_trc_reliability(rsv, sponsored_fraction, strictness) == pytest.approx(expected)


def test_trc_reliability_none_inputs_no_penalty() -> None:
    assert _compute_trc_reliability(None, None, None) == 1.0


def test_trc_reliability_toggle_off_matches_legacy() -> None:
    payload = dict(_base_demand_inputs())
    payload.update({"sponsored_gig_count": 3, "total_gig_count": 10, "search_strictness_used": "SUBCATEGORY"})
    baseline = DemandScoreCalculator().calculate(KEYWORD_ID, FakeDemandDB(demand_inputs={KEYWORD_ID: payload}))
    off_result = DemandScoreCalculator().calculate(
        KEYWORD_ID,
        FakeDemandDB(demand_inputs={KEYWORD_ID: payload}),
        config={"scoring": {"demand": {"use_trc_reliability": False}}},
    )
    assert off_result.score_value == baseline.score_value


def test_keyword_score_trc_reliability_populated_when_on() -> None:
    session, keyword = _build_demand_session()
    try:
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id="r1",
                page_collected=1,
                total_result_count=100,
                sponsored_gig_count=3,
                organic_gig_count=7,
                search_strictness_used="SUBCATEGORY",
            )
        )
        session.add(ResultSetValidation(keyword_id=keyword.id, run_id="r1", result_set_relevance_score=0.60))
        session.commit()
        result = DemandScoreCalculator().calculate(
            keyword.id,
            session,
            config={"scoring": {"demand": {"use_trc_reliability": True}}},
        )
        assert result.trc_reliability == pytest.approx(0.60)
    finally:
        session.close()


def test_autocomplete_absent_penalizes_demand() -> None:
    payload = dict(_base_demand_inputs())
    payload["autocomplete_suggestions"] = []
    legacy = DemandScoreCalculator().calculate(KEYWORD_ID, FakeDemandDB(demand_inputs={KEYWORD_ID: payload}))
    qualified = DemandScoreCalculator().calculate(
        KEYWORD_ID,
        FakeDemandDB(demand_inputs={KEYWORD_ID: payload}),
        config={"scoring": {"demand": {"use_signal_qualifiers": True}}},
    )
    assert _classify_autocomplete_state([]) == "absent"
    assert qualified.score_value is not None and legacy.score_value is not None
    assert qualified.score_value < legacy.score_value


def test_autocomplete_emerging_does_not_over_credit() -> None:
    cfg = {"scoring": {"demand": {"use_signal_qualifiers": True}}}
    present = DemandScoreCalculator().calculate(
        KEYWORD_ID,
        FakeDemandDB(demand_inputs={KEYWORD_ID: {**_base_demand_inputs(), "autocomplete_suggestions": ["a", "b", "c"]}}),
        config=cfg,
    )
    emerging = DemandScoreCalculator().calculate(
        KEYWORD_ID,
        FakeDemandDB(demand_inputs={KEYWORD_ID: {**_base_demand_inputs(), "autocomplete_suggestions": ["a"]}}),
        config=cfg,
    )
    assert emerging.score_value is not None and present.score_value is not None
    assert emerging.score_value <= present.score_value


def test_trends_platform_qualifier_bounds() -> None:
    assert _trends_platform_qualifier(None) == 1.0
    assert 0.0 <= _trends_platform_qualifier({"platform_fit": 0.3}) <= 1.0
    assert 0.0 <= _trends_platform_qualifier({"trends_12mo_score": 80.0}) <= 1.0


def test_signal_qualifiers_toggle_off_matches_legacy() -> None:
    payload = {**_base_demand_inputs(), "autocomplete_suggestions": []}
    baseline = DemandScoreCalculator().calculate(KEYWORD_ID, FakeDemandDB(demand_inputs={KEYWORD_ID: payload}))
    toggled_off = DemandScoreCalculator().calculate(
        KEYWORD_ID,
        FakeDemandDB(demand_inputs={KEYWORD_ID: payload}),
        config={"scoring": {"demand": {"use_signal_qualifiers": False}}},
    )
    assert toggled_off.score_value == baseline.score_value
