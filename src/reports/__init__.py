"""Reporting package exports."""

from src.reports.placeholders import (
    GOVERNANCE_REPORT_ORDER,
    ReportPlaceholder,
    build_governance_report_placeholders,
)
from src.reports.run_summary import (
    RunSummary,
    build_cycle003_report_bundle,
    build_default_template,
    build_phase2_readiness_report,
    build_phase2_readiness_template,
    render_plain_text_summary,
    render_structured_report_markdown,
)
from src.reports.templates import (
    PENDING_PLACEHOLDER,
    PHASE2_REQUIRED_SECTION_TITLES,
    REQUIRED_SECTION_TITLES,
    AnalysisDryRunReport,
    AnalysisMultiStageRunReport,
    CollectionDryRunReport,
    CollectionFixtureRunReport,
    CycleValidationReport,
    FoundationGateReport,
    GigDetailParserCoverageReport,
    Phase2ReadinessReport,
    ReportSection,
    ReportSeverity,
    ReportTemplate,
    SellerProfileParserCoverageReport,
    normalize_report_severity,
)

__all__ = [
    "REQUIRED_SECTION_TITLES",
    "PHASE2_REQUIRED_SECTION_TITLES",
    "PENDING_PLACEHOLDER",
    "normalize_report_severity",
    "CollectionFixtureRunReport",
    "GigDetailParserCoverageReport",
    "SellerProfileParserCoverageReport",
    "AnalysisMultiStageRunReport",
    "FoundationGateReport",
    "CollectionDryRunReport",
    "AnalysisDryRunReport",
    "CycleValidationReport",
    "Phase2ReadinessReport",
    "GOVERNANCE_REPORT_ORDER",
    "ReportPlaceholder",
    "ReportSection",
    "ReportSeverity",
    "ReportTemplate",
    "RunSummary",
    "build_governance_report_placeholders",
    "build_cycle003_report_bundle",
    "build_default_template",
    "build_phase2_readiness_template",
    "build_phase2_readiness_report",
    "render_plain_text_summary",
    "render_structured_report_markdown",
]

