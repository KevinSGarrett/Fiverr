"""Governance helpers for Jira-mapped integration evidence payloads."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

_ALLOWED_GATE_STATUSES = {"pass", "fail", "blocked", "unknown", "not_run"}
_ALLOWED_CODEX_STATUSES = {"valid_fixed", "valid_open", "invalid", "pending", "not_run"}
_ALLOWED_DOD_STATUSES = {"partial", "full", "unknown"}


def _normalize_status(value: Any, field_name: str, allowed: set[str], default: str) -> str:
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise ValueError(f"Invalid {field_name} '{value}'. Allowed: {allowed_values}.")
    return normalized


def _normalize_jira_keys(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        raise ValueError("jira_keys is required and must be a list of Jira issue keys.")
    normalized = sorted({str(item).strip().upper() for item in raw if str(item).strip()})
    if not normalized:
        raise ValueError("jira_keys is required and must include at least one Jira issue key.")
    return normalized


def normalize_gate_evidence(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize gate evidence for report/export use."""
    normalized: dict[str, Any] = {
        "jira_keys": _normalize_jira_keys(evidence.get("jira_keys")),
        "branch": str(evidence.get("branch", "")).strip(),
        "pr_number": evidence.get("pr_number"),
        "ci_status": _normalize_status(
            evidence.get("ci_status"), "ci_status", _ALLOWED_GATE_STATUSES, "unknown"
        ),
        "codecov_status": _normalize_status(
            evidence.get("codecov_status"), "codecov_status", _ALLOWED_GATE_STATUSES, "unknown"
        ),
        "codex_status": _normalize_status(
            evidence.get("codex_status"), "codex_status", _ALLOWED_CODEX_STATUSES, "not_run"
        ),
        "dod_status": _normalize_status(
            evidence.get("dod_status"), "dod_status", _ALLOWED_DOD_STATUSES, "partial"
        ),
    }

    if not normalized["branch"]:
        raise ValueError("branch is required and must be a non-empty string.")

    pr_number = normalized["pr_number"]
    if pr_number is not None and not isinstance(pr_number, int):
        raise ValueError("pr_number must be an integer or None.")

    return normalized


def serialize_gate_evidence(evidence: Mapping[str, Any]) -> str:
    """Return stable JSON for storage, reporting, or transport."""
    return json.dumps(normalize_gate_evidence(evidence), sort_keys=True)
