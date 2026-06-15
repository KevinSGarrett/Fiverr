"""Unit tests for PM_Pack consistency audit checks."""
from __future__ import annotations

from pathlib import Path

from automation.pm_pack_consistency_audit import run_audit


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_warns_when_provider_health_missing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"

    _write(
        repo / "PM_Pack/07_hydration/HYDRATION_HEADER.md",
        "CYCLE_CURRENT: 080\nWAVE_CURRENT: 11\n",
    )
    _write(
        repo / "PM_Pack/07_hydration/STATE_SNAPSHOT.md",
        "# State Snapshot\nCycle 080\n",
    )
    _write(
        repo / "PM_Pack/CURRENT_STATE_CANONICAL.md",
        "# CURRENT_STATE_CANONICAL\nStatus: ACTIVE\n",
    )
    _write(
        repo / "PM_Pack/automation/current_policy_snapshot.json",
        '{"cycle_current": 80, "last_completed_cycle": 79}',
    )
    _write(repo / "PM_Pack/automation/provider_policy.yml", "version: 1\nroutes: {}\n")
    _write(runner / "state/controller_state.json", '{"active_cycle": 80, "status": "PLANNED"}')

    result = run_audit(repo_root=repo, runner_root=runner)

    assert any(c.code == "PROVIDERHEALTHMISSING" for c in result.conflicts)
    assert any("PROVIDERHEALTHMISSING" in w for w in result.warnings)
