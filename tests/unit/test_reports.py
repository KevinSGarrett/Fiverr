"""Unit tests for reporting and export placeholder scaffolding."""

from __future__ import annotations

import pytest
from src.exports import validate_export_format
from src.reports import ReportPlaceholder


def test_report_placeholder_fields_are_available() -> None:
    placeholder = ReportPlaceholder(
        report_type="niche_summary",
        status="pending",
        message="Report generation is not implemented in Cycle 001.",
    )
    assert placeholder.report_type == "niche_summary"
    assert placeholder.status == "pending"


@pytest.mark.parametrize("format_name", ["csv", "xlsx", "json", "html", "pdf"])
def test_validate_export_format_accepts_supported_formats(format_name: str) -> None:
    assert validate_export_format(format_name) is True


def test_validate_export_format_rejects_unsupported_format() -> None:
    with pytest.raises(ValueError, match="Unsupported export format"):
        validate_export_format("docx")

