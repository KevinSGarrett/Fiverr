"""Unit tests for cursor_adapter.py"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

_ON_CI = bool(os.environ.get("CI", "").strip())
_skip_no_binary = pytest.mark.skipif(_ON_CI, reason="no Cursor CLI binary on CI runner")


class TestResolveBinary:
    @_skip_no_binary
    def test_returns_agent_cmd_path(self):
        from automation.cursor_adapter import _resolve_binary
        binary = _resolve_binary()
        assert binary, "Binary path must not be empty"
        assert "cursor" in binary.lower() or "agent" in binary.lower()

    @_skip_no_binary
    def test_does_not_return_desktop_binary(self):
        from automation.cursor_adapter import _resolve_binary
        binary = _resolve_binary()
        assert "Programs" not in binary or "cursor\\resources" not in binary.lower()

    def test_fail_closed_on_desktop_path(self):
        from automation.cursor_adapter import CURSOR_CLI_PATH
        desktop = r"C:\Users\Windows 11\AppData\Local\Programs\cursor\resources\app\bin\cursor.CMD"
        assert CURSOR_CLI_PATH != desktop


class TestBuildCommand:
    def test_includes_p_flag(self, tmp_path):
        from automation.cursor_adapter import _build_command
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text("test prompt content")
        with patch("automation.cursor_adapter._resolve_binary", return_value="/fake/agent.cmd"):
            cmd = _build_command(str(prompt_file), str(tmp_path), "Codex 5.3")
        assert "-p" in cmd

    def test_includes_output_format_text(self, tmp_path):
        from automation.cursor_adapter import _build_command
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text("test prompt content")
        with patch("automation.cursor_adapter._resolve_binary", return_value="/fake/agent.cmd"):
            cmd = _build_command(str(prompt_file), str(tmp_path), "Codex 5.3")
        cmd_str = " ".join(cmd)
        assert "--output-format" in cmd_str and "text" in cmd_str

    def test_includes_trust_flag(self, tmp_path):
        from automation.cursor_adapter import _build_command
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text("test prompt content")
        with patch("automation.cursor_adapter._resolve_binary", return_value="/fake/agent.cmd"):
            cmd = _build_command(str(prompt_file), str(tmp_path), "Codex 5.3")
        assert "--trust" in cmd

    def test_includes_model_flag_when_provided(self, tmp_path):
        from automation.cursor_adapter import _build_command
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text("test prompt content")
        with patch("automation.cursor_adapter._resolve_binary", return_value="/fake/agent.cmd"):
            cmd = _build_command(str(prompt_file), str(tmp_path), "Codex 5.3")
        assert isinstance(cmd, list)


class TestCheckVersion:
    @_skip_no_binary
    def test_returns_string(self):
        from automation.cursor_adapter import check_version
        version = check_version()
        assert isinstance(version, str)
