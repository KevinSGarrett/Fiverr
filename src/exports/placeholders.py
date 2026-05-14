"""Backward-compatible export placeholder helpers."""

from __future__ import annotations

from src.exports.formats import ExportFormat, ExportRequest, validate_export_request

CSV_FORMAT = ExportFormat.CSV.value
XLSX_FORMAT = ExportFormat.XLSX.value
JSON_FORMAT = ExportFormat.JSON.value
HTML_FORMAT = ExportFormat.HTML.value
PDF_FORMAT = ExportFormat.PDF.value
MD_FORMAT = ExportFormat.MD.value

SUPPORTED_EXPORT_FORMATS = frozenset({member.value for member in ExportFormat})


def validate_export_format(format_name: str) -> bool:
    """Validate a legacy single format value."""
    request = ExportRequest(format=format_name, output_path="exports/placeholder.out")
    validate_export_request(request)
    return True


def build_governance_export_status_map(
    *,
    local_parity: str = "pending",
    github_actions: str = "pending",
    codecov_project: str = "pending",
    codecov_patch: str = "pending",
    codex_disposition: str = "pending",
) -> dict[str, str]:
    """Return stable keys for governance status exports."""
    return {
        "local_parity": local_parity,
        "github_actions": github_actions,
        "codecov_project": codecov_project,
        "codecov_patch": codecov_patch,
        "codex_disposition": codex_disposition,
    }

