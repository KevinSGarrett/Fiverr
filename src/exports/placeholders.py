"""Backward-compatible export placeholder helpers."""

from __future__ import annotations

import re

from src.exports.formats import ExportFormat, ExportRequest, validate_export_request

CSV_FORMAT = ExportFormat.CSV.value
XLSX_FORMAT = ExportFormat.XLSX.value
JSON_FORMAT = ExportFormat.JSON.value
HTML_FORMAT = ExportFormat.HTML.value
PDF_FORMAT = ExportFormat.PDF.value
MD_FORMAT = ExportFormat.MD.value

SUPPORTED_EXPORT_FORMATS = frozenset({member.value for member in ExportFormat})
_CODECOV_STATUS_VALUES = frozenset({"pending", "pass", "fail", "warning", "unknown"})
_JIRA_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")


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


def _looks_secret_like(value: str) -> bool:
    lowered = value.lower()
    return any(
        marker in lowered
        for marker in ("token", "secret", "password", "bearer ", "ghp_", "github_pat_", "api_key", "apikey")
    )


def build_governance_manifest_metadata(
    *,
    jira_keys: tuple[str, ...] = (),
    github_pr_number: int | None = None,
    codex_threads_resolved: int = 0,
    codecov_project_status: str = "pending",
    codecov_patch_status: str = "pending",
    coverage_percent: float | None = None,
) -> dict[str, object]:
    """Validate and normalize governance evidence metadata for export manifests."""
    normalized_jira_keys = sorted({key.strip() for key in jira_keys if key.strip()})
    for key in normalized_jira_keys:
        if _looks_secret_like(key):
            raise ValueError("jira_keys must not contain secret-like values.")
        if not _JIRA_KEY_PATTERN.fullmatch(key):
            raise ValueError(f"jira_keys contains an invalid key: {key}")

    if github_pr_number is not None and github_pr_number <= 0:
        raise ValueError("github_pr_number must be a positive integer when provided.")
    if codex_threads_resolved < 0:
        raise ValueError("codex_threads_resolved must be zero or greater.")

    project_status = codecov_project_status.strip().lower()
    patch_status = codecov_patch_status.strip().lower()
    if project_status not in _CODECOV_STATUS_VALUES:
        raise ValueError("codecov_project_status must be one of: pending, pass, fail, warning, unknown.")
    if patch_status not in _CODECOV_STATUS_VALUES:
        raise ValueError("codecov_patch_status must be one of: pending, pass, fail, warning, unknown.")
    if _looks_secret_like(project_status) or _looks_secret_like(patch_status):
        raise ValueError("Codecov status values must not contain secret-like values.")

    if coverage_percent is not None and (coverage_percent < 0 or coverage_percent > 100):
        raise ValueError("coverage_percent must be between 0 and 100.")

    return {
        "jira_keys": normalized_jira_keys,
        "github_pr_number": github_pr_number,
        "codex_threads_resolved": codex_threads_resolved,
        "codecov_project_status": project_status,
        "codecov_patch_status": patch_status,
        "coverage_percent": coverage_percent,
    }

