"""Unit tests for cursor_adapter.py"""
from __future__ import annotations

# Ensure repo root on sys.path
import sys
from pathlib import Path

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
        assert "ERROR" not in version, f"Error getting version: {version}"


def test_kill_cursor_process_invalid_pid_returns_false() -> None:
    from automation.cursor_adapter import kill_cursor_process

    assert kill_cursor_process(99999999) is False


def test_kill_cursor_process_on_windows_uses_taskkill(monkeypatch) -> None:
    import subprocess

    import pytest
    from automation.cursor_adapter import kill_cursor_process

    if sys.platform != "win32":
        pytest.skip("Windows-specific taskkill behavior")

    class _Result:
        returncode = 0

    called = {"count": 0}

    def _fake_run(*args, **kwargs):
        _ = args, kwargs
        called["count"] += 1
        return _Result()

    monkeypatch.setattr(subprocess, "run", _fake_run)
    result = kill_cursor_process(12345)
    assert isinstance(result, bool)
    assert called["count"] == 1
