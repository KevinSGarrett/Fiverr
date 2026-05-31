"""Extended demand score tests for Cycle 048 Agent F."""

from __future__ import annotations

import pytest
from src.models import ClusterAssignment, ResultSetValidation, SearchResult
from src.scoring.demand import (
    DemandScoreCalculator,
    _load_cluster_context_from_session,
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
