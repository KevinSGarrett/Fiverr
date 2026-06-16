from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest
from automation import run_agent_lifecycle as lifecycle
from automation.cursor_adapter import CursorAdapter
from automation.run_agent_lifecycle import AgentLifecycle


def test_ruff_gate_in_lifecycle() -> None:
    source = inspect.getsource(lifecycle._run_pre_commit_gate)
    assert "ruff" in source


def test_pytest_gate_in_lifecycle() -> None:
    source = inspect.getsource(lifecycle._run_pre_commit_gate)
    assert "pytest" in source


def test_process_tree_kill_handles_invalid_pid() -> None:
    assert CursorAdapter().kill_cursor_process(99999999) is False


def test_validation_commands_wired() -> None:
    source = inspect.getsource(AgentLifecycle.run)
    assert "validation_commands" in source


def test_no_commit_on_failing_ruff(monkeypatch: pytest.MonkeyPatch) -> None:
    py = str(Path("C:/Fiverr/Fiverr/.venv/Scripts/python.exe"))

    def fake_run(args, **kwargs):  # type: ignore[no-untyped-def]
        _ = kwargs
        if args[:4] == [py, "-m", "ruff", "check"]:
            return SimpleNamespace(returncode=1, stdout="ruff fail", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(lifecycle.subprocess, "run", fake_run)
    ok, detail = lifecycle._run_pre_commit_gate()
    assert ok is False
    assert "ruff" in detail.lower()
