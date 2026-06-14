"""Unit tests for ai_cycle_controller.py — command surface and mode mapping."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parents[2]))


class TestCommandSurface:
    def test_cli_help_shows_all_commands(self):
        """All required commands must be registered."""
        from automation.ai_cycle_controller import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

        required_commands = [
            "brain-check", "compile-policy", "jira-inventory",
            "plan-cycle", "validate-prompts", "run-agent",
            "cursor-smoke", "tick", "post-cycle-review",
            "merge-gate", "status", "recover",
            "daily-report", "weekly-report", "create-labels",
        ]
        for cmd in required_commands:
            assert cmd in result.output, f"Command '{cmd}' missing from help output"

    def test_cursor_docs_smoke_command_registered(self):
        from automation.ai_cycle_controller import cli

        result = CliRunner().invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "cursor-docs-smoke" in result.output

    def test_brain_check_command_exists(self):
        from automation.ai_cycle_controller import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["brain-check", "--help"])
        assert result.exit_code == 0

    def test_compile_policy_command_exists(self):
        from automation.ai_cycle_controller import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["compile-policy", "--help"])
        assert result.exit_code == 0

    def test_tick_command_exists(self):
        from automation.ai_cycle_controller import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["tick", "--help"])
        assert result.exit_code == 0

    def test_run_agent_requires_agent_and_cycle(self):
        """run-agent must require --agent and --cycle."""
        from automation.ai_cycle_controller import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["run-agent"])
        # Should fail because required options missing
        assert result.exit_code != 0 or "Missing option" in result.output

    def test_validate_prompts_requires_cycle(self):
        """validate-prompts must require --cycle."""
        from automation.ai_cycle_controller import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["validate-prompts"])
        assert result.exit_code != 0 or "Missing option" in result.output

    def test_no_old_modes_in_commands(self):
        """Old stub mode names must NOT be in commands."""
        from automation.ai_cycle_controller import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        banned_modes = ["plan_only", "brain_check", "compile_policy",
                        "jira_inventory", "execute", "repair"]
        for mode in banned_modes:
            # These should NOT be commands (they were the old broken mode names)
            assert mode not in result.output or mode + " " not in result.output


class TestStateHelpers:
    def test_read_runner_state_returns_dict(self, tmp_path):
        import automation.ai_cycle_controller as ctrl
        from automation.ai_cycle_controller import _read_runner_state
        orig_path = ctrl.RUNNER_STATE
        ctrl.RUNNER_STATE = tmp_path / "controller_state.json"
        try:
            result = _read_runner_state()
            assert isinstance(result, dict)
        finally:
            ctrl.RUNNER_STATE = orig_path


def test_status_tick_sets_resolve_drift(tmp_path):
    from automation.ai_cycle_controller import cli

    runner = CliRunner()
    state_path = tmp_path / "controller_state.json"
    state_path.write_text('{"status":"IDLE","active_cycle":75}', encoding="utf-8")
    with patch("automation.ai_cycle_controller.RUNNER_STATE", state_path), patch(
        "automation.drift_detector.DriftDetector.detect",
        return_value=MagicMock(drifts=[MagicMock(severity="BLOCKING"),], passed=False),
    ), patch("automation.freeze_gate.is_frozen", return_value=False), patch(
        "automation.state_writer.write_heartbeat"
    ), patch("subprocess.run") as subrun, patch(
        "automation.notification_router.notify_critical"
    ) as notify_critical:
        subrun.return_value = MagicMock(stdout="")
        result = runner.invoke(cli, ["status-tick"])
    assert result.exit_code == 0
    assert "RESOLVE_DRIFT" in result.output
    notify_critical.assert_called_once()


def test_run_agent_model_blocked_calls_notify(tmp_path):
    from automation.ai_cycle_controller import cli

    prompt = tmp_path / "PM_Pack/automation/prompts/CYCLE_075_AGENT_A_PROMPT.md"
    prompt.parent.mkdir(parents=True, exist_ok=True)
    prompt.write_text("prompt", encoding="utf-8")
    runner = CliRunner()
    with patch("automation.model_gate.check", return_value=MagicMock(passed=False, summary=lambda: "bad")), patch(
        "automation.notification_router.notify_blocked"
    ) as notify, patch("automation.lock_manager.LockManager", create=True) as lock_manager, patch(
        "automation.state_writer.write_controller_state"
    ), patch("automation.state_writer.write_heartbeat"), patch(
        "automation.prompt_validator.validate", return_value=MagicMock(passed=True)
    ):
        lock = MagicMock()
        lock.acquire.return_value = True
        lock_manager.return_value = lock
        result = runner.invoke(cli, ["run-agent", "--agent", "A", "--cycle", "75"])
    assert result.exit_code != 0
    notify.assert_called()


def test_pm_pack_audit_check_only_flag():
    from automation.ai_cycle_controller import cli

    runner = CliRunner()
    with patch("automation.pm_pack_consistency_audit.run_audit") as run_audit:
        run_audit.return_value = MagicMock(passed=True, summary=lambda: "ok", sources={})
        result = runner.invoke(cli, ["pm-pack-audit", "--check-only"])
    assert result.exit_code == 0
    run_audit.assert_called_once()


def test_compile_policy_command_runs_with_mocked_compiler():
    from automation.ai_cycle_controller import cli

    runner = CliRunner()
    fake_snapshot = {
        "cycle_current": 78,
        "active_wave": 0,
        "e2e_score_pct": 50,
        "active_agent_lanes": ["A", "B", "E", "C", "F", "D"],
        "cursor_model": {"status": "VERIFIED"},
    }
    with patch("automation.ai_cycle_controller.compile_policy", return_value=fake_snapshot):
        result = runner.invoke(cli, ["compile-policy"])
    assert result.exit_code == 0
    assert "Policy snapshot written to" in result.output


def test_validate_prompts_cycle_078_with_mocked_validator():
    from automation.ai_cycle_controller import cli

    runner = CliRunner()
    fake_result = MagicMock(passed=True, errors=[], warnings=[], prompt_path="x")
    with patch("automation.prompt_validator.validate_all", return_value={"A": fake_result}):
        result = runner.invoke(cli, ["validate-prompts", "--cycle", "78", "--agents", "A"])
    assert result.exit_code == 0
    assert "PROMPT VALIDATION PASS" in result.output

def test_write_runner_state_writes_json(tmp_path):
    import automation.ai_cycle_controller as ctrl
    from automation.ai_cycle_controller import _write_runner_state

    orig_path = ctrl.RUNNER_STATE
    ctrl.RUNNER_STATE = tmp_path / "controller_state.json"
    try:
        _write_runner_state({"status": "TEST", "cycle": 75})
        data = json.loads(ctrl.RUNNER_STATE.read_text(encoding="utf-8"))
        assert data["status"] == "TEST"
        assert data["cycle"] == 75
    finally:
        ctrl.RUNNER_STATE = orig_path
