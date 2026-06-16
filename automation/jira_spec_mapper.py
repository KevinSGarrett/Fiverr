"""Load PM Pack reference catalogs for Jira-to-spec mapping."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTOMATION_DIR = REPO_ROOT / "PM_Pack" / "automation"


class JiraSpecMapper:
    """Small mapper utility used by prompt-contract generation flows."""

    def __init__(self, automation_dir: Path | None = None) -> None:
        self._automation_dir = automation_dir or AUTOMATION_DIR
        self._pp_catalog = self._load_catalog("project_plan_catalog.json")
        self._dod_catalog = self._load_catalog("dod_catalog.json")
        self._todo_catalog = self._load_catalog("todo_epic_catalog.json")
        self._github_catalog = self._load_catalog("github_governance_catalog.json")

    def _load_catalog(self, filename: str) -> list[str]:
        path = self._automation_dir / filename
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            normalized: list[str] = []
            for item in payload:
                if isinstance(item, str):
                    normalized.append(item)
                    continue
                if isinstance(item, dict):
                    source_path = item.get("source_path")
                    filename_value = item.get("filename")
                    epic_id = item.get("epic_id")
                    if isinstance(source_path, str) and source_path:
                        normalized.append(source_path)
                    elif isinstance(filename_value, str) and filename_value:
                        normalized.append(filename_value)
                    elif isinstance(epic_id, str) and epic_id:
                        normalized.append(epic_id)
            return normalized

        if not isinstance(payload, dict):
            return []
        entries = payload.get("entries", [])
        if not isinstance(entries, list):
            return []
        return [str(item) for item in entries]

    def catalog_counts(self) -> dict[str, int]:
        return {
            "project_plan": len(self._pp_catalog),
            "dod": len(self._dod_catalog),
            "todo": len(self._todo_catalog),
            "github": len(self._github_catalog),
        }

    def sources_for_story(self, jira_key: str) -> dict[str, Any]:
        return {
            "jira_key": jira_key,
            "project_plan_catalog": self._pp_catalog[:5],
            "dod_catalog": self._dod_catalog[:3],
            "todo_catalog": self._todo_catalog[:3],
            "github_catalog": self._github_catalog[:3],
        }
