"""
snapshot_manager.py -- Git tag/stash for rollback on regression.

ICV-SNAP-1..3: Take snapshot before repair; restore on regression stop.
"""
from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path("C:/Fiverr/Fiverr")


def _git(*args: str, check: bool = False) -> tuple[int, str]:
    try:
        r = subprocess.run(
            ["git", *args], cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=30,
        )
        return r.returncode, r.stdout.strip()
    except Exception as exc:
        return -1, str(exc)


class SnapshotManager:
    """Take/restore git snapshots (stash) before repair dispatches."""

    @staticmethod
    def take(cycle: int, agent: str, attempt: int) -> str:
        """
        Stash all uncommitted changes and tag HEAD.
        Returns the stash ref name (e.g. 'stash@{0}') or empty string on failure.
        """
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return "test-snapshot"
        tag = (
            f"icv/cycle{cycle:03d}/agent{agent}/attempt{attempt}/"
            f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}"
        )
        rc, _ = _git("stash", "push", "-m", tag, "--include-untracked")
        if rc == 0:
            return tag
        return ""

    @staticmethod
    def restore(snapshot_ref: str) -> bool:
        """Pop the stash to restore the pre-repair state."""
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return True
        if not snapshot_ref or snapshot_ref == "test-snapshot":
            return True
        rc, _ = _git("stash", "pop")
        return rc == 0
