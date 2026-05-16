"""Keywords page payload builders for deterministic dashboard contracts."""

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
    rows, row_warnings = _normalize_keyword_rows(result.records)

    warnings = [warning["message"] for warning in context["warnings"]]
    warnings.extend(row_warnings)
    missing_cluster_data = any(row["cluster"] == "not available yet" for row in rows)
    if missing_cluster_data:
        warnings.append("Cluster context not available yet from analysis output (SCRUM-157).")
    if context["freshness"].get("freshness_status") == "unknown":
        warnings.append("Freshness status is unknown; verify source timestamps before GO/NO-GO decisions.")

    metrics = build_metric_cards(
        [
            {"card_id": "keyword_count", "label": "Visible Keywords", "value": str(len(rows))},
            {
                "card_id": "with_clusters",
                "label": "Keywords with Clusters",
                "value": str(sum(1 for row in rows if row["cluster"] != "not available yet")),
            },
            {
                "card_id": "unclustered",
                "label": "Unclustered Keywords",
                "value": str(sum(1 for row in rows if row["cluster"] == "not available yet")),
                "status_badge": "warning" if missing_cluster_data else "go",
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
            "source_name",
            "freshness_status",
            "drill_metadata",
        ],
        rows=rows,
        sort_key=context["applied_sort"].get("field", "score") if context["applied_sort"] else "score",
        sort_descending=context["applied_sort"].get("descending", True) if context["applied_sort"] else True,
        empty_message=context["empty_state_message"] or "No keyword analysis results are available yet.",
        warnings=warnings,
        filter_descriptors=_build_filter_descriptors(
            filters=context.get("applied_filters") or {},
            source_descriptors=layer.filter_descriptors(),
        ),
        drill_links=[
            {"label": "Open Keyword Details", "target": "keywords/detail"},
            {"label": "View Linked Opportunities", "target": "opportunities"},
        ],
        source_name=context["source_context"]["source_name"],
        freshness_status=context["freshness"]["freshness_status"],
    )
    cluster_summary = _build_cluster_summary(rows)

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
        "cluster_summary": cluster_summary,
        "empty_state": build_empty_state_payload(
            title="No keyword analysis available" if context["empty_state"] else "Keyword analysis ready",
            message=context["empty_state_message"] or "Keyword payload is ready for rendering.",
            next_steps=list(context.get("next_actions") or []),
        ),
        "source": context["source_context"],
        "freshness": context["freshness"],
        "pagination": context["pagination"],
        "next_actions": context["next_actions"],
    }


def _normalize_keyword_rows(records: tuple[dict[str, Any], ...]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for index, record in enumerate(records, start=1):
        cluster = str(record.get("cluster") or "").strip() or "not available yet"
        confidence = _to_float(record.get("confidence"))
        score = _to_float(record.get("score"))
        if score is None:
            warnings.append(f"Keyword row {index} has missing score; defaulted to 0.0.")
            score = 0.0
        if confidence is None:
            warnings.append(f"Keyword row {index} has missing confidence; defaulted to Unknown.")
        rows.append(
            {
                "keyword": str(record.get("keyword") or record.get("keyword_text") or "unknown keyword"),
                "cluster": cluster,
                "niche": str(record.get("niche", "unknown")),
                "demand": record.get("demand", "unknown"),
                "saturation": record.get("saturation", "unknown"),
                "score": score,
                "confidence": confidence,
                "confidence_text": confidence_to_text(confidence),
                "status": str(record.get("status", "unknown")),
                "source_name": str(record.get("source_name", "analysis_fixture")),
                "freshness_status": str(record.get("freshness_status", "unknown")),
                "drill_metadata": {
                    "keyword_id": str(record.get("id", f"keyword-{index}")),
                    "opportunity_ids": [str(item) for item in record.get("opportunity_ids", [])],
                },
                "opportunity_ids": [str(item) for item in record.get("opportunity_ids", [])],
            }
        )
    return rows, warnings


def _build_cluster_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for row in rows:
        cluster = str(row.get("cluster", "not available yet"))
        counts[cluster] = counts.get(cluster, 0) + 1
    return {
        "cluster_count": len([cluster for cluster in counts if cluster != "not available yet"]),
        "unclustered_count": counts.get("not available yet", 0),
        "clusters": [{"cluster": cluster, "count": count} for cluster, count in sorted(counts.items())],
        "incomplete_analysis": counts.get("not available yet", 0) > 0,
    }


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


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

