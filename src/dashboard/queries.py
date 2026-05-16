"""Reusable dashboard query helpers with deterministic sparse-data behavior.

These helpers intentionally avoid Streamlit and file IO so that tests and callers can
supply fixture-backed data directly.
"""

from __future__ import annotations

from typing import Any, Literal

from src.dashboard.contracts import (
    EmptyStateContract,
    FilterDescriptor,
    FreshnessMetadata,
    PaginationMetadata,
    QueryContext,
    QueryResult,
    QueryWarning,
    SortDescriptor,
    SourceContext,
)
from src.reports import build_integration_evidence_summary

DEFAULT_LIMIT = 25
MAX_LIMIT = 250

_DEFAULT_SOURCE = SourceContext(source_name="fixture", source_type="in_memory")

_FILTER_DESCRIPTORS = (
    FilterDescriptor(
        key="status",
        label="Status",
        field_type="string",
        description="Filter records by status.",
    ),
    FilterDescriptor(
        key="niche",
        label="Niche",
        field_type="string",
        description="Filter records by niche identifier.",
    ),
    FilterDescriptor(
        key="confidence_min",
        label="Minimum Confidence",
        field_type="number",
        description="Only include records with confidence at or above this value.",
        default_value=0.0,
        minimum=0.0,
        maximum=1.0,
    ),
    FilterDescriptor(
        key="score_min",
        label="Minimum Score",
        field_type="number",
        description="Only include records with score at or above this value.",
    ),
    FilterDescriptor(
        key="limit",
        label="Page Size",
        field_type="integer",
        description="Maximum records returned in one query response.",
        default_value=DEFAULT_LIMIT,
        minimum=0,
        maximum=MAX_LIMIT,
    ),
    FilterDescriptor(
        key="offset",
        label="Offset",
        field_type="integer",
        description="Number of records to skip before paging results.",
        default_value=0,
        minimum=0,
    ),
)

_SORT_DESCRIPTORS = (
    SortDescriptor(
        key="score",
        label="Opportunity Score",
        default_descending=True,
        description="Sort by score (higher first by default).",
    ),
    SortDescriptor(
        key="confidence",
        label="Confidence",
        default_descending=True,
        description="Sort by confidence (higher first by default).",
    ),
    SortDescriptor(
        key="generated_at",
        label="Generated Time",
        default_descending=True,
        description="Sort by generated timestamp.",
    ),
    SortDescriptor(
        key="run_id",
        label="Run ID",
        default_descending=True,
        description="Sort by run identifier.",
    ),
)

_VALID_STATUS_VALUES = frozenset(
    {
        "ready",
        "warning",
        "blocked",
        "strong_go",
        "conditional_go",
        "monitor",
        "caution",
        "go",
        "no_go",
        "pass",
        "failed",
        "in_progress",
        "in_review",
        "done",
        "unknown",
    }
)


def get_filter_descriptors() -> tuple[FilterDescriptor, ...]:
    """Return reusable query filter descriptors for dashboard page consumers."""
    return _FILTER_DESCRIPTORS


def get_sort_descriptors() -> tuple[SortDescriptor, ...]:
    """Return reusable query sort descriptors for dashboard page consumers."""
    return _SORT_DESCRIPTORS


def query_opportunities(
    *,
    records: list[dict[str, Any]] | None,
    filters: dict[str, Any] | None = None,
    sort: dict[str, Any] | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    source_context: SourceContext | None = None,
    freshness: FreshnessMetadata | None = None,
) -> QueryResult[dict[str, Any]]:
    """Return standardized opportunities payload.

    Example:
        query_opportunities(records=[{"opportunity": "logo", "score": 82.0}])
    """

    return _query_records(
        query_name="opportunities",
        records=records,
        filters=filters,
        sort=sort,
        limit=limit,
        offset=offset,
        source_context=source_context,
        freshness=freshness,
        default_empty_message="No opportunities are currently available.",
    )


def query_keywords(
    *,
    records: list[dict[str, Any]] | None,
    filters: dict[str, Any] | None = None,
    sort: dict[str, Any] | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    source_context: SourceContext | None = None,
    freshness: FreshnessMetadata | None = None,
) -> QueryResult[dict[str, Any]]:
    """Return standardized keyword payload with sparse-data fallbacks.

    Example:
        query_keywords(records=[{"keyword": "seo audit", "confidence": 0.72}])
    """

    return _query_records(
        query_name="keywords",
        records=records,
        filters=filters,
        sort=sort,
        limit=limit,
        offset=offset,
        source_context=source_context,
        freshness=freshness,
        default_empty_message="No keyword analysis results are available yet.",
    )


def query_run_history(
    *,
    records: list[dict[str, Any]] | None,
    filters: dict[str, Any] | None = None,
    sort: dict[str, Any] | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    source_context: SourceContext | None = None,
    freshness: FreshnessMetadata | None = None,
) -> QueryResult[dict[str, Any]]:
    """Return standardized run-history payload with pagination metadata.

    Example:
        query_run_history(records=[{"run_id": "phase2-smoke", "status": "success"}])
    """

    return _query_records(
        query_name="run_history",
        records=records,
        filters=filters,
        sort=sort,
        limit=limit,
        offset=offset,
        source_context=source_context,
        freshness=freshness,
        default_empty_message="No run history has been recorded.",
    )


def query_app_readiness(
    *,
    page_registry: list[dict[str, Any]] | None,
    startup_diagnostics: dict[str, Any] | None,
    orchestrator_handoff: dict[str, Any] | None = None,
    source_context: SourceContext | None = None,
) -> QueryResult[dict[str, Any]]:
    """Return app-readiness payload for dashboard entry diagnostics."""
    warnings: list[QueryWarning] = []
    registry_rows = list(page_registry or [])
    diagnostics = dict(startup_diagnostics or {})
    handoff = dict(orchestrator_handoff or {})
    blocked_pages = [row["page_id"] for row in registry_rows if row.get("status") == "blocked"]

    if not registry_rows:
        warnings.append(
            QueryWarning(
                code="missing_registry",
                message="Page registry is empty; dashboard operates in safe placeholder mode.",
            )
        )
    if not diagnostics:
        warnings.append(
            QueryWarning(
                code="missing_startup_diagnostics",
                message="Startup diagnostics were not provided by app entry checks.",
            )
        )
    if blocked_pages:
        warnings.append(
            QueryWarning(
                code="blocked_pages",
                message="One or more pages are blocked by readiness checks.",
                field="page_registry",
            )
        )

    payload = {
        "registered_pages": len(registry_rows),
        "blocked_pages": blocked_pages,
        "startup_status": diagnostics.get("status", "warning"),
        "warning_count": diagnostics.get("warning_count", len(warnings)),
        "orchestrator_stage_status": handoff.get("stage_status", "unknown"),
        "next_actions": handoff.get("next_actions", []),
    }

    status: Literal["ok", "warning", "error"] = "warning" if warnings else "ok"
    context = QueryContext(
        status=status,
        empty_state=False,
        empty_state_message="App readiness diagnostics are available.",
        warnings=tuple(warnings),
        source_context=source_context or _DEFAULT_SOURCE,
        freshness=FreshnessMetadata(
            freshness_status="unknown",
            generated_at=diagnostics.get("generated_at"),
        ),
        pagination=None,
        applied_filters={},
        applied_sort={},
        next_actions=tuple(payload["next_actions"]),
    )
    return QueryResult(query_name="app_readiness", records=(payload,), total_count=1, context=context)


def query_source_freshness_summary(
    *,
    source_contexts: list[SourceContext] | None,
    freshness_metadata: list[FreshnessMetadata] | None,
) -> QueryResult[dict[str, Any]]:
    """Return source/freshness summary rows for dashboard traceability pages."""
    contexts = list(source_contexts or [])
    freshness_rows = list(freshness_metadata or [])
    warnings: list[QueryWarning] = []

    if not contexts:
        warnings.append(
            QueryWarning(
                code="missing_source_context",
                message="No source contexts were provided; traceability is incomplete.",
            )
        )
    if not freshness_rows:
        warnings.append(
            QueryWarning(
                code="missing_freshness_metadata",
                message="No freshness metadata was provided; freshness defaults to unknown.",
            )
        )

    rows: list[dict[str, Any]] = []
    max_length = max(len(contexts), len(freshness_rows), 1)
    for idx in range(max_length):
        source = contexts[idx] if idx < len(contexts) else _DEFAULT_SOURCE
        freshness = freshness_rows[idx] if idx < len(freshness_rows) else FreshnessMetadata()
        rows.append(
            {
                "source_name": source.source_name,
                "source_type": source.source_type,
                "generated_at": source.generated_at or freshness.generated_at,
                "freshness_status": freshness.freshness_status,
                "confidence_source": source.confidence_source or "unknown",
            }
        )

    query_context = QueryContext(
        status="warning" if warnings else "ok",
        empty_state=False,
        empty_state_message="Source and freshness summary rows are available.",
        warnings=tuple(warnings),
        source_context=_DEFAULT_SOURCE,
        freshness=FreshnessMetadata(freshness_status="unknown"),
        pagination=PaginationMetadata(
            limit=max_length,
            offset=0,
            total_count=len(rows),
            returned_count=len(rows),
            truncated=False,
        ),
        applied_filters={},
        applied_sort={"field": "source_name", "descending": False},
    )
    return QueryResult(
        query_name="source_freshness_summary",
        records=tuple(rows),
        total_count=len(rows),
        context=query_context,
    )


def query_alert_summary(
    *,
    records: list[dict[str, Any]] | None,
    source_context: SourceContext | None = None,
    freshness: FreshnessMetadata | None = None,
) -> QueryResult[dict[str, Any]]:
    """Return alert summary rows for dashboard diagnostics and readiness pages."""
    warnings: list[QueryWarning] = []
    normalized_records = list(records or [])
    if records is None:
        warnings.append(
            QueryWarning(
                code="missing_alert_records",
                message="Alert records were not provided; returning deterministic empty summary.",
            )
        )
    if not normalized_records:
        warnings.append(
            QueryWarning(
                code="empty_alert_records",
                message="No alert records available; alert summary defaults to safe empty state.",
            )
        )
    severity_counts: dict[str, int] = {"info": 0, "warning": 0, "error": 0, "unknown": 0}
    for row in normalized_records:
        severity = _normalize_optional_string(row.get("severity")) or "unknown"
        if severity not in {"info", "warning", "error", "critical"}:
            severity_counts["unknown"] += 1
            continue
        if severity == "critical":
            severity_counts["error"] += 1
            continue
        severity_counts[severity] += 1
    summary_row = {
        "source": (source_context or _DEFAULT_SOURCE).source_name,
        "generated_at": (freshness or FreshnessMetadata()).generated_at,
        "record_count": len(normalized_records),
        "severity_counts": severity_counts,
    }
    context = QueryContext(
        status="warning" if warnings else "ok",
        empty_state=len(normalized_records) == 0,
        empty_state_message="No alert records available." if not normalized_records else "",
        warnings=tuple(warnings),
        source_context=source_context or _DEFAULT_SOURCE,
        freshness=freshness or FreshnessMetadata(),
        pagination=PaginationMetadata(
            limit=1,
            offset=0,
            total_count=1,
            returned_count=1,
            truncated=False,
        ),
        applied_filters={},
        applied_sort={"field": "severity", "descending": True},
    )
    return QueryResult(
        query_name="alert_summary",
        records=(summary_row,),
        total_count=1,
        context=context,
    )


def query_export_summary(
    *,
    records: list[dict[str, Any]] | None,
    filters: dict[str, Any] | None = None,
    sort: dict[str, Any] | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    source_context: SourceContext | None = None,
    freshness: FreshnessMetadata | None = None,
) -> QueryResult[dict[str, Any]]:
    """Return export-manifest summaries with deterministic sparse-data behavior."""
    return _query_records(
        query_name="export_summary",
        records=records,
        filters=filters,
        sort=sort or {"field": "generated_at", "descending": True},
        limit=limit,
        offset=offset,
        source_context=source_context,
        freshness=freshness,
        default_empty_message="No export manifests are available yet.",
    )


def query_integration_evidence(
    *,
    evidence: dict[str, Any] | None,
    source_context: SourceContext | None = None,
    freshness: FreshnessMetadata | None = None,
) -> QueryResult[dict[str, Any]]:
    """Return integration evidence payload consumable by dashboard/query surfaces."""
    warnings: list[QueryWarning] = []
    if evidence is None:
        warnings.append(
            QueryWarning(
                code="missing_integration_evidence",
                message="Integration evidence was not provided; using default deterministic summary.",
            )
        )
    evidence_payload = evidence if isinstance(evidence, dict) else {}
    if evidence is not None and not isinstance(evidence, dict):
        warnings.append(
            QueryWarning(
                code="invalid_integration_evidence_payload",
                message="Integration evidence payload must be an object; using deterministic fallback values.",
                field="evidence",
            )
        )
    raw_stage_status = evidence_payload.get("stage_status", {})
    stage_status = dict(raw_stage_status) if isinstance(raw_stage_status, dict) else {}
    if raw_stage_status and not isinstance(raw_stage_status, dict):
        warnings.append(
            QueryWarning(
                code="invalid_integration_stage_status",
                message="Integration stage_status must be a map; using empty stage status fallback.",
                field="stage_status",
            )
        )
    raw_jira_progress = evidence_payload.get("jira_progress", [])
    jira_progress: list[dict[str, Any]]
    if isinstance(raw_jira_progress, list):
        jira_progress = [row for row in raw_jira_progress if isinstance(row, dict)]
        if len(jira_progress) != len(raw_jira_progress):
            warnings.append(
                QueryWarning(
                    code="invalid_integration_jira_progress_rows",
                    message="Non-object Jira progress rows were ignored for deterministic summary generation.",
                    field="jira_progress",
                )
            )
    else:
        jira_progress = []
        if raw_jira_progress:
            warnings.append(
                QueryWarning(
                    code="invalid_integration_jira_progress",
                    message="Jira progress must be a list of objects; using empty fallback.",
                    field="jira_progress",
                )
            )
    normalized_evidence = build_integration_evidence_summary(
        stage_status=stage_status,
        codex_status=str(evidence_payload.get("codex_status", "pending")),
        codecov_project_status=str(evidence_payload.get("codecov_project_status", "pending")),
        codecov_patch_status=str(evidence_payload.get("codecov_patch_status", "pending")),
        jira_progress=jira_progress,
    )
    generated_at = str(evidence_payload.get("generated_at", "")).strip() or None
    payload = {
        "source": (source_context or _DEFAULT_SOURCE).source_name,
        "generated_at": generated_at,
        "record_count": normalized_evidence["summary"]["jira_rows"],
        "validation_count": normalized_evidence["summary"]["validation_count"],
        "stage_status": normalized_evidence["stage_status"],
        "codex_status": normalized_evidence["codex_status"],
        "codecov": normalized_evidence["codecov"],
        "jira_progress": normalized_evidence["jira_progress"],
    }
    context = QueryContext(
        status="warning" if warnings else "ok",
        empty_state=False,
        empty_state_message="Integration evidence summary is available.",
        warnings=tuple(warnings),
        source_context=source_context or _DEFAULT_SOURCE,
        freshness=freshness or FreshnessMetadata(generated_at=generated_at),
        pagination=PaginationMetadata(
            limit=1,
            offset=0,
            total_count=1,
            returned_count=1,
            truncated=False,
        ),
        applied_filters={},
        applied_sort={"field": "generated_at", "descending": True},
    )
    return QueryResult(
        query_name="integration_evidence",
        records=(payload,),
        total_count=1,
        context=context,
    )


def _query_records(
    *,
    query_name: str,
    records: list[dict[str, Any]] | None,
    filters: dict[str, Any] | None,
    sort: dict[str, Any] | None,
    limit: int,
    offset: int,
    source_context: SourceContext | None,
    freshness: FreshnessMetadata | None,
    default_empty_message: str,
) -> QueryResult[dict[str, Any]]:
    warnings: list[QueryWarning] = []
    normalized_records = [row for row in (records or []) if isinstance(row, dict)]
    active_filters = dict(filters or {})
    active_sort = dict(sort or {})

    if records is None:
        warnings.append(
            QueryWarning(
                code="missing_records",
                message="Upstream data set is missing; returning deterministic empty records.",
            )
        )
    elif len(normalized_records) != len(records):
        warnings.append(
            QueryWarning(
                code="invalid_record_shape",
                message="Non-object rows were dropped from query payload.",
                field="records",
            )
        )

    warnings.extend(_validate_data_integrity(normalized_records))

    filtered = _apply_filters(normalized_records, active_filters)
    sorted_records = _apply_sort(filtered, active_sort)
    bounded_limit, bounded_offset = _normalize_pagination_inputs(limit=limit, offset=offset, warnings=warnings)
    paged_records, pagination = _slice_records(
        records=sorted_records,
        limit=bounded_limit,
        offset=bounded_offset,
    )

    if len(sorted_records) == 0:
        warnings.append(QueryWarning(code="empty_result", message=default_empty_message))

    status: Literal["ok", "warning", "error"] = "warning" if warnings else "ok"
    empty_state = len(paged_records) == 0
    context = QueryContext(
        status=status,
        empty_state=empty_state,
        empty_state_message=default_empty_message if empty_state else "",
        warnings=tuple(warnings),
        source_context=source_context or _DEFAULT_SOURCE,
        freshness=freshness or FreshnessMetadata(),
        pagination=pagination,
        applied_filters=active_filters,
        applied_sort=active_sort,
        next_actions=(
            "Run collection and analysis to hydrate dashboard artifacts.",
            "Verify source freshness before operational review.",
        )
        if empty_state
        else (),
        empty_state_contract=_build_empty_state_contract(
            query_name=query_name,
            default_empty_message=default_empty_message,
        )
        if empty_state
        else None,
    )
    return QueryResult(
        query_name=query_name,
        records=tuple(paged_records),
        total_count=len(sorted_records),
        context=context,
    )


def _apply_filters(records: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
    results = list(records)
    status_filter = _normalize_optional_string(filters.get("status"))
    niche_filter = _normalize_optional_string(filters.get("niche"))
    confidence_min = _to_float(filters.get("confidence_min"))
    score_min = _to_float(filters.get("score_min"))

    if status_filter:
        results = [
            record
            for record in results
            if _normalize_optional_string(record.get("status")) == status_filter
        ]
    if niche_filter:
        results = [
            record for record in results if _normalize_optional_string(record.get("niche")) == niche_filter
        ]
    if confidence_min is not None:
        results = [record for record in results if _to_float_value(record.get("confidence")) >= confidence_min]
    if score_min is not None:
        results = [record for record in results if _to_float_value(record.get("score")) >= score_min]
    return results


def _apply_sort(records: list[dict[str, Any]], sort: dict[str, Any]) -> list[dict[str, Any]]:
    if not sort:
        return sorted(
            records,
            key=lambda row: _to_float_value(row.get("score")),
            reverse=True,
        )
    field = _normalize_optional_string(sort.get("field")) or "score"
    descending = bool(sort.get("descending", True))
    numeric_rows: list[tuple[float, dict[str, Any]]] = []
    textual_rows: list[dict[str, Any]] = []
    missing_rows: list[dict[str, Any]] = []
    for row in records:
        raw_value = row.get(field)
        numeric_value = _to_float(raw_value)
        if numeric_value is not None:
            numeric_rows.append((numeric_value, row))
            continue
        if raw_value is None:
            missing_rows.append(row)
            continue
        textual_rows.append(row)
    numeric_sorted = [row for _, row in sorted(numeric_rows, key=lambda item: item[0], reverse=descending)]
    textual_sorted = sorted(textual_rows, key=lambda row: str(row.get(field)).lower(), reverse=descending)
    return [*numeric_sorted, *textual_sorted, *missing_rows]


def _slice_records(
    *,
    records: list[dict[str, Any]],
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], PaginationMetadata]:
    total_count = len(records)
    paged_records = records[offset : offset + limit] if limit > 0 else records[offset:]
    returned_count = len(paged_records)
    truncated = (offset + returned_count) < total_count
    pagination = PaginationMetadata(
        limit=limit,
        offset=offset,
        total_count=total_count,
        returned_count=returned_count,
        truncated=truncated,
    )
    return (paged_records, pagination)


def _normalize_pagination_inputs(
    *,
    limit: int,
    offset: int,
    warnings: list[QueryWarning],
) -> tuple[int, int]:
    normalized_limit, limit_warning = _coerce_int(limit)
    normalized_offset, offset_warning = _coerce_int(offset)
    if limit_warning:
        warnings.append(
            QueryWarning(
                code="invalid_limit_type",
                message="Non-integer limit was coerced to default.",
                field="limit",
            )
        )
    if offset_warning:
        warnings.append(
            QueryWarning(
                code="invalid_offset_type",
                message="Non-integer offset was coerced to 0.",
                field="offset",
            )
        )
    if normalized_limit < 0:
        warnings.append(
            QueryWarning(
                code="invalid_limit",
                message="Negative limit is not allowed; limit was coerced to 0.",
                field="limit",
            )
        )
        normalized_limit = 0
    if normalized_limit > MAX_LIMIT:
        warnings.append(
            QueryWarning(
                code="limit_capped",
                message=f"Limit exceeded max ({MAX_LIMIT}); limit was capped.",
                field="limit",
            )
        )
        normalized_limit = MAX_LIMIT
    if normalized_offset < 0:
        warnings.append(
            QueryWarning(
                code="invalid_offset",
                message="Negative offset is not allowed; offset was coerced to 0.",
                field="offset",
            )
        )
        normalized_offset = 0
    return (normalized_limit, normalized_offset)


def _validate_data_integrity(records: list[dict[str, Any]]) -> list[QueryWarning]:
    warnings: list[QueryWarning] = []
    seen_ids: set[str] = set()
    seen_ranks: set[int] = set()
    for row in records:
        row_id = str(row.get("id", row.get("run_id", ""))).strip()
        if row_id:
            if row_id in seen_ids:
                warnings.append(
                    QueryWarning(
                        code="duplicate_record_id",
                        message="Duplicate record identifier detected.",
                        field="id",
                    )
                )
            seen_ids.add(row_id)
        score_value = row.get("score")
        numeric_score = _to_float(score_value)
        if score_value is not None and numeric_score is None:
            warnings.append(
                QueryWarning(
                    code="invalid_score",
                    message="One or more score values are non-numeric and will be treated as 0.",
                    field="score",
                )
            )
        confidence_value = row.get("confidence")
        confidence_score = _to_float(confidence_value)
        if confidence_value is not None and confidence_score is None:
            warnings.append(
                QueryWarning(
                    code="invalid_confidence",
                    message="One or more confidence values are non-numeric and will be treated as 0.",
                    field="confidence",
                )
            )
        rank_value, rank_warning = _coerce_optional_int(row.get("rank"))
        if rank_warning:
            warnings.append(
                QueryWarning(
                    code="invalid_rank",
                    message="One or more rank values are invalid and ignored.",
                    field="rank",
                )
            )
        if rank_value is not None:
            if rank_value in seen_ranks:
                warnings.append(
                    QueryWarning(
                        code="duplicate_rank",
                        message="Duplicate rank values detected; ordering remains deterministic.",
                        field="rank",
                    )
                )
            seen_ranks.add(rank_value)
        normalized_status = _normalize_optional_string(row.get("status"))
        if normalized_status and normalized_status not in _VALID_STATUS_VALUES:
            warnings.append(
                QueryWarning(
                    code="invalid_status_category",
                    message="Unexpected status category detected in query payload.",
                    field="status",
                )
            )
    deduped: dict[tuple[str, str | None], QueryWarning] = {}
    for warning in warnings:
        deduped[(warning.code, warning.field)] = warning
    return list(deduped.values())


def _build_empty_state_contract(*, query_name: str, default_empty_message: str) -> EmptyStateContract:
    return EmptyStateContract(
        title=f"{query_name.replace('_', ' ').title()} Empty State",
        explanation=default_empty_message,
        remediation="Run fixture-backed collection/analysis inputs and refresh query consumers.",
        severity="warning",
        source="dashboard.query_layer",
    )


def _coerce_int(value: Any, *, default: int = 0) -> tuple[int, bool]:
    if isinstance(value, bool):
        return (1 if value else 0, True)
    if isinstance(value, int):
        return (value, False)
    if value is None:
        return (default, False)
    try:
        return (int(value), True)
    except (TypeError, ValueError):
        return (default, True)


def _coerce_optional_int(value: Any) -> tuple[int | None, bool]:
    if value is None:
        return (None, False)
    coerced, had_coercion = _coerce_int(value, default=0)
    return (coerced, had_coercion)


def _normalize_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    return normalized or None


def _to_float(value: Any, *, default: float | None = None) -> float | None:
    if value is None:
        return default
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_float_value(value: Any) -> float:
    converted = _to_float(value, default=0.0)
    if converted is None:
        return 0.0
    return converted


