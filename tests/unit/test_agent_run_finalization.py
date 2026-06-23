"""Finalize-completed-agent-run fixes (observed live, cycle-84 agent B, which built +
committed real wave-11 code and wrote its AGENT_COMPLETE report, yet the runner failed
to credit it):

  1. _run_validation ran `pytest tests/unit/` with a 300s timeout while the suite takes
     ~11 min, so TimeoutExpired propagated UNCAUGHT and crashed the whole post-agent
     lifecycle. It must now treat a timeout/error as a validation FAIL, never crash, and
     the pytest timeout is sized for the full suite (env-tunable).
  2. cursor-agent in --print mode often does not exit after finishing; it idled until the
     no-output watchdog killed it as a false 'no_output'. run_agent now accepts a
     completion_marker (the agent's report path) and ends the run promptly once it
     contains AGENT_COMPLETE.
"""
from __future__ import annotations

import inspect
import subprocess

import automation.cursor_adapter as ca
import automation.run_agent_lifecycle as ral


def test_run_validation_catches_timeout_and_does_not_crash(monkeypatch):
    def _raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=(args[0] if args else "cmd"),
                                        timeout=kwargs.get("timeout", 1))
    monkeypatch.setattr(ral.subprocess, "run", _raise_timeout)
    # Must NOT raise; must report failure with a TIMEOUT detail.
    passed, details = ral._run_validation("B")
    assert passed is False
    assert "TIMEOUT" in details


def test_run_validation_catches_generic_error_not_crash(monkeypatch):
    def _raise(*args, **kwargs):
        raise OSError("boom")
    monkeypatch.setattr(ral.subprocess, "run", _raise)
    passed, details = ral._run_validation("B")
    assert passed is False
    assert "ERROR" in details


def test_run_validation_pytest_timeout_is_env_tunable(monkeypatch):
    captured = {}
    def _capture(cmd, **kwargs):
        if "pytest" in cmd:
            captured["timeout"] = kwargs.get("timeout")
        class _R:
            returncode = 0
            stdout = ""
            stderr = ""
        return _R()
    monkeypatch.setenv("AGENT_VALIDATION_PYTEST_TIMEOUT", "777")
    monkeypatch.setattr(ral.subprocess, "run", _capture)
    ral._run_validation("B")
    assert captured.get("timeout") == 777


def test_run_validation_default_pytest_timeout_fits_full_suite(monkeypatch):
    captured = {}
    def _capture(cmd, **kwargs):
        if "pytest" in cmd:
            captured["timeout"] = kwargs.get("timeout")
        class _R:
            returncode = 0
            stdout = ""
            stderr = ""
        return _R()
    monkeypatch.delenv("AGENT_VALIDATION_PYTEST_TIMEOUT", raising=False)
    monkeypatch.setattr(ral.subprocess, "run", _capture)
    ral._run_validation("B")
    # The unit suite runs ~11 min (~680s); the default must comfortably exceed it.
    assert captured.get("timeout", 0) >= 900


def test_run_agent_accepts_completion_marker():
    assert "completion_marker" in inspect.signature(ca.run_agent).parameters
