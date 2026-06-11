"""Unit tests for ai_cycle_controller.py — command surface and mode mapping."""
from __future__ import annotations

import json
import sys
from pathlib import Path

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

    def test_write_runner_state_writes_json(self, tmp_path):
        import automation.ai_cycle_controller as ctrl
        from automation.ai_cycle_controller import _write_runner_state
        orig_path = ctrl.RUNNER_STATE
        ctrl.RUNNER_STATE = tmp_path / "controller_state.json"
        try:
            _write_runner_state({"status": "TEST", "cycle": 75})
            data = json.loads(ctrl.RUNNER_STATE.read_text())
            assert data["status"] == "TEST"
            assert data["cycle"] == 75
        finally:
            ctrl.RUNNER_STATE = orig_path
