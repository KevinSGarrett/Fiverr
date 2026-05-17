"""Opportunities page payload builders for deterministic dashboard contracts."""

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
    build_ranking_cards,
    build_runtime_acceptance_status,
    build_state_descriptor,
    build_table_descriptor,
    build_warning_summary,
    get_status_semantics,
)
from src.dashboard.design import normalize_run_severity
from src.dashboard.queries import map_warning_codes_to_operator_severity
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
    pagination = _extract_pagination(filters or {})
    result = layer.opportunities(
        records=records,
        filters=filters,
        sort=sort,
        limit=pagination["limit"],
        offset=pagination["offset"],
    )
    context = result.context.as_dict()
    rows, row_warnings = _normalize_rows(result.records)
    warnings = [warning["message"] for warning in context["warnings"]]
    warnings.extend(row_warnings)

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
            {
                "card_id": "go_recommendations",
                "label": "GO Recommendations",
                "value": str(sum(1 for row in rows if row.get("go_decision") in {"GO", "Strong GO"})),
                "status_badge": "go",
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
    drill_links = [
        {
            "label": "Open Opportunity Details",
            "target": "opportunities/detail",
        },
        {
            "label": "View Related Keywords",
            "target": "keywords",
        },
    ]
    table = build_table_descriptor(
        table_id="opportunities_table",
        columns=[
            "opportunity",
            "niche",
            "score",
            "confidence",
            "confidence_text",
            "go_decision",
            "rank",
            "status",
            "keyword_links",
        ],
        rows=rows,
        sort_key=context["applied_sort"].get("field", "score") if context["applied_sort"] else "score",
        sort_descending=context["applied_sort"].get("descending", True) if context["applied_sort"] else True,
        empty_message=context["empty_state_message"] or "No opportunities are currently available.",
        warnings=warnings,
        filter_descriptors=filter_descriptors,
        drill_links=drill_links,
        source_name=context["source_context"]["source_name"],
        freshness_status=context["freshness"]["freshness_status"],
    )
    warning_summary = build_warning_summary(warnings=warnings)
    detail_panel_schema = build_detail_panel_schema(
        panel_id="opportunity_detail",
        row_id_key="id",
        title_field="opportunity",
        fields=[
            "niche",
            "score",
            "confidence",
            "confidence_text",
            "go_decision",
            "rank",
            "status",
            "keyword_links",
        ],
    )

    state_key: ComponentState = "ready"
    if context["empty_state"]:
        state_key = "empty"
    elif context["status"] == "warning" or warnings:
        state_key = "warning"
    state = build_state_descriptor(
        state=state_key,
        message=context["empty_state_message"] or "Opportunities payload ready.",
        warnings=warnings,
        source_name=context["source_context"]["source_name"],
        freshness_status=context["freshness"]["freshness_status"],
    )
    acceptance_status = build_runtime_acceptance_status(
        state=state_key,
        warnings=warnings,
        stale_data=context["freshness"].get("freshness_status") == "stale",
        evidence_ids=[row["id"] for row in rows[:5]],
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
        "warning_summary": warning_summary,
        "detail_panel_schema": detail_panel_schema,
        "empty_state": build_empty_state_payload(
            title="No opportunities available"
            if context["empty_state"]
            else "Opportunities ready",
            message=context["empty_state_message"] or "Opportunities payload is ready for rendering.",
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


def _format_score_for_metric(value: Any) -> str:
    if value is None:
        return "0.0"
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return "0.0"


def _normalize_rows(records: tuple[dict[str, Any], ...]) -> tuple[list[dict[str, Any]], list[str]]:
    normalized: list[dict[str, Any]] = []
    warnings: list[str] = []
    for index, row in enumerate(records, start=1):
        score = _to_float(row.get("score"))
        confidence = _to_float(row.get("confidence"))
        if score is None:
            warnings.append(f"Opportunity row {index} is missing score; defaulted to 0.0.")
            score = 0.0
        if confidence is None:
            warnings.append(f"Opportunity row {index} is missing confidence; defaulted to 0.0.")
            confidence = 0.0
        semantics = get_status_semantics(str(row.get("status", "unknown")))
        normalized.append(
            {
                "id": str(row.get("id", f"opportunity-{index}")),
                "opportunity": str(row.get("opportunity", "Unknown Opportunity")),
                "niche": str(row.get("niche", "unknown")),
                "score": score,
                "confidence": confidence,
                "confidence_text": "High" if confidence >= 0.75 else ("Medium" if confidence >= 0.5 else "Low"),
                "go_decision": row.get("go_decision") or semantics["status_label"],
                "rank": index,
                "status": str(row.get("status", "unknown")),
                "status_severity": semantics["severity"],
                "keyword_links": [str(link) for link in row.get("keyword_links", [])],
            }
        )
    return normalized, warnings


def _build_filter_descriptors(
    *,
    filters: dict[str, Any],
    source_descriptors: tuple[Any, ...],
) -> list[dict[str, str]]:
    descriptor_map = {descriptor.key: descriptor for descriptor in source_descriptors}
    rows: list[dict[str, str]] = []
    for descriptor in source_descriptors:
        value = filters.get(descriptor.key)
        rows.append(
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
        rows.append(
            {
                "key": key,
                "label": key.replace("_", " ").title(),
                "value": str(value),
                "description": "Temporary page-level adapter descriptor.",
            }
        )
    return rows


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


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_query_contract(context: dict[str, Any]) -> dict[str, Any]:
    warning_codes = sorted(
        {
            str(warning.get("code", "")).strip()
            for warning in context.get("warnings", [])
            if isinstance(warning, dict) and str(warning.get("code", "")).strip()
        }
    )
    return {
        "query_name": "opportunities",
        "status": context.get("status", "warning"),
        "warning_codes": warning_codes,
        "warning_severity": map_warning_codes_to_operator_severity(warning_codes),
        "applied_filters": context.get("applied_filters", {}),
        "applied_sort": context.get("applied_sort", {}),
        "pagination": context.get("pagination"),
        "source_context": context.get("source_context", {}),
        "freshness": context.get("freshness", {}),
    }


def _extract_pagination(filters: dict[str, Any]) -> dict[str, int]:
    default_limit = 25
    default_offset = 0
    try:
        limit = int(filters.get("limit", default_limit))
    except (TypeError, ValueError):
        limit = default_limit
    try:
        offset = int(filters.get("offset", default_offset))
    except (TypeError, ValueError):
        offset = default_offset
    return {"limit": limit, "offset": offset}

