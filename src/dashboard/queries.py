"""Reusable dashboard query helpers with deterministic sparse-data behavior.

These helpers intentionally avoid Streamlit and file IO so that tests and callers can
supply fixture-backed data directly.
"""

from __future__ import annotations

from typing import Any, Literal

from src.dashboard.contracts import (
    FilterDescriptor,
    FreshnessMetadata,
    PaginationMetadata,
    QueryContext,
    QueryResult,
    QueryWarning,
    SortDescriptor,
    SourceContext,
)

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
    normalized_records = list(records or [])
    active_filters = dict(filters or {})
    active_sort = dict(sort or {})

    if records is None:
        warnings.append(
            QueryWarning(
                code="missing_records",
                message="Upstream data set is missing; returning deterministic empty records.",
            )
        )

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
    normalized_limit = limit
    normalized_offset = offset
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


