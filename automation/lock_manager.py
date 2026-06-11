"""
lock_manager.py — Prevent duplicate/colliding controller runs.
Lock files live in PM_Pack/automation/locks/ (repo-visible) and C:\\AI_Runner\\state\\.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


LOCK_DIR = Path("PM_Pack/automation/locks")
RUNNER_LOCK_DIR = Path("C:/AI_Runner/state")
STALE_HOURS = 12.0


class LockError(Exception):
    pass


def acquire(lock_id: str, runner_id: str, branch: str, run_id: str) -> Path:
    """Write a lock file. Raises LockError if active lock exists."""
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = LOCK_DIR / f"{lock_id}.lock"

    if lock_path.exists():
        existing = json.loads(lock_path.read_text())
        age_h = (time.time() - existing.get("heartbeat_ts", 0)) / 3600
        if age_h < STALE_HOURS and _process_alive(existing.get("pid", 0)):
            raise LockError(
                f"Active lock {lock_id} held by PID {existing.get('pid')} "
                f"(age {age_h:.1f}h). Use recover command to clear stale locks."
            )
        _move_stale(lock_path)

    payload = {
        "lock_id": lock_id,
        "runner": runner_id,
        "pid": os.getpid(),
        "started_at": _now(),
        "heartbeat_at": _now(),
        "heartbeat_ts": time.time(),
        "branch": branch,
        "run_id": run_id,
    }
    lock_path.write_text(json.dumps(payload, indent=2))
    return lock_path


def release(lock_id: str) -> None:
    lock_path = LOCK_DIR / f"{lock_id}.lock"
    if lock_path.exists():
        lock_path.unlink()


def heartbeat(lock_id: str) -> None:
    lock_path = LOCK_DIR / f"{lock_id}.lock"
    if lock_path.exists():
        data = json.loads(lock_path.read_text())
        data["heartbeat_at"] = _now()
        data["heartbeat_ts"] = time.time()
        lock_path.write_text(json.dumps(data, indent=2))


def is_locked(lock_id: str) -> bool:
    lock_path = LOCK_DIR / f"{lock_id}.lock"
    if not lock_path.exists():
        return False
    existing = json.loads(lock_path.read_text())
    age_h = (time.time() - existing.get("heartbeat_ts", 0)) / 3600
    return age_h < STALE_HOURS and _process_alive(existing.get("pid", 0))


def _move_stale(lock_path: Path) -> None:
    stale_dir = LOCK_DIR / "stale_locks"
    stale_dir.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stale_path = stale_dir / f"{lock_path.stem}_{ts}.lock"
    lock_path.rename(stale_path)


def _process_alive(pid: int) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
