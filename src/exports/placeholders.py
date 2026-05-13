"""Export format placeholders and validation helper."""

from __future__ import annotations

CSV_FORMAT = "csv"
XLSX_FORMAT = "xlsx"
JSON_FORMAT = "json"
HTML_FORMAT = "html"
PDF_FORMAT = "pdf"

SUPPORTED_EXPORT_FORMATS = frozenset(
    {CSV_FORMAT, XLSX_FORMAT, JSON_FORMAT, HTML_FORMAT, PDF_FORMAT}
)


def validate_export_format(format_name: str) -> bool:
    """Validate that an export format is supported."""
    normalized = format_name.strip().lower()
    if normalized in SUPPORTED_EXPORT_FORMATS:
        return True

    supported = ", ".join(sorted(SUPPORTED_EXPORT_FORMATS))
    raise ValueError(f"Unsupported export format '{format_name}'. Supported: {supported}.")

