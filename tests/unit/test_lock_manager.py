from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from automation.lock_manager import LockManager


def test_acquire_creates_file(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    assert manager.acquire("cycle_run", "owner-a") is True
    assert (tmp_path / "cycle_run.lock").exists()


def test_release_deletes_file(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    manager.acquire("cycle_run", "owner-a")
    assert manager.release("cycle_run", "owner-a") is True
    assert not (tmp_path / "cycle_run.lock").exists()


def test_different_owner_returns_false(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    manager.acquire("cycle_run", "owner-a")
    assert manager.acquire("cycle_run", "owner-b") is False


def test_same_owner_reacquire_returns_true(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    manager.acquire("cycle_run", "owner-a")
    assert manager.acquire("cycle_run", "owner-a") is True


def test_cleanup_stale_by_age(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    old_lock = {
        "owner": "owner-a",
        "acquired_at": (datetime.now(UTC) - timedelta(minutes=300)).isoformat(),
        "expires_at": None,
        "pid": 99999999,
    }
    lock_path = tmp_path / "cycle_run.lock"
    lock_path.write_text(json.dumps(old_lock), encoding="utf-8")
    assert manager.cleanup_stale("cycle_run", max_age_minutes=120) is True
    assert not lock_path.exists()


def test_cleanup_stale_dead_pid(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    lock = {
        "owner": "owner-a",
        "acquired_at": datetime.now(UTC).isoformat(),
        "expires_at": None,
        "pid": 99999999,
    }
    lock_path = tmp_path / "cycle_run.lock"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    assert manager.cleanup_stale("cycle_run") is True
    assert not lock_path.exists()


def test_context_manager_releases_on_success(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    with manager.lock_context("cycle_run", "owner-a"):
        assert (tmp_path / "cycle_run.lock").exists()
    assert not (tmp_path / "cycle_run.lock").exists()


def test_context_manager_releases_on_exception(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    with pytest.raises(ValueError):
        with manager.lock_context("cycle_run", "owner-a"):
            raise ValueError("boom")
    assert not (tmp_path / "cycle_run.lock").exists()


def test_lock_file_is_valid_json(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    manager.acquire("cycle_run", "owner-a")
    payload = json.loads((tmp_path / "cycle_run.lock").read_text(encoding="utf-8"))
    assert {"owner", "acquired_at", "expires_at", "pid"}.issubset(payload.keys())


def test_is_locked_returns_false_for_stale_expired(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    expired = {
        "owner": "owner-a",
        "acquired_at": datetime.now(UTC).isoformat(),
        "expires_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
        "pid": 99999999,
    }
    (tmp_path / "cycle_run.lock").write_text(json.dumps(expired), encoding="utf-8")
    assert manager.is_locked("cycle_run") is False


def test_release_returns_false_on_wrong_owner(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    manager.acquire("cycle_run", "owner-a")
    assert manager.release("cycle_run", "owner-b") is False
    assert (tmp_path / "cycle_run.lock").exists()


def test_release_returns_false_when_file_missing(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    assert manager.release("does_not_exist", "owner-a") is False


def test_is_locked_returns_true_when_file_exists(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    manager.acquire("cycle_run", "owner-a")
    assert manager.is_locked("cycle_run") is True


def test_is_locked_returns_false_when_stale_by_dead_pid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manager = LockManager(lock_dir=tmp_path)
    manager.acquire("cycle_run", "owner-a")

    class _PsutilStub:
        @staticmethod
        def pid_exists(_pid: int) -> bool:
            return False

    monkeypatch.setattr("automation.lock_manager.psutil", _PsutilStub())
    assert manager.is_locked("cycle_run") is False


def test_lock_manager_simulated_concurrent_access(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path)
    assert manager.acquire("cycle_run", "owner-a") is True
    outcomes = [manager.acquire("cycle_run", f"owner-{idx}") for idx in range(1, 5)]
    assert outcomes == [False, False, False, False]
    assert manager.release("cycle_run", "owner-a") is True


# Prompt-required name aliases for traceability.
def test_acquire_creates_lock_file_at_correct_path(tmp_path: Path) -> None:
    test_acquire_creates_file(tmp_path)


def test_acquire_file_is_valid_json(tmp_path: Path) -> None:
    test_lock_file_is_valid_json(tmp_path)


def test_double_acquire_different_owner_returns_false(tmp_path: Path) -> None:
    test_different_owner_returns_false(tmp_path)


def test_lock_context_manager_acquires_and_releases(tmp_path: Path) -> None:
    test_context_manager_releases_on_success(tmp_path)


def test_lock_context_manager_releases_on_exception(tmp_path: Path) -> None:
    test_context_manager_releases_on_exception(tmp_path)


def test_release_deletes_file_on_correct_owner(tmp_path: Path) -> None:
    test_release_deletes_file(tmp_path)


def test_cleanup_stale_by_age_removes_old_file(tmp_path: Path) -> None:
    test_cleanup_stale_by_age(tmp_path)
