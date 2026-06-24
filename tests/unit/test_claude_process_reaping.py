"""Observed-live: reap the claude process TREE + hard-timeout a hung tick.

Bug seen on the live runner: a stalled Claude prompt-gen call timed out, but
`proc.kill()` reaped only the DIRECT child — the claude CLI's grandchildren (node
workers) orphaned and kept running, accumulating across runs (10+ runaway claude
procs, ~29h old, hours of CPU each). And the parent autopilot loop blocked forever
on `for _line in _proc.stdout` of a hung tick, so the circuit breaker could never
trip. Fixes: _kill_process_tree reaps the whole tree on timeout; the autopilot
guards each tick with a state-aware hard-timeout watchdog.
"""
from __future__ import annotations

import inspect
import os
import subprocess

import automation.claude_prompt_creator as cpc


# ---- _kill_process_tree --------------------------------------------------

def test_kill_tree_none_is_noop(monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: calls.append(a))
    cpc._kill_process_tree(None)
    cpc._kill_process_tree(0)
    assert calls == [], "a falsy pid must be a no-op (no subprocess)"


def test_kill_tree_windows_uses_taskkill_T(monkeypatch):
    """On Windows, reap the whole tree via `taskkill /PID <pid> /T /F`."""
    monkeypatch.setattr(os, "name", "nt")
    captured = {}
    monkeypatch.setattr(subprocess, "run",
                        lambda args, **k: captured.update(args=list(args)))
    cpc._kill_process_tree(4321)
    a = captured["args"]
    assert a[0] == "taskkill"
    assert "/T" in a and "/F" in a, "must kill the TREE (/T), forcibly (/F)"
    assert "4321" in a


def test_kill_tree_posix_uses_killpg(monkeypatch):
    """Codex P1: on POSIX, kill the whole process GROUP (not just the pid) so claude/
    node grandchildren die too."""
    monkeypatch.setattr(os, "name", "posix")
    monkeypatch.setattr(os, "getpgid", lambda pid: pid, raising=False)
    killed = {}
    monkeypatch.setattr(os, "killpg",
                        lambda pgid, sig: killed.update(pgid=pgid), raising=False)
    monkeypatch.setattr(os, "kill",
                        lambda *a: killed.update(fellback=True), raising=False)
    cpc._kill_process_tree(777)
    assert killed.get("pgid") == 777, "must killpg the process group"
    assert not killed.get("fellback"), "killpg succeeded → must not fall back to os.kill"


def test_kill_tree_posix_falls_back_to_kill(monkeypatch):
    """If the pid isn't a group leader (getpgid/killpg fail), fall back to os.kill."""
    monkeypatch.setattr(os, "name", "posix")
    def _no_pgid(pid):
        raise ProcessLookupError()
    monkeypatch.setattr(os, "getpgid", _no_pgid, raising=False)
    killed = {}
    monkeypatch.setattr(os, "kill", lambda pid, sig: killed.update(pid=pid), raising=False)
    cpc._kill_process_tree(555)
    assert killed.get("pid") == 555


def test_kill_tree_never_raises(monkeypatch):
    """Best-effort: a failing taskkill/os.kill must be swallowed, never propagate."""
    monkeypatch.setattr(os, "name", "nt")
    def boom(*a, **k):
        raise OSError("nope")
    monkeypatch.setattr(subprocess, "run", boom)
    cpc._kill_process_tree(123)  # must not raise


# ---- _call_claude_pm reaps the tree on timeout ---------------------------

def test_call_claude_pm_timeout_reaps_tree():
    """The prompt-gen timeout path must reap the tree (not the orphan-leaking
    bare proc.kill())."""
    src = inspect.getsource(cpc._call_claude_pm)
    ti = src.index("except subprocess.TimeoutExpired")
    seg = src[ti:ti + 400]
    assert "_kill_process_tree(proc.pid)" in seg
    # the old single-process kill must be gone as an ACTUAL statement (a comment may
    # still mention it for context) — check no bare `proc.kill()` call line remains.
    code_lines = [ln.split("#", 1)[0].strip() for ln in seg.splitlines()]
    assert "proc.kill()" not in code_lines


# ---- autopilot tick hard-timeout watchdog --------------------------------

def test_subprocesses_lead_new_session_on_posix():
    """Codex P1: both the claude prompt-gen and the tick subprocess must launch with
    start_new_session=True (POSIX) so killpg can reap their whole tree."""
    import automation.ai_cycle_controller as ctrl
    csrc = inspect.getsource(cpc._call_claude_pm)
    assert "start_new_session" in csrc
    tsrc = inspect.getsource(ctrl.cmd_start_autopilot.callback)
    assert "start_new_session" in tsrc


def test_autopilot_tick_has_hard_timeout_watchdog():
    import automation.ai_cycle_controller as ctrl
    src = inspect.getsource(ctrl.cmd_start_autopilot.callback)
    # state-aware timeout envs (long for dispatch, short for planning/review/merge)
    assert "AUTOPILOT_TICK_TIMEOUT_SEC" in src
    assert "AUTOPILOT_DISPATCH_TICK_TIMEOUT_SEC" in src
    # watchdog kills the tick TREE
    assert "_tick_watchdog" in src
    assert "_kill_process_tree" in src
    # a timed-out tick is counted as a failed tick so the breaker can trip: the
    # HARD-TIMEOUT branch must increment consecutive_tick_failures.
    hi = src.index("HARD-TIMEOUT")
    seg = src[hi:hi + 400]
    assert "consecutive_tick_failures += 1" in seg
