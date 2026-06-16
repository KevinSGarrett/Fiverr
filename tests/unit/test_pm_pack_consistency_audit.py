"""Unit tests for PM_Pack consistency audit checks."""
from __future__ import annotations

from pathlib import Path

from automation.pm_pack_consistency_audit import run_audit


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_minimal_baseline(repo: Path, runner: Path, cycle: int = 81, status: str = "PLANNED") -> None:
    _write(
        repo / "PM_Pack/07_hydration/HYDRATION_HEADER.md",
        f"CYCLE_CURRENT: {cycle:03d}\nWAVE_CURRENT: 11\n",
    )
    _write(repo / "PM_Pack/07_hydration/STATE_SNAPSHOT.md", f"# State Snapshot\nCycle {cycle:03d}\n")
    _write(repo / "PM_Pack/CURRENT_STATE_CANONICAL.md", "# CURRENT_STATE_CANONICAL\nStatus: ACTIVE\n")
    _write(
        repo / "PM_Pack/automation/current_policy_snapshot.json",
        f'{{"cycle_current": {cycle}, "last_completed_cycle": {max(0, cycle - 1)}}}',
    )
    _write(
        repo / "PM_Pack/automation/provider_policy.yml",
        "version: 1\nglobal_rules: {}\nroutes: {}\nproviders: {}\n",
    )
    _write(
        repo / "PM_Pack/automation/policies/autonomy_freeze.yml",
        "frozen: false\nreason: none\n",
    )
    _write(
        runner / "state/controller_state.json",
        f'{{"active_cycle": {cycle}, "status": "{status}"}}',
    )
    _write(runner / "state/provider_health.json", '{"cursorcli":{"status":"READY"}}')


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


def test_fc8_postcycle_advisory_blocks_dispatch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _write(
        repo / "PM_Pack/07_hydration/HYDRATION_HEADER.md",
        "CYCLE_CURRENT: 081\nWAVE_CURRENT: 11\n",
    )
    _write(repo / "PM_Pack/07_hydration/STATE_SNAPSHOT.md", "# State Snapshot\nCycle 081\n")
    _write(repo / "PM_Pack/CURRENT_STATE_CANONICAL.md", "# CURRENT_STATE_CANONICAL\nStatus: ACTIVE\n")
    _write(
        repo / "PM_Pack/automation/current_policy_snapshot.json",
        '{"cycle_current": 81, "last_completed_cycle": 80}',
    )
    _write(
        repo / "PM_Pack/automation/provider_policy.yml",
        "version: 1\nglobal_rules: {}\nroutes: {}\nproviders: {}\n",
    )
    _write(runner / "state/controller_state.json", '{"active_cycle": 81, "status": "PLANNED"}')
    _write(
        repo / "PM_Pack/automation/post_cycle_reviews/CYCLE_081_POST_CYCLE_PM_REVIEW.json",
        '{"cycle": 81, "status": "ADVISORY_ONLY"}',
    )

    result = run_audit(repo_root=repo, runner_root=runner)
    assert any(c.code == "FC-8" for c in result.conflicts)
    assert any("FC-8: ADVISORY_ONLY result in post_cycle_review" in w for w in result.warnings)


def test_statesnapshot_stale_sets_blocking_conflict(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _write_minimal_baseline(repo, runner, cycle=81, status="PLANNED")
    _write(repo / "PM_Pack/07_hydration/STATE_SNAPSHOT.md", "# State Snapshot\nCycle 010\n")

    result = run_audit(repo_root=repo, runner_root=runner)
    assert any(c.code == "STATESNAPSHOTSTALE" for c in result.conflicts)
    assert result.passed is False


def test_cycle_source_disagreement_detected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _write_minimal_baseline(repo, runner, cycle=81, status="AGENT_DISPATCH")
    _write(runner / "status/current_status.md", "Cycle not started")

    result = run_audit(repo_root=repo, runner_root=runner)
    assert any(c.code == "CYCLESOURCEDISAGREEMENT" for c in result.conflicts)
    assert result.passed is False


def test_hydration_controller_cycle_mismatch_warns(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _write_minimal_baseline(repo, runner, cycle=81, status="PLANNED")
    _write(repo / "PM_Pack/07_hydration/HYDRATION_HEADER.md", "CYCLE_CURRENT: 050\nWAVE_CURRENT: 11\n")

    result = run_audit(repo_root=repo, runner_root=runner)
    assert any("HYDRATION_HEADER shows cycle" in warning for warning in result.warnings)


def test_frozen_status_in_canonical_adds_warning(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _write_minimal_baseline(repo, runner, cycle=81, status="PLANNED")
    _write(repo / "PM_Pack/CURRENT_STATE_CANONICAL.md", "# CURRENT_STATE_CANONICAL\nFROZEN\n")

    result = run_audit(repo_root=repo, runner_root=runner)
    assert any("CURRENT_STATE_CANONICAL mentions FROZEN" in warning for warning in result.warnings)


def test_missing_autonomy_freeze_file_warns(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _write_minimal_baseline(repo, runner, cycle=81, status="PLANNED")
    freeze_file = repo / "PM_Pack/automation/policies/autonomy_freeze.yml"
    freeze_file.unlink()

    result = run_audit(repo_root=repo, runner_root=runner)
    assert any("autonomy_freeze.yml not found" in warning for warning in result.warnings)


def test_run_audit_passes_on_consistent_inputs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _write_minimal_baseline(repo, runner, cycle=81, status="PLANNED")

    result = run_audit(repo_root=repo, runner_root=runner)
    assert result.passed is True
