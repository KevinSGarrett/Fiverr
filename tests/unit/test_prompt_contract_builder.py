from __future__ import annotations

import pytest
from automation.prompt_contract_builder import build_prompt_contract
from automation.prompt_generator import PlanningIncompleteError


def _lanes() -> dict:
    return {
        "lanes": {
            "A": {
                "description": "Planner lane",
                "owns": ["PM_Pack/**", "docs/**"],
                "prohibited": ["src/**"],
            }
        }
    }


def _story() -> dict:
    return {
        "key": "SCRUM-1000",
        "summary": "Build prompt contract",
        "acceptance_criteria": "Prompt includes required sections and policy blocks.",
        "definition_of_done": "Prompt validates and includes final end marker.",
    }


def test_contract_contains_secrets_reference_block() -> None:
    contract = build_prompt_contract("A", 78, [_story()], _lanes())
    assert "C:\\Fiverr\\Fiverr\\.env" in contract
    assert "JIRA_API_TOKEN" in contract


def test_contract_contains_directory_map() -> None:
    contract = build_prompt_contract("A", 78, [_story()], _lanes())
    assert "C:\\AI_Runner\\" in contract
    assert "C:\\Fiverr\\Fiverr\\automation\\" in contract


def test_contract_contains_pmpack_ref_section() -> None:
    contract = build_prompt_contract("A", 78, [_story()], _lanes())
    assert "PM_Pack\\ref\\project_plan" in contract
    assert "PM_Pack\\ref\\dod" in contract
    assert "PM_Pack\\ref\\todo" in contract


def test_contract_has_55_plus_tasks() -> None:
    contract = build_prompt_contract("A", 78, [_story()], _lanes())
    assert contract.count("### TASK ") >= 55


def test_contract_has_end_of_prompt_marker() -> None:
    contract = build_prompt_contract("A", 78, [_story()], _lanes())
    assert contract.rstrip().endswith("END OF PROMPT")


def test_contract_has_model_block() -> None:
    contract = build_prompt_contract("A", 78, [_story()], _lanes())
    assert "Model: Codex 5.3" in contract
    assert "Effort: medium" in contract


def test_contract_has_jira_scope_with_ac_dod() -> None:
    contract = build_prompt_contract("A", 78, [_story()], _lanes())
    assert "## Jira Scope" in contract
    assert "AC:" in contract
    assert "DoD:" in contract


def test_contract_fails_when_task_floor_not_met(monkeypatch: pytest.MonkeyPatch) -> None:
    from automation import prompt_contract_builder as pcb

    monkeypatch.setattr(pcb, "_render_tasks", lambda *args, **kwargs: ["### TASK 01 — too short", ""])
    with pytest.raises(ValueError):
        build_prompt_contract("A", 78, [_story()], _lanes())


def test_contract_raises_planning_incomplete_for_empty_ac_and_dod() -> None:
    story = {
        "key": "SCRUM-1",
        "summary": "test",
        "acceptance_criteria": "",
        "definition_of_done": "",
    }
    with pytest.raises(PlanningIncompleteError):
        build_prompt_contract("A", 78, [story], _lanes())


def test_contract_supports_empty_story_list_for_scope_rendering() -> None:
    contract = build_prompt_contract(
        "A",
        78,
        [],
        _lanes(),
        preamble_text="custom preamble",
    )
    assert "No stories assigned." in contract
    assert "custom preamble" in contract


def test_contract_catalog_hint_variants() -> None:
    story = _story()
    malformed = {"entries": "bad-shape"}
    contract = build_prompt_contract("A", 78, [story], _lanes(), pp_catalog=malformed)
    assert "catalog malformed" in contract

    matching = {"entries": [{"source_path": "PM_Pack/ref/project_plan/sample.md", "jira_keys": ["SCRUM-1000"]}]}
    contract_match = build_prompt_contract("A", 78, [story], _lanes(), pp_catalog=matching)
    assert "PM_Pack/ref/project_plan/sample.md" in contract_match
