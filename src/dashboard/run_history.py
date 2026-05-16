"""Run history payload builders for deterministic dashboard contracts."""

from __future__ import annotations

from typing import Any

from src.dashboard.components import (
    ComponentState,
    EvidenceCardPayload,
    StatusCardPayload,
    build_descriptor_contract,
    build_detail_panel_schema,
    build_empty_state_payload,
    build_metric_cards,
    build_runtime_acceptance_status,
    build_state_descriptor,
    build_table_descriptor,
    build_warning_summary,
)
from src.dashboard.design import normalize_run_severity
from src.dashboard.query_layer import DashboardQueryLayer, get_dashboard_query_layer

RUN_STATUS_SEVERITY = {
    "pass": "ok",
    "warning": "warning",
    "failed": "error",
    "blocked": "blocked",
    "unknown": "unknown",
    "skipped": "skipped",
}


def map_run_status_to_severity(status: str | None) -> str:
    """Map run statuses into stable severity values used by dashboard payloads."""
    normalized = (status or "").strip().lower()
    if normalized in RUN_STATUS_SEVERITY:
        return RUN_STATUS_SEVERITY[normalized]
    return normalize_run_severity(normalized)


def build_run_history_payload(
    *,
    records: list[dict[str, Any]] | None,
    filters: dict[str, Any] | None = None,
    sort: dict[str, Any] | None = None,
    query_layer: DashboardQueryLayer | None = None,
) -> dict[str, Any]:
    """Build run-history payload with stage/duration/failure summaries."""
    layer = query_layer or get_dashboard_query_layer()
    result = layer.run_history(records=records, filters=filters, sort=sort)
    context = result.context.as_dict()
    rows, row_warnings = _normalize_run_rows(result.records)

    warnings = [warning["message"] for warning in context["warnings"]]
    warnings.extend(row_warnings)
    metrics = build_metric_cards(
        [
            {"card_id": "run_count", "label": "Visible Runs", "value": str(len(rows))},
            {
                "card_id": "warning_count",
                "label": "Warnings",
                "value": str(sum(int(row["warning_count"]) for row in rows)),
            },
            {
                "card_id": "failures",
                "label": "Failed Runs",
                "value": str(sum(1 for row in rows if row["severity"] in {"error", "blocked"})),
                "status_badge": "warning" if rows else "unknown",
            },
        ]
    )
    status_cards = [
        StatusCardPayload(
            card_id="run_history_status",
            label="Run History Status",
            severity=map_run_status_to_severity(context.get("status")),
            message=context["empty_state_message"] if context["empty_state"] else "Run history payload available",
        ).as_dict()
    ]
    evidence_cards = [
        EvidenceCardPayload(
            card_id="run_history_source",
            title="Run History Source and Freshness",
            source_name=context["source_context"]["source_name"],
            freshness_status=context["freshness"]["freshness_status"],
            details=tuple(warnings),
        ).as_dict()
    ]
    filter_descriptors = _build_filter_descriptors(
        filters=context.get("applied_filters") or {},
        source_descriptors=layer.filter_descriptors(),
    )
    sort_descriptors = _build_sort_descriptors(
        applied_sort=context.get("applied_sort") or {},
        source_descriptors=layer.sort_descriptors(),
    )
    table = build_table_descriptor(
        table_id="run_history_table",
        columns=[
            "run_id",
            "status",
            "severity",
            "stage_names",
            "stage_chips",
            "duration_seconds",
            "warning_count",
            "failure_count",
            "failure_summary",
            "evidence_links",
            "next_action",
        ],
        rows=rows,
        sort_key=context["applied_sort"].get("field", "run_id") if context["applied_sort"] else "run_id",
        sort_descending=context["applied_sort"].get("descending", True) if context["applied_sort"] else True,
        empty_message=context["empty_state_message"] or "No run history has been recorded.",
        warnings=warnings,
        filter_descriptors=filter_descriptors,
        drill_links=[
            {"label": "Open Run Detail", "target": "run_history/detail"},
            {"label": "Open Monitoring Alerts", "target": "alerts"},
        ],
        source_name=context["source_context"]["source_name"],
        freshness_status=context["freshness"]["freshness_status"],
    )
    warning_summary = build_warning_summary(warnings=warnings, blocked=context["status"] == "error")
    detail_panel_schema = build_detail_panel_schema(
        panel_id="run_history_detail",
        row_id_key="run_id",
        title_field="run_id",
        fields=[
            "status",
            "severity",
            "stage_names",
            "duration_seconds",
            "warning_count",
            "failure_summary",
            "evidence_links",
            "started_at",
            "completed_at",
            "next_action",
        ],
    )

    state_key: ComponentState = "ready"
    if context["empty_state"]:
        state_key = "empty"
    elif warnings:
        state_key = "warning"
    state = build_state_descriptor(
        state=state_key,
        message=context["empty_state_message"] or "Run history payload ready.",
        warnings=warnings,
        source_name=context["source_context"]["source_name"],
        freshness_status=context["freshness"]["freshness_status"],
    )
    acceptance_status = build_runtime_acceptance_status(
        state=state_key,
        warnings=warnings,
        stale_data=context["freshness"].get("freshness_status") == "stale",
        evidence_ids=[row["run_id"] for row in rows[:5]],
    )

    return {
        "page_id": "run_history",
        "title": "Run History",
        "filters": context["applied_filters"],
        "sort": context["applied_sort"],
        "state": state,
        "metric_cards": metrics,
        "status_cards": status_cards,
        "evidence_cards": evidence_cards,
        "table": table,
        "warning_summary": warning_summary,
        "detail_panel_schema": detail_panel_schema,
        "empty_state": build_empty_state_payload(
            title="No run history available" if context["empty_state"] else "Run history ready",
            message=context["empty_state_message"] or "Run history payload is ready for rendering.",
            next_steps=list(context.get("next_actions") or []),
        ),
        "source": context["source_context"],
        "freshness": context["freshness"],
        "pagination": context["pagination"],
        "filter_descriptor_contract": build_descriptor_contract(
            applied=context["applied_filters"],
            available=filter_descriptors,
        ),
        "sort_descriptor_contract": build_descriptor_contract(
            applied=context["applied_sort"],
            available=sort_descriptors,
        ),
        "query_contract": _build_query_contract(context),
        "acceptance_status": acceptance_status,
        "next_actions": context["next_actions"],
    }


def _normalize_run_rows(records: tuple[dict[str, Any], ...]) -> tuple[list[dict[str, Any]], list[str]]:
    normalized: list[dict[str, Any]] = []
    warnings: list[str] = []
    for index, record in enumerate(records, start=1):
        status = str(record.get("status", "unknown"))
        run_id_raw = str(record.get("run_id", "")).strip()
        run_id = run_id_raw or f"missing-run-id-{index}"
        if not run_id_raw:
            warnings.append(f"Run row {index} is missing run_id; deterministic placeholder assigned.")
        stage_names = [str(stage.get("name", "unknown")) for stage in record.get("stages", [])]
        if not stage_names and record.get("stage_names"):
            stage_names = [str(name) for name in record.get("stage_names", [])]
        if not stage_names:
            warnings.append(f"Run {run_id} has no stage records; stage list defaulted to unknown.")
            stage_names = ["unknown"]
        warning_count = _to_int(record.get("warning_count"))
        duration_seconds = _to_int(record.get("duration_seconds"))
        started_at = str(record.get("started_at", "")).strip() or "unknown"
        completed_at = str(record.get("completed_at", "")).strip() or "unknown"
        if started_at == "unknown" or completed_at == "unknown":
            warnings.append(f"Run {run_id} is missing timestamps; duration evidence is partial.")
        failure_summary = str(record.get("failure_summary", "")).strip() or "None"
        failure_count = 0 if failure_summary == "None" else 1
        report_path = str(record.get("report_path", "")).strip()
        pr_url = str(record.get("pr_url", "")).strip()
        check_url = str(record.get("check_url", "")).strip()
        evidence_link_warnings: list[str] = []
        if not report_path:
            evidence_link_warnings.append("Missing report path")
        if not pr_url:
            evidence_link_warnings.append("Missing PR reference")
        if not check_url:
            evidence_link_warnings.append("Missing check reference")
        if evidence_link_warnings:
            warnings.append(
                f"Run {run_id} has incomplete evidence links: {', '.join(evidence_link_warnings)}."
            )
        normalized.append(
            {
                "run_id": run_id,
                "status": status,
                "severity": map_run_status_to_severity(status),
                "stage_names": stage_names,
                "stage_chips": [{"name": name, "status": "complete" if status == "pass" else "partial"} for name in stage_names],
                "duration_seconds": duration_seconds,
                "warning_count": warning_count,
                "failure_count": failure_count,
                "failure_summary": failure_summary,
                "evidence_links": [
                    {"label": "Run Summary", "target": report_path or f"run://{run_id}/summary", "required": True},
                    {"label": "Pull Request", "target": pr_url or "", "required": False},
                    {"label": "Check Run", "target": check_url or "", "required": False},
                    {"label": "Run Logs", "target": f"run://{run_id}/logs", "required": True},
                ],
                "evidence_link_status": "warning" if evidence_link_warnings else "ready",
                "evidence_link_warnings": evidence_link_warnings,
                "next_action": str(record.get("next_action", "Review warnings and re-run if required")),
                "started_at": started_at,
                "completed_at": completed_at,
            }
        )
    return normalized, warnings


def _build_filter_descriptors(
    *,
    filters: dict[str, Any],
    source_descriptors: tuple[Any, ...],
) -> list[dict[str, str]]:
    descriptor_map = {descriptor.key: descriptor for descriptor in source_descriptors}
    descriptors: list[dict[str, str]] = []
    for descriptor in source_descriptors:
        value = filters.get(descriptor.key)
        descriptors.append(
            {
                "key": descriptor.key,
                "label": descriptor.label,
                "value": "" if value is None else str(value),
                "description": descriptor.description,
            }
        )
    for key, value in filters.items():
        if key in descriptor_map:
            continue
        descriptors.append(
            {
                "key": key,
                "label": key.replace("_", " ").title(),
                "value": str(value),
                "description": "Temporary page-level adapter descriptor.",
            }
        )
    return descriptors


def _build_sort_descriptors(
    *,
    applied_sort: dict[str, Any],
    source_descriptors: tuple[Any, ...],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    applied_field = str(applied_sort.get("field", "")).strip()
    for descriptor in source_descriptors:
        rows.append(
            {
                "key": descriptor.key,
                "label": descriptor.label,
                "value": "desc"
                if applied_field == descriptor.key and bool(applied_sort.get("descending", True))
                else (
                    "asc"
                    if applied_field == descriptor.key and not bool(applied_sort.get("descending", True))
                    else ""
                ),
                "description": descriptor.description,
            }
        )
    return rows


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _build_query_contract(context: dict[str, Any]) -> dict[str, Any]:
    warning_codes = sorted(
        {
            str(warning.get("code", "")).strip()
            for warning in context.get("warnings", [])
            if isinstance(warning, dict) and str(warning.get("code", "")).strip()
        }
    )
    return {
        "query_name": "run_history",
        "status": context.get("status", "warning"),
        "warning_codes": warning_codes,
        "applied_filters": context.get("applied_filters", {}),
        "applied_sort": context.get("applied_sort", {}),
        "pagination": context.get("pagination"),
    }

