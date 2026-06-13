from __future__ import annotations

from pathlib import Path

from automation.lock_manager import LockManager
from automation.state_writer import write_heartbeat


def test_lock_manager_end_to_end_with_heartbeat(tmp_path: Path) -> None:
    manager = LockManager(lock_dir=tmp_path / "locks")
    with manager.lock_context("cycle_run", "agent-f"):
        assert (tmp_path / "locks" / "cycle_run.lock").exists()
        write_heartbeat("RUNNING", 75, "F", runner_root=tmp_path)
        assert (tmp_path / "state/heartbeat.json").exists()
    assert not (tmp_path / "locks" / "cycle_run.lock").exists()
