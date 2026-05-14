"""Placeholder reporting models for foundation scaffolding."""

from __future__ import annotations

from dataclasses import dataclass


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

