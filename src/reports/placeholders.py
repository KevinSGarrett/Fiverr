"""Placeholder reporting models for foundation scaffolding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class ReportPlaceholder:
    """Minimal placeholder for report generation state."""

    report_type: str
    status: str
    message: str


GOVERNANCE_REPORT_ORDER = (
    "local_parity",
    "github_actions",
    "codecov_project",
    "codecov_patch",
    "codex_disposition",
)


def build_governance_report_placeholders(
    *,
    local_parity: str = "pending",
    github_actions: str = "pending",
    codecov_project: str = "pending",
    codecov_patch: str = "pending",
    codex_disposition: str = "pending",
) -> tuple[ReportPlaceholder, ...]:
    """Return user-facing governance checks with deterministic ordering."""
    statuses = {
        "local_parity": local_parity,
        "github_actions": github_actions,
        "codecov_project": codecov_project,
        "codecov_patch": codecov_patch,
        "codex_disposition": codex_disposition,
    }
    messages = {
        "local_parity": "Local parity checks (ruff, mypy, pytest coverage gate, config-check, foundation-gate, phase2-smoke).",
        "github_actions": "GitHub Actions workflow checks for the PR head commit.",
        "codecov_project": "Codecov project status check for repository-wide coverage.",
        "codecov_patch": "Codecov patch status check for diff coverage.",
        "codex_disposition": "Codex review-thread disposition and resolution state.",
    }
    return tuple(
        ReportPlaceholder(report_type=report_type, status=statuses[report_type], message=messages[report_type])
        for report_type in GOVERNANCE_REPORT_ORDER
    )


def build_jira_mapping_table(
    rows: list[dict[str, Any]],
    *,
    output_format: str = "dict",
) -> list[dict[str, Any]] | str:
    """Build deterministic Jira mapping rows for governance and product stories."""
    normalized_rows: list[dict[str, Any]] = []
    for raw_row in rows:
        changed_file_group = str(raw_row.get("changed_file_group", "")).strip()
        jira_keys = raw_row.get("jira_keys")
        status = str(raw_row.get("status", "pending")).strip() or "pending"
        dod_status = str(raw_row.get("dod_status", "pending")).strip() or "pending"
        not_applicable_reason = str(raw_row.get("not_applicable_reason", "")).strip()

        if not changed_file_group:
            raise ValueError("changed_file_group is required for Jira mapping rows.")

        normalized_keys: list[str] = []
        if jira_keys is None:
            normalized_keys = []
        elif isinstance(jira_keys, str):
            normalized_keys = [jira_keys.strip()] if jira_keys.strip() else []
        else:
            normalized_keys = [str(key).strip() for key in jira_keys if str(key).strip()]

        if not normalized_keys and not not_applicable_reason:
            raise ValueError("jira_keys are required unless not_applicable_reason is provided.")

        normalized_rows.append(
            {
                "changed_file_group": changed_file_group,
                "jira_keys": normalized_keys,
                "status": status,
                "dod_status": dod_status,
                "not_applicable_reason": not_applicable_reason,
            }
        )

    if output_format == "dict":
        return normalized_rows
    if output_format != "markdown":
        raise ValueError("output_format must be 'dict' or 'markdown'.")

    header = (
        "| Changed File Group | Jira Keys | Status | DOD Status | Not Applicable Reason |\n"
        "| --- | --- | --- | --- | --- |"
    )
    body_lines = []
    for row in normalized_rows:
        jira_keys = ", ".join(row["jira_keys"]) if row["jira_keys"] else "-"
        not_applicable_reason = row["not_applicable_reason"] or "-"
        body_lines.append(
            f"| {row['changed_file_group']} | {jira_keys} | {row['status']} | {row['dod_status']} | {not_applicable_reason} |"
        )
    return "\n".join([header, *body_lines])

