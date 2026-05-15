"""Dashboard app shell for future Streamlit-based presentation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.dashboard.components import build_state_descriptor
from src.dashboard.keywords import build_keywords_payload
from src.dashboard.navigation import (
    DashboardPage,
)
from src.dashboard.navigation import (
    get_available_pages as get_navigation_pages,
)
from src.dashboard.opportunities import build_opportunities_payload
from src.dashboard.pages import build_registered_page_payloads
from src.dashboard.run_history import build_run_history_payload
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
_READINESS_SEVERITY_ORDER = {"ok": 0, "ready": 0, "warning": 1, "error": 2, "blocked": 3}


@dataclass(frozen=True, slots=True)
class PageRegistryEntry:
    """Deterministic app-entry page registry contract."""

    page_id: str
    label: str
    order: int
    status: str
    enabled: bool
    required_contracts: tuple[str, ...]
    disabled_reason: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "page_id": self.page_id,
            "label": self.label,
            "order": self.order,
            "status": self.status,
            "enabled": self.enabled,
            "required_contracts": list(self.required_contracts),
            "disabled_reason": self.disabled_reason,
        }


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
    """Return opportunities page descriptor using reusable payload contracts."""
    return build_opportunities_payload(records=opportunities)


def get_keywords_page_descriptor(
    keywords: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return keywords page descriptor using reusable payload contracts."""
    return build_keywords_payload(records=keywords)


def get_run_history_page_descriptor(
    runs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return run history descriptor using reusable payload contracts."""
    return build_run_history_payload(records=runs)


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


def _normalize_required_page_ids(page_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for page_id in page_ids:
        if page_id in seen:
            continue
        seen.add(page_id)
        normalized.append(page_id)
    return normalized


def build_page_registry() -> list[dict[str, Any]]:
    """Return deterministic page registry with contract + disabled metadata."""
    contract_map: dict[str, tuple[str, ...]] = {
        "overview": ("governance_status", "app_readiness"),
        "foundation_status": ("cycle003_state",),
        "collection_dry_run": ("cycle003_state",),
        "analysis_dry_run": ("cycle003_state",),
        "phase2_readiness": ("phase2_readiness",),
        "phase2_reports": ("query_layer", "run_history"),
        "phase2_exports": ("export_system",),
        "opportunities": ("opportunities", "source_freshness_summary"),
        "niches": ("opportunities", "source_freshness_summary"),
        "keywords": ("keywords", "source_freshness_summary"),
        "run_history": ("run_history",),
        "scores": ("opportunities",),
        "recommendations": ("opportunities", "keywords"),
        "reports": ("query_layer", "governance_status"),
        "settings": ("app_readiness",),
    }
    registry: list[PageRegistryEntry] = []
    for order, page in enumerate(get_navigation_pages()):
        disabled_reason = None
        if not page.enabled:
            disabled_reason = (
                "Feature is preview-only for cycle 004."
                if page.status == "preview_cycle004"
                else "Feature is not implemented yet."
            )
        registry.append(
            PageRegistryEntry(
                page_id=page.page_id,
                label=page.label,
                order=order,
                status="ready" if page.enabled else "disabled",
                enabled=page.enabled,
                required_contracts=contract_map.get(page.page_id, ("app_readiness",)),
                disabled_reason=disabled_reason,
            )
        )
    return [entry.as_dict() for entry in registry]


def compute_page_readiness(
    *,
    page_registry: list[dict[str, Any]],
    startup: dict[str, Any],
    orchestrator_handoff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute readiness severity and next actions from registry + startup evidence."""
    blocked_pages = [row["page_id"] for row in page_registry if row.get("status") == "blocked"]
    startup_status = str(startup.get("status", "warning")).strip().lower() or "warning"
    orchestrator_status = str((orchestrator_handoff or {}).get("stage_status", "ready")).strip().lower()
    statuses = [startup_status, orchestrator_status]
    if blocked_pages:
        statuses.append("blocked")
    severity = max(statuses, key=lambda status: _READINESS_SEVERITY_ORDER.get(status, 1))
    next_actions: list[str] = []
    if blocked_pages:
        next_actions.append("Implement blocked dashboard pages or mark explicit non-goals for this cycle.")
    if startup_status != "ready":
        next_actions.append("Provide config/data fixtures so app startup diagnostics can become ready.")
    if orchestrator_status in {"warning", "error", "blocked"}:
        next_actions.append("Run phase2-smoke and publish orchestrator readiness handoff evidence.")
    if not next_actions:
        next_actions.append("Readiness checks are healthy; continue with page-level product work.")
    return {
        "severity": severity,
        "blocked_pages": blocked_pages,
        "startup_status": startup_status,
        "orchestrator_status": orchestrator_status,
        "next_actions": next_actions,
    }


def build_app_startup_diagnostics(
    *,
    config_path: str = "config.yaml",
    data_dir: str = "data",
) -> dict[str, Any]:
    """Return deterministic startup diagnostics for app-entry smoke checks."""
    resolved_config = Path(config_path)
    resolved_data_dir = Path(data_dir)
    data_entries = sorted(item.name for item in resolved_data_dir.iterdir()) if resolved_data_dir.exists() else []
    config_exists = resolved_config.is_file()
    data_dir_exists = resolved_data_dir.is_dir()
    has_data_entries = len(data_entries) > 0
    safe_empty_state = not has_data_entries

    checks = [
        {
            "name": "config_file",
            "path": str(resolved_config),
            "status": "ready" if config_exists else "warning",
            "message": (
                "Config file is available for dashboard startup."
                if config_exists
                else "Config file is missing; dashboard uses safe placeholder state."
            ),
        },
        {
            "name": "data_directory",
            "path": str(resolved_data_dir),
            "status": "ready" if data_dir_exists else "warning",
            "message": (
                "Data directory is available for dashboard data hydration."
                if data_dir_exists
                else "Data directory is missing; dashboard remains in empty-state mode."
            ),
        },
        {
            "name": "data_entries",
            "path": str(resolved_data_dir),
            "status": "ready" if has_data_entries else "warning",
            "message": (
                f"Found {len(data_entries)} data entries for dashboard hydration."
                if has_data_entries
                else "No data entries found; dashboard renders safe empty-state diagnostics."
            ),
        },
    ]
    warning_count = sum(1 for check in checks if check["status"] == "warning")
    return {
        "config_path": str(resolved_config),
        "data_dir": str(resolved_data_dir),
        "checks": checks,
        "warning_count": warning_count,
        "status": "warning" if warning_count else "ready",
        "safe_empty_state": safe_empty_state,
        "data_entries": data_entries,
    }


def build_app_entry_smoke_state(
    *,
    branch: str | None = None,
    cycle: str | None = None,
    config_path: str = "config.yaml",
    data_dir: str = "data",
) -> dict[str, Any]:
    """Return app-entry smoke state for startup behavior and page registration."""
    page_registry = build_page_registry()
    required_page_ids = _normalize_required_page_ids([row["page_id"] for row in page_registry])
    registered_page_ids = _normalize_required_page_ids([page.page_id for page in get_navigation_pages()])
    missing_pages = [page_id for page_id in required_page_ids if page_id not in registered_page_ids]
    startup = build_app_startup_diagnostics(config_path=config_path, data_dir=data_dir)
    if missing_pages:
        page_registry = [
            row
            if row["page_id"] not in missing_pages
            else {**row, "status": "blocked", "disabled_reason": "Page missing from registration surface."}
            for row in page_registry
        ]
    readiness = compute_page_readiness(page_registry=page_registry, startup=startup)
    registration_status = "blocked" if missing_pages else "ready"
    status = "blocked" if missing_pages else readiness["severity"]
    return {
        "entry": get_app_entry_descriptor(branch=branch, cycle=cycle),
        "page_registry": page_registry,
        "page_registration": {
            "required_page_ids": required_page_ids,
            "registered_page_ids": registered_page_ids,
            "missing_pages": missing_pages,
            "status": registration_status,
        },
        "startup": startup,
        "readiness": readiness,
        "status": status,
        "safe_empty_state": startup["safe_empty_state"],
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


def get_page_registry() -> list[dict[str, Any]]:
    """Expose deterministic app-entry page registry metadata."""
    return build_page_registry()


def get_product_page_payloads(
    *,
    opportunities_records: list[dict[str, Any]] | None = None,
    keywords_records: list[dict[str, Any]] | None = None,
    run_history_records: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Expose product page payload builders via one import-safe registry call."""
    payloads = build_registered_page_payloads(
        opportunities_records=opportunities_records,
        keywords_records=keywords_records,
        run_history_records=run_history_records,
    )
    if all(payload["state"]["state"] == "empty" for payload in payloads.values()):
        payloads["registry_state"] = build_state_descriptor(
            state="empty",
            message="All product pages are in safe empty-state mode pending data hydration.",
            warnings=["No records were supplied for opportunities, keywords, or run history."],
        )
    else:
        payloads["registry_state"] = build_state_descriptor(
            state="ready",
            message="Product page payloads are registered and available.",
        )
    return payloads


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

    st.subheader("App Entry Startup Diagnostics")
    app_entry_state = build_app_entry_smoke_state()
    st.write(f"- Entry module: {app_entry_state['entry']['entry_module']}")
    st.write(f"- Registration status: {app_entry_state['page_registration']['status']}")
    st.write(f"- Startup status: {app_entry_state['startup']['status']}")
    if app_entry_state["safe_empty_state"]:
        st.caption("Safe empty-state mode is active while data artifacts are unavailable.")

    st.subheader("Cycle 014 Product Page Payloads")
    product_payloads = get_product_page_payloads()
    st.write(f"- Registry state: {product_payloads['registry_state']['state']}")
    st.caption(product_payloads["registry_state"]["message"])
    for page_id in ("opportunities", "keywords", "run_history"):
        payload = product_payloads[page_id]
        st.write(f"### {payload['title']}")
        st.write(f"- State: {payload['state']['state']}")
        st.write(f"- Rows: {len(payload['table']['rows'])}")
        if payload["table"]["warning_rows"]:
            st.write(f"- Warning: {payload['table']['warning_rows'][0]['message']}")

