"""R11 first-recommendation quality gate tests."""

from __future__ import annotations

from src.analysis.quality_gate import first_recommendation_quality_gate


def test_first_recommendation_quality_gate_blocks_missing_rsv() -> None:
    class MockKS:
        ghost_market_flag = False
        llm_inputs_used = {"prompt_tokens": 3}

    result = first_recommendation_quality_gate(MockKS(), None)
    assert result["passed"] is False
    assert "missing_rsv" in result["failing_checks"]


def test_first_recommendation_quality_gate_blocks_ghost() -> None:
    class MockKS:
        ghost_market_flag = True
        llm_inputs_used = {"prompt_tokens": 3}

    class MockRSV:
        result_set_relevance_score = 0.85
        search_strictness_used = "SUBCATEGORY"

    result = first_recommendation_quality_gate(MockKS(), MockRSV())
    assert "ghost_market" in result["failing_checks"]


def test_first_recommendation_quality_gate_passes_clean() -> None:
    class MockKS:
        ghost_market_flag = False
        llm_inputs_used = None
        llm_validated = None

    class MockRSV:
        result_set_relevance_score = 0.85
        search_strictness_used = "SUBCATEGORY"

    result = first_recommendation_quality_gate(MockKS(), MockRSV())
    assert result["passed"] is True


def test_gate_blocks_relevance_below_threshold() -> None:
    class MockKS:
        ghost_market_flag = False
        llm_validated = None

    class MockRSV:
        result_set_relevance_score = 0.65
        search_strictness_used = "SUBCATEGORY"

    result = first_recommendation_quality_gate(MockKS(), MockRSV())
    assert any("relevance_below" in check for check in result["failing_checks"])
    assert result["passed"] is False


def test_gate_blocks_unconstrained_search() -> None:
    class MockKS:
        ghost_market_flag = False
        llm_validated = None

    class MockRSV:
        result_set_relevance_score = 0.85
        search_strictness_used = "NONE"

    result = first_recommendation_quality_gate(MockKS(), MockRSV())
    assert "unconstrained_search" in result["failing_checks"]


def test_gate_blocks_failed_llm_validation() -> None:
    class MockKS:
        ghost_market_flag = False
        llm_validated = False

    class MockRSV:
        result_set_relevance_score = 0.85
        search_strictness_used = "SUBCATEGORY"

    result = first_recommendation_quality_gate(MockKS(), MockRSV())
    assert "llm_not_validated" in result["failing_checks"]


def test_gate_passes_when_llm_not_required() -> None:
    class MockKS:
        ghost_market_flag = False
        llm_validated = None
        llm_inputs_used = None

    class MockRSV:
        result_set_relevance_score = 0.85
        search_strictness_used = "SUBCATEGORY"

    result = first_recommendation_quality_gate(MockKS(), MockRSV())
    assert result["passed"] is True


def test_gate_passes_at_relevance_exactly_070() -> None:
    class MockKS:
        ghost_market_flag = False
        llm_validated = None

    class MockRSV:
        result_set_relevance_score = 0.70
        search_strictness_used = "SUBCATEGORY"

    result = first_recommendation_quality_gate(MockKS(), MockRSV())
    assert result["passed"] is True


def test_gate_reports_all_failing_checks() -> None:
    class MockKS:
        ghost_market_flag = True
        llm_validated = False

    class MockRSV:
        result_set_relevance_score = 0.40
        search_strictness_used = "NONE"

    result = first_recommendation_quality_gate(MockKS(), MockRSV())
    failing = result["failing_checks"]
    assert result["passed"] is False
    assert "ghost_market" in failing
    assert any("relevance_below" in check for check in failing)
    assert "unconstrained_search" in failing
    assert "llm_not_validated" in failing
