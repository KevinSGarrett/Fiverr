from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from automation.pm_pack_consistency_audit import run_audit


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _seed_state(repo: Path, runner: Path, cycle: int = 78) -> None:
    _write(
        repo / "PM_Pack/automation/current_policy_snapshot.json",
        f'{{"cycle_current": {cycle}, "last_completed_cycle": "C077"}}',
    )
    _write(
        runner / "state/controller_state.json",
        f'{{"status":"PLANNED","active_cycle":{cycle}}}',
    )
    _write(
        runner / "state/heartbeat.json",
        f'{{"status":"OK","active_cycle":{cycle}}}',
    )
    _write(repo / "PM_Pack/07_hydration/HYDRATION_HEADER.md", f"Active cycle: {cycle}\n")
    _write(repo / "PM_Pack/07_hydration/STATE_SNAPSHOT.md", f"Cycle: {cycle}\n")


def test_fails_when_controller_state_missing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _seed_state(repo, runner)
    (runner / "state/controller_state.json").unlink()

    with patch.dict("os.environ", {}, clear=True):
        result = run_audit(repo_root=repo, runner_root=runner)

    assert result.passed is False
    assert any(c.code == "MISSING_CONTROLLER_STATE" for c in result.conflicts)


def test_fails_when_policy_cycle_zero(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _seed_state(repo, runner, cycle=78)
    _write(
        repo / "PM_Pack/automation/current_policy_snapshot.json",
        '{"cycle_current": 0, "last_completed_cycle": null}',
    )

    result = run_audit(repo_root=repo, runner_root=runner)

    assert result.passed is False
    assert any(c.code == "POLICY_SNAPSHOT_CYCLE_ZERO" for c in result.conflicts)


def test_fails_when_cycles_disagree_by_more_than_one(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _seed_state(repo, runner, cycle=78)
    _write(runner / "state/controller_state.json", '{"status":"PLANNED","active_cycle":78}')
    _write(runner / "state/heartbeat.json", '{"status":"OK","active_cycle":82}')
    _write(repo / "PM_Pack/07_hydration/HYDRATION_HEADER.md", "Active cycle: 80\n")
    _write(repo / "PM_Pack/07_hydration/STATE_SNAPSHOT.md", "Cycle: 78\n")

    result = run_audit(repo_root=repo, runner_root=runner)

    assert result.passed is False
    assert any(c.code == "CYCLE_SOURCE_DISAGREEMENT" for c in result.conflicts)


def test_fails_when_post_cycle_result_blocks_dispatch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _seed_state(repo, runner, cycle=78)
    _write(
        runner / "runs/CYCLE_078_post_cycle_result.json",
        '{"cycle":78,"blocks_dispatch":true}',
    )

    result = run_audit(repo_root=repo, runner_root=runner)

    assert result.passed is False
    assert any(c.code == "POST_CYCLE_REVIEW_BLOCKS_DISPATCH" for c in result.conflicts)


def test_fails_when_active_prompts_invalid(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _seed_state(repo, runner, cycle=78)
    _write(
        repo / "PM_Pack/automation/prompts/validated/CYCLE_078_manifest.json",
        '{"cycle": 78}',
    )

    fake_results = {
        "A": SimpleNamespace(passed=True),
        "B": SimpleNamespace(passed=False),
        "E": SimpleNamespace(passed=True),
        "C": SimpleNamespace(passed=True),
        "F": SimpleNamespace(passed=True),
        "D": SimpleNamespace(passed=True),
    }
    with patch("automation.prompt_validator.validate_all", return_value=fake_results):
        result = run_audit(repo_root=repo, runner_root=runner)

    assert result.passed is False
    assert any(c.code == "ACTIVE_PROMPTS_INVALID" for c in result.conflicts)


def test_fails_when_provider_policy_malformed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _seed_state(repo, runner, cycle=78)
    _write(
        repo / "PM_Pack/automation/provider_policy.yml",
        "version: 1\nproviders: [bad\n",
    )

    result = run_audit(repo_root=repo, runner_root=runner)

    assert result.passed is False
    assert any(c.code == "PROVIDERPOLICY_INVALID" for c in result.conflicts)
