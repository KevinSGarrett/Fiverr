"""Unit tests for checkpoint manager and retry configuration."""

from __future__ import annotations

import json
from pathlib import Path

from src.collection.checkpoint import CheckpointManager
from src.collection.session_manager import SessionLoginError
from src.scheduler.retry_config import (
    RETRY_CONFIG,
    classify_error,
    get_retry_config,
    is_no_retry_error,
    should_dead_letter_on_error,
)


class _HTTPError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"http status {status_code}")
        self.status_code = status_code


def test_checkpoint_write_creates_file(tmp_path: Path) -> None:
    manager = CheckpointManager(run_id="run_001", data_dir=str(tmp_path))
    manager.write("stage04", "niche_a", {"records_complete": 5})
    assert (tmp_path / "checkpoints" / "run_001" / "stage04_niche_a.json").exists()


def test_checkpoint_write_atomic(tmp_path: Path) -> None:
    manager = CheckpointManager(run_id="run_001", data_dir=str(tmp_path))
    manager.write("stage04", "niche_a", {"records_complete": 5})
    checkpoint_dir = tmp_path / "checkpoints" / "run_001"
    assert list(checkpoint_dir.glob("*.tmp")) == []
    assert (checkpoint_dir / "stage04_niche_a.json").exists()


def test_checkpoint_write_merges_common_fields(tmp_path: Path) -> None:
    manager = CheckpointManager(run_id="run_001", data_dir=str(tmp_path))
    manager.write("stage04", "niche_a", {"records_complete": 5})
    payload = json.loads((tmp_path / "checkpoints" / "run_001" / "stage04_niche_a.json").read_text())
    assert payload["schema_version"] == "1.0"
    assert payload["run_id"] == "run_001"
    assert payload["checkpoint_at"].endswith("Z")


def test_checkpoint_write_merges_data(tmp_path: Path) -> None:
    manager = CheckpointManager(run_id="run_001", data_dir=str(tmp_path))
    manager.write("stage04", "niche_a", {"records_complete": 5, "records_total": 10})
    payload = json.loads((tmp_path / "checkpoints" / "run_001" / "stage04_niche_a.json").read_text())
    assert payload["records_complete"] == 5
    assert payload["records_total"] == 10


def test_checkpoint_write_common_fields_not_overwritten(tmp_path: Path) -> None:
    manager = CheckpointManager(run_id="run_001", data_dir=str(tmp_path))
    manager.write(
        "stage04",
        "niche_a",
        {
            "schema_version": "9.9",
            "run_id": "hijacked",
            "stage": "stage99",
            "niche_id": "wrong",
        },
    )
    payload = json.loads((tmp_path / "checkpoints" / "run_001" / "stage04_niche_a.json").read_text())
    assert payload["schema_version"] == "1.0"
    assert payload["run_id"] == "run_001"
    assert payload["stage"] == "stage04"
    assert payload["niche_id"] == "niche_a"


def test_checkpoint_read_existing(tmp_path: Path) -> None:
    manager = CheckpointManager(run_id="run_001", data_dir=str(tmp_path))
    manager.write("stage04", "niche_a", {"records_complete": 5})
    loaded = manager.read("stage04", "niche_a")
    assert loaded is not None
    assert loaded["records_complete"] == 5


def test_checkpoint_read_missing(tmp_path: Path) -> None:
    manager = CheckpointManager(run_id="run_001", data_dir=str(tmp_path))
    assert manager.read("stage04", "missing_niche") is None


def test_checkpoint_read_corrupt(tmp_path: Path) -> None:
    manager = CheckpointManager(run_id="run_001", data_dir=str(tmp_path))
    checkpoint_path = tmp_path / "checkpoints" / "run_001" / "stage04_niche_a.json"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text("{not valid json")
    assert manager.read("stage04", "niche_a") is None


def test_checkpoint_read_non_mapping_payload_returns_none(tmp_path: Path) -> None:
    manager = CheckpointManager(run_id="run_001", data_dir=str(tmp_path))
    checkpoint_path = tmp_path / "checkpoints" / "run_001" / "stage04_niche_a.json"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text('["not", "a", "mapping"]', encoding="utf-8")
    assert manager.read("stage04", "niche_a") is None


def test_checkpoint_cleanup(tmp_path: Path) -> None:
    manager = CheckpointManager(run_id="run_001", data_dir=str(tmp_path))
    manager.write("stage04", "niche_a", {"records_complete": 5})
    manager.cleanup()
    assert not (tmp_path / "checkpoints" / "run_001").exists()


def test_checkpoint_cleanup_nonexistent(tmp_path: Path) -> None:
    manager = CheckpointManager(run_id="run_001", data_dir=str(tmp_path))
    manager.cleanup()
    assert not (tmp_path / "checkpoints" / "run_001").exists()


def test_checkpoint_list_checkpoints(tmp_path: Path) -> None:
    manager = CheckpointManager(run_id="run_001", data_dir=str(tmp_path))
    manager.write("stage02", "niche_b", {"records_complete": 2})
    manager.write("stage01", "niche_a", {"records_complete": 1})
    checkpoints = manager.list_checkpoints()
    assert [checkpoint["stage"] for checkpoint in checkpoints] == ["stage01", "stage02"]


def test_checkpoint_list_skips_malformed_checkpoint_filenames(tmp_path: Path) -> None:
    manager = CheckpointManager(run_id="run_001", data_dir=str(tmp_path))
    malformed = tmp_path / "checkpoints" / "run_001" / "stage01.json"
    malformed.parent.mkdir(parents=True, exist_ok=True)
    malformed.write_text("{}", encoding="utf-8")
    assert manager.list_checkpoints() == []


def test_checkpoint_find_latest_run_none(tmp_path: Path) -> None:
    assert CheckpointManager.find_latest_run(str(tmp_path)) is None


def test_checkpoint_find_latest_run_returns_none_for_empty_run_dirs(tmp_path: Path) -> None:
    checkpoint_root = tmp_path / "checkpoints"
    (checkpoint_root / "run_empty_a").mkdir(parents=True)
    (checkpoint_root / "run_empty_b").mkdir(parents=True)
    assert CheckpointManager.find_latest_run(str(tmp_path)) is None


def test_checkpoint_find_latest_run_exists(tmp_path: Path) -> None:
    old = CheckpointManager(run_id="run_old", data_dir=str(tmp_path))
    old.write("stage01", "niche_a", {"records_complete": 1})
    latest = CheckpointManager(run_id="run_latest", data_dir=str(tmp_path))
    latest.write("stage02", "niche_b", {"records_complete": 2})
    assert CheckpointManager.find_latest_run(str(tmp_path)) == "run_latest"


def test_get_retry_config_known() -> None:
    assert get_retry_config("FIVERR_SEARCH") == RETRY_CONFIG["FIVERR_SEARCH"]


def test_get_retry_config_default() -> None:
    assert get_retry_config("UNKNOWN_JOB") == RETRY_CONFIG["_default"]


def test_should_dead_letter_http404() -> None:
    assert should_dead_letter_on_error("FIVERR_SEARCH", "HTTP_404") is True


def test_is_no_retry_error_http410() -> None:
    assert is_no_retry_error("GIG_DETAIL", "HTTP_410") is True


def test_classify_error_timeout() -> None:
    assert classify_error(TimeoutError()) == "TIMEOUT"


def test_classify_error_http_404() -> None:
    http_error = _HTTPError(status_code=404)
    assert classify_error(http_error) == "HTTP_404"


def test_classify_error_http_410() -> None:
    http_error = _HTTPError(status_code=410)
    assert classify_error(http_error) == "HTTP_410"


def test_classify_error_http_429() -> None:
    http_error = _HTTPError(status_code=429)
    assert classify_error(http_error) == "HTTP_429"


def test_classify_error_connection() -> None:
    assert classify_error(ConnectionError("connection failed")) == "CONNECT_ERROR"


def test_classify_error_permanent_ban() -> None:
    assert classify_error(SessionLoginError("login failed")) == "PERMANENT_BAN"


def test_classify_error_unknown() -> None:
    assert classify_error(Exception("boom")) == "UNKNOWN"
