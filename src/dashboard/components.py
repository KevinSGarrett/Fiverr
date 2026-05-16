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
    status_severity: RunSeverity = "unknown"

    def as_dict(self) -> dict[str, str]:
        return {
            "type": "metric_card",
            "card_id": self.card_id,
            "label": self.label,
            "value": self.value,
            "hint": self.hint,
            "status_badge": self.status_badge,
            "status_severity": self.status_severity,
            "status_accessible_label": SEVERITY_LABELS[self.status_severity],
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
            "accessibility_text": f"{self.label}: {SEVERITY_LABELS[severity]}",
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
    filter_descriptors: tuple[dict[str, str], ...] = ()
    drill_links: tuple[dict[str, str], ...] = ()
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
            "filter_descriptors": list(self.filter_descriptors),
            "drill_links": list(self.drill_links),
            "source_name": self.source_name,
            "freshness_status": self.freshness_status,
        }


@dataclass(frozen=True, slots=True)
class EmptyStatePayload:
    """Reusable empty/incomplete payload descriptor."""

    title: str
    message: str
    next_steps: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "message": self.message,
            "next_steps": list(self.next_steps),
        }


@dataclass(frozen=True, slots=True)
class RuntimeAcceptanceStatus:
    """Stable runtime acceptance contract for dashboard product payloads."""

    status: Literal["ready", "warning", "blocked", "unknown"]
    reasons: tuple[str, ...] = ()
    warning_count: int = 0
    blocker_count: int = 0
    stale_data: bool = False
    evidence_ids: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reasons": list(self.reasons),
            "warning_count": self.warning_count,
            "blocker_count": self.blocker_count,
            "stale_data": self.stale_data,
            "evidence_ids": list(self.evidence_ids),
        }


def normalize_status_badge(status: str | None) -> str:
    """Convert status values into stable badge text for payload consumers."""
    normalized = (status or "").strip().lower()
    mapping = {
        "strong_go": "Strong GO",
        "go": "GO",
        "conditional_go": "Conditional GO",
        "no_go": "NO-GO",
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


def get_status_semantics(status: str | None) -> dict[str, str]:
    """Return stable status/severity semantics without visual-token coupling."""
    normalized = (status or "").strip().lower()
    category_map = {
        "strong_go": "go",
        "go": "go",
        "conditional_go": "monitor",
        "monitor": "monitor",
        "caution": "monitor",
        "warning": "monitor",
        "no_go": "no_go",
        "blocked": "blocked",
        "failed": "no_go",
        "pass": "go",
    }
    severity_map: dict[str, RunSeverity] = {
        "strong_go": "ok",
        "go": "ok",
        "conditional_go": "warning",
        "monitor": "warning",
        "caution": "warning",
        "warning": "warning",
        "no_go": "error",
        "blocked": "blocked",
        "failed": "error",
        "pass": "ok",
    }
    severity = severity_map.get(normalized, "unknown")
    return {
        "status_key": normalized or "unknown",
        "status_label": normalize_status_badge(normalized),
        "severity": severity,
        "severity_label": SEVERITY_LABELS[severity],
        "category": category_map.get(normalized, "unknown"),
        "accessibility_text": (
            f"Status {normalize_status_badge(normalized)} with {SEVERITY_LABELS[severity]} severity"
        ),
    }


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
        semantics = get_status_semantics(str(row.get("status_badge", "unknown")))
        cards.append(
            MetricCardPayload(
                card_id=str(row.get("card_id", row.get("label", "metric"))),
                label=str(row.get("label", "Metric")),
                value=str(row.get("value", "0")),
                hint=str(row.get("hint", "")),
                status_badge=semantics["status_label"],
                status_severity=semantics["severity"],  # type: ignore[arg-type]
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
    filter_descriptors: list[dict[str, str]] | None = None,
    drill_links: list[dict[str, str]] | None = None,
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
        filter_descriptors=tuple(filter_descriptors or ()),
        drill_links=tuple(drill_links or ()),
        source_name=source_name,
        freshness_status=freshness_status,
    ).as_dict()


def build_empty_state_payload(
    *,
    title: str,
    message: str,
    next_steps: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build deterministic empty/incomplete state payload."""
    return EmptyStatePayload(
        title=title,
        message=message,
        next_steps=tuple(next_steps or ()),
    ).as_dict()


def build_warning_summary(
    *,
    warnings: list[str] | tuple[str, ...] | None = None,
    blocked: bool = False,
) -> dict[str, Any]:
    """Build deterministic warning-summary contract shared across pages."""
    warning_rows = [str(item) for item in (warnings or ()) if str(item).strip()]
    severity = "blocked" if blocked else ("warning" if warning_rows else "ok")
    return {
        "severity": severity,
        "count": len(warning_rows),
        "messages": warning_rows,
    }


def build_descriptor_contract(
    *,
    applied: dict[str, Any],
    available: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build reusable descriptor contract with applied + available values."""
    return {
        "applied": dict(applied),
        "available": available,
    }


def build_runtime_acceptance_status(
    *,
    state: ComponentState,
    warnings: list[str] | tuple[str, ...] | None = None,
    stale_data: bool = False,
    evidence_ids: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Return deterministic runtime acceptance status for page payloads."""
    warning_rows = [str(item) for item in (warnings or ()) if str(item).strip()]
    blockers = [message for message in warning_rows if "blocked" in message.lower()]
    status: Literal["ready", "warning", "blocked", "unknown"] = "unknown"
    if state == "blocked":
        status = "blocked"
    elif state in {"warning", "error"} or warning_rows:
        status = "warning"
    elif state == "ready":
        status = "ready"
    reasons: list[str] = []
    if warning_rows:
        reasons.append("Warnings present in payload contract.")
    if stale_data:
        reasons.append("Freshness state indicates stale runtime evidence.")
    if not reasons and status == "ready":
        reasons.append("Payload contract is ready for runtime consumption.")
    if not reasons:
        reasons.append("Runtime status is unknown until additional evidence is supplied.")
    return RuntimeAcceptanceStatus(
        status=status,
        reasons=tuple(reasons),
        warning_count=len(warning_rows),
        blocker_count=len(blockers),
        stale_data=stale_data,
        evidence_ids=tuple(str(item) for item in (evidence_ids or ()) if str(item).strip()),
    ).as_dict()


def build_detail_panel_schema(
    *,
    panel_id: str,
    row_id_key: str,
    title_field: str,
    fields: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    """Build stable detail-panel schema for UI adapters."""
    return {
        "panel_id": panel_id,
        "row_id_key": row_id_key,
        "title_field": title_field,
        "fields": [str(field) for field in fields],
    }


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

