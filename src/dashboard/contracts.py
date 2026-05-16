"""Typed dashboard query contracts that are UI-framework agnostic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Literal, TypeVar

QueryStatus = Literal["ok", "warning", "error"]
FreshnessStatus = Literal["fresh", "stale", "unknown"]
FieldType = Literal["string", "number", "integer", "boolean", "enum"]

TRecord = TypeVar("TRecord")


@dataclass(frozen=True, slots=True)
class QueryWarning:
    """Structured warning for sparse or missing upstream data."""

    code: str
    message: str
    field: str | None = None

    def as_dict(self) -> dict[str, str]:
        payload = {"code": self.code, "message": self.message}
        if self.field:
            payload["field"] = self.field
        return payload


@dataclass(frozen=True, slots=True)
class SourceContext:
    """Traceability metadata for where a payload came from."""

    source_name: str
    source_type: str
    generated_at: str | None = None
    confidence_source: str | None = None

    def as_dict(self) -> dict[str, str]:
        payload = {
            "source_name": self.source_name,
            "source_type": self.source_type,
        }
        if self.generated_at:
            payload["generated_at"] = self.generated_at
        if self.confidence_source:
            payload["confidence_source"] = self.confidence_source
        return payload


@dataclass(frozen=True, slots=True)
class FreshnessMetadata:
    """Freshness metadata attached to each query result."""

    freshness_status: FreshnessStatus = "unknown"
    generated_at: str | None = None

    def as_dict(self) -> dict[str, str]:
        payload: dict[str, str] = {"freshness_status": str(self.freshness_status)}
        if self.generated_at:
            payload["generated_at"] = self.generated_at
        return payload


@dataclass(frozen=True, slots=True)
class PaginationMetadata:
    """Deterministic pagination details for reusable page consumers."""

    limit: int
    offset: int
    total_count: int
    returned_count: int
    truncated: bool

    def as_dict(self) -> dict[str, int | bool]:
        return {
            "limit": self.limit,
            "offset": self.offset,
            "total_count": self.total_count,
            "returned_count": self.returned_count,
            "truncated": self.truncated,
        }


@dataclass(frozen=True, slots=True)
class FilterDescriptor:
    """Declarative filter descriptor for query layer callers."""

    key: str
    label: str
    field_type: FieldType
    description: str
    default_value: Any | None = None
    allowed_values: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "field_type": self.field_type,
            "description": self.description,
            "default_value": self.default_value,
            "allowed_values": list(self.allowed_values),
            "minimum": self.minimum,
            "maximum": self.maximum,
        }


@dataclass(frozen=True, slots=True)
class SortDescriptor:
    """Declarative sort descriptor for query layer callers."""

    key: str
    label: str
    default_descending: bool
    description: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "default_descending": self.default_descending,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class EmptyStateContract:
    """Consistent empty-state payload for runtime page consumers."""

    title: str
    explanation: str
    remediation: str
    severity: Literal["info", "warning", "error"] = "warning"
    source: str = "query_layer"

    def as_dict(self) -> dict[str, str]:
        return {
            "title": self.title,
            "explanation": self.explanation,
            "remediation": self.remediation,
            "severity": self.severity,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class QueryContext:
    """Operational metadata returned with every query."""

    status: QueryStatus
    empty_state: bool
    empty_state_message: str
    warnings: tuple[QueryWarning, ...] = ()
    source_context: SourceContext = field(
        default_factory=lambda: SourceContext(source_name="fixture", source_type="in_memory")
    )
    freshness: FreshnessMetadata = field(default_factory=FreshnessMetadata)
    pagination: PaginationMetadata | None = None
    applied_filters: dict[str, Any] = field(default_factory=dict)
    applied_sort: dict[str, Any] = field(default_factory=dict)
    next_actions: tuple[str, ...] = ()
    empty_state_contract: EmptyStateContract | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "empty_state": self.empty_state,
            "empty_state_message": self.empty_state_message,
            "warnings": [warning.as_dict() for warning in self.warnings],
            "source_context": self.source_context.as_dict(),
            "freshness": self.freshness.as_dict(),
            "pagination": self.pagination.as_dict() if self.pagination else None,
            "applied_filters": self.applied_filters,
            "applied_sort": self.applied_sort,
            "next_actions": list(self.next_actions),
            "empty_state_contract": (
                self.empty_state_contract.as_dict() if self.empty_state_contract else None
            ),
        }


@dataclass(frozen=True, slots=True)
class QueryResult(Generic[TRecord]):
    """Standardized query payload contract."""

    query_name: str
    records: tuple[TRecord, ...]
    total_count: int
    context: QueryContext

    def as_dict(self) -> dict[str, Any]:
        return {
            "query_name": self.query_name,
            "records": list(self.records),
            "total_count": self.total_count,
            "context": self.context.as_dict(),
        }
