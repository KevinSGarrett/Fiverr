"""Keywords page payload builders for deterministic dashboard contracts."""

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
from src.dashboard.design import confidence_to_text, normalize_run_severity
from src.dashboard.query_layer import DashboardQueryLayer, get_dashboard_query_layer


def build_keywords_payload(
    *,
    records: list[dict[str, Any]] | None,
    filters: dict[str, Any] | None = None,
    sort: dict[str, Any] | None = None,
    query_layer: DashboardQueryLayer | None = None,
) -> dict[str, Any]:
    """Build keyword page payload with cluster context and sparse-data warnings."""
    layer = query_layer or get_dashboard_query_layer()
    result = layer.keywords(records=records, filters=filters, sort=sort)
    context = result.context.as_dict()
    rows = [_normalize_keyword_row(record) for record in result.records]

    warnings = [warning["message"] for warning in context["warnings"]]
    missing_cluster_data = any(row["cluster"] == "not available yet" for row in rows)
    if missing_cluster_data:
        warnings.append("Cluster context not available yet from analysis output (SCRUM-157).")

    metrics = build_metric_cards(
        [
            {"card_id": "keyword_count", "label": "Visible Keywords", "value": str(len(rows))},
            {
                "card_id": "with_clusters",
                "label": "Keywords with Clusters",
                "value": str(sum(1 for row in rows if row["cluster"] != "not available yet")),
            },
        ]
    )
    status_cards = [
        StatusCardPayload(
            card_id="keywords_status",
            label="Keywords Status",
            severity=normalize_run_severity(context.get("status")),
            message=context["empty_state_message"] if context["empty_state"] else "Keyword payload available",
        ).as_dict()
    ]
    evidence_cards = [
        EvidenceCardPayload(
            card_id="keywords_source",
            title="Keyword Source and Freshness",
            source_name=context["source_context"]["source_name"],
            freshness_status=context["freshness"]["freshness_status"],
            details=tuple(warnings),
        ).as_dict()
    ]
    table = build_table_descriptor(
        table_id="keywords_table",
        columns=[
            "keyword",
            "cluster",
            "niche",
            "demand",
            "saturation",
            "score",
            "confidence",
            "confidence_text",
        ],
        rows=rows,
        sort_key=context["applied_sort"].get("field", "score") if context["applied_sort"] else "score",
        sort_descending=context["applied_sort"].get("descending", True) if context["applied_sort"] else True,
        empty_message=context["empty_state_message"] or "No keyword analysis results are available yet.",
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
        message=context["empty_state_message"] or "Keywords payload ready.",
        warnings=warnings,
        source_name=context["source_context"]["source_name"],
        freshness_status=context["freshness"]["freshness_status"],
    )

    return {
        "page_id": "keywords",
        "title": "Keyword Cluster Health",
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


def _normalize_keyword_row(record: dict[str, Any]) -> dict[str, Any]:
    cluster = str(record.get("cluster") or "").strip() or "not available yet"
    confidence = _to_float(record.get("confidence"))
    return {
        "keyword": str(record.get("keyword") or record.get("keyword_text") or "unknown keyword"),
        "cluster": cluster,
        "niche": str(record.get("niche", "unknown")),
        "demand": record.get("demand", "unknown"),
        "saturation": record.get("saturation", "unknown"),
        "score": _to_float(record.get("score")),
        "confidence": confidence,
        "confidence_text": confidence_to_text(confidence),
        "status": str(record.get("status", "unknown")),
        "opportunity_ids": [str(item) for item in record.get("opportunity_ids", [])],
    }


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

