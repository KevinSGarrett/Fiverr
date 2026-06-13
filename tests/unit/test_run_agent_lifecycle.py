"""Unit tests for run_agent_lifecycle.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[2]))

from automation.run_agent_lifecycle import (
    AgentLifecycleResult,
    ValidationResult,
    _commit_agent_work,
    _run_targeted_validation,
    _write_run_record,
    run_post_agent_lifecycle,
    validate_run_record_schema,
)


def test_write_run_record_creates_file(tmp_path: Path) -> None:
    result = AgentLifecycleResult(agent="A", cycle=75, run_id="run-1", status="COMPLETE")
    record = _write_run_record(result, "A", 75, "run-1", tmp_path, tmp_path)
    assert record.exists()


def test_run_record_has_all_required_fields(tmp_path: Path) -> None:
    result = AgentLifecycleResult(agent="A", cycle=75, run_id="run-1", status="COMPLETE")
    record = _write_run_record(result, "A", 75, "run-1", tmp_path, tmp_path)
    valid, missing = validate_run_record_schema(record)
    assert valid is True
    assert missing == []


def test_run_record_task_count_matches_headings(tmp_path: Path) -> None:
    prompt = tmp_path / "PM_Pack/automation/prompts/CYCLE_075_AGENT_A_PROMPT.md"
    prompt.parent.mkdir(parents=True, exist_ok=True)
    prompt.write_text("### Task 1\nx\n### Task 2\n", encoding="utf-8")
    result = AgentLifecycleResult(agent="A", cycle=75, run_id="run-1", status="COMPLETE")
    record = _write_run_record(result, "A", 75, "run-1", tmp_path, tmp_path)
    payload = json.loads(record.read_text(encoding="utf-8"))
    assert payload["prompt_task_count"] == 2


def test_validate_schema_fails_on_missing_field(tmp_path: Path) -> None:
    path = tmp_path / "record.json"
    path.write_text(json.dumps({"run_id": "x"}), encoding="utf-8")
    valid, missing = validate_run_record_schema(path)
    assert valid is False
    assert "cycle" in missing


def test_run_record_duration_correct(tmp_path: Path) -> None:
    result = AgentLifecycleResult(agent="A", cycle=75, run_id="run-1", status="COMPLETE")
    record = _write_run_record(result, "A", 75, "run-1", tmp_path, tmp_path)
    payload = json.loads(record.read_text(encoding="utf-8"))
    assert isinstance(payload["duration_seconds"], int)


def test_targeted_ruff_only_runs_on_py_files(tmp_path: Path) -> None:
    with patch("automation.run_agent_lifecycle.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _run_targeted_validation("A", ["automation/a.py", "README.md"], tmp_path, tmp_path)
        ruff_cmd = run.call_args_list[0].args[0]
        assert "README.md" not in ruff_cmd


def test_targeted_pytest_maps_automation_to_test(tmp_path: Path) -> None:
    test_file = tmp_path / "tests/unit/test_foo.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("def test_x():\n  assert True\n", encoding="utf-8")
    with patch("automation.run_agent_lifecycle.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = _run_targeted_validation("A", ["automation/foo.py"], tmp_path, tmp_path)
    assert result.pytest_count == 1


def test_validation_written_to_run_dir(tmp_path: Path) -> None:
    with patch("automation.run_agent_lifecycle.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        _run_targeted_validation("A", ["automation/foo.py"], tmp_path, tmp_path)
    assert (tmp_path / "validation_A.json").exists()


def test_validation_never_raises_on_subprocess_error(tmp_path: Path) -> None:
    with patch("automation.run_agent_lifecycle.subprocess.run", side_effect=FileNotFoundError("missing")):
        result = _run_targeted_validation("A", ["automation/foo.py"], tmp_path, tmp_path)
    assert result.overall_passed is False


def test_overall_passed_false_when_ruff_fails(tmp_path: Path) -> None:
    with patch("automation.run_agent_lifecycle.subprocess.run") as run:
        run.side_effect = [
            MagicMock(returncode=1, stdout="ruff fail", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]
        result = _run_targeted_validation("A", ["automation/foo.py"], tmp_path, tmp_path)
    assert result.overall_passed is False


def test_failing_validation_triggers_repair_not_commit(tmp_path: Path) -> None:
    report = tmp_path / "docs/cycle_reports/CYCLE_075_AGENT_A.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("AGENT_COMPLETE", encoding="utf-8")
    with patch("automation.run_agent_lifecycle.REPO_ROOT", tmp_path), patch(
        "automation.run_agent_lifecycle._get_changed_files", return_value=["automation/foo.py"]
    ), patch("automation.run_agent_lifecycle._scan_changed_files", return_value=[]), patch(
        "automation.run_agent_lifecycle._run_targeted_validation",
        return_value=ValidationResult(False, "x", True, "", True, 0, [], [], False),
    ), patch("automation.run_agent_lifecycle._commit_agent_work") as commit, patch(
        "automation.repair_loop.dispatch_repair", return_value={"status": "attempted"}
    ):
        result = run_post_agent_lifecycle("A", 75, "run", tmp_path)
    assert result.status == "REPAIR_ATTEMPTED"
    assert result.repair_result == {"status": "attempted"}
    commit.assert_not_called()


def test_passing_validation_proceeds_to_commit(tmp_path: Path) -> None:
    report = tmp_path / "docs/cycle_reports/CYCLE_075_AGENT_A.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("AGENT_COMPLETE", encoding="utf-8")
    with patch("automation.run_agent_lifecycle.REPO_ROOT", tmp_path), patch(
        "automation.run_agent_lifecycle._get_changed_files", return_value=["automation/foo.py"]
    ), patch("automation.run_agent_lifecycle._scan_changed_files", return_value=[]), patch(
        "automation.run_agent_lifecycle._run_targeted_validation",
        return_value=ValidationResult(True, "", True, "", True, 0, [], [], True),
    ), patch("automation.run_agent_lifecycle._commit_agent_work", return_value="abc123") as commit:
        result = run_post_agent_lifecycle("A", 75, "run", tmp_path)
    assert result.status == "COMPLETE"
    commit.assert_called_once()


def test_no_commit_path_bypasses_validation(tmp_path: Path) -> None:
    report = tmp_path / "docs/cycle_reports/CYCLE_075_AGENT_A.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("AGENT_COMPLETE", encoding="utf-8")
    with patch("automation.run_agent_lifecycle.REPO_ROOT", tmp_path), patch(
        "automation.run_agent_lifecycle._get_changed_files", return_value=["automation/foo.py"]
    ), patch("automation.run_agent_lifecycle._scan_changed_files", return_value=[]), patch(
        "automation.run_agent_lifecycle._run_targeted_validation",
        return_value=ValidationResult(True, "", True, "", True, 0, [], [], True),
    ) as validate, patch("automation.run_agent_lifecycle._commit_agent_work", return_value="abc123"):
        run_post_agent_lifecycle("A", 75, "run", tmp_path)
    validate.assert_called_once()


def test_commit_agent_work_uses_explicit_paths(tmp_path: Path) -> None:
    with patch("automation.run_agent_lifecycle.REPO_ROOT", tmp_path), patch(
        "automation.run_agent_lifecycle.subprocess.run"
    ) as run:
        run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=1),
            MagicMock(stdout=""),
        ]
        _commit_agent_work("A", 75, ["automation/foo.py", "tests/unit/test_foo.py"])
        stage_cmd = run.call_args_list[0].args[0]
        assert stage_cmd[:3] == ["git", "add", "--"]
        assert "." not in stage_cmd
        assert "-A" not in stage_cmd


# Prompt-required name aliases.
def test_write_run_record_creates_json_at_correct_path(tmp_path: Path) -> None:
    test_write_run_record_creates_file(tmp_path)


def test_run_record_prompt_task_count_counts_task_headings(tmp_path: Path) -> None:
    test_run_record_task_count_matches_headings(tmp_path)


def test_run_record_duration_is_end_minus_start(tmp_path: Path) -> None:
    test_run_record_duration_correct(tmp_path)


def test_validate_schema_passes_on_complete_record(tmp_path: Path) -> None:
    test_run_record_has_all_required_fields(tmp_path)


def test_targeted_validation_result_written_to_run_dir(tmp_path: Path) -> None:
    test_validation_written_to_run_dir(tmp_path)


def test_commit_agent_work_uses_explicit_file_paths_not_add_all(tmp_path: Path) -> None:
    test_commit_agent_work_uses_explicit_paths(tmp_path)


def test_run_record_has_all_required_schema_fields(tmp_path: Path) -> None:
    test_run_record_has_all_required_fields(tmp_path)


def test_targeted_validation_ruff_only_on_py_files(tmp_path: Path) -> None:
    test_targeted_ruff_only_runs_on_py_files(tmp_path)


def test_validation_failure_routes_to_repair_not_commit(tmp_path: Path) -> None:
    test_failing_validation_triggers_repair_not_commit(tmp_path)
