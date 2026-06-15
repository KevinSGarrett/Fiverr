from __future__ import annotations

import pytest
from automation.provider_task_classifier import classify, list_known_types, validate_task_type


def test_known_task_types_classify_with_expected_routes() -> None:
    expected_routes = {
        "implementation": "cursorcli",
        "repair": "cursorcli",
        "test_generation": "cursorcli",
        "docs_agent_work": "cursorcli",
        "prompt_lint": "openai_api",
        "json_classification": "openai_api",
        "official_post_cycle_review": "claude_subscription",
        "merge_gate": "deterministic_controller",
        "jira_transition": "deterministic_controller",
    }

    for task_type, route in expected_routes.items():
        result = classify(task_type)
        assert result.is_known is True
        assert result.primary_route == route


def test_unknown_task_type_returns_block() -> None:
    result = classify("not_a_real_task")
    assert result.is_known is False
    assert result.primary_route == "BLOCK"


@pytest.mark.parametrize("bad_input", ["", None])
def test_classify_never_raises_on_empty_or_none(bad_input: object) -> None:
    result = classify(bad_input)
    assert result.primary_route == "BLOCK"
    assert result.is_known is False


def test_list_known_types_returns_exactly_9_items() -> None:
    known = list_known_types()
    assert len(known) == 9
    assert sorted(known) == known


def test_validate_task_type_true_for_known_false_for_unknown() -> None:
    assert validate_task_type("implementation") is True
    assert validate_task_type("unknown_task_type_123") is False
