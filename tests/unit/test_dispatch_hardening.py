from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest
from automation import run_agent_lifecycle as lifecycle
from automation.cursor_adapter import CursorAdapter
from automation.run_agent_lifecycle import AgentLifecycle


def test_kill_cursor_process_invalid_pid_returns_false() -> None:
    adapter = CursorAdapter()
    assert adapter.kill_cursor_process(99999999) is False


def test_run_agent_lifecycle_no_input_calls() -> None:
    source = inspect.getsource(AgentLifecycle)
    assert "input(" not in source


def test_ruff_gate_blocks_bad_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    py = str(Path("C:/Fiverr/Fiverr/.venv/Scripts/python.exe"))

    def fake_run(args, **kwargs):  # type: ignore[no-untyped-def]
        if args[:4] == [py, "-m", "ruff", "check"]:
            return SimpleNamespace(returncode=1, stdout="ruff fail", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(lifecycle.subprocess, "run", fake_run)
    ok, detail = lifecycle._run_pre_commit_gate()
    assert ok is False
    assert "ruff" in detail.lower()


def test_pytest_gate_blocks_bad_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    py = str(Path("C:/Fiverr/Fiverr/.venv/Scripts/python.exe"))

    def fake_run(args, **kwargs):  # type: ignore[no-untyped-def]
        if args[:4] == [py, "-m", "ruff", "check"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if args[:3] == [py, "-m", "mypy"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if args[:3] == [py, "-m", "pytest"]:
            return SimpleNamespace(returncode=1, stdout="pytest fail", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(lifecycle.subprocess, "run", fake_run)
    ok, detail = lifecycle._run_pre_commit_gate()
    assert ok is False
    assert "pytest" in detail.lower()


def test_validation_commands_run_after_agent() -> None:
    source = inspect.getsource(AgentLifecycle)
    assert "validation_commands" in source
