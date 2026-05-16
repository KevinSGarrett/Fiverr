"""Dashboard app shell for future Streamlit-based presentation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config import ConfigLoader
from src.dashboard.alerts import build_dashboard_alerts
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
from src.dashboard.queries import (
    build_data_integrity_readiness_signal,
    summarize_data_integrity_records,
)
from src.dashboard.query_layer import DashboardQueryLayer, get_dashboard_query_layer
from src.dashboard.run_history import build_run_history_payload
from src.dashboard.state import build_cycle003_status_state, build_phase2_readiness_state
from src.reports import build_governance_report_placeholders
from src.reports.placeholders import (
    build_active_story_groups,
    build_first_run_readiness_baseline_payload,
    build_integration_run_context_model,
)

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


_RUNTIME_REQUIRED_PAGE_REGISTRY_ENTRIES: tuple[PageRegistryEntry, ...] = (
    PageRegistryEntry(
        page_id="export_alerts",
        label="Export/Alerts",
        order=1000,
        status="disabled",
        enabled=False,
        required_contracts=("export_system", "alert_summary"),
        disabled_reason="Runtime page registration placeholder pending UI implementation.",
    ),
    PageRegistryEntry(
        page_id="diagnostics",
        label="Diagnostics",
        order=1001,
        status="disabled",
        enabled=False,
        required_contracts=("app_readiness", "source_freshness_summary"),
        disabled_reason="Runtime page registration placeholder pending UI implementation.",
    ),
    PageRegistryEntry(
        page_id="integration_evidence",
        label="Integration Evidence",
        order=1002,
        status="disabled",
        enabled=False,
        required_contracts=("integration_evidence", "analysis_output_contract"),
        disabled_reason="Runtime page registration placeholder pending UI implementation.",
    ),
)


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
    existing_page_ids = {entry.page_id for entry in registry}
    for required_entry in _RUNTIME_REQUIRED_PAGE_REGISTRY_ENTRIES:
        if required_entry.page_id in existing_page_ids:
            continue
        registry.append(required_entry)
    registry.sort(key=lambda entry: entry.order)
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
    config_visibility = build_niche_config_visibility_summary(config_path=config_path)
    first_run_readiness = build_first_run_readiness_summary(
        config_path=config_path,
        data_dir=data_dir,
    )
    if config_visibility["status"] != "ready":
        warning_count += 1
    if first_run_readiness["status"] != "ready":
        warning_count += 1
    return {
        "config_path": str(resolved_config),
        "data_dir": str(resolved_data_dir),
        "checks": checks,
        "warning_count": warning_count,
        "status": "warning" if warning_count else "ready",
        "safe_empty_state": safe_empty_state,
        "data_entries": data_entries,
        "config_visibility": config_visibility,
        "first_run_readiness": first_run_readiness,
    }


def build_niche_config_visibility_summary(*, config_path: str = "config.yaml") -> dict[str, Any]:
    """Return import-safe niche configuration readiness for all nine niches."""
    try:
        config = ConfigLoader(config_path).load()
    except Exception as exc:  # pragma: no cover - exercised via unit tests
        return {
            "status": "warning",
            "expected_niches": 9,
            "loaded_niches": 0,
            "scoring_profiles": [],
            "warnings": [f"Unable to load config: {exc}"],
            "niches": [],
        }
    niche_rows = [
        {
            "niche_id": niche.niche_id,
            "name": niche.name,
            "depth": niche.depth,
            "seed_keywords_count": len(niche.seed_keywords),
            "has_required_fields": bool(niche.niche_id and niche.name and niche.category_path),
        }
        for niche in config.niches
    ]
    warnings: list[str] = []
    if len(config.niches) != 9:
        warnings.append("Config does not expose exactly nine niches.")
    if any(not row["has_required_fields"] for row in niche_rows):
        warnings.append("One or more niches are missing required fields.")
    return {
        "status": "warning" if warnings else "ready",
        "expected_niches": 9,
        "loaded_niches": len(config.niches),
        "scoring_profiles": sorted(config.scoring.profiles.keys()),
        "warnings": warnings,
        "niches": niche_rows,
    }


def build_first_run_readiness_summary(
    *,
    config_path: str = "config.yaml",
    data_dir: str = "data",
) -> dict[str, Any]:
    """Return deterministic first-run readiness summary from local prerequisites."""
    fixture_paths = [
        "tests/fixtures/dashboard/factories.py",
        "tests/fixtures/analysis/factories.py",
    ]
    required_outputs = [
        "artifacts",
        "exports",
        "docs/cycle_reports",
    ]
    missing_outputs = [path for path in required_outputs if not Path(path).exists()]
    prerequisites = {
        "config_exists": Path(config_path).is_file(),
        "data_dir_exists": Path(data_dir).is_dir(),
        "fixture_files_available": all(Path(path).is_file() for path in fixture_paths),
    }
    known_blockers = []
    if missing_outputs:
        known_blockers.append("Missing output directories for reviewable first-run artifacts.")
    if not prerequisites["fixture_files_available"]:
        known_blockers.append("Fixture files required for controlled first-run validation are missing.")
    if not prerequisites["config_exists"]:
        known_blockers.append("Configuration file is missing for first-run readiness.")
    return {
        "status": "warning" if known_blockers else "ready",
        "prerequisites": prerequisites,
        "expected_stages": ["collection", "analysis", "reporting", "validation"],
        "fixture_paths": fixture_paths,
        "required_outputs": required_outputs,
        "missing_outputs": missing_outputs,
        "known_blockers": known_blockers,
    }


def build_app_entry_smoke_state(
    *,
    branch: str | None = None,
    cycle: str | None = None,
    config_path: str = "config.yaml",
    data_dir: str = "data",
    orchestrator_handoff: dict[str, Any] | None = None,
    alert_records: list[dict[str, Any]] | None = None,
    export_records: list[dict[str, Any]] | None = None,
    integration_evidence: dict[str, Any] | None = None,
    query_layer: DashboardQueryLayer | None = None,
) -> dict[str, Any]:
    """Return app-entry smoke state for startup behavior and page registration."""
    page_registry = build_page_registry()
    required_page_ids = _normalize_required_page_ids(
        [
            row["page_id"]
            for row in page_registry
            if row.get("enabled") is True or row.get("status") == "ready"
        ]
    )
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
    effective_handoff = dict(orchestrator_handoff or {})
    if not effective_handoff:
        effective_handoff = {
            "stage_status": readiness["severity"],
            "next_actions": readiness["next_actions"],
        }
    query_diagnostics = build_app_entry_query_diagnostics(
        page_registry=page_registry,
        startup=startup,
        orchestrator_handoff=effective_handoff,
        alert_records=alert_records,
        export_records=export_records,
        integration_evidence=integration_evidence,
        query_layer=query_layer,
    )
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
        "query_diagnostics": query_diagnostics,
        "status": status,
        "safe_empty_state": startup["safe_empty_state"],
    }


def build_app_entry_query_diagnostics(
    *,
    page_registry: list[dict[str, Any]],
    startup: dict[str, Any],
    orchestrator_handoff: dict[str, Any] | None = None,
    alert_records: list[dict[str, Any]] | None = None,
    export_records: list[dict[str, Any]] | None = None,
    integration_evidence: dict[str, Any] | None = None,
    analysis_output_records: list[dict[str, Any]] | None = None,
    query_layer: DashboardQueryLayer | None = None,
) -> dict[str, Any]:
    """Build query-layer diagnostics consumed by app-entry and startup checks."""
    layer = query_layer or get_dashboard_query_layer()
    app_readiness = layer.app_readiness(
        page_registry=page_registry,
        startup_diagnostics=startup,
        orchestrator_handoff=orchestrator_handoff,
    )
    alerts = layer.alert_summary(records=alert_records)
    exports = layer.export_summary(records=export_records, sort={"field": "generated_at", "descending": True})
    evidence = layer.integration_evidence(evidence=integration_evidence)
    analysis_contract = layer.analysis_output_contract(records=analysis_output_records)
    integrity_summary = summarize_data_integrity_records(records=analysis_output_records)
    integrity_signal = build_data_integrity_readiness_signal(records=analysis_output_records)
    startup_run_context = startup.get("run_context")
    if isinstance(startup_run_context, dict):
        runtime_run_context = dict(startup_run_context)
    else:
        cwd = str(Path.cwd())
        runtime_run_context = build_integration_run_context_model(
            expected_root=cwd,
            git_root=cwd,
            branch="unknown",
            worktrees=[cwd],
            dirty_entries=[],
            preflight_status="unknown",
        )
    niche_status = str(startup.get("config_visibility", {}).get("status", "unknown")).strip().lower() or "unknown"
    first_run_status = str(startup.get("first_run_readiness", {}).get("status", "unknown")).strip().lower() or "unknown"
    readiness_baseline = build_first_run_readiness_baseline_payload(
        run_context=runtime_run_context,
        diagnostics_status=str(app_readiness.context.status),
        niche_validation_status=niche_status,
        data_integrity_signal=integrity_signal,
    )
    query_results = {
        "app_readiness": app_readiness.as_dict(),
        "alerts": alerts.as_dict(),
        "exports": exports.as_dict(),
        "integration_evidence": evidence.as_dict(),
        "analysis_output_contract": analysis_contract.as_dict(),
    }
    categories = {
        "app_readiness": app_readiness.context.status,
        "alerts": alerts.context.status,
        "exports": exports.context.status,
        "integration_evidence": evidence.context.status,
        "analysis_output_contract": analysis_contract.context.status,
        "niche_config_validation": niche_status,
        "first_run_readiness": first_run_status,
        "data_integrity": integrity_summary["status"],
        "data_integrity_readiness": integrity_signal["status"],
    }
    payload_availability = _build_query_payload_availability(query_results)
    blocking_categories = [
        category for category, status in categories.items() if status in {"error", "blocked"}
    ]
    warning_categories = [
        category for category, status in categories.items() if status in {"warning", "unknown"}
    ]
    status = "error" if blocking_categories else ("warning" if warning_categories else "ready")
    return {
        "status": status,
        "categories": categories,
        "payload_availability": payload_availability,
        "warning_codes": {
            category: payload["warning_codes"] for category, payload in payload_availability.items()
        },
        "warning_categories": warning_categories,
        "blocking_categories": blocking_categories,
        "results": query_results,
        "data_integrity": integrity_summary,
        "data_integrity_readiness": integrity_signal,
        "runtime_readiness_baseline": readiness_baseline,
    }


def _build_query_payload_availability(
    query_results: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Summarize available/stale/sparse/missing states for query-layer payloads."""
    summary: dict[str, dict[str, Any]] = {}
    for category, payload in query_results.items():
        context = payload.get("context", {})
        freshness = context.get("freshness", {})
        warning_rows = context.get("warnings", [])
        warning_codes = sorted(
            {
                str(row.get("code", "")).strip()
                for row in warning_rows
                if isinstance(row, dict) and str(row.get("code", "")).strip()
            }
        )
        empty_state = bool(context.get("empty_state", False))
        records = payload.get("records")
        has_records = isinstance(records, list) and len(records) > 0
        if not has_records and empty_state:
            availability = "missing"
        elif empty_state or warning_codes:
            availability = "sparse"
        else:
            availability = "available"
        freshness_status = str(freshness.get("freshness_status", "unknown")).strip().lower() or "unknown"
        if freshness_status == "stale":
            availability = "stale"
        summary[category] = {
            "availability": availability,
            "freshness_status": freshness_status,
            "generated_at": freshness.get("generated_at"),
            "warning_codes": warning_codes,
            "source": context.get("source_context", {}),
        }
    return summary


def build_alert_readiness_placeholders(
    alerts: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Normalize alert placeholders without requiring a runtime alerting system."""
    normalized_alerts = build_dashboard_alerts(opportunities=alerts or [])
    return [
        {
            "id": str(alert["id"]),
            "type": str(alert["type"]),
            "severity": str(alert["severity"]),
            "title": str(alert["title"]),
            "source": str(alert["source_context"].get("source", "dashboard")),
            "jira_key": str(alert["jira_key"]),
            "message": str(alert["explanation"]),
            "recommended_action": str(alert["recommended_action"]),
            "dismissible": "true" if bool(alert["dismissible"]) else "false",
            "resolution_status": "dismissible" if bool(alert["dismissible"]) else "action_required",
        }
        for alert in normalized_alerts
    ]


def get_alert_system_descriptor(alerts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return deterministic placeholder metadata for alert-system readiness."""
    normalized_alerts = build_alert_readiness_placeholders(alerts)
    severity_counts = {
        "info": sum(1 for alert in normalized_alerts if alert["severity"] == "info"),
        "warning": sum(1 for alert in normalized_alerts if alert["severity"] == "warning"),
        "error": sum(1 for alert in normalized_alerts if alert["severity"] in {"error", "critical"}),
        "unknown": sum(1 for alert in normalized_alerts if alert["severity"] not in {"info", "warning", "error", "critical"}),
    }
    return {
        "page_id": "alert_system",
        "title": "Alert System",
        "columns": [
            "id",
            "type",
            "severity",
            "title",
            "source",
            "jira_key",
            "message",
            "recommended_action",
            "dismissible",
            "resolution_status",
        ],
        "rows": normalized_alerts,
        "summary": severity_counts,
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
    payloads["registry_metadata"] = {
        "pages_with_payload_support": [
            page_id
            for page_id in ("opportunities", "keywords", "run_history")
            if payloads.get(page_id, {}).get("payload_support", {}).get("implemented") is True
        ],
        "ui_runtime_required": ["opportunities", "keywords", "run_history"],
        "ui_runtime_pending": True,
    }
    acceptance_rollup = build_product_page_acceptance_rollup(payloads=payloads)
    payloads["acceptance_rollup"] = acceptance_rollup
    payloads["runtime_acceptance_matrix"] = build_runtime_acceptance_matrix(payloads=payloads)
    payloads["docs_snippet"] = {
        "title": "Dashboard Runtime Contract Notes",
        "summary": (
            "Payloads expose deterministic query contracts, descriptor contracts, warning summaries, "
            "detail panel schemas, and runtime acceptance states for Opportunities, Keywords, and Run History."
        ),
        "status_rollup": acceptance_rollup["status"],
    }
    product_page_ids = ("opportunities", "keywords", "run_history")
    if acceptance_rollup["status"] == "blocked":
        payloads["registry_state"] = build_state_descriptor(
            state="blocked",
            message="At least one product payload is blocked by missing runtime acceptance prerequisites.",
            warnings=acceptance_rollup["reasons"],
        )
    elif all(payloads[page_id]["state"]["state"] == "empty" for page_id in product_page_ids):
        payloads["registry_state"] = build_state_descriptor(
            state="empty",
            message="All product pages are in safe empty-state mode pending data hydration.",
            warnings=["No records were supplied for opportunities, keywords, or run history."],
        )
    elif acceptance_rollup["status"] == "warning":
        payloads["registry_state"] = build_state_descriptor(
            state="warning",
            message="Product payloads are available with sparse-data warnings.",
            warnings=acceptance_rollup["reasons"],
        )
    elif acceptance_rollup["status"] == "unknown":
        # Unknown acceptance means one or more pages are unresolved; do not over-report readiness.
        payloads["registry_state"] = build_state_descriptor(
            state="warning",
            message="Product payload acceptance is unresolved for at least one page.",
            warnings=acceptance_rollup["reasons"] or ["One or more product pages reported unknown acceptance status."],
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


def build_product_page_acceptance_rollup(*, payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Roll up acceptance status across Opportunities, Keywords, and Run History payloads."""
    page_ids = ("opportunities", "keywords", "run_history")
    rows: list[dict[str, Any]] = []
    reasons: list[str] = []
    status_order = {"ready": 0, "warning": 1, "unknown": 2, "blocked": 3}
    overall = "ready"
    for page_id in page_ids:
        page_payload = payloads.get(page_id, {})
        acceptance = page_payload.get("acceptance_status", {})
        status = str(acceptance.get("status", "unknown")).strip().lower() or "unknown"
        rows.append(
            {
                "page_id": page_id,
                "status": status,
                "warning_count": int(acceptance.get("warning_count", 0)),
                "blocker_count": int(acceptance.get("blocker_count", 0)),
            }
        )
        if status_order.get(status, 2) > status_order.get(overall, 2):
            overall = status
        for reason in acceptance.get("reasons", []):
            normalized_reason = str(reason).strip()
            if normalized_reason and normalized_reason not in reasons:
                reasons.append(normalized_reason)
    return {
        "status": overall,
        "pages": rows,
        "reasons": reasons,
    }


def build_runtime_acceptance_matrix(*, payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Build page-level runtime contract acceptance matrix for operator review."""
    page_ids = ("opportunities", "keywords", "run_history")
    rows: list[dict[str, Any]] = []
    summary = {"ready": 0, "warning": 0, "blocked": 0, "unknown": 0}
    status_order = {"ready": 0, "warning": 1, "unknown": 2, "blocked": 3}
    overall = "ready"
    for page_id in page_ids:
        payload = payloads.get(page_id, {})
        acceptance = payload.get("acceptance_status", {})
        query_contract = payload.get("query_contract", {})
        contract_status = str(acceptance.get("status", "unknown")).strip().lower() or "unknown"
        if contract_status not in summary:
            contract_status = "unknown"
        summary[contract_status] += 1
        if status_order[contract_status] > status_order[overall]:
            overall = contract_status
        pagination = query_contract.get("pagination") or payload.get("pagination") or {}
        warning_severity = query_contract.get("warning_severity", {})
        rows.append(
            {
                "page_id": page_id,
                "acceptance_status": contract_status,
                "warning_count": int(acceptance.get("warning_count", 0)),
                "blocker_count": int(acceptance.get("blocker_count", 0)),
                "has_filter_contract": bool(payload.get("filter_descriptor_contract", {}).get("available")),
                "has_sort_contract": bool(payload.get("sort_descriptor_contract", {}).get("available")),
                "has_detail_schema": bool(payload.get("detail_panel_schema", {}).get("row_id_key")),
                "source_name": str(query_contract.get("source_context", {}).get("source_name", "unknown")),
                "freshness_status": str(query_contract.get("freshness", {}).get("freshness_status", "unknown")),
                "pagination_limit": int(pagination.get("limit", 0) or 0),
                "pagination_offset": int(pagination.get("offset", 0) or 0),
                "pagination_total_count": int(pagination.get("total_count", 0) or 0),
                "pagination_truncated": bool(pagination.get("truncated", False)),
                "warning_severity": str(warning_severity.get("highest_severity", "info")),
            }
        )
    return {
        "status": overall,
        "summary": summary,
        "rows": rows,
    }


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
    st.write(f"- Query diagnostics status: {app_entry_state['query_diagnostics']['status']}")
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

