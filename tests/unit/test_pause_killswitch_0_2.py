"""Item 0.2 — pause kill-switch tests.

Verifies that the autopilot pause sentinel actually stops the loop:
  * ``_write_pause`` always writes ``paused: true`` + reason + ts.
  * ``tick`` pauses on the sentinel's EXISTENCE — including legacy files with
    no ``paused`` key (the negative reproduction) and corrupt files (fail-safe).
  * ``pause-autopilot`` / ``resume-autopilot`` CLI commands round-trip.
  * Absence of the sentinel does NOT pause.

Relies on the conftest from item 0.4: ``AUTOPILOT_RUNNER_ROOT`` is redirected to
a per-session tmp root and a write-guard blocks writes under the live root.
"""
from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from automation import runner_paths
from automation.ai_cycle_controller import _write_pause, cli


def _pause_path():
    return runner_paths.state_dir() / "autopilot_paused.json"


def _tick_lock_path():
    return runner_paths.locks_dir() / "tick.lock"


@pytest.fixture(autouse=True)
def _clean_pause_file():
    """Ensure no stale sentinel / tick lock leaks between tests.

    The session-scoped tmp runner root is shared across tests, and tick writes a
    lock file it only releases on a full completion — a tick that returns early
    (e.g. on pause) leaves the lock behind, so we clear both before/after.
    """
    _pause_path().unlink(missing_ok=True)
    _tick_lock_path().unlink(missing_ok=True)
    yield
    _pause_path().unlink(missing_ok=True)
    _tick_lock_path().unlink(missing_ok=True)


def test_write_pause_sets_paused_true_and_reason():
    _write_pause("X")
    p = _pause_path()
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["paused"] is True
    assert data["reason"] == "X"
    assert "ts" in data and data["ts"]


def test_write_pause_includes_detail_when_given():
    _write_pause("Y", detail="boom" * 100)
    data = json.loads(_pause_path().read_text(encoding="utf-8"))
    assert data["reason"] == "Y"
    # detail is truncated to 200 chars
    assert data["detail"] == ("boom" * 100)[:200]


def test_reader_pauses_on_existence_without_paused_key():
    """NEGATIVE REPRODUCTION: a legacy sentinel with NO 'paused' key must pause.

    Before the fix, cmd_tick only paused when ``_pdata.get('paused')`` was truthy,
    so a legacy ``{"reason": ...}`` file was silently ignored. It must now pause.
    """
    p = _pause_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"reason": "CLAUDE_PM_PARTIAL", "ts": "2026-06-19T00:00:00+00:00"}),
        encoding="utf-8",
    )
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0
    assert "PAUSED" in result.output
    assert "CLAUDE_PM_PARTIAL" in result.output
    # Must NOT have dispatched / run a cycle — it returns before the state machine.
    assert "[TICK]" not in result.output
    assert "[TICK COMPLETE]" not in result.output


def test_reader_pauses_on_paused_true():
    p = _pause_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"paused": True, "reason": "manual_operator", "ts": "x"}),
        encoding="utf-8",
    )
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0
    assert "PAUSED" in result.output
    assert "[TICK COMPLETE]" not in result.output


def test_reader_pauses_on_corrupt_file():
    """Fail-safe: an unparseable sentinel must STILL pause (presence == paused)."""
    p = _pause_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{not valid json at all", encoding="utf-8")
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0
    assert "PAUSED" in result.output
    assert "[TICK COMPLETE]" not in result.output


def test_pause_then_resume_cli():
    runner = CliRunner()

    # pause-autopilot writes the sentinel with paused:true
    r1 = runner.invoke(cli, ["pause-autopilot", "--reason", "operator_test"])
    assert r1.exit_code == 0
    assert "PAUSED" in r1.output
    p = _pause_path()
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["paused"] is True
    assert data["reason"] == "operator_test"

    # resume-autopilot removes the sentinel
    r2 = runner.invoke(cli, ["resume-autopilot"])
    assert r2.exit_code == 0
    assert "RESUMED" in r2.output
    assert not p.exists()

    # resume again is idempotent (no error, no file)
    r3 = runner.invoke(cli, ["resume-autopilot"])
    assert r3.exit_code == 0
    assert not p.exists()


def test_no_pause_file_no_pause(monkeypatch):
    """Absence of the sentinel must NOT trigger a pause — tick proceeds past it.

    We short-circuit the heavy downstream by making the cycle-guard reconcile
    return a CORRECTED report, so tick aborts right after the pause check. The
    key assertion is that the PAUSED line is NOT printed.
    """
    assert not _pause_path().exists()

    import automation.cycle_authority as ca

    def _fake_reconcile(verbose: bool = True) -> dict:
        return {"action": "CORRECTED", "consensus": 75, "confidence": "HIGH"}

    monkeypatch.setattr(ca, "reconcile", _fake_reconcile)

    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0
    # It proceeded past the pause check (no PAUSED line) into the cycle guard.
    assert "PAUSED" not in result.output
    assert "CYCLE GUARD" in result.output


def test_pause_does_not_acquire_lock(monkeypatch, tmp_path):
    """A paused tick must NOT create/leak tick.lock (pause check precedes lock)."""
    import json as _json
    from click.testing import CliRunner
    from automation import runner_paths
    from automation.ai_cycle_controller import cli

    state_dir = runner_paths.state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "autopilot_paused.json").write_text(
        _json.dumps({"reason": "manual_operator", "ts": "t"}), encoding="utf-8"
    )
    lock_file = runner_paths.locks_dir() / "tick.lock"
    if lock_file.exists():
        lock_file.unlink()
    result = CliRunner().invoke(cli, ["tick"])
    assert "PAUSED" in result.output
    assert not lock_file.exists(), "paused tick must not create tick.lock"
