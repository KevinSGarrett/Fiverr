"""Unit tests for reporting and export contract scaffolding."""

from __future__ import annotations

import pytest
from src.exports import (
    ExportFormat,
    ExportManifest,
    ExportRequest,
    validate_export_format,
    validate_export_request,
)
from src.reports import (
    ReportSection,
    ReportSeverity,
    ReportTemplate,
    RunSummary,
    build_default_template,
    render_plain_text_summary,
)


def test_run_summary_with_minimal_data_validates() -> None:
    summary = RunSummary(run_id="run-002", status="success")
    assert summary.validate() is True


@pytest.mark.parametrize("format_name", ["csv", "xlsx", "json", "html", "pdf"])
def test_validate_export_format_accepts_supported_formats(format_name: str) -> None:
    assert validate_export_format(format_name) is True


def test_validate_export_format_rejects_unsupported_format() -> None:
    with pytest.raises(ValueError, match="Unsupported export format"):
        validate_export_format("docx")


def test_validate_export_request_rejects_parent_directory_traversal() -> None:
    request = ExportRequest(format=ExportFormat.JSON, output_path="../outside.json")
    with pytest.raises(ValueError, match="parent directory traversal"):
        validate_export_request(request)


def test_export_manifest_is_serializable() -> None:
    manifest = ExportManifest(
        artifact_path="exports/run-002-summary.json",
        format=ExportFormat.JSON,
        row_count=12,
        source_run_id="run-002",
        checksum="abc123",
    )
    serialized = manifest.to_dict()
    assert serialized["artifact_path"] == "exports/run-002-summary.json"
    assert serialized["format"] == "json"
    assert serialized["row_count"] == 12
    assert serialized["source_run_id"] == "run-002"


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
    section = ReportSection(title="Executive Summary", severity=ReportSeverity.INFO, body="ok")
    assert section.severity == ReportSeverity.INFO


def test_report_section_rejects_invalid_severity_value() -> None:
    with pytest.raises(ValueError, match="ReportSeverity"):
        ReportSection(title="Executive Summary", severity="urgent", body="invalid")  # type: ignore[arg-type]

