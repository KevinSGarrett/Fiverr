from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from automation.ai_cycle_controller import cli
from click.testing import CliRunner


def test_safe_docs_only_exits_nonzero_when_prompt_validation_fails(tmp_path: Path) -> None:
    prompt = tmp_path / "PM_Pack/automation/prompts/CYCLE_078_AGENT_A_PROMPT.md"
    prompt.parent.mkdir(parents=True, exist_ok=True)
    prompt.write_text("stub", encoding="utf-8")

    lock = MagicMock()
    lock.acquire.return_value = True

    with patch("automation.ai_cycle_controller.REPO_ROOT", tmp_path), patch(
        "automation.lock_manager.LockManager", return_value=lock
    ), patch(
        "automation.model_gate.check", return_value=MagicMock(passed=True, summary=lambda: "ok")
    ), patch(
        "automation.prompt_validator.validate",
        return_value=MagicMock(passed=False, summary=lambda: "prompt failed"),
    ), patch(
        "automation.state_writer.write_controller_state"
    ) as write_state, patch(
        "automation.state_writer.write_heartbeat"
    ):
        result = CliRunner().invoke(
            cli,
            ["run-agent", "--agent", "A", "--cycle", "78", "--safe-docs-only"],
        )

    assert result.exit_code != 0
    write_state.assert_any_call("PROMPT_VALIDATION_FAILED", cycle=78)


def test_cursor_docs_smoke_command_registered() -> None:
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "cursor-docs-smoke" in result.output
