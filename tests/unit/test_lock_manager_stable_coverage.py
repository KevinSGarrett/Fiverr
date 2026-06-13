from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from automation.lock_manager import LockAcquireError, LockManager


def test_acquire_creates_lock_and_reacquire_same_owner(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    assert manager.acquire("cycle_run", "owner-a") is True
    assert manager.acquire("cycle_run", "owner-a") is True


def test_acquire_different_owner_without_timeout_returns_false(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    manager.acquire("cycle_run", "owner-a")
    assert manager.acquire("cycle_run", "owner-b", timeout_minutes=0) is False


def test_acquire_timeout_raises_lock_acquire_error(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    manager.acquire("cycle_run", "owner-a")
    base = datetime.now(UTC)
    with patch.object(manager, "_read_lock", return_value={"owner": "owner-a"}), patch(
        "automation.lock_manager.time.sleep", return_value=None
    ), patch("automation.lock_manager.datetime") as dt:
        dt.now.side_effect = [base, base + timedelta(minutes=2)]
        with pytest.raises(LockAcquireError):
            manager.acquire("cycle_run", "owner-b", timeout_minutes=1)


def test_release_and_release_mismatch_cases(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    assert manager.release("missing", "owner") is False
    manager.acquire("cycle_run", "owner-a")
    assert manager.release("cycle_run", "owner-b") is False
    assert manager.release("cycle_run", "owner-a") is True


def test_is_locked_false_when_missing(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    assert manager.is_locked("missing") is False


def test_cleanup_stale_removes_invalid_acquired_at(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    lock = tmp_path / "cycle_run.lock"
    lock.write_text(
        json.dumps({"owner": "a", "acquired_at": "invalid", "expires_at": None, "pid": 1}),
        encoding="utf-8",
    )
    assert manager.cleanup_stale("cycle_run") is True
    assert not lock.exists()


def test_cleanup_stale_by_age_and_dead_pid(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    lock = tmp_path / "cycle_run.lock"
    lock.write_text(
        json.dumps(
            {
                "owner": "a",
                "acquired_at": (datetime.now(UTC) - timedelta(hours=5)).isoformat(),
                "expires_at": None,
                "pid": 999999,
            }
        ),
        encoding="utf-8",
    )
    assert manager.cleanup_stale("cycle_run", max_age_minutes=120) is True


def test_cleanup_stale_returns_false_for_fresh_live_lock(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    lock = tmp_path / "cycle_run.lock"
    lock.write_text(
        json.dumps(
            {
                "owner": "a",
                "acquired_at": datetime.now(UTC).isoformat(),
                "expires_at": None,
                "pid": 1,
            }
        ),
        encoding="utf-8",
    )
    with patch.object(manager, "_pid_exists", return_value=True):
        assert manager.cleanup_stale("cycle_run", max_age_minutes=120) is False


def test_read_lock_invalid_json_returns_none(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    lock = tmp_path / "cycle_run.lock"
    lock.write_text("{invalid", encoding="utf-8")
    assert manager._read_lock(lock) is None


def test_parse_iso_variants(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    assert manager._parse_iso(None) is None
    assert manager._parse_iso("not-a-date") is None
    parsed = manager._parse_iso("2026-01-01T00:00:00")
    assert parsed is not None
    assert parsed.tzinfo is not None


def test_pid_exists_fallback_paths(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    with patch("automation.lock_manager.psutil", None), patch(
        "automation.lock_manager.os.kill", side_effect=ProcessLookupError
    ):
        assert manager._pid_exists(10) is False
    with patch("automation.lock_manager.psutil", None), patch("automation.lock_manager.os.kill", return_value=None):
        assert manager._pid_exists(10) is True
