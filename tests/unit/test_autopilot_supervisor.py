"""Tests for autopilot_supervisor — the 24/7 process-level keep-alive.

The supervisor restarts the autopilot when its process dies (observed live: the autopilot
vanished when its host shell was terminated). These tests drive the supervise() loop with
injected runner/sleeper/clock so nothing real spawns or sleeps.
"""
from __future__ import annotations

import automation.autopilot_supervisor as sup


class _Clock:
    def __init__(self):
        self.t = 0.0
    def __call__(self):
        return self.t
    def advance(self, d):
        self.t += d


def _runner(rc, duration, clock, calls):
    def _r(cmd, env):
        calls.append(cmd)
        clock.advance(duration)
        return rc
    return _r


def _no_stop(monkeypatch, tmp_path):
    """Point the stop sentinel at a path that does not exist (loop proceeds)."""
    monkeypatch.setattr(sup, "_stop_path", lambda: tmp_path / "nope.stop")


def _not_frozen(monkeypatch):
    monkeypatch.setattr(sup, "freeze_state", lambda: (False, "policy_missing"))


# ── restart behaviour ─────────────────────────────────────────────────────────
def test_restarts_autopilot_on_each_exit(monkeypatch, tmp_path):
    _no_stop(monkeypatch, tmp_path)
    _not_frozen(monkeypatch)
    monkeypatch.setattr(sup, "acquire_singleton", lambda: True)
    monkeypatch.setattr(sup, "release_singleton", lambda: None)
    clock = _Clock()
    calls, sleeps = [], []
    runner = _runner(0, 700, clock, calls)  # long, healthy runs (>fast_window)
    sup.supervise(max_loops=3, runner=runner, sleeper=sleeps.append, clock=clock,
                  base_backoff=30, fast_window_s=600)
    assert len(calls) == 3, "autopilot restarted on every exit"
    assert sleeps == [30, 30, 30], "healthy runs → base backoff, no storm escalation"


def test_storm_guard_backs_off_on_fast_exits(monkeypatch, tmp_path):
    _no_stop(monkeypatch, tmp_path)
    _not_frozen(monkeypatch)
    monkeypatch.setattr(sup, "acquire_singleton", lambda: True)
    monkeypatch.setattr(sup, "release_singleton", lambda: None)
    clock = _Clock()
    calls, sleeps = [], []
    runner = _runner(1, 1, clock, calls)  # crash instantly every time (<fast_window)
    sup.supervise(max_loops=8, runner=runner, sleeper=sleeps.append, clock=clock,
                  base_backoff=30, fast_window_s=600, max_fast_restarts=5)
    assert len(calls) == 8
    # first 4 fast exits stay at base backoff; once the window hits max_fast_restarts (5),
    # backoff escalates beyond base (exponential, capped at 1800).
    assert sleeps[0] == 30 and sleeps[3] == 30
    assert max(sleeps) > 30, "a restart storm must escalate the backoff"
    assert max(sleeps) <= 1800, "backoff stays capped"


def test_healthy_long_run_resets_storm_counter(monkeypatch, tmp_path):
    _no_stop(monkeypatch, tmp_path)
    _not_frozen(monkeypatch)
    monkeypatch.setattr(sup, "acquire_singleton", lambda: True)
    monkeypatch.setattr(sup, "release_singleton", lambda: None)
    clock = _Clock()
    calls, sleeps = [], []
    # alternate: a long healthy run should clear the fast-restart deque
    seq = iter([1, 1, 1, 700])  # 3 fast crashes then a healthy run
    def runner(cmd, env):
        calls.append(cmd)
        dur = next(seq)
        clock.advance(dur)
        return 0 if dur > 100 else 1
    sup.supervise(max_loops=4, runner=runner, sleeper=sleeps.append, clock=clock,
                  base_backoff=30, fast_window_s=600, max_fast_restarts=5)
    assert len(calls) == 4


# ── stop sentinel ──────────────────────────────────────────────────────────────
def test_stop_sentinel_prevents_run(monkeypatch, tmp_path):
    _not_frozen(monkeypatch)
    monkeypatch.setattr(sup, "acquire_singleton", lambda: True)
    monkeypatch.setattr(sup, "release_singleton", lambda: None)
    stop = tmp_path / "supervisor.stop"
    stop.write_text("stop")
    monkeypatch.setattr(sup, "_stop_path", lambda: stop)
    calls = []
    sup.supervise(max_loops=5, runner=lambda c, e: calls.append(c) or 0,
                  sleeper=lambda s: None, clock=_Clock())
    assert calls == [], "stop sentinel must prevent the autopilot from launching"


# ── freeze handling ─────────────────────────────────────────────────────────────
def test_breaker_freeze_cools_down_clears_and_retries(monkeypatch, tmp_path):
    _no_stop(monkeypatch, tmp_path)
    monkeypatch.setattr(sup, "acquire_singleton", lambda: True)
    monkeypatch.setattr(sup, "release_singleton", lambda: None)
    # frozen by the circuit breaker on the first loop, then cleared.
    states = iter([(True, "circuit_breaker: 10 consecutive failed ticks"), (False, "ok")])
    monkeypatch.setattr(sup, "freeze_state", lambda: next(states))
    cleared = {"n": 0}
    monkeypatch.setattr(sup, "clear_freeze", lambda: cleared.__setitem__("n", cleared["n"] + 1))
    clock = _Clock()
    calls, sleeps = [], []
    runner = _runner(0, 700, clock, calls)
    sup.supervise(max_loops=2, runner=runner, sleeper=sleeps.append, clock=clock,
                  breaker_cooldown_s=1800)
    assert cleared["n"] == 1, "breaker freeze must be auto-cleared after cooldown"
    assert 1800 in sleeps, "must cool down before clearing"
    assert len(calls) == 1, "after clearing, the next loop runs the autopilot"


def test_manual_freeze_is_respected(monkeypatch, tmp_path):
    _no_stop(monkeypatch, tmp_path)
    monkeypatch.setattr(sup, "acquire_singleton", lambda: True)
    monkeypatch.setattr(sup, "release_singleton", lambda: None)
    monkeypatch.setattr(sup, "freeze_state", lambda: (True, "operator pressed stop"))
    cleared = {"n": 0}
    monkeypatch.setattr(sup, "clear_freeze", lambda: cleared.__setitem__("n", cleared["n"] + 1))
    calls, sleeps = [], []
    sup.supervise(max_loops=3, runner=lambda c, e: calls.append(c) or 0,
                  sleeper=sleeps.append, clock=_Clock(), manual_freeze_idle_s=300)
    assert calls == [], "a human freeze must NOT launch the autopilot"
    assert cleared["n"] == 0, "a human freeze must NOT be auto-cleared"
    assert sleeps == [300, 300, 300], "idle on each loop, re-checking for unfreeze"


def test_is_breaker_freeze_classifier():
    assert sup.is_breaker_freeze("circuit_breaker: 10 consecutive failed ticks") is True
    assert sup.is_breaker_freeze("CIRCUIT_BREAKER: x") is True
    assert sup.is_breaker_freeze("operator manual stop") is False
    assert sup.is_breaker_freeze("") is False


# ── singleton ──────────────────────────────────────────────────────────────────
def test_singleton_refuses_when_live_holder(monkeypatch, tmp_path):
    monkeypatch.setattr(sup, "_lock_path", lambda: tmp_path / "supervisor.lock")
    (tmp_path / "supervisor.lock").write_text("999999")  # a different pid
    monkeypatch.setattr(sup, "_pid_alive", lambda pid: True)  # pretend it's alive
    assert sup.acquire_singleton() is False


def test_singleton_acquires_when_holder_dead(monkeypatch, tmp_path):
    lock = tmp_path / "supervisor.lock"
    monkeypatch.setattr(sup, "_lock_path", lambda: lock)
    lock.write_text("999999")
    monkeypatch.setattr(sup, "_pid_alive", lambda pid: False)  # stale holder
    assert sup.acquire_singleton() is True
    assert lock.read_text().strip() == str(__import__("os").getpid())
