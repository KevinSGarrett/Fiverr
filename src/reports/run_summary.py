"""Run summary contracts and plain-text preview helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.reports.templates import (
    REQUIRED_SECTION_TITLES,
    ReportSection,
    ReportSeverity,
    ReportTemplate,
)


@dataclass(frozen=True, slots=True)
class RunSummary:
    """Minimal summary of one orchestration run for reporting."""

    run_id: str
    status: str
    niche_count: int = 0
    keyword_count: int = 0
    notes: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> bool:
        """Validate minimal run-summary requirements."""
        if not self.run_id.strip():
            raise ValueError("run_id is required.")
        if not self.status.strip():
            raise ValueError("status is required.")
        if self.niche_count < 0 or self.keyword_count < 0:
            raise ValueError("niche_count and keyword_count must be non-negative.")
        return True


def build_default_template() -> ReportTemplate:
    """Build a foundation report template with required sections."""
    sections = tuple(
        ReportSection(title=title, severity=ReportSeverity.INFO, body="")
        for title in REQUIRED_SECTION_TITLES
    )
    return ReportTemplate(name="foundation_run_summary", sections=sections)


def render_plain_text_summary(summary: RunSummary) -> str:
    """Render a safe text-only run summary preview."""
    summary.validate()
    lines = [
        "Fiverr Research Run Summary",
        f"Run ID: {summary.run_id}",
        f"Status: {summary.status}",
        f"Niche Count: {summary.niche_count}",
        f"Keyword Count: {summary.keyword_count}",
    ]

    if summary.notes:
        lines.append("Notes:")
        lines.extend(f"- {note}" for note in summary.notes)

    return "\n".join(lines)
