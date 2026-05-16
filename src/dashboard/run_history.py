"""Run history payload builders for deterministic dashboard contracts."""

from __future__ import annotations

from typing import Any

from src.dashboard.components import (
    ComponentState,
    EvidenceCardPayload,
    StatusCardPayload,
    build_metric_cards,
    build_state_descriptor,
    build_table_descriptor,
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
    rows = [_normalize_run_row(row) for row in result.records]

    warnings = [warning["message"] for warning in context["warnings"]]
    metrics = build_metric_cards(
        [
            {"card_id": "run_count", "label": "Visible Runs", "value": str(len(rows))},
            {
                "card_id": "warning_count",
                "label": "Warnings",
                "value": str(sum(int(row["warning_count"]) for row in rows)),
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
    table = build_table_descriptor(
        table_id="run_history_table",
        columns=[
            "run_id",
            "status",
            "severity",
            "stage_names",
            "duration_seconds",
            "warning_count",
            "failure_summary",
            "next_action",
        ],
        rows=rows,
        sort_key=context["applied_sort"].get("field", "run_id") if context["applied_sort"] else "run_id",
        sort_descending=context["applied_sort"].get("descending", True) if context["applied_sort"] else True,
        empty_message=context["empty_state_message"] or "No run history has been recorded.",
        warnings=warnings,
        source_name=context["source_context"]["source_name"],
        freshness_status=context["freshness"]["freshness_status"],
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
        "source": context["source_context"],
        "freshness": context["freshness"],
        "pagination": context["pagination"],
        "next_actions": context["next_actions"],
    }


def _normalize_run_row(record: dict[str, Any]) -> dict[str, Any]:
    status = str(record.get("status", "unknown"))
    stage_names = [str(stage.get("name", "unknown")) for stage in record.get("stages", [])]
    if not stage_names and record.get("stage_names"):
        stage_names = [str(name) for name in record.get("stage_names", [])]
    failure_summary = str(record.get("failure_summary", "")).strip() or "None"
    warning_count = _to_int(record.get("warning_count"))
    duration_seconds = _to_int(record.get("duration_seconds"))
    return {
        "run_id": str(record.get("run_id", "unknown")),
        "status": status,
        "severity": map_run_status_to_severity(status),
        "stage_names": stage_names,
        "duration_seconds": duration_seconds,
        "warning_count": warning_count,
        "failure_summary": failure_summary,
        "next_action": str(record.get("next_action", "Review warnings and re-run if required")),
    }


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

