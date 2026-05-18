"""Typed report template contracts for foundation reporting."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class ReportSeverity(StrEnum):
    """Allowed severity values for report sections."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
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

PHASE2_REQUIRED_SECTION_TITLES = (
    "Collection Fixture Run",
    "Gig Detail Parser Coverage",
    "Seller Profile Parser Coverage",
    "Analysis Multi-Stage Run",
    "Phase 2 PR Readiness",
)

PENDING_PLACEHOLDER = "Pending"


def normalize_report_severity(value: ReportSeverity | str) -> ReportSeverity:
    """Normalize severity values and enforce the Cycle 002 severity contract."""
    if isinstance(value, ReportSeverity):
        return value

    normalized = value.strip().lower()
    try:
        return ReportSeverity(normalized)
    except ValueError as exc:
        supported = ", ".join(member.value for member in ReportSeverity)
        raise ValueError(f"severity must be one of: {supported}.") from exc


@dataclass(frozen=True, slots=True)
class ReportSection:
    """Single section in a report template."""

    title: str
    severity: ReportSeverity | str
    body: str = ""

    def __post_init__(self) -> None:
        """Ensure severity is constrained to the defined enum values."""
        object.__setattr__(self, "severity", normalize_report_severity(self.severity))


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


@dataclass(frozen=True, slots=True)
class OpportunityCard:
    """E09 dashboard card contract for ranked opportunities."""

    opportunity_id: str
    keyword_text: str
    niche: str
    score: float
    confidence: float
    tag: Literal["STRONG GO", "CONDITIONAL GO", "MONITOR", "CAUTION", "PASS"]
    demand_score: float | None = None
    competition_score: float | None = None
    opportunity_score: float | None = None
    feasibility_score: float | None = None
    recommendation_available: bool = False


def _render_section_lines(sections: tuple[ReportSection, ...]) -> list[str]:
    if not sections:
        return [f"- {PENDING_PLACEHOLDER}"]

    lines: list[str] = []
    for section in sections:
        body = section.body.strip() or PENDING_PLACEHOLDER
        lines.append(f"- [{normalize_report_severity(section.severity).value}] {section.title}: {body}")
    return lines


def _render_mapping_lines(
    values: Mapping[str, str | int | float | None] | None,
    empty_message: str = PENDING_PLACEHOLDER,
) -> list[str]:
    if not values:
        return [f"- {empty_message}"]
    return [f"- {key}: {value if value is not None else PENDING_PLACEHOLDER}" for key, value in values.items()]


@dataclass(frozen=True, slots=True)
class FoundationGateReport:
    """Foundation gate review report for cycle validation workflows."""

    cycle_id: str
    gate_status: str = "pending"
    findings: tuple[ReportSection, ...] = ()
    metrics: Mapping[str, str | int | float | None] | None = None
    blocking_issues: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "report_type": "foundation_gate",
            "cycle_id": self.cycle_id,
            "gate_status": self.gate_status,
            "metrics": dict(self.metrics) if self.metrics else {},
            "blocking_issues": list(self.blocking_issues),
            "findings": [
                {
                    "title": section.title,
                    "severity": normalize_report_severity(section.severity).value,
                    "body": section.body,
                }
                for section in self.findings
            ],
        }

    def to_markdown(self) -> str:
        blocking_issue_lines = [f"- {issue}" for issue in self.blocking_issues]
        if not blocking_issue_lines:
            blocking_issue_lines = [f"- {PENDING_PLACEHOLDER}"]

        lines = [
            "# Foundation Gate Report",
            f"- Cycle: {self.cycle_id}",
            f"- Gate Status: {self.gate_status}",
            "## Metrics",
            *_render_mapping_lines(self.metrics),
            "## Findings",
            *_render_section_lines(self.findings),
            "## Blocking Issues",
            *blocking_issue_lines,
        ]
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class CollectionDryRunReport:
    """Collection dry-run report that is safe to render before full execution."""

    cycle_id: str
    run_id: str | None = None
    sample_size: int | None = None
    findings: tuple[ReportSection, ...] = ()
    coverage_notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "report_type": "collection_dry_run",
            "cycle_id": self.cycle_id,
            "run_id": self.run_id,
            "sample_size": self.sample_size,
            "coverage_notes": list(self.coverage_notes),
            "findings": [
                {
                    "title": section.title,
                    "severity": normalize_report_severity(section.severity).value,
                    "body": section.body,
                }
                for section in self.findings
            ],
        }

    def to_markdown(self) -> str:
        coverage_lines = [f"- {note}" for note in self.coverage_notes]
        if not coverage_lines:
            coverage_lines = [f"- {PENDING_PLACEHOLDER}"]

        lines = [
            "# Collection Dry Run Report",
            f"- Cycle: {self.cycle_id}",
            f"- Run ID: {self.run_id or PENDING_PLACEHOLDER}",
            f"- Sample Size: {self.sample_size if self.sample_size is not None else PENDING_PLACEHOLDER}",
            "## Findings",
            *_render_section_lines(self.findings),
            "## Coverage Notes",
            *coverage_lines,
        ]
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class AnalysisDryRunReport:
    """Analysis dry-run report contract for cycle-level QA."""

    cycle_id: str
    analyzed_keywords: int | None = None
    scored_niches: int | None = None
    findings: tuple[ReportSection, ...] = ()
    next_actions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "report_type": "analysis_dry_run",
            "cycle_id": self.cycle_id,
            "analyzed_keywords": self.analyzed_keywords,
            "scored_niches": self.scored_niches,
            "next_actions": list(self.next_actions),
            "findings": [
                {
                    "title": section.title,
                    "severity": normalize_report_severity(section.severity).value,
                    "body": section.body,
                }
                for section in self.findings
            ],
        }

    def to_markdown(self) -> str:
        next_action_lines = [f"- {action}" for action in self.next_actions]
        if not next_action_lines:
            next_action_lines = [f"- {PENDING_PLACEHOLDER}"]

        lines = [
            "# Analysis Dry Run Report",
            f"- Cycle: {self.cycle_id}",
            "- Analyzed Keywords: "
            f"{self.analyzed_keywords if self.analyzed_keywords is not None else PENDING_PLACEHOLDER}",
            f"- Scored Niches: {self.scored_niches if self.scored_niches is not None else PENDING_PLACEHOLDER}",
            "## Findings",
            *_render_section_lines(self.findings),
            "## Next Actions",
            *next_action_lines,
        ]
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class CycleValidationReport:
    """Cycle-level validation report for lint/type/test command outcomes."""

    cycle_id: str
    checks: Mapping[str, str | None] | None = None
    findings: tuple[ReportSection, ...] = ()
    summary: str = PENDING_PLACEHOLDER

    def to_dict(self) -> dict[str, object]:
        return {
            "report_type": "cycle_validation",
            "cycle_id": self.cycle_id,
            "summary": self.summary,
            "checks": dict(self.checks) if self.checks else {},
            "findings": [
                {
                    "title": section.title,
                    "severity": normalize_report_severity(section.severity).value,
                    "body": section.body,
                }
                for section in self.findings
            ],
        }

    def to_markdown(self) -> str:
        lines = [
            "# Cycle Validation Report",
            f"- Cycle: {self.cycle_id}",
            f"- Summary: {self.summary or PENDING_PLACEHOLDER}",
            "## Checks",
            *_render_mapping_lines(self.checks),
            "## Findings",
            *_render_section_lines(self.findings),
        ]
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class CollectionFixtureRunReport:
    """Structured report for fixture-backed collection run coverage."""

    cycle_id: str
    run_id: str | None = None
    fixture_records_total: int | None = None
    fixture_records_processed: int | None = None
    severity: ReportSeverity | str = ReportSeverity.INFO
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "severity", normalize_report_severity(self.severity))

    def to_dict(self) -> dict[str, object]:
        return {
            "report_type": "collection_fixture_run",
            "cycle_id": self.cycle_id,
            "run_id": self.run_id,
            "fixture_records_total": self.fixture_records_total,
            "fixture_records_processed": self.fixture_records_processed,
            "severity": normalize_report_severity(self.severity).value,
            "notes": list(self.notes),
        }

    def to_markdown(self) -> str:
        notes = [f"- {item}" for item in self.notes] if self.notes else [f"- {PENDING_PLACEHOLDER}"]
        lines = [
            "# Collection Fixture Run Report",
            f"- Cycle: {self.cycle_id}",
            f"- Run ID: {self.run_id or PENDING_PLACEHOLDER}",
            "- Fixture Records Total: "
            f"{self.fixture_records_total if self.fixture_records_total is not None else PENDING_PLACEHOLDER}",
            "- Fixture Records Processed: "
            f"{self.fixture_records_processed if self.fixture_records_processed is not None else PENDING_PLACEHOLDER}",
            f"- Severity: {normalize_report_severity(self.severity).value}",
            "## Notes",
            *notes,
        ]
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class GigDetailParserCoverageReport:
    """Structured report for gig-detail parser fixture coverage."""

    cycle_id: str
    coverage_percent: float | None = None
    parsed_count: int | None = None
    expected_count: int | None = None
    severity: ReportSeverity | str = ReportSeverity.INFO
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "severity", normalize_report_severity(self.severity))

    def to_dict(self) -> dict[str, object]:
        return {
            "report_type": "gig_detail_parser_coverage",
            "cycle_id": self.cycle_id,
            "coverage_percent": self.coverage_percent,
            "parsed_count": self.parsed_count,
            "expected_count": self.expected_count,
            "severity": normalize_report_severity(self.severity).value,
            "notes": list(self.notes),
        }

    def to_markdown(self) -> str:
        notes = [f"- {item}" for item in self.notes] if self.notes else [f"- {PENDING_PLACEHOLDER}"]
        lines = [
            "# Gig Detail Parser Coverage Report",
            f"- Cycle: {self.cycle_id}",
            f"- Coverage Percent: {self.coverage_percent if self.coverage_percent is not None else PENDING_PLACEHOLDER}",
            f"- Parsed Count: {self.parsed_count if self.parsed_count is not None else PENDING_PLACEHOLDER}",
            f"- Expected Count: {self.expected_count if self.expected_count is not None else PENDING_PLACEHOLDER}",
            f"- Severity: {normalize_report_severity(self.severity).value}",
            "## Notes",
            *notes,
        ]
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class SellerProfileParserCoverageReport:
    """Structured report for seller-profile parser fixture coverage."""

    cycle_id: str
    coverage_percent: float | None = None
    parsed_count: int | None = None
    expected_count: int | None = None
    severity: ReportSeverity | str = ReportSeverity.INFO
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "severity", normalize_report_severity(self.severity))

    def to_dict(self) -> dict[str, object]:
        return {
            "report_type": "seller_profile_parser_coverage",
            "cycle_id": self.cycle_id,
            "coverage_percent": self.coverage_percent,
            "parsed_count": self.parsed_count,
            "expected_count": self.expected_count,
            "severity": normalize_report_severity(self.severity).value,
            "notes": list(self.notes),
        }

    def to_markdown(self) -> str:
        notes = [f"- {item}" for item in self.notes] if self.notes else [f"- {PENDING_PLACEHOLDER}"]
        lines = [
            "# Seller Profile Parser Coverage Report",
            f"- Cycle: {self.cycle_id}",
            f"- Coverage Percent: {self.coverage_percent if self.coverage_percent is not None else PENDING_PLACEHOLDER}",
            f"- Parsed Count: {self.parsed_count if self.parsed_count is not None else PENDING_PLACEHOLDER}",
            f"- Expected Count: {self.expected_count if self.expected_count is not None else PENDING_PLACEHOLDER}",
            f"- Severity: {normalize_report_severity(self.severity).value}",
            "## Notes",
            *notes,
        ]
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class AnalysisMultiStageRunReport:
    """Structured report for multi-stage analysis dry-run readiness."""

    cycle_id: str
    run_id: str | None = None
    stages_completed: tuple[str, ...] = ()
    stages_pending: tuple[str, ...] = ()
    severity: ReportSeverity | str = ReportSeverity.INFO
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "severity", normalize_report_severity(self.severity))

    def to_dict(self) -> dict[str, object]:
        return {
            "report_type": "analysis_multi_stage_run",
            "cycle_id": self.cycle_id,
            "run_id": self.run_id,
            "stages_completed": list(self.stages_completed),
            "stages_pending": list(self.stages_pending),
            "severity": normalize_report_severity(self.severity).value,
            "notes": list(self.notes),
        }

    def to_markdown(self) -> str:
        completed = [f"- {item}" for item in self.stages_completed] if self.stages_completed else [f"- {PENDING_PLACEHOLDER}"]
        pending = [f"- {item}" for item in self.stages_pending] if self.stages_pending else [f"- {PENDING_PLACEHOLDER}"]
        notes = [f"- {item}" for item in self.notes] if self.notes else [f"- {PENDING_PLACEHOLDER}"]
        lines = [
            "# Analysis Multi-Stage Run Report",
            f"- Cycle: {self.cycle_id}",
            f"- Run ID: {self.run_id or PENDING_PLACEHOLDER}",
            f"- Severity: {normalize_report_severity(self.severity).value}",
            "## Stages Completed",
            *completed,
            "## Stages Pending",
            *pending,
            "## Notes",
            *notes,
        ]
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class Phase2ReadinessReport:
    """Phase 2 readiness report used for PR summaries and handoff packets."""

    cycle_id: str
    run_id: str | None = None
    status: str = "pending"
    sections: tuple[ReportSection, ...] = ()
    checks: Mapping[str, str | int | float | None] | None = None
    blockers: tuple[str, ...] = ()

    def missing_required_sections(self) -> tuple[str, ...]:
        present = {section.title for section in self.sections}
        return tuple(title for title in PHASE2_REQUIRED_SECTION_TITLES if title not in present)

    def to_dict(self) -> dict[str, object]:
        return {
            "report_type": "phase2_readiness",
            "cycle_id": self.cycle_id,
            "run_id": self.run_id,
            "status": self.status,
            "checks": dict(self.checks) if self.checks else {},
            "blockers": list(self.blockers),
            "missing_sections": list(self.missing_required_sections()),
            "sections": [
                {
                    "title": section.title,
                    "severity": normalize_report_severity(section.severity).value,
                    "body": section.body,
                }
                for section in self.sections
            ],
        }

    def to_markdown(self) -> str:
        blocker_lines = [f"- {item}" for item in self.blockers]
        if not blocker_lines:
            blocker_lines = [f"- {PENDING_PLACEHOLDER}"]

        missing_section_lines = [f"- {item}" for item in self.missing_required_sections()]
        if not missing_section_lines:
            missing_section_lines = ["- None"]

        lines = [
            "# Phase 2 PR Readiness Report",
            f"- Cycle: {self.cycle_id}",
            f"- Run ID: {self.run_id or PENDING_PLACEHOLDER}",
            f"- Status: {self.status}",
            "## Checks",
            *_render_mapping_lines(self.checks),
            "## Sections",
            *_render_section_lines(self.sections),
            "## Missing Required Sections",
            *missing_section_lines,
            "## Blockers",
            *blocker_lines,
        ]
        return "\n".join(lines)
