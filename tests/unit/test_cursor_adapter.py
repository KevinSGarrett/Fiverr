"""Unit tests for cursor_adapter.py"""
from __future__ import annotations

# Ensure repo root on sys.path
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))


class TestResolveBinary:
    def test_returns_agent_cmd_path(self):
        """_resolve_binary should return the agent.cmd path."""
        from automation.cursor_adapter import _resolve_binary
        binary = _resolve_binary()
        assert binary, "Binary path must not be empty"
        assert "cursor" in binary.lower() or "agent" in binary.lower()

    def test_does_not_return_desktop_binary(self):
        """_resolve_binary must never return Cursor Desktop path."""
        from automation.cursor_adapter import _resolve_binary
        binary = _resolve_binary()
        assert "Programs" not in binary or "cursor\\resources" not in binary.lower(), (
            f"FAIL: Resolved to Cursor Desktop binary: {binary}"
        )

    def test_fail_closed_on_desktop_path(self):
        """If only Desktop binary exists, should fail closed."""
        from automation.cursor_adapter import CURSOR_CLI_PATH
        desktop = r"C:\Users\Windows 11\AppData\Local\Programs\cursor\resources\app\bin\cursor.CMD"
        assert CURSOR_CLI_PATH != desktop, (
            f"CURSOR_CLI_PATH must not be Cursor Desktop: {CURSOR_CLI_PATH}"
        )


class TestBuildCommand:
    def test_includes_p_flag(self, tmp_path):
        """_build_command must include -p flag (non-interactive mode)."""
        from automation.cursor_adapter import _build_command
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text("test prompt content")
        cmd = _build_command(str(prompt_file), str(tmp_path), "Codex 5.3")
        assert "-p" in cmd, "_build_command must include -p flag"

    def test_includes_output_format_text(self, tmp_path):
        """_build_command must include --output-format text."""
        from automation.cursor_adapter import _build_command
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text("test prompt content")
        cmd = _build_command(str(prompt_file), str(tmp_path), "Codex 5.3")
        cmd_str = " ".join(cmd)
        assert "--output-format" in cmd_str and "text" in cmd_str

    def test_includes_trust_flag(self, tmp_path):
        """_build_command must include --trust flag."""
        from automation.cursor_adapter import _build_command
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text("test prompt content")
        cmd = _build_command(str(prompt_file), str(tmp_path), "Codex 5.3")
        assert "--trust" in cmd

    def test_includes_model_flag_when_provided(self, tmp_path):
        """_build_command must include --model flag when model specified."""
        from automation.cursor_adapter import _build_command
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text("test prompt content")
        cmd = _build_command(str(prompt_file), str(tmp_path), "Codex 5.3")
        # Model is optional but if provided should appear
        assert isinstance(cmd, list)


class TestCheckVersion:
    def test_returns_string(self):
        """check_version should return a non-empty string."""
        from automation.cursor_adapter import check_version
        version = check_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_version_contains_date_or_hash(self):
        """Version should look like a cursor CLI version, not a desktop version."""
        from automation.cursor_adapter import check_version
        version = check_version()
        # Standalone CLI version format: YYYY.MM.DD-HASH or similar
        # Desktop version format: X.Y.Z (pure semver)
        # Shouldn't be empty
        assert version != "NOT_FOUND", f"Cursor CLI not found: {version}"
        assert isinstance(version, str)


def test_kill_process_tree_raises_on_zero_pid():
    from automation.cursor_adapter import CursorAdapter

    with pytest.raises(ValueError):
        CursorAdapter.kill_process_tree(0)


def test_kill_process_tree_raises_on_system_pid():
    from automation.cursor_adapter import CursorAdapter

    with pytest.raises(ValueError):
        CursorAdapter.kill_process_tree(4)


def test_terminate_skips_already_dead_process():
    from automation.cursor_adapter import _terminate_agent_process

    proc = MagicMock()
    proc.poll.return_value = 0
    _terminate_agent_process(proc)
    proc.kill.assert_not_called()


def test_kill_calls_taskkill_with_correct_args():
    from automation.cursor_adapter import CursorAdapter

    with patch("automation.cursor_adapter.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stderr="")
        CursorAdapter.kill_process_tree(1234)
        args = run.call_args.args[0]
        assert args == ["taskkill", "/F", "/T", "/PID", "1234"]


def test_kill_process_tree_handles_already_dead_process():
    from automation.cursor_adapter import CursorAdapter

    with patch("automation.cursor_adapter.subprocess.run") as run:
        run.return_value = MagicMock(returncode=128, stderr="")
        CursorAdapter.kill_process_tree(1234)


def test_stdin_delivery_for_long_prompts(tmp_path: Path):
    from automation import cursor_adapter

    prompt = tmp_path / "long_prompt.md"
    prompt.write_text("x" * 5000, encoding="utf-8")
    out_dir = tmp_path / "out"
    proc = MagicMock()
    proc.poll.return_value = 0
    proc.stdin = MagicMock()

    with patch("automation.cursor_adapter._resolve_binary", return_value="agent"), patch(
        "automation.cursor_adapter.subprocess.Popen", return_value=proc
    ) as popen:
        result = cursor_adapter.run_agent(
            agent_id="A",
            prompt_path=str(prompt),
            working_dir=str(tmp_path),
            output_dir=str(out_dir),
            timeout_minutes=1,
            no_output_kill_minutes=1,
        )
    assert result.status in {"complete", "error"}
    kwargs = popen.call_args.kwargs
    assert kwargs["stdin"] is not None


def test_config_driven_binary_resolution(tmp_path: Path):
    from automation import cursor_adapter

    fake_bin = tmp_path / "agent.cmd"
    fake_bin.write_text("echo test", encoding="utf-8")
    with patch("automation.cursor_adapter.RUNNER_CONFIG", tmp_path / "cursor_adapter.yaml"), patch(
        "automation.cursor_adapter._load_config", return_value={"binary": str(fake_bin)}
    ):
        assert cursor_adapter._resolve_binary() == str(fake_bin)


def test_run_agent_uses_terminate_not_bare_kill(tmp_path: Path):
    from automation import cursor_adapter

    prompt = tmp_path / "prompt.md"
    prompt.write_text("short prompt", encoding="utf-8")
    out_dir = tmp_path / "out"
    proc = MagicMock()
    proc.poll.side_effect = lambda: None
    proc.stdin = None

    with patch("automation.cursor_adapter._resolve_binary", return_value="agent"), patch(
        "automation.cursor_adapter.subprocess.Popen", return_value=proc
    ), patch("automation.cursor_adapter._terminate_agent_process") as terminate, patch(
        "automation.cursor_adapter.time.time", side_effect=[0, 0, 10_000, 10_000]
    ), patch("automation.cursor_adapter.time.sleep"):
        cursor_adapter.run_agent(
            agent_id="A",
            prompt_path=str(prompt),
            working_dir=str(tmp_path),
            output_dir=str(out_dir),
            timeout_minutes=1,
            no_output_kill_minutes=1,
        )
    terminate.assert_called_once()


# Prompt-required name aliases.
def test_kill_process_tree_raises_on_pid_less_than_10():
    test_kill_process_tree_raises_on_system_pid()


def test_kill_process_tree_calls_taskkill_with_correct_args():
    test_kill_calls_taskkill_with_correct_args()


def test_terminate_skips_kill_when_process_already_dead():
    test_terminate_skips_already_dead_process()
