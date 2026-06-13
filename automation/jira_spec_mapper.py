"""Map Jira stories to PM_Pack project-plan/DoD context."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_MAP_PATH = REPO_ROOT / "PM_Pack" / "automation" / "jira_spec_map.json"


def map_jira_to_project_plan(
    issue_key: str,
    story: dict[str, Any],
    project_plan_catalog: dict[str, Any] | None = None,
    dod_catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Map a Jira story to project-plan context.

    If optional catalogs are unavailable, the mapper still returns Jira-sourced AC/DoD
    values and best-effort seed mappings.
    """
    normalized = _normalize_story(story)
    seed = _seed_mapping(issue_key)
    project_plan_path = _from_catalog(project_plan_catalog, issue_key, "project_plan_path")
    dod_path = _from_catalog(dod_catalog, issue_key, "dod_path")
    todo_epic_path = _from_catalog(project_plan_catalog, issue_key, "todo_epic_path")
    wave = _from_catalog(project_plan_catalog, issue_key, "wave")

    if project_plan_path is None:
        project_plan_path = _as_str(seed.get("project_plan_path"))
    if dod_path is None:
        dod_path = _as_str(seed.get("dod_path"))
    if todo_epic_path is None:
        todo_epic_path = _as_str(seed.get("todo_epic_path"))
    if wave is None:
        wave = _as_str(seed.get("wave"))

    definition_of_done = normalized["definition_of_done"]
    if not definition_of_done and dod_path:
        definition_of_done = f"See DoD reference: {dod_path}"

    return {
        "issue_key": issue_key,
        "acceptance_criteria": normalized["acceptance_criteria"],
        "definition_of_done": definition_of_done,
        "project_plan_path": project_plan_path,
        "dod_path": dod_path,
        "todo_epic_path": todo_epic_path,
        "wave": wave,
    }


def _normalize_story(story: dict[str, Any]) -> dict[str, str]:
    acceptance = _first_non_empty(
        story.get("acceptance_criteria"),
        story.get("acceptanceCriteria"),
        story.get("ac"),
        story.get("description"),
    )
    dod = _first_non_empty(
        story.get("definition_of_done"),
        story.get("definitionOfDone"),
        story.get("dod"),
    )
    return {
        "acceptance_criteria": acceptance,
        "definition_of_done": dod,
    }


def _from_catalog(
    catalog: dict[str, Any] | None, issue_key: str, field: str
) -> str | None:
    if not isinstance(catalog, dict):
        return None
    mappings = catalog.get("mappings")
    if not isinstance(mappings, dict):
        return None
    issue_map = mappings.get(issue_key)
    if not isinstance(issue_map, dict):
        return None
    return _as_str(issue_map.get(field))


def _seed_mapping(issue_key: str) -> dict[str, Any]:
    if not SEED_MAP_PATH.exists():
        return {}
    try:
        payload = json.loads(SEED_MAP_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    mappings = payload.get("mappings")
    if not isinstance(mappings, dict):
        return {}
    issue_map = mappings.get(issue_key)
    return issue_map if isinstance(issue_map, dict) else {}


def _first_non_empty(*values: Any) -> str:
    for value in values:
        text = _as_str(value)
        if text:
            return text
    return ""


def _as_str(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""
