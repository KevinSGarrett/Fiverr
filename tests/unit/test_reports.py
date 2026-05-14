"""Unit tests for reporting and export contract scaffolding."""

from __future__ import annotations

import pytest
from src.exports import (
    ALLOWED_EXPORT_ROOTS,
    CHECKSUM_PLACEHOLDER,
    ExportFormat,
    ExportManifest,
    ExportRequest,
    normalize_export_format,
    validate_export_format,
    validate_export_request,
)
from src.reports import (
    PENDING_PLACEHOLDER,
    PHASE2_REQUIRED_SECTION_TITLES,
    AnalysisDryRunReport,
    CollectionDryRunReport,
    CycleValidationReport,
    FoundationGateReport,
    Phase2ReadinessReport,
    ReportSection,
    ReportSeverity,
    ReportTemplate,
    RunSummary,
    build_default_template,
    build_phase2_readiness_report,
    build_phase2_readiness_template,
    render_plain_text_summary,
)


def test_run_summary_with_minimal_data_validates() -> None:
    summary = RunSummary(run_id="run-002", status="success")
    assert summary.validate() is True


@pytest.mark.parametrize("format_name", ["csv", "xlsx", "json", "html", "pdf", "md"])
def test_validate_export_format_accepts_supported_formats(format_name: str) -> None:
    assert validate_export_format(format_name) is True


def test_validate_export_format_rejects_unsupported_format() -> None:
    with pytest.raises(ValueError, match="Unsupported export format"):
        validate_export_format("docx")


def test_validate_export_request_rejects_parent_directory_traversal() -> None:
    request = ExportRequest(format=ExportFormat.JSON, output_path="../outside.json")
    with pytest.raises(ValueError, match="parent directory traversal"):
        validate_export_request(request)


def test_normalize_export_format_accepts_md() -> None:
    assert normalize_export_format("md") == ExportFormat.MD


def test_export_manifest_is_serializable() -> None:
    manifest = ExportManifest(
        artifact_type="cycle_validation",
        format=ExportFormat.JSON,
        source_cycle="003",
        path="exports/cycle003/validation.json",
        included_sections=("checks", "findings"),
    )
    serialized = manifest.to_dict()
    assert serialized["artifact_type"] == "cycle_validation"
    assert serialized["format"] == "json"
    assert serialized["source_cycle"] == "003"
    assert serialized["path"] == "exports/cycle003/validation.json"
    assert serialized["checksum"] == CHECKSUM_PLACEHOLDER
    assert serialized["allow_pending_checksum"] is True
    assert serialized["included_sections"] == ["checks", "findings"]


def test_export_manifest_rejects_disallowed_root_path() -> None:
    with pytest.raises(ValueError, match="path root must be one of"):
        ExportManifest(
            artifact_type="cycle_validation",
            format=ExportFormat.JSON,
            source_cycle="004",
            path="tmp/cycle004/validation.json",
        )


def test_export_manifest_rejects_traversal_path() -> None:
    with pytest.raises(ValueError, match="parent directory traversal"):
        ExportManifest(
            artifact_type="cycle_validation",
            format=ExportFormat.JSON,
            source_cycle="004",
            path="artifacts/../outside.json",
        )


def test_export_manifest_rejects_unsupported_format() -> None:
    with pytest.raises(ValueError, match="Unsupported export format"):
        ExportManifest(
            artifact_type="cycle_validation",
            format="docx",
            source_cycle="003",
            path="exports/cycle003/validation.docx",
        )


def test_export_manifest_rejects_invalid_checksum_placeholder() -> None:
    with pytest.raises(ValueError, match="checksum must be"):
        ExportManifest(
            artifact_type="cycle_validation",
            format=ExportFormat.MD,
            source_cycle="003",
            path="exports/cycle003/validation.md",
            checksum="pending",
        )


def test_export_manifest_requires_checksum_when_pending_not_allowed() -> None:
    with pytest.raises(ValueError, match="checksum is required"):
        ExportManifest(
            artifact_type="dry_run_summary",
            format=ExportFormat.JSON,
            source_cycle="004",
            path="artifacts/cycle004/dry_run_summary.json",
            allow_pending_checksum=False,
        )


def test_plain_text_summary_includes_run_id_and_status() -> None:
    summary = RunSummary(run_id="run-xyz", status="in_progress", notes=("scaffold only",))
    rendered = render_plain_text_summary(summary)
    assert "Run ID: run-xyz" in rendered
    assert "Status: in_progress" in rendered


def test_missing_required_section_is_detected() -> None:
    template = build_default_template()
    trimmed_template = ReportTemplate(name=template.name, sections=template.sections[:-1])
    assert "Data Freshness" in trimmed_template.missing_required_sections()
    assert trimmed_template.is_valid() is False


def test_report_section_severity_is_constrained() -> None:
    section = ReportSection(title="Executive Summary", severity="info", body="ok")
    assert section.severity == ReportSeverity.INFO


def test_report_section_rejects_invalid_severity_value() -> None:
    with pytest.raises(ValueError, match="severity must be one of"):
        ReportSection(title="Executive Summary", severity="urgent", body="invalid")  # type: ignore[arg-type]


def test_structured_reports_render_markdown_with_data() -> None:
    finding = ReportSection(title="Gate check", severity=ReportSeverity.WARNING, body="Dry run only")
    reports = [
        FoundationGateReport(cycle_id="003", gate_status="conditional", findings=(finding,)),
        CollectionDryRunReport(cycle_id="003", run_id="dry-1", sample_size=10, findings=(finding,)),
        AnalysisDryRunReport(cycle_id="003", analyzed_keywords=12, scored_niches=3, findings=(finding,)),
        CycleValidationReport(cycle_id="003", checks={"pytest": "pass"}, findings=(finding,), summary="green"),
    ]
    for report in reports:
        rendered = report.to_markdown()
        assert "# " in rendered
        assert "003" in rendered
        assert "Gate check" in rendered


def test_structured_reports_render_pending_placeholders_when_optional_missing() -> None:
    reports = [
        FoundationGateReport(cycle_id="003"),
        CollectionDryRunReport(cycle_id="003"),
        AnalysisDryRunReport(cycle_id="003"),
        CycleValidationReport(cycle_id="003"),
    ]
    for report in reports:
        rendered = report.to_markdown()
        assert PENDING_PLACEHOLDER in rendered


def test_phase2_readiness_report_renders_markdown_and_detects_missing_sections() -> None:
    section = ReportSection(
        title="Collection Fixture Run",
        severity=ReportSeverity.INFO,
        body="Fixture run completed for 25 records.",
    )
    report = Phase2ReadinessReport(
        cycle_id="004",
        run_id="phase2-001",
        status="conditional",
        checks={"pytest": "pass", "ruff": "pass"},
        sections=(section,),
        blockers=("Awaiting seller parser fixture delta.",),
    )
    rendered = report.to_markdown()
    assert "Phase 2 PR Readiness Report" in rendered
    assert "conditional" in rendered
    assert "Collection Fixture Run" in rendered
    assert "Gig Detail Parser Coverage" in report.missing_required_sections()


def test_phase2_readiness_template_contains_required_sections() -> None:
    template = build_phase2_readiness_template()
    section_titles = [section.title for section in template.sections]
    assert section_titles == list(PHASE2_REQUIRED_SECTION_TITLES)


def test_phase2_readiness_report_dict_is_json_serializable_shape() -> None:
    report = build_phase2_readiness_report(cycle_id="004", run_id="phase2-pr")
    serialized = report.to_dict()
    assert serialized["report_type"] == "phase2_readiness"
    assert serialized["cycle_id"] == "004"
    assert serialized["run_id"] == "phase2-pr"
    assert serialized["missing_sections"] == []
    assert isinstance(serialized["sections"], list)


def test_report_section_invalid_severity_fails_for_phase2_report() -> None:
    with pytest.raises(ValueError, match="severity must be one of"):
        Phase2ReadinessReport(
            cycle_id="004",
            sections=(ReportSection(title="Phase 2 PR Readiness", severity="urgent", body="invalid"),),  # type: ignore[arg-type]
        )


def test_allowed_export_roots_are_artifacts_and_exports() -> None:
    assert ALLOWED_EXPORT_ROOTS == ("artifacts", "exports")

