"""Reusable dashboard payload components.

These components define deterministic, typed data contracts for page payload builders.
They are intentionally framework-agnostic so Streamlit rendering can be added later
without changing business-oriented payload tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from src.dashboard.design import (
    SEVERITY_ICON_NAMES,
    SEVERITY_LABELS,
    STATE_ACCESSIBLE_LABELS,
    RunSeverity,
    confidence_to_text,
    normalize_run_severity,
)

ComponentState = Literal["loading", "empty", "warning", "error", "blocked", "ready"]


@dataclass(frozen=True, slots=True)
class ComponentStateDescriptor:
    """Standardized state descriptor shared by all dashboard payloads."""

    state: ComponentState
    message: str
    warnings: tuple[str, ...] = ()
    source_name: str = "fixture"
    freshness_status: str = "unknown"
    accessible_label: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "message": self.message,
            "warnings": list(self.warnings),
            "source_name": self.source_name,
            "freshness_status": self.freshness_status,
            "accessible_label": self.accessible_label or STATE_ACCESSIBLE_LABELS[self.state],
        }


@dataclass(frozen=True, slots=True)
class MetricCardPayload:
    """Reusable metric card payload for summary counts and key KPIs."""

    card_id: str
    label: str
    value: str
    hint: str = ""
    status_badge: str = "Unknown"

    def as_dict(self) -> dict[str, str]:
        return {
            "type": "metric_card",
            "card_id": self.card_id,
            "label": self.label,
            "value": self.value,
            "hint": self.hint,
            "status_badge": self.status_badge,
        }


@dataclass(frozen=True, slots=True)
class StatusCardPayload:
    """Reusable status card payload for run and recommendation states."""

    card_id: str
    label: str
    severity: str
    message: str

    def as_dict(self) -> dict[str, str]:
        severity = _normalize_severity(self.severity)
        return {
            "type": "status_card",
            "card_id": self.card_id,
            "label": self.label,
            "severity": severity,
            "severity_label": SEVERITY_LABELS[severity],
            "icon_name": SEVERITY_ICON_NAMES[severity],
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class RankingCardPayload:
    """Reusable ranking card payload for opportunities and keyword highlights."""

    card_id: str
    rank: int
    title: str
    score: float | None
    confidence: float | None
    status: str
    niche: str = "unknown"
    keyword_links: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "type": "ranking_card",
            "card_id": self.card_id,
            "rank": self.rank,
            "title": self.title,
            "score": self.score,
            "confidence": self.confidence,
            "confidence_text": confidence_to_text(self.confidence),
            "status_badge": normalize_status_badge(self.status),
            "niche": self.niche,
            "keyword_links": list(self.keyword_links),
        }


@dataclass(frozen=True, slots=True)
class EvidenceCardPayload:
    """Reusable evidence card payload for source and freshness context."""

    card_id: str
    title: str
    source_name: str
    freshness_status: str
    details: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "type": "evidence_card",
            "card_id": self.card_id,
            "title": self.title,
            "source_name": self.source_name,
            "freshness_status": self.freshness_status,
            "details": list(self.details),
        }


@dataclass(frozen=True, slots=True)
class TableDescriptor:
    """Reusable table/list payload descriptor for dashboard pages."""

    table_id: str
    columns: tuple[str, ...]
    rows: tuple[dict[str, Any], ...]
    sort_key: str = "score"
    sort_descending: bool = True
    empty_message: str = "No rows available."
    warning_rows: tuple[dict[str, str], ...] = ()
    source_name: str = "fixture"
    freshness_status: str = "unknown"

    def as_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "columns": list(self.columns),
            "rows": list(self.rows),
            "sort": {"key": self.sort_key, "descending": self.sort_descending},
            "empty_state": len(self.rows) == 0,
            "empty_message": self.empty_message,
            "warning_rows": list(self.warning_rows),
            "source_name": self.source_name,
            "freshness_status": self.freshness_status,
        }


def normalize_status_badge(status: str | None) -> str:
    """Convert status values into stable badge text for payload consumers."""
    normalized = (status or "").strip().lower()
    mapping = {
        "strong_go": "Strong GO",
        "go": "GO",
        "conditional_go": "Conditional GO",
        "monitor": "Monitor",
        "caution": "Caution",
        "pass": "Pass",
        "warning": "Warning",
        "failed": "Failed",
        "blocked": "Blocked",
    }
    return mapping.get(normalized, "Unknown")


def _normalize_severity(raw_severity: str) -> RunSeverity:
    return normalize_run_severity(raw_severity)


def build_state_descriptor(
    *,
    state: ComponentState,
    message: str,
    warnings: list[str] | tuple[str, ...] | None = None,
    source_name: str = "fixture",
    freshness_status: str = "unknown",
) -> dict[str, Any]:
    """Build deterministic loading/empty/error/sparse state payload."""
    return ComponentStateDescriptor(
        state=state,
        message=message,
        warnings=tuple(warnings or ()),
        source_name=source_name,
        freshness_status=freshness_status,
    ).as_dict()


def build_metric_cards(metrics: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Build reusable metric cards from row dictionaries."""
    cards: list[dict[str, str]] = []
    for row in metrics:
        cards.append(
            MetricCardPayload(
                card_id=str(row.get("card_id", row.get("label", "metric"))),
                label=str(row.get("label", "Metric")),
                value=str(row.get("value", "0")),
                hint=str(row.get("hint", "")),
                status_badge=normalize_status_badge(str(row.get("status_badge", "unknown"))),
            ).as_dict()
        )
    return cards


def build_table_descriptor(
    *,
    table_id: str,
    columns: list[str],
    rows: list[dict[str, Any]],
    sort_key: str,
    sort_descending: bool = True,
    empty_message: str = "No rows available.",
    warnings: list[str] | None = None,
    source_name: str = "fixture",
    freshness_status: str = "unknown",
) -> dict[str, Any]:
    """Build standardized list/table descriptor with warning rows."""
    warning_rows = tuple({"message": warning} for warning in (warnings or []))
    return TableDescriptor(
        table_id=table_id,
        columns=tuple(columns),
        rows=tuple(rows),
        sort_key=sort_key,
        sort_descending=sort_descending,
        empty_message=empty_message,
        warning_rows=warning_rows,
        source_name=source_name,
        freshness_status=freshness_status,
    ).as_dict()


def build_ranking_cards(rows: list[dict[str, Any]], *, title_field: str) -> list[dict[str, Any]]:
    """Build ranking cards from sorted rows with stable confidence and status text."""
    cards: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        cards.append(
            RankingCardPayload(
                card_id=str(row.get("id", f"{title_field}-{index}")),
                rank=index,
                title=str(row.get(title_field, "Unknown")),
                score=_to_float_or_none(row.get("score")),
                confidence=_to_float_or_none(row.get("confidence")),
                status=str(row.get("status", "unknown")),
                niche=str(row.get("niche", "unknown")),
                keyword_links=tuple(str(link) for link in row.get("keyword_links", [])),
            ).as_dict()
        )
    return cards


def _to_float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

