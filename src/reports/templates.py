"""Typed report template contracts for foundation reporting."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ReportSeverity(StrEnum):
    """Allowed severity values for report sections."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


REQUIRED_SECTION_TITLES = (
    "Executive Summary",
    "Niche Overview",
    "Demand Signals",
    "Competition Signals",
    "Scoring Summary",
    "Recommendations",
    "Risks/Limitations",
    "Data Freshness",
)


@dataclass(frozen=True, slots=True)
class ReportSection:
    """Single section in a report template."""

    title: str
    severity: ReportSeverity
    body: str = ""

    def __post_init__(self) -> None:
        """Ensure severity is constrained to the defined enum values."""
        if not isinstance(self.severity, ReportSeverity):
            raise ValueError("severity must be a ReportSeverity value.")


@dataclass(frozen=True, slots=True)
class ReportTemplate:
    """Collection of report sections with required-section validation."""

    name: str
    sections: tuple[ReportSection, ...]

    def missing_required_sections(self) -> tuple[str, ...]:
        """Return required section titles that are absent from the template."""
        present = {section.title for section in self.sections}
        return tuple(title for title in REQUIRED_SECTION_TITLES if title not in present)

    def is_valid(self) -> bool:
        """Return True when all required foundation sections are present."""
        return not self.missing_required_sections()
