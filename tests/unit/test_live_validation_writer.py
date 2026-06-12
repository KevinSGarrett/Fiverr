"""Unit tests for live validation evidence writer helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError

from automation import live_validation_writer


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_write_v1_evidence_pass_updates_file(tmp_path: Path) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"

    live_validation_writer.write_v1_evidence(
        status="PASS",
        run_id="run-123",
        keywords_attempted=["seo"],
        keywords_successful=["seo"],
        keywords_failed=[],
        total_gigs=3,
        payload_path="data/evidence/v1_payload_20260612.json",
        duration_seconds=12.5,
        error_summary=None,
        cycle=76,
        evidence_path=evidence_path,
    )

    payload = _load_json(evidence_path)
    assert payload["v1_status"] == "PASS"
    assert payload["v1_collection_run_id"] == "run-123"
    assert payload["v1_total_gigs_collected"] == 3
    assert payload["updated_by_cycle"] == 76


def test_write_v1_evidence_fail_updates_error_summary(tmp_path: Path) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"

    live_validation_writer.write_v1_evidence(
        status="FAIL",
        run_id="run-124",
        keywords_attempted=["logo design"],
        keywords_successful=[],
        keywords_failed=["logo design"],
        total_gigs=0,
        payload_path=None,
        duration_seconds=7.1,
        error_summary="Session validation failed",
        cycle=76,
        evidence_path=evidence_path,
    )

    payload = _load_json(evidence_path)
    assert payload["v1_status"] == "FAIL"
    assert payload["v1_error_summary"] == "Session validation failed"
    assert payload["v1_keywords_failed"] == ["logo design"]


def test_read_v1_evidence_when_file_exists_returns_dict(tmp_path: Path) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"
    evidence_path.write_text(
        json.dumps(
            {
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
                "last_updated": "2026-06-12T00:00:00+00:00",
                "updated_by_cycle": 76,
            }
        ),
        encoding="utf-8",
    )

    payload = live_validation_writer.read_v1_evidence(evidence_path=evidence_path)
    assert isinstance(payload, dict)
    assert payload["v1_status"] == "NOT_RUN"


def test_read_v1_evidence_when_file_missing_returns_default(tmp_path: Path) -> None:
    evidence_path = tmp_path / "missing.json"
    payload = live_validation_writer.read_v1_evidence(evidence_path=evidence_path)

    assert payload["v1_status"] == "NOT_RUN"
    assert payload["v1_total_gigs_collected"] == 0
    assert payload["v2_status"] == "NOT_RUN"
    assert payload["v3_status"] == "NOT_RUN"


def test_get_v1_status_when_not_run_returns_notrun(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        live_validation_writer,
        "read_v1_evidence",
        lambda evidence_path=live_validation_writer.DEFAULT_EVIDENCE_PATH: {"v1_status": "NOT_RUN"},
    )
    assert live_validation_writer.get_v1_status() == "NOTRUN"


def test_schema_validation_malformed_data_raises_validation_error(tmp_path: Path) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"
    evidence_path.write_text(json.dumps({"schema_version": "1.0"}), encoding="utf-8")

    with pytest.raises(ValidationError):
        live_validation_writer.read_v1_evidence(evidence_path=evidence_path)


def test_write_v1_evidence_preserves_existing_v2_v3_fields(tmp_path: Path) -> None:
    evidence_path = tmp_path / "live_validation_evidence.json"
    evidence_path.write_text(
        json.dumps(
            {
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
                "v2_status": "PASS",
                "v2_parsing_passed": True,
                "v2_schema_violations": [],
                "v3_status": "FAIL",
                "v3_scoring_passed": False,
                "v3_golden_anchor_deviation": 3.4,
                "last_updated": "2026-06-12T00:00:00+00:00",
                "updated_by_cycle": 75,
            }
        ),
        encoding="utf-8",
    )

    live_validation_writer.write_v1_evidence(
        status="PASS",
        run_id="run-125",
        keywords_attempted=["python"],
        keywords_successful=["python"],
        keywords_failed=[],
        total_gigs=2,
        payload_path="data/evidence/v1_payload_20260612.json",
        duration_seconds=2.0,
        error_summary=None,
        cycle=76,
        evidence_path=evidence_path,
    )

    payload = _load_json(evidence_path)
    assert payload["v2_status"] == "PASS"
    assert payload["v2_parsing_passed"] is True
    assert payload["v3_status"] == "FAIL"
    assert payload["v3_golden_anchor_deviation"] == 3.4
