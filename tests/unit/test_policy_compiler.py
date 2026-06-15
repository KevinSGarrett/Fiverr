"""Smoke tests for policy compiler."""
from __future__ import annotations

from pathlib import Path

from automation.policy_compiler import compile_policy


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_compile_policy_reads_active_cycle_format(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(
        repo / "PM_Pack/07_hydration/HYDRATION_HEADER.md",
        "Active cycle: 080\nWAVE_CURRENT: 11\nEND_TO_END_PRODUCTION_READINESS: 50%\n",
    )
    _write(repo / "PM_Pack/07_hydration/STATE_SNAPSHOT.md", "Last completed: C079\n")
    _write(repo / "PM_Pack/automation/agent_lanes.yml", "default_order: [A, B, E, C, F, D]\n")

    snapshot = compile_policy(repo)
    assert snapshot["cycle_current"] == 80
