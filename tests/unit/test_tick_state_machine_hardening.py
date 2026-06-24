"""Audit cluster A + state-machine no-dead-end hardening (tick).

Pins: the tick lock is released on EVERY early return (cluster A — else the state
machine freezes up to 600s); PR_CREATE_FAILED retry is bounded (else an expired
token loops forever); BLOCKED_EXPORT_SECRETS holds for the operator (never silently
resets to IDLE + re-dispatches the staged secret); AWAITING_DISPATCH recovers.
"""
from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from automation import runner_paths
from automation.ai_cycle_controller import cli
from automation.state_writer import write_controller_state


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch):
    def _wipe():
        for n in ("controller_state.json", "tick_counters.json"):
            try:
                (runner_paths.state_dir() / n).unlink()
            except OSError:
                pass
        try:
            (runner_paths.locks_dir() / "tick.lock").unlink()
        except OSError:
            pass
    _wipe()
    # Silence notifications (their real impl writes under the live runner root).
    import automation.notification_router as nr
    monkeypatch.setattr(nr, "notify_blocked", lambda *a, **k: None)
    monkeypatch.setattr(nr, "notify_info", lambda *a, **k: None)
    yield
    _wipe()


@pytest.fixture
def no_drift(monkeypatch):
    import automation.cycle_authority as ca
    monkeypatch.setattr(ca, "reconcile", lambda **k: {"action": "OK", "consensus": None})
    return monkeypatch


def _state() -> dict:
    return json.loads((runner_paths.state_dir() / "controller_state.json").read_text())


def _lock_exists() -> bool:
    return (runner_paths.locks_dir() / "tick.lock").exists()


# ── cluster A: tick lock released on early returns ─────────────────────────────
def test_lock_released_on_cycle_guard_correction(monkeypatch):
    # reconcile returns CORRECTED → the tick early-returns at the CYCLE_GUARD path.
    # That return previously skipped the lock release → 10-min freeze. Now released.
    import automation.cycle_authority as ca
    monkeypatch.setattr(ca, "reconcile",
                        lambda **k: {"action": "CORRECTED", "consensus": 99, "confidence": 1.0})
    write_controller_state("IDLE", cycle=50)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert not _lock_exists(), "tick lock LEAKED on the CYCLE_GUARD early return"


def test_lock_released_on_normal_tick(no_drift, monkeypatch):
    # A normal terminal-state tick must also leave no lock behind (epilogue release).
    write_controller_state("MERGE_BLOCKED", cycle=51)  # no active_pr → quick terminal path
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert not _lock_exists(), "tick lock LEAKED on the normal epilogue path"


# ── #5: PR_CREATE_FAILED bounded retry ─────────────────────────────────────────
def test_pr_create_failed_escalates_after_cap(no_drift, monkeypatch):
    from automation import pr_builder
    calls = {"n": 0}
    monkeypatch.setattr(pr_builder, "open_cycle_pr",
                        lambda *a, **k: (calls.__setitem__("n", calls["n"] + 1)
                                         or {"created": False, "error": "401"}))
    monkeypatch.setenv("AUTOPILOT_PR_CREATE_RETRY_MAX", "2")
    sd = runner_paths.state_dir()
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "tick_counters.json").write_text(json.dumps({"pr_create_retry_60": 2}))
    write_controller_state("PR_CREATE_FAILED", cycle=60)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "PR_CREATE_FAILED"  # held, not advanced
    assert calls["n"] == 0, "must STOP re-attempting open_cycle_pr after the cap"


def test_pr_create_failed_retries_under_cap(no_drift, monkeypatch):
    from automation import pr_builder
    calls = {"n": 0}
    monkeypatch.setattr(pr_builder, "open_cycle_pr",
                        lambda *a, **k: (calls.__setitem__("n", calls["n"] + 1)
                                         or {"created": True, "pr_number": 1234, "url": "u"}))
    write_controller_state("PR_CREATE_FAILED", cycle=61)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert calls["n"] == 1, "must re-attempt open_cycle_pr while under the cap"
    assert _state()["status"] == "AGENT_COMPLETE"  # recovered


# ── #16: BLOCKED_EXPORT_SECRETS holds (never silent IDLE reset) ─────────────────
def test_blocked_export_secrets_holds_for_operator(no_drift, monkeypatch):
    write_controller_state("BLOCKED_EXPORT_SECRETS", cycle=62)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    # Must NOT silently reset to IDLE (which would re-dispatch with the secret staged).
    assert _state()["status"] == "BLOCKED_EXPORT_SECRETS"


# ── #21: AWAITING_DISPATCH recovers ────────────────────────────────────────────
def test_awaiting_dispatch_recovers(no_drift, monkeypatch):
    write_controller_state("AWAITING_DISPATCH", cycle=63)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "READY_TO_DISPATCH"  # not the 'Unknown status -> IDLE' path
