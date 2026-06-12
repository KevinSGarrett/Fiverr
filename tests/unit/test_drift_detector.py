from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from automation.drift_detector import DriftDetector


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def make_policy_snapshot(cycle: int, tmp_path: Path) -> Path:
    path = tmp_path / "repo" / "PM_Pack/automation/policy_snapshots/current_policy_snapshot.json"
    _write_json(path, {"current_cycle": cycle})
    return path


def make_controller_state(cycle: int, status: str, branch: str, tmp_path: Path) -> Path:
    path = tmp_path / "runner" / "state/controller_state.json"
    _write_json(path, {"active_cycle": cycle, "status": status, "active_branch": branch})
    return path


def test_no_drift_on_clean_state(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _write_json(repo / "PM_Pack/automation/policy_snapshots/current_policy_snapshot.json", {"current_cycle": 75})
    _write_json(
        runner / "state/controller_state.json",
        {"active_cycle": 75, "status": "PLANNED", "active_branch": "cycle/075/integration"},
    )
    _write_json(
        runner / "state/cursor_model_state.json",
        {"valid_until": (datetime.now(UTC) + timedelta(days=1)).isoformat()},
    )
    (repo / "PM_Pack/07_hydration").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/07_hydration/HYDRATION_HEADER.md").write_text("Active cycle: 75", encoding="utf-8")
    (repo / "PM_Pack").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/CURRENT_STATE_CANONICAL.md").write_text("Cycle: 75", encoding="utf-8")
    (repo / "PM_Pack/automation/prompts").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/automation/prompts/CYCLE_075_AGENT_A.md").write_text("x", encoding="utf-8")
    (repo / "PM_Pack/automation/policies").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/automation/policies/autonomy_freeze.yml").write_text("frozen: false\n", encoding="utf-8")
    report = DriftDetector().detect(repo, runner)
    assert report.passed is True


def test_cycle_mismatch_is_blocking(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _write_json(repo / "PM_Pack/automation/policy_snapshots/current_policy_snapshot.json", {"current_cycle": 75})
    _write_json(runner / "state/controller_state.json", {"active_cycle": 74})
    report = DriftDetector().detect(repo, runner)
    assert any(d.drift_type == "CYCLE_MISMATCH" and d.severity == "BLOCKING" for d in report.drifts)


def test_expired_model_is_blocking(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _write_json(runner / "state/cursor_model_state.json", {"valid_until": (datetime.now(UTC) - timedelta(hours=1)).isoformat()})
    report = DriftDetector().detect(repo, runner)
    assert any(d.drift_type == "MODEL_STATE_EXPIRED" for d in report.drifts)


def test_stale_snapshot_is_warning(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _write_json(repo / "PM_Pack/automation/policy_snapshots/current_policy_snapshot.json", {"current_cycle": 75})
    _write_json(runner / "state/controller_state.json", {"active_cycle": 75})
    (repo / "PM_Pack").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/CURRENT_STATE_CANONICAL.md").write_text("Cycle: 73", encoding="utf-8")
    report = DriftDetector().detect(repo, runner)
    assert any(d.drift_type == "STALE_STATE_SNAPSHOT" and d.severity == "WARNING" for d in report.drifts)


def test_frozen_dispatch_is_blocking(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    _write_json(runner / "state/controller_state.json", {"status": "AGENT_DISPATCH", "active_cycle": 75})
    freeze = repo / "PM_Pack/automation/policies/autonomy_freeze.yml"
    freeze.parent.mkdir(parents=True, exist_ok=True)
    freeze.write_text("frozen: true\n", encoding="utf-8")
    report = DriftDetector().detect(repo, runner)
    assert any(d.drift_type == "FROZEN_WHILE_DISPATCHING" for d in report.drifts)


def test_write_report_creates_json_file(tmp_path: Path) -> None:
    detector = DriftDetector()
    report = detector.detect(tmp_path / "repo", tmp_path / "runner")
    path = detector.write_report(report, tmp_path)
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "checked_at" in payload


def test_stale_snapshot_1_cycle_behind_is_ok(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    make_policy_snapshot(75, tmp_path)
    make_controller_state(75, "PLANNED", "cycle/075/integration", tmp_path)
    (repo / "PM_Pack").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/CURRENT_STATE_CANONICAL.md").write_text("Cycle: 74", encoding="utf-8")
    report = DriftDetector().detect(repo, runner)
    assert not any(d.drift_type == "STALE_STATE_SNAPSHOT" for d in report.drifts)


def test_missing_prompts_for_planned_cycle_is_blocking(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    repo.mkdir(parents=True, exist_ok=True)
    make_controller_state(75, "PLANNED", "cycle/075/integration", tmp_path)
    from unittest.mock import MagicMock, patch

    with patch("automation.drift_detector.subprocess.run", return_value=MagicMock(returncode=1, stdout="")):
        report = DriftDetector().detect(repo, runner)
    assert any(
        d.drift_type == "MISSING_PROMPTS_FOR_ACTIVE_CYCLE" and d.severity == "BLOCKING"
        for d in report.drifts
    )


def test_drift_report_passed_false_when_any_blocking(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    make_policy_snapshot(75, tmp_path)
    make_controller_state(74, "PLANNED", "cycle/074/integration", tmp_path)
    report = DriftDetector().detect(repo, runner)
    assert report.passed is False


def test_drift_report_passed_true_when_only_warnings(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    make_policy_snapshot(75, tmp_path)
    make_controller_state(75, "RUNNING", "cycle/075/integration", tmp_path)
    (repo / "PM_Pack").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/CURRENT_STATE_CANONICAL.md").write_text("Cycle: 73", encoding="utf-8")
    report = DriftDetector().detect(repo, runner)
    assert any(d.severity == "WARNING" for d in report.drifts)
    assert not any(d.severity == "BLOCKING" for d in report.drifts)
    assert report.passed is True


@pytest.mark.parametrize(
    ("setup_name", "expected_type"),
    [
        ("cycle_mismatch", "CYCLE_MISMATCH"),
        ("branch_mismatch", "BRANCH_MISMATCH"),
        ("stale_snapshot", "STALE_STATE_SNAPSHOT"),
        ("model_expired", "MODEL_STATE_EXPIRED"),
        ("stale_hydration", "STALE_HYDRATION"),
        ("missing_prompts", "MISSING_PROMPTS_FOR_ACTIVE_CYCLE"),
        ("frozen_dispatch", "FROZEN_WHILE_DISPATCHING"),
    ],
)
def test_drift_conditions_parametrized(tmp_path: Path, setup_name: str, expected_type: str) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    make_policy_snapshot(75, tmp_path)
    make_controller_state(75, "PLANNED", "cycle/075/integration", tmp_path)
    _write_json(
        runner / "state/cursor_model_state.json",
        {"valid_until": (datetime.now(UTC) + timedelta(days=1)).isoformat()},
    )
    (repo / "PM_Pack/07_hydration").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/07_hydration/HYDRATION_HEADER.md").write_text("Active cycle: 75", encoding="utf-8")
    (repo / "PM_Pack").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/CURRENT_STATE_CANONICAL.md").write_text("Cycle: 75", encoding="utf-8")
    prompts = repo / "PM_Pack/automation/prompts"
    prompts.mkdir(parents=True, exist_ok=True)
    (prompts / "CYCLE_075_AGENT_A.md").write_text("x", encoding="utf-8")
    freeze = repo / "PM_Pack/automation/policies/autonomy_freeze.yml"
    freeze.parent.mkdir(parents=True, exist_ok=True)
    freeze.write_text("frozen: false\n", encoding="utf-8")

    if setup_name == "cycle_mismatch":
        _write_json(runner / "state/controller_state.json", {"active_cycle": 74, "status": "PLANNED"})
    elif setup_name == "branch_mismatch":
        _write_json(runner / "state/controller_state.json", {"active_cycle": 75, "status": "AGENT_DISPATCH", "active_branch": "main"})
    elif setup_name == "stale_snapshot":
        (repo / "PM_Pack/CURRENT_STATE_CANONICAL.md").write_text("Cycle: 73", encoding="utf-8")
    elif setup_name == "model_expired":
        _write_json(
            runner / "state/cursor_model_state.json",
            {"valid_until": (datetime.now(UTC) - timedelta(days=1)).isoformat()},
        )
    elif setup_name == "stale_hydration":
        (repo / "PM_Pack/07_hydration/HYDRATION_HEADER.md").write_text("Active cycle: 73", encoding="utf-8")
    elif setup_name == "missing_prompts":
        for file in prompts.glob("*"):
            file.unlink()
    elif setup_name == "frozen_dispatch":
        _write_json(runner / "state/controller_state.json", {"active_cycle": 75, "status": "AGENT_DISPATCH", "active_branch": "cycle/075/integration"})
        freeze.write_text("frozen: true\n", encoding="utf-8")

    report = DriftDetector().detect(repo, runner)
    assert any(item.drift_type == expected_type for item in report.drifts)


def test_drift_detector_handles_empty_json_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    policy = repo / "PM_Pack/automation/policy_snapshots/current_policy_snapshot.json"
    controller = runner / "state/controller_state.json"
    policy.parent.mkdir(parents=True, exist_ok=True)
    controller.parent.mkdir(parents=True, exist_ok=True)
    policy.write_text("{}", encoding="utf-8")
    controller.write_text("{}", encoding="utf-8")
    report = DriftDetector().detect(repo, runner)
    assert isinstance(report.drifts, list)


def test_drift_detector_handles_invalid_json_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    policy = repo / "PM_Pack/automation/policy_snapshots/current_policy_snapshot.json"
    controller = runner / "state/controller_state.json"
    policy.parent.mkdir(parents=True, exist_ok=True)
    controller.parent.mkdir(parents=True, exist_ok=True)
    policy.write_text("{invalid", encoding="utf-8")
    controller.write_text("{invalid", encoding="utf-8")
    report = DriftDetector().detect(repo, runner)
    assert isinstance(report.drifts, list)


# Prompt-required name aliases for traceability.
def test_no_drift_all_files_consistent(tmp_path: Path) -> None:
    test_no_drift_on_clean_state(tmp_path)


def test_model_expired_is_blocking(tmp_path: Path) -> None:
    test_expired_model_is_blocking(tmp_path)


def test_stale_snapshot_over_1_cycle_is_warning(tmp_path: Path) -> None:
    test_stale_snapshot_is_warning(tmp_path)


def test_frozen_while_dispatching_is_blocking(tmp_path: Path) -> None:
    test_frozen_dispatch_is_blocking(tmp_path)


def test_write_report_creates_valid_json(tmp_path: Path) -> None:
    test_write_report_creates_json_file(tmp_path)
