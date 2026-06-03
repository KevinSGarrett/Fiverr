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
