"""Export format and request contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class ExportFormat(StrEnum):
    """Supported export formats for future reporting artifacts."""

    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    MD = "md"


@dataclass(frozen=True, slots=True)
class ExportRequest:
    """Request contract for export orchestration."""

    format: ExportFormat | str
    output_path: str
    include_metadata: bool = True
    redaction_level: str = "none"
    created_by: str | None = None


def normalize_export_format(value: ExportFormat | str) -> ExportFormat:
    if isinstance(value, ExportFormat):
        return value
    normalized = value.strip().lower()
    try:
        return ExportFormat(normalized)
    except ValueError as exc:
        supported = ", ".join(format_member.value for format_member in ExportFormat)
        raise ValueError(f"Unsupported export format '{value}'. Supported: {supported}.") from exc


def _validate_output_path(output_path: str) -> None:
    if not output_path.strip():
        raise ValueError("output_path must be a non-empty path.")

    candidate = Path(output_path)
    if ".." in candidate.parts:
        raise ValueError("output_path must not contain parent directory traversal ('..').")

    if candidate.name in {"", ".", ".."}:
        raise ValueError("output_path must point to a file path.")


def validate_export_request(request: ExportRequest) -> ExportRequest:
    """Validate format and output-path safety for export requests."""
    resolved_format = normalize_export_format(request.format)
    _validate_output_path(request.output_path)

    return ExportRequest(
        format=resolved_format,
        output_path=request.output_path,
        include_metadata=request.include_metadata,
        redaction_level=request.redaction_level,
        created_by=request.created_by,
    )
