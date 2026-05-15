"""Deterministic JSON export helpers for dashboard/report payloads."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any

from src.exports.formats import ExportFormat

JSON_SCHEMA_VERSION = "1.0"
_DEFAULT_EXPORT_DIR = "exports/cycle014"


def build_json_export(
    *,
    export_name: str,
    payload: dict[str, Any] | list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    schema_version: str = JSON_SCHEMA_VERSION,
    generated_at: str | None = None,
    output_dir: str = _DEFAULT_EXPORT_DIR,
) -> dict[str, Any]:
    """Build deterministic JSON content and metadata with strict serialization checks."""
    normalized_name = _normalize_export_name(export_name)
    normalized_payload = _normalize_payload(payload)
    sparse_data = _is_sparse_payload(normalized_payload)
    warnings: list[str] = []
    if sparse_data:
        warnings.append("Payload contains sparse or empty records; JSON was exported with metadata and placeholders.")

    envelope: dict[str, Any] = {
        "format": ExportFormat.JSON.value,
        "schema_version": schema_version.strip() or JSON_SCHEMA_VERSION,
        "generated_at": generated_at or datetime.now(tz=UTC).isoformat(),
        "record_count": _count_records(normalized_payload),
        "sparse_data": sparse_data,
        "warnings": warnings,
        "payload": normalized_payload,
    }
    content = _dump_json(envelope)
    checksum = f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"
    return {
        **envelope,
        "path": _build_output_path(output_dir=output_dir, export_name=normalized_name, suffix=".json"),
        "checksum": checksum,
        "content": content,
    }


def _normalize_payload(payload: dict[str, Any] | list[dict[str, Any]] | tuple[dict[str, Any], ...] | None) -> Any:
    if payload is None:
        return {"records": [], "note": "No payload provided."}
    if isinstance(payload, tuple):
        return list(payload)
    return payload


def _is_sparse_payload(payload: Any) -> bool:
    if isinstance(payload, dict):
        if not payload:
            return True
        records = payload.get("records")
        if isinstance(records, list | tuple):
            return len(records) == 0
        return False
    if isinstance(payload, list):
        return len(payload) == 0
    return False


def _count_records(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        records = payload.get("records")
        if isinstance(records, list | tuple):
            return len(records)
        return 1
    return 0


def _dump_json(payload: Any) -> str:
    try:
        return json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2)
    except TypeError as exc:
        raise ValueError("JSON export payload contains non-serializable values.") from exc


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
