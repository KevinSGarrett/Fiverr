"""Reporting package exports."""

from src.reports.placeholders import ReportPlaceholder
from src.reports.run_summary import RunSummary, build_default_template, render_plain_text_summary
from src.reports.templates import (
    REQUIRED_SECTION_TITLES,
    ReportSection,
    ReportSeverity,
    ReportTemplate,
)

__all__ = [
    "REQUIRED_SECTION_TITLES",
    "ReportPlaceholder",
    "ReportSection",
    "ReportSeverity",
    "ReportTemplate",
    "RunSummary",
    "build_default_template",
    "render_plain_text_summary",
]

