"""Non-visual dashboard design tokens for deterministic payload contracts.

This module intentionally excludes Streamlit/CSS dependencies so payload builders can
be imported in unit tests and query layers without UI runtime side effects.
"""

from __future__ import annotations

from typing import Literal

RunSeverity = Literal["ok", "warning", "error", "blocked", "unknown", "skipped"]

SEVERITY_LABELS: dict[RunSeverity, str] = {
    "ok": "Pass",
    "warning": "Warning",
    "error": "Failed",
    "blocked": "Blocked",
    "unknown": "Unknown",
    "skipped": "Skipped",
}

SEVERITY_ICON_NAMES: dict[RunSeverity, str] = {
    "ok": "check-circle",
    "warning": "alert-triangle",
    "error": "x-circle",
    "blocked": "slash-circle",
    "unknown": "help-circle",
    "skipped": "minus-circle",
}

CONFIDENCE_TEXT_RULES: tuple[tuple[float, str], ...] = (
    (0.9, "Very High"),
    (0.75, "High"),
    (0.5, "Medium"),
    (0.25, "Low"),
    (0.0, "Very Low"),
)

TEXT_HIERARCHY_HINTS: dict[str, str] = {
    "title": "heading-lg",
    "subtitle": "heading-md",
    "section": "heading-sm",
    "body": "text-md",
    "caption": "text-sm",
    "meta": "text-xs",
}

SPACING_GROUPS: dict[str, str] = {
    "compact": "space-1",
    "default": "space-2",
    "comfortable": "space-3",
    "section": "space-4",
}

STATE_ACCESSIBLE_LABELS: dict[str, str] = {
    "loading": "Dashboard data is loading",
    "empty": "Dashboard page has no data",
    "warning": "Dashboard page has partial data warnings",
    "error": "Dashboard page has data errors",
    "blocked": "Dashboard page is blocked by missing prerequisites",
    "ready": "Dashboard page data is ready",
}


def confidence_to_text(confidence: float | None) -> str:
    """Map confidence value into deterministic text bands."""
    if confidence is None:
        return "Unknown"
    bounded = max(0.0, min(1.0, confidence))
    for threshold, label in CONFIDENCE_TEXT_RULES:
        if bounded >= threshold:
            return label
    return "Unknown"


def normalize_run_severity(status: str | None) -> RunSeverity:
    """Convert status strings into dashboard severity tokens."""
    normalized = (status or "").strip().lower()
    if normalized in {"pass", "passed", "ok", "ready", "complete", "success"}:
        return "ok"
    if normalized in {"warn", "warning", "partial"}:
        return "warning"
    if normalized in {"fail", "failed", "error"}:
        return "error"
    if normalized in {"blocked"}:
        return "blocked"
    if normalized in {"skip", "skipped"}:
        return "skipped"
    return "unknown"

