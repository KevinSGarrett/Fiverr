from __future__ import annotations

import pytest
from automation.jira_client import JiraClient


@pytest.mark.skip(reason="Live Jira required; not run in CI")
def test_jira_live_board_inventory() -> None:
    client = JiraClient()
    stories = client.board_inventory(project="SCRUM", max_results=5)
    assert len(stories) >= 1
    assert "description" in stories[0]


@pytest.mark.skip(reason="Live Jira required; not run in CI")
def test_jira_live_hydrate_ac_dod() -> None:
    client = JiraClient()
    stories = client.board_inventory(project="SCRUM", max_results=1)
    assert stories, "No Jira stories found for live smoke"
    hydrated = client.hydrate_ac_dod(stories[0]["key"])
    assert "description" in hydrated
    assert "acceptance_criteria" in hydrated
    assert "definition_of_done" in hydrated
