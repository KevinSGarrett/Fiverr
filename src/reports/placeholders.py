"""Placeholder reporting models for foundation scaffolding."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ReportPlaceholder:
    """Minimal placeholder for report generation state."""

    report_type: str
    status: str
    message: str

