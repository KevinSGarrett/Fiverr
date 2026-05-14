"""Backward-compatible export placeholder helpers."""

from __future__ import annotations

from src.exports.formats import ExportFormat, ExportRequest, validate_export_request

CSV_FORMAT = ExportFormat.CSV.value
XLSX_FORMAT = ExportFormat.XLSX.value
JSON_FORMAT = ExportFormat.JSON.value
HTML_FORMAT = ExportFormat.HTML.value
PDF_FORMAT = ExportFormat.PDF.value

SUPPORTED_EXPORT_FORMATS = frozenset({member.value for member in ExportFormat})


def validate_export_format(format_name: str) -> bool:
    """Validate a legacy single format value."""
    request = ExportRequest(format=format_name, output_path="exports/placeholder.out")
    validate_export_request(request)
    return True

