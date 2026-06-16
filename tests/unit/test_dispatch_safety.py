from __future__ import annotations

from automation import run_agent_lifecycle as lifecycle


def test_run_pre_commit_gate_ruff_failure_blocks(monkeypatch) -> None:
    class _Result:
        def __init__(self, code: int) -> None:
            self.returncode = code
            self.stdout = ""
            self.stderr = ""

    calls = {"idx": 0}

    def _fake_run(*args, **kwargs):
        _ = args, kwargs
        calls["idx"] += 1
        if calls["idx"] == 1:
            return _Result(1)
        return _Result(0)

    monkeypatch.setattr("automation.run_agent_lifecycle.subprocess.run", _fake_run)
    passed, detail = lifecycle._run_pre_commit_gate()
    assert passed is False
    assert "ruff failures detected" in detail


def test_run_pre_commit_gate_pytest_failure_blocks(monkeypatch) -> None:
    class _Result:
        def __init__(self, code: int) -> None:
            self.returncode = code
            self.stdout = ""
            self.stderr = ""

    calls = {"idx": 0}

    def _fake_run(*args, **kwargs):
        _ = args, kwargs
        calls["idx"] += 1
        if calls["idx"] == 2:
            return _Result(1)
        return _Result(0)

    monkeypatch.setattr("automation.run_agent_lifecycle.subprocess.run", _fake_run)
    passed, detail = lifecycle._run_pre_commit_gate()
    assert passed is False
    assert "pytest failures detected" in detail
