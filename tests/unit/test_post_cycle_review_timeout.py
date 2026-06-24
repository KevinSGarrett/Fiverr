"""Observed-live regression: the post-cycle review's local pytest+coverage run
must NOT propagate a TimeoutExpired.

Bug seen on the live runner: ``_run_local_suite`` ran ``pytest tests/unit/ --cov
--cov-fail-under=80`` with a fixed 900s timeout. The suite grew past that on a
loaded runner, ``subprocess.run`` raised ``TimeoutExpired``, the exception
propagated out of ``run_review``, the controller caught it and stayed in
POST_CYCLE_PENDING, and the next tick re-ran the same slow suite — FOREVER. The
tick "succeeds" (the controller catches the error), so the autopilot circuit
breaker never trips.

Fix: a timeout is a NON-fatal red fact (``local_pytest = False``) and the timeout
is env-tunable via ``POST_CYCLE_PYTEST_TIMEOUT`` (default 1800s). Plus a
defense-in-depth bound in the controller's POST_CYCLE_PENDING handler.
"""
from __future__ import annotations

import inspect
import subprocess

import automation.post_cycle_review as pcr


def test_local_suite_timeout_is_non_fatal(monkeypatch):
    """A pytest TimeoutExpired sets local_pytest=False and does NOT raise."""
    # ruff/mypy pre-checks: short-circuit so the test doesn't shell out.
    monkeypatch.setattr(pcr, "_run_check", lambda *a, **k: True)

    def _raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="pytest", timeout=kwargs.get("timeout", 1800))

    monkeypatch.setattr(pcr.subprocess, "run", _raise_timeout)

    facts = pcr.PostCycleFacts(cycle=84, mode=pcr.ReviewMode.POST_AGENT)
    # Must not raise — the whole point of the fix.
    pcr._run_local_suite(facts)
    assert facts.local_pytest is False


def test_local_suite_timeout_is_env_tunable():
    """The fixed 900s is gone; the timeout reads POST_CYCLE_PYTEST_TIMEOUT."""
    src = inspect.getsource(pcr._run_local_suite)
    assert "POST_CYCLE_PYTEST_TIMEOUT" in src
    assert "timeout=900" not in src
    # The TimeoutExpired path must record a red fact and return, not propagate.
    assert "except subprocess.TimeoutExpired" in src
    ti = src.index("except subprocess.TimeoutExpired")
    tail = src[ti:ti + 400]
    assert "local_pytest = False" in tail
    assert "return" in tail


def test_controller_bounds_post_cycle_review_errors():
    """Defense-in-depth: the controller's POST_CYCLE_PENDING handler must bound
    consecutive review exceptions and route to POST_CYCLE_FAIL instead of looping
    forever (the circuit breaker can't catch it — the tick 'succeeds')."""
    import automation.ai_cycle_controller as ctrl
    src = inspect.getsource(ctrl.cmd_tick.callback)
    # The PENDING handler increments a per-cycle review-error counter...
    assert "post_cycle_review_err_" in src
    assert "AUTOPILOT_POST_CYCLE_REVIEW_ERR_MAX" in src
    # ...and on exceeding the cap writes POST_CYCLE_FAIL (bounded recovery).
    i = src.index("AUTOPILOT_POST_CYCLE_REVIEW_ERR_MAX")
    seg = src[i:i + 600]
    assert 'write_controller_state("POST_CYCLE_FAIL"' in seg
    # Codex P2: the cap must be honored EXACTLY — escalate on the Nth exception
    # (>=), never the (N+1)th (`>` would let a cap of 3 loop a 4th time).
    assert "_rerr >= _rcap" in seg
    assert "_rerr > _rcap" not in seg
    # A clean review resets the counter (only CONSECUTIVE failures count).
    assert "reset=True" in src
