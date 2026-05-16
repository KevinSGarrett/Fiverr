"""Deterministic CSV export helpers for dashboard/report payloads."""

from __future__ import annotations

import csv
import hashlib
import io
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any

from src.exports.formats import ExportFormat

CSV_SCHEMA_VERSION = "1.0"
_DEFAULT_EXPORT_DIR = "exports/cycle014"


def build_csv_export(
    *,
    export_name: str,
    records: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    columns: tuple[str, ...] | None = None,
    schema_version: str = CSV_SCHEMA_VERSION,
    generated_at: str | None = None,
    output_dir: str = _DEFAULT_EXPORT_DIR,
) -> dict[str, Any]:
    """Build deterministic CSV content and metadata without file-system side effects."""
    normalized_name = _normalize_export_name(export_name)
    normalized_columns = _resolve_columns(records=records, columns=columns)
    normalized_records = [dict(item) for item in (records or [])]
    sparse_data = len(normalized_records) == 0
    warnings: list[str] = []

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(normalized_columns), extrasaction="ignore")
    writer.writeheader()
    for row in normalized_records:
        writer.writerow({key: _normalize_cell(row.get(key)) for key in normalized_columns})
    content = output.getvalue()
    checksum = f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"

    if sparse_data:
        warnings.append("No records were provided; CSV contains header-only output.")
    if not normalized_columns:
        warnings.append("No columns were supplied or inferred; CSV includes an empty header row.")

    path = _build_output_path(output_dir=output_dir, export_name=normalized_name, suffix=".csv")
    return {
        "format": ExportFormat.CSV.value,
        "schema_version": schema_version.strip() or CSV_SCHEMA_VERSION,
        "record_count": len(normalized_records),
        "generated_at": generated_at or datetime.now(tz=UTC).isoformat(),
        "path": path,
        "columns": list(normalized_columns),
        "sparse_data": sparse_data,
        "warnings": warnings,
        "checksum": checksum,
        "content": content,
    }


def _resolve_columns(
    *,
    records: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    columns: tuple[str, ...] | None,
) -> tuple[str, ...]:
    if columns is not None:
        return tuple(column.strip() for column in columns if column.strip())
    if not records:
        return ()
    ordered: list[str] = []
    seen: set[str] = set()
    for row in records:
        for key in row:
            normalized = str(key).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
    return tuple(ordered)


def _normalize_export_name(name: str) -> str:
    normalized = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in name.strip().lower())
    normalized = normalized.strip("_")
    return normalized or "export"


def _build_output_path(*, output_dir: str, export_name: str, suffix: str) -> str:
    normalized_dir = PurePosixPath(output_dir.replace("\\", "/"))
    if normalized_dir.is_absolute() or ".." in normalized_dir.parts:
        raise ValueError("output_dir must be a safe relative path.")
    if not normalized_dir.parts:
        raise ValueError("output_dir must not be empty.")
    return str(normalized_dir / f"{export_name}{suffix}")


def _normalize_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, list | tuple):
        return "; ".join(_normalize_cell(item) for item in value)
    return str(value)
