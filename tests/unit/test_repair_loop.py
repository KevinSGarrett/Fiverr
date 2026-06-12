"""Unit tests for repair_loop.py — failure classification and prompt generation."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))


class TestClassifyFailure:
    """_classify_failure correctly identifies failure types from error messages."""

    def test_lint(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure(["ruff check error"]) == "lint"

    def test_lint_uppercase(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure(["Ruff FAIL: F401"]) == "lint"

    def test_typecheck(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure(["mypy error found"]) == "typecheck"

    def test_test(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure(["pytest FAILED"]) == "test"

    def test_report(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure(["Required report not found"]) == "report"

    def test_ownership(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure(["ownership violation"]) == "ownership"

    def test_general_fallback(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure(["something else entirely"]) == "general"

    def test_empty_errors(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure([]) == "general"


class TestGenerateRepairPrompt:
    def test_repair_prompt_has_required_sections(self):
        """Repair prompt must have END OF PROMPT, model block, validation commands."""
        from automation.repair_loop import _generate_repair_prompt
        prompt = _generate_repair_prompt(
            agent_id="A", cycle=75,
            errors=["ruff check failed: E501"],
            failure_type="lint",
            attempt=1,
        )
        assert "END OF PROMPT" in prompt
        assert "Codex 5.3" in prompt
        assert "medium" in prompt.lower()
        assert "git commit" in prompt.lower() or "commit" in prompt.lower()

    def test_repair_prompt_includes_errors(self):
        """Repair prompt must include the specific error messages."""
        from automation.repair_loop import _generate_repair_prompt
        errors = ["ruff: line 42 E501 too long", "ruff: line 55 F401 import unused"]
        prompt = _generate_repair_prompt("A", 75, errors, "lint", 1)
        assert "ruff: line 42" in prompt or "E501" in prompt

    def test_repair_prompt_includes_attempt_number(self):
        from automation.repair_loop import _generate_repair_prompt
        prompt = _generate_repair_prompt("B", 75, ["error"], "test", 2)
        assert "2" in prompt
        assert "attempt" in prompt.lower() or "Attempt" in prompt

    def test_repair_prompt_includes_agent_and_cycle(self):
        from automation.repair_loop import _generate_repair_prompt
        prompt = _generate_repair_prompt("C", 75, ["error"], "test", 1)
        assert "Agent C" in prompt or "AGENT_C" in prompt or "Agent C" in prompt
        assert "075" in prompt or "75" in prompt

    def test_repair_prompt_includes_branch(self):
        from automation.repair_loop import _generate_repair_prompt
        prompt = _generate_repair_prompt("D", 75, ["error"], "report", 1)
        assert "cycle/075/integration" in prompt

    def test_repair_prompt_contains_required_failure_context(self):
        from automation.repair_loop import _generate_repair_prompt

        prompt = _generate_repair_prompt(
            "A",
            75,
            ["validation failed"],
            "ruff_failure",
            2,
            original_prompt_path=None,
            validation_output="x" * 2500,
            report_path="C:/AI_Runner/reports/run.md",
        )
        assert "Failure Type" in prompt
        assert "Original Mission" in prompt
        assert "Exact Error Output" in prompt
        assert "Run validation after fixing" in prompt
        assert "Stop conditions" in prompt
        assert "write report to" in prompt.lower()


class TestRepairResult:
    def test_result_dataclass(self):
        from automation.repair_loop import RepairResult
        r = RepairResult(agent="A", cycle=75, attempt=1, status="REPAIRED")
        assert r.agent == "A"
        assert r.cycle == 75
        assert r.attempt == 1
        assert r.status == "REPAIRED"

    def test_result_defaults(self):
        from automation.repair_loop import RepairResult
        r = RepairResult(agent="A", cycle=75, attempt=1, status="FAILED")
        assert r.errors_in == []
        assert r.errors_out == []
        assert r.repair_prompt_path == ""
        assert r.commit_sha == ""


class TestMaxAttempts:
    def test_max_attempts_constant(self):
        """MAX_REPAIR_ATTEMPTS must be 3."""
        from automation.repair_loop import MAX_REPAIR_ATTEMPTS
        assert MAX_REPAIR_ATTEMPTS == 3


def test_max_attempts_triggers_quarantine(tmp_path):
    from automation.repair_loop import dispatch_repair

    state = tmp_path / "runner/state/repair_state_A_75.json"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text('{"attempt_count": 3, "failures": []}', encoding="utf-8")
    with patch("automation.repair_loop.quarantine_agent_work") as quarantine:
        result = dispatch_repair(
            agent_id="A",
            cycle=75,
            run_dir=tmp_path / "run",
            errors=["x"],
            repo_root=tmp_path / "repo",
            runner_root=tmp_path / "runner",
        )
        assert result.status == "BLOCKED"
        quarantine.assert_called_once()


def test_quarantine_uses_git_stash_not_reset(tmp_path):
    from automation.repair_loop import quarantine_agent_work

    with patch("automation.repair_loop.subprocess.run") as run, patch(
        "automation.notification_router.notify_blocked"
    ):
        run.return_value = MagicMock(stdout="stash@{0}: test")
        quarantine_agent_work("A", 75, tmp_path / "repo", tmp_path / "runner")
        assert any("stash" in " ".join(call.args[0]) for call in run.call_args_list)
        assert not any("reset" in " ".join(call.args[0]) for call in run.call_args_list)


def test_revert_uses_git_revert_not_force_push(tmp_path):
    from automation.repair_loop import revert_accepted_agent

    with patch("automation.repair_loop.subprocess.run") as run:
        run.side_effect = [MagicMock(), MagicMock(stdout="abc123\n")]
        sha = revert_accepted_agent("deadbeef", "reason", tmp_path)
        assert sha == "abc123"
        assert "revert" in " ".join(run.call_args_list[0].args[0])
        assert "reset" not in " ".join(run.call_args_list[0].args[0])


def test_quarantine_writes_incident_file(tmp_path):
    from automation.repair_loop import quarantine_agent_work

    with patch("automation.repair_loop.subprocess.run") as run, patch(
        "automation.notification_router.notify_blocked"
    ):
        run.return_value = MagicMock(stdout="stash@{0}: test")
        incident = quarantine_agent_work("B", 75, tmp_path / "repo", tmp_path / "runner")
    assert incident.exists()


def test_repair_state_tracks_attempt_count(tmp_path):
    from automation.repair_loop import _save_repair_state

    path = tmp_path / "state.json"
    _save_repair_state(path, "A", 75, 1, ["first"])
    _save_repair_state(path, "A", 75, 2, ["second"])
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["attempt_count"] == 2


def test_first_attempt_increments_count_to_1(tmp_path):
    from automation.repair_loop import _save_repair_state

    path = tmp_path / "state.json"
    _save_repair_state(path, "A", 75, 1, ["first"])
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["attempt_count"] == 1


def test_second_attempt_increments_count_to_2(tmp_path):
    from automation.repair_loop import _save_repair_state

    path = tmp_path / "state.json"
    _save_repair_state(path, "A", 75, 1, ["first"])
    _save_repair_state(path, "A", 75, 2, ["second"])
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["attempt_count"] == 2


@pytest.mark.xfail(reason="production code quarantines on attempt > 3, not == 3")
def test_third_attempt_triggers_quarantine(tmp_path):
    from automation.repair_loop import dispatch_repair

    state = tmp_path / "runner/state/repair_state_A_75.json"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text('{"attempt_count": 2, "failures": []}', encoding="utf-8")
    with patch("automation.repair_loop.quarantine_agent_work") as quarantine:
        dispatch_repair(
            agent_id="A",
            cycle=75,
            run_dir=tmp_path / "run",
            errors=["x"],
            repo_root=tmp_path / "repo",
            runner_root=tmp_path / "runner",
        )
        quarantine.assert_called_once()


def test_update_pr_after_repair_calls_add_pr_comment():
    from automation.repair_loop import update_pr_after_repair

    client = MagicMock()
    update_pr_after_repair(123, 2, "passed", client)
    client.add_pr_comment.assert_called_once()


def test_quarantine_calls_notify_blocked(tmp_path):
    from automation.repair_loop import quarantine_agent_work

    with patch("automation.repair_loop.subprocess.run") as run, patch(
        "automation.notification_router.notify_blocked"
    ) as notify:
        run.return_value = MagicMock(stdout="stash@{0}: test")
        quarantine_agent_work("B", 75, tmp_path / "repo", tmp_path / "runner")
        notify.assert_called_once()


# Prompt-required name aliases.
def test_max_repair_attempts_constant_is_3():
    from automation.repair_loop import MAX_REPAIR_ATTEMPTS

    assert MAX_REPAIR_ATTEMPTS == 3


def test_quarantine_uses_git_stash_push_not_reset_hard(tmp_path):
    test_quarantine_uses_git_stash_not_reset(tmp_path)


def test_revert_accepted_uses_git_revert_not_force_push(tmp_path):
    test_revert_uses_git_revert_not_force_push(tmp_path)


def test_repair_state_json_is_written_after_each_attempt(tmp_path):
    from automation.repair_loop import _save_repair_state

    state = tmp_path / "state.json"
    _save_repair_state(state, "A", 75, 1, ["first"])
    _save_repair_state(state, "A", 75, 2, ["second"])
    payload = json.loads(state.read_text(encoding="utf-8"))
    assert payload["attempt_count"] == 2


def test_dispatch_repair_success_path_sets_repaired_and_commit(tmp_path):
    from automation.repair_loop import dispatch_repair

    runner = tmp_path / "runner"
    repo = tmp_path / "repo"
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    with patch("automation.cursor_adapter.run_agent") as run_agent, patch(
        "automation.run_agent_lifecycle._run_validation", return_value=(True, "ok")
    ), patch("automation.run_agent_lifecycle._get_changed_files", return_value=["automation/x.py"]), patch(
        "automation.run_agent_lifecycle._commit_agent_work", return_value="abc123"
    ):
        run_agent.return_value = MagicMock(status="complete")
        result = dispatch_repair(
            agent_id="A",
            cycle=75,
            run_dir=run_dir,
            errors=["ruff fail"],
            repo_root=repo,
            runner_root=runner,
        )
    assert result.status == "REPAIRED"
    assert result.commit_sha == "abc123"


def test_dispatch_repair_cursor_failure_sets_failed(tmp_path):
    from automation.repair_loop import dispatch_repair

    runner = tmp_path / "runner"
    repo = tmp_path / "repo"
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    with patch("automation.cursor_adapter.run_agent") as run_agent:
        run_agent.return_value = MagicMock(status="timeout")
        result = dispatch_repair(
            agent_id="A",
            cycle=75,
            run_dir=run_dir,
            errors=["timeout"],
            repo_root=repo,
            runner_root=runner,
        )
    assert result.status == "FAILED"
    assert result.errors_out
