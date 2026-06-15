from __future__ import annotations

from automation.jira_spec_mapper import JiraSpecMapper


def test_mapper_loads_all_four_catalogs() -> None:
    mapper = JiraSpecMapper()
    counts = mapper.catalog_counts()
    assert counts["project_plan"] > 0
    assert counts["dod"] > 0
    assert counts["todo"] > 0
    assert counts["github"] > 0


def test_mapper_story_sources_shape() -> None:
    mapper = JiraSpecMapper()
    payload = mapper.sources_for_story("SCRUM-999")
    assert payload["jira_key"] == "SCRUM-999"
    assert isinstance(payload["project_plan_catalog"], list)
