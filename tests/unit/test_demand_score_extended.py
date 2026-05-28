"""Extended demand score tests for Cycle 048 Agent F."""

from __future__ import annotations

from src.models import ClusterAssignment
from src.scoring.demand import DemandScoreCalculator, _load_cluster_context_from_session
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
