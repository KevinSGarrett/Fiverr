"""Opportunities page payload builders for deterministic dashboard contracts."""

from __future__ import annotations

from typing import Any

from src.dashboard.components import (
    ComponentState,
    EvidenceCardPayload,
    StatusCardPayload,
    build_metric_cards,
    build_ranking_cards,
    build_state_descriptor,
    build_table_descriptor,
)
from src.dashboard.design import normalize_run_severity
from src.dashboard.query_layer import DashboardQueryLayer, get_dashboard_query_layer


def build_opportunities_payload(
    *,
    records: list[dict[str, Any]] | None,
    filters: dict[str, Any] | None = None,
    sort: dict[str, Any] | None = None,
    query_layer: DashboardQueryLayer | None = None,
) -> dict[str, Any]:
    """Build opportunities page payload with filters, sorting, and safe empty states."""
    layer = query_layer or get_dashboard_query_layer()
    result = layer.opportunities(records=records, filters=filters, sort=sort)
    context = result.context.as_dict()
    rows = list(result.records)

    ranking_cards = build_ranking_cards(rows[:3], title_field="opportunity")
    metrics = build_metric_cards(
        [
            {"card_id": "total", "label": "Visible Opportunities", "value": str(len(rows))},
            {
                "card_id": "top_score",
                "label": "Top Score",
                "value": _format_score_for_metric(rows[0].get("score")) if rows else "0.0",
                "status_badge": rows[0].get("status", "unknown") if rows else "unknown",
            },
        ]
    )
    status_cards = [
        StatusCardPayload(
            card_id="opportunity_status",
            label="Opportunities Status",
            severity=normalize_run_severity(context.get("status")),
            message=context["empty_state_message"] if context["empty_state"] else "Opportunities available",
        ).as_dict()
    ]
    evidence_cards = [
        EvidenceCardPayload(
            card_id="opportunities_source",
            title="Source and Freshness",
            source_name=context["source_context"]["source_name"],
            freshness_status=context["freshness"]["freshness_status"],
            details=tuple(warning["message"] for warning in context["warnings"]),
        ).as_dict()
    ]
    table = build_table_descriptor(
        table_id="opportunities_table",
        columns=["opportunity", "niche", "score", "confidence", "status", "keyword_links"],
        rows=rows,
        sort_key=context["applied_sort"].get("field", "score") if context["applied_sort"] else "score",
        sort_descending=context["applied_sort"].get("descending", True) if context["applied_sort"] else True,
        empty_message=context["empty_state_message"] or "No opportunities are currently available.",
        warnings=[warning["message"] for warning in context["warnings"]],
        source_name=context["source_context"]["source_name"],
        freshness_status=context["freshness"]["freshness_status"],
    )

    state_key: ComponentState = "ready"
    if context["empty_state"]:
        state_key = "empty"
    elif context["status"] == "warning":
        state_key = "warning"
    state = build_state_descriptor(
        state=state_key,
        message=context["empty_state_message"] or "Opportunities payload ready.",
        warnings=[warning["message"] for warning in context["warnings"]],
        source_name=context["source_context"]["source_name"],
        freshness_status=context["freshness"]["freshness_status"],
    )

    return {
        "page_id": "opportunities",
        "title": "Top Opportunities",
        "filters": context["applied_filters"],
        "sort": context["applied_sort"],
        "state": state,
        "metric_cards": metrics,
        "status_cards": status_cards,
        "ranking_cards": ranking_cards,
        "evidence_cards": evidence_cards,
        "table": table,
        "source": context["source_context"],
        "freshness": context["freshness"],
        "pagination": context["pagination"],
        "next_actions": context["next_actions"],
    }


def _format_score_for_metric(value: Any) -> str:
    if value is None:
        return "0.0"
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return "0.0"

