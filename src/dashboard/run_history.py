"""Run history payload builders for deterministic dashboard contracts."""

from __future__ import annotations

from typing import Any

from src.dashboard.components import (
    ComponentState,
    EvidenceCardPayload,
    StatusCardPayload,
    build_empty_state_payload,
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
        filter_descriptors=_build_filter_descriptors(
            filters=context.get("applied_filters") or {},
            source_descriptors=layer.filter_descriptors(),
        ),
        drill_links=[
            {"label": "Open Run Detail", "target": "run_history/detail"},
            {"label": "Open Monitoring Alerts", "target": "alerts"},
        ],
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
        "empty_state": build_empty_state_payload(
            title="No run history available" if context["empty_state"] else "Run history ready",
            message=context["empty_state_message"] or "Run history payload is ready for rendering.",
            next_steps=list(context.get("next_actions") or []),
        ),
        "source": context["source_context"],
        "freshness": context["freshness"],
        "pagination": context["pagination"],
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
                    f"run://{run_id}/summary",
                    f"run://{run_id}/logs",
                ],
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
    for key, value in filters.items():
        descriptor = descriptor_map.get(key)
        descriptors.append(
            {
                "key": key,
                "label": descriptor.label if descriptor else key.replace("_", " ").title(),
                "value": str(value),
                "description": descriptor.description if descriptor else "Temporary page-level adapter descriptor.",
            }
        )
    return descriptors


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

