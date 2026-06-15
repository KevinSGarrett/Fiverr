"""File-lock coordination utilities for cycle automation."""

from __future__ import annotations

import json
import os
import time
from contextlib import AbstractContextManager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

try:
    import psutil
except Exception:  # pragma: no cover - fallback path when psutil unavailable
    psutil = None


LOCK_DIR = Path("C:/AI_Runner/state/locks")  # module-level constant for tests


class LockAcquireError(RuntimeError):
    """Raised when lock acquisition times out."""


class LockContext(AbstractContextManager["LockContext"]):
    """Context manager wrapper around LockManager acquire/release."""

    def __init__(
        self,
        manager: LockManager,
        lock_name: str,
        owner: str,
        timeout_minutes: int = 0,
        raise_on_fail: bool = True,
    ) -> None:
        self._manager = manager
        self._lock_name = lock_name
        self._owner = owner
        self._timeout_minutes = timeout_minutes
        self._raise_on_fail = raise_on_fail
        self.acquired = False

    def __enter__(self) -> LockContext:
        self.acquired = self._manager.acquire(
            self._lock_name,
            self._owner,
            timeout_minutes=self._timeout_minutes,
        )
        if not self.acquired and self._raise_on_fail:
            raise LockAcquireError(f"Could not acquire lock {self._lock_name}")
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Literal[False]:
        self._manager.release(self._lock_name, self._owner)
        return False


class LockManager:
    """Manage lock files for cross-process cycle coordination."""

    def __init__(self, lock_dir: Path = Path("C:/AI_Runner/state/locks")) -> None:
        """Initialize a lock manager with lazy-created lock directory."""
        self.lock_dir = lock_dir

    def acquire(self, lock_name: str, owner: str, timeout_minutes: int = 0) -> bool:
        """Acquire a named lock, waiting up to timeout_minutes when requested."""
        self._ensure_lock_dir()
        lock_path = self._lock_path(lock_name)
        start = datetime.now(UTC)
        wait_seconds = max(timeout_minutes * 60, 0)

        while True:
            existing = self._read_lock(lock_path)
            if existing is None:
                payload = {
                    "owner": owner,
                    "acquired_at": datetime.now(UTC).isoformat(),
                    "expires_at": (
                        datetime.now(UTC) + timedelta(minutes=timeout_minutes)
                    ).isoformat()
                    if timeout_minutes > 0
                    else None,
                    "pid": os.getpid(),
                }
                lock_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                return True

            if existing.get("owner") == owner:
                return True

            if timeout_minutes == 0:
                return False

            elapsed = (datetime.now(UTC) - start).total_seconds()
            if elapsed >= wait_seconds:
                raise LockAcquireError(
                    f"Could not acquire {lock_name} within {timeout_minutes} min"
                )
            time.sleep(5)

    def release(self, lock_name: str, owner: str) -> bool:
        """Release lock if owner matches. Missing lock is treated as success=False."""
        lock_path = self._lock_path(lock_name)
        data = self._read_lock(lock_path)
        if data is None:
            return False
        if data.get("owner") != owner:
            return False
        lock_path.unlink(missing_ok=True)
        return True

    def is_locked(self, lock_name: str) -> bool:
        """Return True only for existing non-stale lock files."""
        lock_path = self._lock_path(lock_name)
        data = self._read_lock(lock_path)
        if data is None:
            return False
        return not self._is_stale(data)

    def cleanup_stale(self, lock_name: str, max_age_minutes: int = 120) -> bool:
        """Remove stale lock by age or dead holder process."""
        lock_path = self._lock_path(lock_name)
        data = self._read_lock(lock_path)
        if data is None:
            return False

        acquired = self._parse_iso(data.get("acquired_at"))
        if acquired is None:
            lock_path.unlink(missing_ok=True)
            return True

        too_old = datetime.now(UTC) - acquired > timedelta(minutes=max_age_minutes)
        dead_pid = not self._pid_exists(int(data.get("pid", 0)))
        if too_old or dead_pid:
            lock_path.unlink(missing_ok=True)
            return True
        return False

    def lock_context(
        self,
        lock_name: str,
        owner: str,
        timeout_minutes: int = 0,
        raise_on_fail: bool = True,
    ) -> LockContext:
        """Return context manager that acquires on enter and always releases."""
        return LockContext(
            self,
            lock_name,
            owner,
            timeout_minutes=timeout_minutes,
            raise_on_fail=raise_on_fail,
        )

    def _ensure_lock_dir(self) -> None:
        self.lock_dir.mkdir(parents=True, exist_ok=True)

    def _lock_path(self, lock_name: str) -> Path:
        return self.lock_dir / f"{lock_name}.lock"

    def _read_lock(self, lock_path: Path) -> dict[str, Any] | None:
        if not lock_path.exists():
            return None
        try:
            return json.loads(lock_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _is_stale(self, lock_data: dict[str, Any]) -> bool:
        pid = int(lock_data.get("pid", 0))
        if not self._pid_exists(pid):
            return True
        expires_raw = lock_data.get("expires_at")
        expires_at = self._parse_iso(expires_raw)
        if expires_at is not None and expires_at < datetime.now(UTC):
            return True
        return False

    def _parse_iso(self, value: Any) -> datetime | None:
        if not value or not isinstance(value, str):
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

    def _pid_exists(self, pid: int) -> bool:
        if pid <= 0:
            return False
        if psutil is not None:
            return bool(psutil.pid_exists(pid))
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError, OSError):
            return False


def _process_alive(pid: int) -> bool:
    """Module-level process alive check. Patchable in tests."""
    if pid <= 0:
        return False
    try:
        import psutil
        return bool(psutil.pid_exists(pid))
    except Exception:
        try:
            import os
            os.kill(pid, 0)
            return True
        except OSError:
            return False


# ------------------------------------------------------------------ #
# Module-level convenience API (patchable by tests via LOCK_DIR)
# ------------------------------------------------------------------ #

LockError = LockAcquireError  # alias at module level for tests


def _lock_file(lock_id: str) -> Path:
    return LOCK_DIR / f"{lock_id}.lock"


def acquire(lock_id: str, run_id: str, branch: str, cycle: str | int) -> Path:
    """Acquire a lock. Returns the lock file Path. Raises LockError if held."""
    import time as _time
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lp = _lock_file(lock_id)
    if lp.exists():
        try:
            import json as _json
            data = _json.loads(lp.read_text(encoding="utf-8"))
            pid = int(data.get("pid", 0))
            if _process_alive(pid):
                raise LockError(f"Lock '{lock_id}' held by pid {pid}")
        except LockError:
            raise
        except Exception:
            pass
    import json as _json
    import os as _os
    payload = {
        "lock_id": lock_id,
        "pid": _os.getpid(),
        "run_id": str(run_id),
        "branch": str(branch),
        "cycle": str(cycle),
        "heartbeat_ts": _time.time(),
    }
    lp.write_text(_json.dumps(payload, indent=2), encoding="utf-8")
    return lp


def is_locked(lock_id: str) -> bool:
    import json as _json
    import time as _time
    lp = _lock_file(lock_id)
    if not lp.exists():
        return False
    try:
        data = _json.loads(lp.read_text(encoding="utf-8"))
        pid = int(data.get("pid", 0))
        heartbeat_ts = float(data.get("heartbeat_ts", 0))
        if not _process_alive(pid):
            return False
        if (_time.time() - heartbeat_ts) > 12 * 3600:
            return False
        return True
    except Exception:
        return False


def heartbeat(lock_id: str) -> None:
    import json as _json
    import time as _time
    lp = _lock_file(lock_id)
    if lp.exists():
        try:
            data = _json.loads(lp.read_text(encoding="utf-8"))
            data["heartbeat_ts"] = _time.time()
            lp.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass


def release(lock_id: str) -> None:
    lp = _lock_file(lock_id)
    if lp.exists():
        try:
            lp.unlink()
        except Exception:
            pass
