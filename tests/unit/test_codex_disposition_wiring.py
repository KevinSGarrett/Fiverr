"""The controller's per-tick Codex disposition (audit BLOCKER 2 wiring).

`_maybe_dispatch_codex_repair` decides, each AWAITING_CI_GREEN tick, whether the PR
is clean to merge, needs a repair dispatched, is still awaiting the reviewer, or
should escalate. These tests pin that decision table with all I/O seams mocked.
"""
from __future__ import annotations

import automation.ai_cycle_controller as ctl
import automation.codex_thread_reader as reader
import automation.codex_thread_resolver as resolver
from automation.codex_thread_reader import CodexDispositionResult, CodexThread


def _disp(threads, read_error=""):
    r = CodexDispositionResult(pr_number=1, threads=list(threads))
    r.read_error = read_error
    return r


def _thread():
    return CodexThread(thread_id="T1", is_resolved=False, is_outdated=False,
                       author="chatgpt-codex-connector", body="P1: fix foo.py:1")


def _wire(monkeypatch, *, threads, reviewed, repair_ok=True, counters=None):
    counters = counters if counters is not None else {}

    def _tc(key, *, increment=False, reset=False):
        if reset:
            counters[key] = 0
        elif increment:
            counters[key] = counters.get(key, 0) + 1
        return counters.get(key, 0)

    monkeypatch.setattr(ctl, "_tick_counter", _tc)
    monkeypatch.setattr(reader, "read_threads", lambda pr, *a, **k: _disp(threads))
    monkeypatch.setattr(reader, "codex_has_reviewed", lambda pr, *a, **k: reviewed)
    monkeypatch.setattr(resolver, "_resolve_already_fixed", lambda t: 0)
    monkeypatch.setattr(ctl, "_dispatch_codex_repair", lambda c, p: repair_ok)
    return counters


def test_clean_when_reviewed_and_no_threads(monkeypatch):
    _wire(monkeypatch, threads=[], reviewed=True)
    assert ctl._maybe_dispatch_codex_repair(84, 1) == "CLEAN"


def test_await_review_when_not_reviewed(monkeypatch):
    _wire(monkeypatch, threads=[], reviewed=False)
    assert ctl._maybe_dispatch_codex_repair(84, 1) == "AWAIT_REVIEW"


def test_escalate_when_review_wait_exhausted(monkeypatch):
    monkeypatch.setenv("CODEX_REVIEW_WAIT_MAX_TICKS", "2")
    counters = {"codex_review_wait_pr1": 2}  # already at cap; next increment > cap
    _wire(monkeypatch, threads=[], reviewed=False, counters=counters)
    assert ctl._maybe_dispatch_codex_repair(84, 1) == "ESCALATE"


def test_repairing_when_actionable_threads(monkeypatch):
    _wire(monkeypatch, threads=[_thread()], reviewed=True)
    assert ctl._maybe_dispatch_codex_repair(84, 1) == "REPAIRING"


def test_error_when_repair_dispatch_fails(monkeypatch):
    _wire(monkeypatch, threads=[_thread()], reviewed=True, repair_ok=False)
    assert ctl._maybe_dispatch_codex_repair(84, 1) == "ERROR"


def test_escalate_when_repair_budget_exhausted(monkeypatch):
    monkeypatch.setenv("CODEX_REPAIR_MAX_ROUNDS", "2")
    counters = {"codex_repair_pr1": 2}  # next increment > cap
    _wire(monkeypatch, threads=[_thread()], reviewed=True, counters=counters)
    assert ctl._maybe_dispatch_codex_repair(84, 1) == "ESCALATE"


def test_error_on_read_failure(monkeypatch):
    _wire(monkeypatch, threads=[], reviewed=True)
    monkeypatch.setattr(reader, "read_threads",
                        lambda pr, *a, **k: _disp([], read_error="gh down"))
    assert ctl._maybe_dispatch_codex_repair(84, 1) == "ERROR"
