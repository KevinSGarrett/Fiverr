"""Dashboard app shell for future Streamlit-based presentation."""

from __future__ import annotations

from typing import Any

from src.dashboard.navigation import (
    DashboardPage,
)
from src.dashboard.navigation import (
    get_available_pages as get_navigation_pages,
)
from src.dashboard.state import build_cycle003_status_state, build_phase2_readiness_state
from src.reports import build_governance_report_placeholders

GOVERNANCE_STATUS_ORDER = (
    "local_parity",
    "github_actions",
    "codecov_project",
    "codecov_patch",
    "codex_disposition",
    "jira_mapping",
    "merge_readiness",
)

_GOVERNANCE_STATUS_MESSAGES = {
    "local_parity": "Local parity checks (ruff, mypy, pytest coverage gate, config-check, foundation-gate, phase2-smoke).",
    "github_actions": "GitHub Actions workflow checks for the PR head commit.",
    "codecov_project": "Codecov project status check for repository-wide coverage.",
    "codecov_patch": "Codecov patch status check for diff coverage.",
    "codex_disposition": "Codex review-thread disposition and resolution state.",
    "jira_mapping": "Jira governance and product-story mapping completeness for changed file groups.",
    "merge_readiness": "Branch policy and merge-readiness confirmation from latest validation and review state.",
}


def _normalize_governance_status(raw_status: str | None) -> tuple[str, str]:
    if raw_status is None or not raw_status.strip():
        return ("unknown", "warning")
    return (raw_status.strip(), "ok")


def build_governance_presentation_state(
    *,
    local_parity: str | None = None,
    github_actions: str | None = None,
    codecov_project: str | None = None,
    codecov_patch: str | None = None,
    codex_disposition: str | None = None,
    jira_mapping: str | None = None,
    merge_readiness: str | None = None,
) -> list[dict[str, str]]:
    """Return import-safe governance presentation data for dashboard rendering."""
    statuses = {
        "local_parity": local_parity,
        "github_actions": github_actions,
        "codecov_project": codecov_project,
        "codecov_patch": codecov_patch,
        "codex_disposition": codex_disposition,
        "jira_mapping": jira_mapping,
        "merge_readiness": merge_readiness,
    }
    rows: list[dict[str, str]] = []
    for category in GOVERNANCE_STATUS_ORDER:
        normalized_status, severity = _normalize_governance_status(statuses[category])
        rows.append(
            {
                "category": category,
                "status": normalized_status,
                "severity": severity,
                "message": _GOVERNANCE_STATUS_MESSAGES[category],
            }
        )
    return rows


def build_page_title() -> str:
    """Return a stable dashboard title for the foundation shell."""
    return "Fiverr Research System Dashboard (Foundation Shell)"


def get_available_pages() -> list[DashboardPage]:
    """Expose dashboard page metadata for callers and tests."""
    return get_navigation_pages()


def get_cycle003_status_state() -> dict[str, Any]:
    """Expose import-safe status sections for Foundation/Collection/Analysis dry runs."""
    return build_cycle003_status_state()


def get_phase2_readiness_state() -> dict[str, Any]:
    """Expose import-safe Phase 2 readiness placeholders."""
    return build_phase2_readiness_state()


def get_governance_status_state() -> list[dict[str, str]]:
    """Expose gate-level governance statuses for operator visibility."""
    report_checks = {item.report_type: item.status for item in build_governance_report_placeholders()}
    return [
        {
            "check": row["category"],
            "status": row["status"],
            "severity": row["severity"],
            "message": row["message"],
        }
        for row in build_governance_presentation_state(
            local_parity=report_checks.get("local_parity"),
            github_actions=report_checks.get("github_actions"),
            codecov_project=report_checks.get("codecov_project"),
            codecov_patch=report_checks.get("codecov_patch"),
            codex_disposition=report_checks.get("codex_disposition"),
        )
    ]


def main() -> None:
    """Render a minimal Streamlit shell when explicitly invoked."""
    import streamlit as st

    st.title(build_page_title())
    st.caption("Dashboard UX implementation is planned for a later cycle.")

    st.subheader("Available Pages")
    for page in get_available_pages():
        status = "ready" if page.enabled else f"disabled ({page.status})"
        st.write(f"- {page.label}: {status}")

    st.subheader("Cycle 003 Status")
    status_state = get_cycle003_status_state()
    for section in status_state["sections"]:
        st.write(f"### {section['label']}")
        for metric in section["metrics"]:
            st.write(f"- {metric['name']}: {metric['value']}")

    st.subheader("Cycle 004 Phase 2 Readiness (Preview)")
    readiness_state = get_phase2_readiness_state()
    st.write(f"- Collection Dry Run: {readiness_state['collection_dry_run']['status']}")
    st.write(f"- Analysis Dry Run: {readiness_state['analysis_dry_run']['status']}")
    st.write(
        "- Fixture Coverage (gig detail parser): "
        f"{readiness_state['fixture_coverage']['gig_detail_parser']}"
    )
    st.write(f"- Gate Status (foundation gate): {readiness_state['gate_status']['foundation_gate']}")
    st.write(f"- Gate Status (phase2 smoke): {readiness_state['gate_status']['phase2_smoke']}")

    st.subheader("Cycle 007 Governance and Readiness")
    for check in get_governance_status_state():
        st.write(f"- {check['check']}: {check['status']}")
        st.caption(check["message"])

