from __future__ import annotations

from automation.jira_spec_mapper import map_jira_to_project_plan


def test_maps_story_with_ac_from_jira() -> None:
    result = map_jira_to_project_plan(
        "SCRUM-100",
        {"acceptance_criteria": "AC from Jira", "definition_of_done": ""},
        None,
        None,
    )
    assert result["issue_key"] == "SCRUM-100"
    assert result["acceptance_criteria"] == "AC from Jira"


def test_maps_story_with_dod_from_dod_catalog() -> None:
    dod_catalog = {"mappings": {"SCRUM-101": {"dod_path": "PM_Pack/ref/dod/DOD_EPIC_01.md"}}}
    result = map_jira_to_project_plan(
        "SCRUM-101",
        {"acceptance_criteria": "AC", "definition_of_done": ""},
        None,
        dod_catalog,
    )
    assert result["dod_path"] == "PM_Pack/ref/dod/DOD_EPIC_01.md"
    assert "DOD_EPIC_01.md" in result["definition_of_done"]


def test_returns_only_jira_fields_when_catalog_none() -> None:
    result = map_jira_to_project_plan(
        "SCRUM-102",
        {"acceptance_criteria": "AC", "definition_of_done": "DoD"},
        None,
        None,
    )
    assert result["acceptance_criteria"] == "AC"
    assert result["definition_of_done"] == "DoD"


def test_handles_unknown_story_key_gracefully() -> None:
    result = map_jira_to_project_plan("SCRUM-UNKNOWN", {}, None, None)
    assert result["issue_key"] == "SCRUM-UNKNOWN"
    assert result["acceptance_criteria"] == ""
    assert result["definition_of_done"] == ""
