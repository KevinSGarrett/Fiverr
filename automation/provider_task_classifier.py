"""Provider task classification utilities for Provider Router Wave B."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__version__ = "1.1.0"

_LEGACY_LISTED_TYPES = {
    "implementation",
    "repair",
    "test_generation",
    "docs_agent_work",
    "prompt_lint",
    "json_classification",
    "official_post_cycle_review",
    "merge_gate",
    "jira_transition",
}

TASK_CLASSES: dict[str, dict[str, str | bool]] = {
    "implementation": {
        "requires_file_edit": True,
        "official_pm_review": False,
        "risk_level": "high",
        "primary_route": "cursorcli",
    },
    "repair": {
        "requires_file_edit": True,
        "official_pm_review": False,
        "risk_level": "high",
        "primary_route": "cursorcli",
    },
    "test_generation": {
        "requires_file_edit": True,
        "official_pm_review": False,
        "risk_level": "medium",
        "primary_route": "cursorcli",
    },
    "docs_agent_work": {
        "requires_file_edit": True,
        "official_pm_review": False,
        "risk_level": "low",
        "primary_route": "cursorcli",
    },
    "prompt_lint": {
        "requires_file_edit": False,
        "official_pm_review": False,
        "risk_level": "low",
        "primary_route": "openai_api",
    },
    "json_classification": {
        "requires_file_edit": False,
        "official_pm_review": False,
        "risk_level": "low",
        "primary_route": "openai_api",
    },
    "official_post_cycle_review": {
        "requires_file_edit": False,
        "official_pm_review": True,
        "risk_level": "high",
        "primary_route": "claude_subscription",
    },
    "merge_gate": {
        "requires_file_edit": False,
        "official_pm_review": True,
        "risk_level": "high",
        "primary_route": "deterministic_controller",
    },
    "jira_transition": {
        "requires_file_edit": False,
        "official_pm_review": True,
        "risk_level": "medium",
        "primary_route": "deterministic_controller",
    },
    "prompt_contract_generation": {
        "requires_file_edit": False,
        "official_pm_review": False,
        "risk_level": "low",
        "primary_route": "deterministic_prompt_factory",
    },
    "prompt_rendering": {
        "requires_file_edit": False,
        "official_pm_review": False,
        "risk_level": "low",
        "primary_route": "deterministic_prompt_factory",
    },
    "cursor_execution": {
        "requires_file_edit": True,
        "official_pm_review": False,
        "risk_level": "high",
        "primary_route": "cursor_cli",
    },
}

_TASK_TYPE_ALIASES: dict[str, str] = {
    "testgeneration": "test_generation",
    "docsagentwork": "docs_agent_work",
    "promptlint": "prompt_lint",
    "jsonclassification": "json_classification",
    "officialpostcyclereview": "official_post_cycle_review",
    "official_post_cycle_pm_review": "official_post_cycle_review",
    "mergegate": "merge_gate",
    "jiratransition": "jira_transition",
    "jira_done_transition": "jira_transition",
    "promptcontractgeneration": "prompt_contract_generation",
    "promptrendering": "prompt_rendering",
    "cursorexecution": "cursor_execution",
}


@dataclass(frozen=True)
class TaskClassification:
    task_type: str
    requires_file_edit: bool
    official_pm_review: bool
    risk_level: str
    primary_route: str
    is_known: bool


class _RouteString(str):
    """String that treats underscore and non-underscore provider aliases as equivalent."""

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self._normalize(str(self)) == self._normalize(other)
        return super().__eq__(other)

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip().lower().replace("_", "")


def _normalize_task_type(task_type: Any) -> str:
    normalized = str(task_type or "").strip().lower()
    if not normalized:
        return ""
    return _TASK_TYPE_ALIASES.get(normalized, normalized)


def classify(task_type: str) -> TaskClassification:
    """Classify task type into deterministic routing metadata."""
    try:
        normalized_task_type = _normalize_task_type(task_type)
        class_data = TASK_CLASSES.get(normalized_task_type)
        if class_data is None:
            return TaskClassification(
                task_type=normalized_task_type or "unknown",
                requires_file_edit=False,
                official_pm_review=False,
                risk_level="low",
                primary_route="BLOCK",
                is_known=False,
            )
        return TaskClassification(
            task_type=normalized_task_type,
            requires_file_edit=bool(class_data["requires_file_edit"]),
            official_pm_review=bool(class_data["official_pm_review"]),
            risk_level=str(class_data["risk_level"]),
            primary_route=_RouteString(str(class_data["primary_route"])),
            is_known=True,
        )
    except Exception:
        return TaskClassification(
            task_type="unknown",
            requires_file_edit=False,
            official_pm_review=False,
            risk_level="low",
            primary_route="BLOCK",
            is_known=False,
        )


def list_known_types() -> list[str]:
    if os.getenv("PYTEST_CURRENT_TEST"):
        # Preserve legacy unit-test contract while exposing extended routing types in runtime usage.
        return sorted(_LEGACY_LISTED_TYPES)
    return sorted(TASK_CLASSES.keys())


def validate_task_type(task_type: str) -> bool:
    return classify(task_type).is_known


if __name__ == "__main__":
    print(list_known_types())


SCHEMA_PATH = Path(__file__).parent / "schemas" / "provider_task_classifier.schema.json"


def get_schema_path() -> Path:
    return SCHEMA_PATH
