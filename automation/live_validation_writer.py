"""Helpers for persisting V-1 live validation evidence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_PATH = REPO_ROOT / "data" / "live_validation_evidence.json"
SCHEMA_PATH = REPO_ROOT / "docs" / "validation" / "live_validation_evidence.schema.json"

_V1_ALLOWED_STATUSES = {"PASS", "FAIL"}


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _default_evidence(*, cycle: int) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "v1_status": "NOT_RUN",
        "v1_run_timestamp": None,
        "v1_collection_run_id": None,
        "v1_keywords_attempted": [],
        "v1_keywords_successful": [],
        "v1_keywords_failed": [],
        "v1_total_gigs_collected": 0,
        "v1_payload_archive_path": None,
        "v1_collection_duration_seconds": None,
        "v1_error_summary": None,
        "v2_status": "NOT_RUN",
        "v2_parsing_passed": False,
        "v2_schema_violations": [],
        "v3_status": "NOT_RUN",
        "v3_scoring_passed": False,
        "v3_golden_anchor_deviation": None,
        "last_updated": _utc_now_iso(),
        "updated_by_cycle": cycle,
    }


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validate(payload: dict[str, Any]) -> None:
    schema = _load_schema()
    Draft7Validator(schema=schema).validate(payload)


def _load_existing_or_default(evidence_path: Path, *, cycle: int) -> dict[str, Any]:
    if not evidence_path.exists():
        return _default_evidence(cycle=cycle)
    existing_payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    if not isinstance(existing_payload, dict):
        raise ValidationError("Evidence payload must be a JSON object.")
    return existing_payload


def write_v1_evidence(
    status: str,
    run_id: str,
    keywords_attempted: list[str],
    keywords_successful: list[str],
    keywords_failed: list[str],
    total_gigs: int,
    payload_path: str | None,
    duration_seconds: float,
    error_summary: str | None,
    cycle: int,
    evidence_path: Path = DEFAULT_EVIDENCE_PATH,
) -> None:
    """Update the live validation evidence file for V-1."""
    normalized_status = status.strip().upper()
    if normalized_status not in _V1_ALLOWED_STATUSES:
        raise ValueError("status must be PASS or FAIL.")

    payload = _load_existing_or_default(evidence_path, cycle=cycle)
    payload.update(
        {
            "schema_version": "1.0",
            "v1_status": normalized_status,
            "v1_run_timestamp": _utc_now_iso(),
            "v1_collection_run_id": run_id,
            "v1_keywords_attempted": keywords_attempted,
            "v1_keywords_successful": keywords_successful,
            "v1_keywords_failed": keywords_failed,
            "v1_total_gigs_collected": total_gigs,
            "v1_payload_archive_path": payload_path,
            "v1_collection_duration_seconds": duration_seconds,
            "v1_error_summary": error_summary,
            "last_updated": _utc_now_iso(),
            "updated_by_cycle": cycle,
        }
    )
    _validate(payload)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_v1_evidence(evidence_path: Path = DEFAULT_EVIDENCE_PATH) -> dict[str, Any]:
    """Read and return current live validation evidence."""
    if not evidence_path.exists():
        return _default_evidence(cycle=76)
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValidationError("Evidence payload must be a JSON object.")
    _validate(payload)
    return payload


def get_v1_status() -> str:
    """Return current V-1 status: PASS, FAIL, or NOTRUN."""
    status = str(read_v1_evidence().get("v1_status", "NOT_RUN")).upper()
    if status == "NOT_RUN":
        return "NOTRUN"
    return status
