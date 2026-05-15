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
from src.reports.placeholders import build_active_story_groups

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

GOVERNANCE_PAGE_CATEGORY_ORDER = (
    "jira_mapping",
    "codex_disposition",
    "github_actions",
    "codecov_project",
    "codecov_patch",
    "local_parity",
    "merge_readiness",
)

_STATUS_TO_SEVERITY = {
    "pass": "ok",
    "ready": "ok",
    "complete": "ok",
    "done": "ok",
    "in_review": "warning",
    "pending": "warning",
    "unknown": "warning",
    "warning": "warning",
    "fail": "error",
    "error": "error",
    "blocked": "error",
}
_ALERT_SEVERITIES = frozenset({"warning", "error", "governance"})


def _normalize_governance_status(raw_status: str | None) -> tuple[str, str]:
    if raw_status is None or not raw_status.strip():
        return ("unknown", "warning")
    normalized_status = raw_status.strip().lower()
    severity = _STATUS_TO_SEVERITY.get(normalized_status, "warning")
    return (normalized_status, severity)


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


def build_governance_page_ready_state(
    *,
    local_parity: str | None = None,
    github_actions: str | None = None,
    codecov_project: str | None = None,
    codecov_patch: str | None = None,
    codex_disposition: str | None = None,
    jira_mapping: str | None = None,
    merge_readiness: str | None = None,
) -> dict[str, Any]:
    """Return page-ready governance structures for dashboard rendering layers."""
    rows_by_category = {
        row["category"]: row
        for row in build_governance_presentation_state(
            local_parity=local_parity,
            github_actions=github_actions,
            codecov_project=codecov_project,
            codecov_patch=codecov_patch,
            codex_disposition=codex_disposition,
            jira_mapping=jira_mapping,
            merge_readiness=merge_readiness,
        )
    }
    ordered_rows = [rows_by_category[category] for category in GOVERNANCE_PAGE_CATEGORY_ORDER]
    summary = {
        "ok": sum(1 for row in ordered_rows if row["severity"] == "ok"),
        "warning": sum(1 for row in ordered_rows if row["severity"] == "warning"),
        "error": sum(1 for row in ordered_rows if row["severity"] == "error"),
    }
    readiness_severity = "error" if summary["error"] else ("warning" if summary["warning"] else "ok")
    return {
        "component": "governance_status",
        "categories": ordered_rows,
        "summary": summary,
        "readiness_severity": readiness_severity,
        "empty_state": all(row["status"] == "unknown" for row in ordered_rows),
    }


def get_opportunities_page_descriptor(
    opportunities: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return deterministic placeholder metadata for the Opportunities page."""
    normalized_rows = list(opportunities or [])
    return {
        "page_id": "opportunities",
        "title": "Top Opportunities",
        "cards": ["top_opportunity", "runner_up", "watchlist"],
        "table_columns": ["opportunity", "niche", "score", "confidence", "status"],
        "rows": normalized_rows,
        "empty_state": len(normalized_rows) == 0,
    }


def get_keywords_page_descriptor(
    keywords: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return deterministic placeholder metadata for the Keywords page."""
    normalized_rows = list(keywords or [])
    return {
        "page_id": "keywords",
        "title": "Keyword Cluster Health",
        "columns": ["keyword", "niche", "cluster", "score", "confidence", "freshness_status"],
        "rows": normalized_rows,
        "empty_state": len(normalized_rows) == 0,
    }


def get_run_history_page_descriptor(
    runs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return deterministic placeholder metadata for Run History."""
    normalized_rows = list(runs or [])
    return {
        "page_id": "run_history",
        "title": "Run History",
        "columns": [
            "run_id",
            "branch",
            "pull_request",
            "status",
            "stages",
            "warning_count",
            "duration",
            "validation_status",
        ],
        "rows": normalized_rows,
        "empty_state": len(normalized_rows) == 0,
    }


def get_query_layer_descriptor(
    *,
    report_rows: list[dict[str, Any]] | None = None,
    manifest_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return deterministic query-layer placeholder metadata for active story evidence."""
    story_groups = query_active_story_groups(report_rows=report_rows, manifest_rows=manifest_rows)
    return {
        "page_id": "query_layer",
        "title": "Active Story Query Layer",
        "columns": ["story_group", "jira_keys", "statuses", "sources", "cycles", "branches"],
        "rows": story_groups,
        "empty_state": len(story_groups) == 0,
    }


def get_export_system_descriptor(
    exports: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return deterministic placeholder metadata for export governance tracking."""
    normalized_rows = list(exports or [])
    return {
        "page_id": "export_system",
        "title": "Export System",
        "columns": [
            "artifact_type",
            "format",
            "path",
            "jira_keys",
            "github_pr_number",
            "codecov_project_status",
            "codecov_patch_status",
        ],
        "rows": normalized_rows,
        "empty_state": len(normalized_rows) == 0,
    }


def get_app_entry_descriptor(*, branch: str | None = None, cycle: str | None = None) -> dict[str, str]:
    """Return deterministic app-entry placeholder metadata for stewardship visibility."""
    return {
        "page_id": "app_entry",
        "title": "Dashboard App Entry",
        "entry_module": "src.dashboard.app:main",
        "branch": (branch or "unknown").strip() or "unknown",
        "cycle": (cycle or "unknown").strip() or "unknown",
        "status": "placeholder",
    }


def build_alert_readiness_placeholders(
    alerts: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Normalize alert placeholders without requiring a runtime alerting system."""
    normalized_alerts: list[dict[str, str]] = []
    for raw_alert in alerts or []:
        raw_severity = str(raw_alert.get("severity", "warning")).strip().lower() or "warning"
        severity = raw_severity if raw_severity in _ALERT_SEVERITIES else "unknown"
        jira_key = str(raw_alert.get("jira_key", "")).strip() or "UNMAPPED"
        normalized_alerts.append(
            {
                "severity": severity,
                "source": str(raw_alert.get("source", "dashboard")).strip() or "dashboard",
                "jira_key": jira_key,
                "message": str(raw_alert.get("message", "pending")).strip() or "pending",
                "resolution_status": str(raw_alert.get("resolution_status", "open")).strip() or "open",
            }
        )
    return normalized_alerts


def get_alert_system_descriptor(alerts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return deterministic placeholder metadata for alert-system readiness."""
    normalized_alerts = build_alert_readiness_placeholders(alerts)
    return {
        "page_id": "alert_system",
        "title": "Alert System",
        "columns": ["severity", "source", "jira_key", "message", "resolution_status"],
        "rows": normalized_alerts,
        "summary": {
            "warning": sum(1 for alert in normalized_alerts if alert["severity"] == "warning"),
            "error": sum(1 for alert in normalized_alerts if alert["severity"] == "error"),
            "governance": sum(1 for alert in normalized_alerts if alert["severity"] == "governance"),
            "unknown": sum(1 for alert in normalized_alerts if alert["severity"] == "unknown"),
        },
        "empty_state": len(normalized_alerts) == 0,
    }


def query_active_story_groups(
    *,
    report_rows: list[dict[str, Any]] | None = None,
    manifest_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Query-layer placeholder for active Jira story groups from structured evidence."""
    normalized_rows: list[dict[str, Any]] = []
    for row in report_rows or []:
        normalized_rows.append({**row, "source": row.get("source", "report")})
    for row in manifest_rows or []:
        normalized_rows.append({**row, "source": row.get("source", "manifest")})
    return build_active_story_groups(normalized_rows)


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


def get_governance_page_state() -> dict[str, Any]:
    """Expose page-ready governance dictionary for dashboard UI composition."""
    report_checks = {item.report_type: item.status for item in build_governance_report_placeholders()}
    return build_governance_page_ready_state(
        local_parity=report_checks.get("local_parity"),
        github_actions=report_checks.get("github_actions"),
        codecov_project=report_checks.get("codecov_project"),
        codecov_patch=report_checks.get("codecov_patch"),
        codex_disposition=report_checks.get("codex_disposition"),
    )


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

