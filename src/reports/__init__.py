"""Reporting package exports."""

from src.reports.placeholders import ReportPlaceholder
from src.reports.run_summary import (
    RunSummary,
    build_cycle003_report_bundle,
    build_default_template,
    render_plain_text_summary,
    render_structured_report_markdown,
)
from src.reports.templates import (
    PENDING_PLACEHOLDER,
    REQUIRED_SECTION_TITLES,
    AnalysisDryRunReport,
    CollectionDryRunReport,
    CycleValidationReport,
    FoundationGateReport,
    ReportSection,
    ReportSeverity,
    ReportTemplate,
    normalize_report_severity,
)

__all__ = [
    "REQUIRED_SECTION_TITLES",
    "PENDING_PLACEHOLDER",
    "normalize_report_severity",
    "FoundationGateReport",
    "CollectionDryRunReport",
    "AnalysisDryRunReport",
    "CycleValidationReport",
    "ReportPlaceholder",
    "ReportSection",
    "ReportSeverity",
    "ReportTemplate",
    "RunSummary",
    "build_cycle003_report_bundle",
    "build_default_template",
    "render_plain_text_summary",
    "render_structured_report_markdown",
]

