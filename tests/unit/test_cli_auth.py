"""CLI tests for Fiverr authentication commands."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import run as run_module
from click.testing import CliRunner
from run import cli


def _patch_config_loader(monkeypatch: pytest.MonkeyPatch, session_file: Path) -> None:
    config = SimpleNamespace(fiverr=SimpleNamespace(session_file=str(session_file)))

    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            self._config_path = _config_path

        def load(self):
            return config

    monkeypatch.setattr(run_module, "ConfigLoader", _FakeLoader)


def test_relogin_command_exists() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["relogin", "--help"])
    assert result.exit_code == 0
    assert "Trigger a headed Fiverr login" in result.output


def test_relogin_command_calls_force_relogin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = CliRunner()
    _patch_config_loader(monkeypatch, tmp_path / "fiverr_session.json")
    session_manager = MagicMock()
    session_manager.force_relogin = AsyncMock()
    session_manager.close = AsyncMock()
    monkeypatch.setattr(run_module, "SessionManager", lambda _config: session_manager)

    result = runner.invoke(cli, ["relogin", "--config-path", "config.yaml"])

    assert result.exit_code == 0
    assert "Session saved successfully." in result.output
    session_manager.force_relogin.assert_awaited_once()
    session_manager.close.assert_awaited_once()


def test_session_check_valid(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = CliRunner()
    session_file = tmp_path / "fiverr_session.json"
    session_file.write_text('{"cookies":[{"name":"sid"}],"origins":[{"origin":"https://www.fiverr.com"}]}')
    _patch_config_loader(monkeypatch, session_file)
    session_manager = MagicMock()
    session_manager.is_session_valid = AsyncMock(return_value=True)
    session_manager.close = AsyncMock()
    monkeypatch.setattr(run_module, "SessionManager", lambda _config: session_manager)

    result = runner.invoke(cli, ["session-check", "--config-path", "config.yaml"])

    assert result.exit_code == 0
    assert "Session is VALID. Ready for collection." in result.output


def test_session_check_expired(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = CliRunner()
    session_file = tmp_path / "fiverr_session.json"
    session_file.write_text('{"cookies":[{"name":"sid"}],"origins":[{"origin":"https://www.fiverr.com"}]}')
    _patch_config_loader(monkeypatch, session_file)
    session_manager = MagicMock()
    session_manager.is_session_valid = AsyncMock(return_value=False)
    session_manager.close = AsyncMock()
    monkeypatch.setattr(run_module, "SessionManager", lambda _config: session_manager)

    result = runner.invoke(cli, ["session-check", "--config-path", "config.yaml"])

    assert result.exit_code == 1
    assert "Session is EXPIRED. Run: python run.py relogin" in result.output


def test_session_check_missing_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = CliRunner()
    _patch_config_loader(monkeypatch, tmp_path / "missing_session.json")
    session_manager = MagicMock()
    monkeypatch.setattr(run_module, "SessionManager", lambda _config: session_manager)

    result = runner.invoke(cli, ["session-check", "--config-path", "config.yaml"])

    assert result.exit_code == 1
    assert "ERROR: Session file not found. Run: python run.py relogin" in result.output


def test_session_file_is_gitignored() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["git", "check-ignore", "data/sessions/fiverr_session.json"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "data/sessions/fiverr_session.json" in result.stdout.replace("\\", "/")
