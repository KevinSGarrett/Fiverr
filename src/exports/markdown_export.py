"""Deterministic Markdown export helpers for summary and evidence packages."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any

from src.exports.formats import ExportFormat

MARKDOWN_SCHEMA_VERSION = "1.0"
_DEFAULT_EXPORT_DIR = "exports/cycle014"


def build_markdown_export(
    *,
    export_name: str,
    title: str,
    sections: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    schema_version: str = MARKDOWN_SCHEMA_VERSION,
    generated_at: str | None = None,
    output_dir: str = _DEFAULT_EXPORT_DIR,
) -> dict[str, Any]:
    """Build deterministic Markdown content and metadata without writing files."""
    normalized_name = _normalize_export_name(export_name)
    normalized_sections = [dict(section) for section in (sections or [])]
    sparse_data = len(normalized_sections) == 0
    warnings: list[str] = []
    if sparse_data:
        warnings.append("No sections were provided; Markdown export contains a placeholder section.")
        normalized_sections = [
            {
                "heading": "No Data Available",
                "body": "This export completed without source records. Review upstream collection and analysis stages.",
                "items": [],
            }
        ]

    markdown_lines = [
        f"# {title.strip() or 'Export Report'}",
        "",
        f"- Generated At: {generated_at or datetime.now(tz=UTC).isoformat()}",
        f"- Schema Version: {schema_version.strip() or MARKDOWN_SCHEMA_VERSION}",
        f"- Section Count: {len(normalized_sections)}",
        "",
    ]
    for section in normalized_sections:
        heading = str(section.get("heading", "Section")).strip() or "Section"
        body = str(section.get("body", "")).strip()
        items = section.get("items")
        markdown_lines.append(f"## {heading}")
        if body:
            markdown_lines.append(body)
        if isinstance(items, list | tuple):
            for item in items:
                markdown_lines.append(f"- {str(item).strip()}")
        markdown_lines.append("")

    content = "\n".join(markdown_lines).rstrip() + "\n"
    checksum = f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"
    return {
        "format": ExportFormat.MD.value,
        "schema_version": schema_version.strip() or MARKDOWN_SCHEMA_VERSION,
        "record_count": len(normalized_sections),
        "generated_at": generated_at or datetime.now(tz=UTC).isoformat(),
        "path": _build_output_path(output_dir=output_dir, export_name=normalized_name, suffix=".md"),
        "sparse_data": sparse_data,
        "warnings": warnings,
        "checksum": checksum,
        "content": content,
    }


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
