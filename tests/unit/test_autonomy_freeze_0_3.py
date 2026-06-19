"""Item 0.3 — autonomy-freeze wiring + removal of the PYTEST production short-circuit.

Covers:
  * ``_run_and_stream`` has NO PYTEST early-return and runs a REAL subprocess
    (proving a leaked env var can no longer silently no-op a dispatch).
  * The SAFE-01 autonomy-freeze kill-switch blocks ``tick`` when frozen.
  * ``freeze`` / ``unfreeze`` CLI commands round-trip the policy file.
  * The fail-closed ENTRY GUARD refuses ``tick`` when ``PYTEST_CURRENT_TEST`` is
    set but the test harness opt-in is NOT (a leaked var → fail closed).
  * ``model_gate.check`` runs real logic (no PYTEST auto-pass).
  * ``codex_verifier`` config is not force-disabled solely because PYTEST is set.

Relies on the global conftest: ``AUTOPILOT_RUNNER_ROOT`` is redirected to a
per-session tmp root, ``AUTOPILOT_TEST_HARNESS=1`` is set for the session, and
``_run_and_stream`` is faked autouse (restored explicitly where needed below).
"""
from __future__ import annotations

import inspect
import sys

import pytest
import yaml
from click.testing import CliRunner

from automation import runner_paths
import automation.ai_cycle_controller as ctrl
from automation.ai_cycle_controller import cli


def _tick_lock_path():
    return runner_paths.locks_dir() / "tick.lock"


@pytest.fixture(autouse=True)
def _clean_locks():
    """Clear any tick lock leaked by an early-returning tick between tests."""
    _tick_lock_path().unlink(missing_ok=True)
    (runner_paths.state_dir() / "autopilot_paused.json").unlink(missing_ok=True)
    yield
    _tick_lock_path().unlink(missing_ok=True)
    (runner_paths.state_dir() / "autopilot_paused.json").unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# B4: _run_and_stream — no PYTEST short-circuit, real subprocess.
# ---------------------------------------------------------------------------
def _load_real_run_and_stream():
    """Recover the genuine _run_and_stream impl.

    The autouse conftest fixture monkeypatches the module attribute with a fake,
    so re-import the controller fresh under a throwaway name and return its
    untouched ``_run_and_stream``.
    """
    import importlib.util
    from pathlib import Path

    mod_path = Path(ctrl.__file__)
    spec = importlib.util.spec_from_file_location("_acc_real_for_test", mod_path)
    assert spec and spec.loader
    fresh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fresh)
    return fresh._run_and_stream


def test_run_and_stream_no_pytest_shortcircuit():
    """The REAL _run_and_stream spawns a subprocess and returns its rc.

    1) Source must not contain a PYTEST_CURRENT_TEST early-return.
    2) Calling the genuine impl with a harmless local command returns rc 0 from
       an ACTUAL subprocess — proving there is no silent short-circuit.
    """
    # (1) Source inspection — confirm the production body has no env *branch*.
    # (Comments/docstrings may mention the var by name; we look for the code
    # form ``environ.get("PYTEST_CURRENT_TEST")`` which signals an actual read.)
    src = inspect.getsource(ctrl)
    start = src.index("def _run_and_stream(")
    nxt = src.index("\ndef ", start + 1)
    body = src[start:nxt]
    assert 'environ.get("PYTEST_CURRENT_TEST")' not in body
    assert "environ.get('PYTEST_CURRENT_TEST')" not in body

    # (2) Run a harmless local command through the real implementation.
    real = _load_real_run_and_stream()
    rc, out = real([sys.executable, "-c", "print(1)"], label="probe")
    assert rc == 0
    assert "1" in out


# ---------------------------------------------------------------------------
# A2: frozen state blocks tick (fail closed, no dispatch, no lock).
# ---------------------------------------------------------------------------
def test_frozen_blocks_tick(tmp_path, monkeypatch):
    policy = tmp_path / "autonomy_freeze.yml"
    policy.write_text(
        yaml.safe_dump({"frozen": True, "reason": "TEST_FREEZE"}), encoding="utf-8"
    )
    monkeypatch.setattr(ctrl, "_autonomy_freeze_path", lambda: policy)

    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0
    assert "FROZEN" in result.output
    assert "TEST_FREEZE" in result.output
    # Fail closed: no dispatch, did not reach the state machine, no lock created.
    assert "[TICK]" not in result.output
    assert "[TICK COMPLETE]" not in result.output
    assert not _tick_lock_path().exists()


def test_not_frozen_does_not_block_tick(tmp_path, monkeypatch):
    """frozen: false must NOT block — tick proceeds past the freeze check."""
    policy = tmp_path / "autonomy_freeze.yml"
    policy.write_text(
        yaml.safe_dump({"frozen": False, "reason": "OK"}), encoding="utf-8"
    )
    monkeypatch.setattr(ctrl, "_autonomy_freeze_path", lambda: policy)

    # Short-circuit the heavy downstream right after the freeze check via the
    # cycle-guard reconcile returning CORRECTED.
    import automation.cycle_authority as ca
    monkeypatch.setattr(
        ca, "reconcile",
        lambda verbose=True: {"action": "CORRECTED", "consensus": 75, "confidence": "HIGH"},
    )
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0
    assert "FROZEN" not in result.output
    assert "CYCLE GUARD" in result.output


def test_missing_policy_is_not_frozen(tmp_path, monkeypatch):
    """Fail-safe: a missing policy must be treated as NOT frozen (warns, runs)."""
    missing = tmp_path / "does_not_exist.yml"
    monkeypatch.setattr(ctrl, "_autonomy_freeze_path", lambda: missing)
    frozen, reason = ctrl._is_frozen()
    assert frozen is False
    assert reason == "policy_missing"


# ---------------------------------------------------------------------------
# A3: freeze / unfreeze CLI round-trip.
# ---------------------------------------------------------------------------
def test_freeze_unfreeze_cli_roundtrip(tmp_path, monkeypatch):
    policy = tmp_path / "autonomy_freeze.yml"
    # Seed with realistic extra keys to prove they are preserved.
    policy.write_text(
        yaml.safe_dump(
            {"frozen": False, "reason": "START", "incident_ref": "KEEP_ME"}
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(ctrl, "_autonomy_freeze_path", lambda: policy)
    runner = CliRunner()

    r1 = runner.invoke(cli, ["freeze", "--reason", "operator_test_freeze"])
    assert r1.exit_code == 0
    assert "FROZEN" in r1.output
    data = yaml.safe_load(policy.read_text(encoding="utf-8"))
    assert data["frozen"] is True
    assert data["reason"] == "operator_test_freeze"
    assert data["incident_ref"] == "KEEP_ME"  # other keys preserved
    assert "frozen_at" in data

    r2 = runner.invoke(cli, ["unfreeze", "--reason", "operator_test_unfreeze"])
    assert r2.exit_code == 0
    assert "UNFROZEN" in r2.output
    data2 = yaml.safe_load(policy.read_text(encoding="utf-8"))
    assert data2["frozen"] is False
    assert data2["reason"] == "operator_test_unfreeze"
    assert data2["incident_ref"] == "KEEP_ME"
    assert "unfrozen_at" in data2


# ---------------------------------------------------------------------------
# B5: fail-closed entry guard against a leaked PYTEST var.
# ---------------------------------------------------------------------------
def test_entry_guard_refuses_on_leaked_pytest_without_harness(monkeypatch):
    """PYTEST_CURRENT_TEST set + AUTOPILOT_TEST_HARNESS UNSET → REFUSE, no dispatch."""
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "leaked_value")
    monkeypatch.delenv("AUTOPILOT_TEST_HARNESS", raising=False)

    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0
    assert "REFUSE" in result.output
    # Fail closed: did not reach pause/state machine, no lock acquired.
    assert "[TICK]" not in result.output
    assert not _tick_lock_path().exists()


def test_entry_guard_allows_with_harness(monkeypatch):
    """With the harness opt-in set (normal test condition) tick proceeds."""
    # Harness is set session-wide by conftest; assert the guard does not refuse.
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "present")
    monkeypatch.setenv("AUTOPILOT_TEST_HARNESS", "1")
    import automation.cycle_authority as ca
    monkeypatch.setattr(
        ca, "reconcile",
        lambda verbose=True: {"action": "CORRECTED", "consensus": 75, "confidence": "HIGH"},
    )
    result = CliRunner().invoke(cli, ["tick"])
    assert "REFUSE" not in result.output


def test_entry_guard_refuses_run_cycle_on_leaked_pytest(monkeypatch):
    """run-cycle also fails closed on a leaked var without the harness."""
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "leaked_value")
    monkeypatch.delenv("AUTOPILOT_TEST_HARNESS", raising=False)
    result = CliRunner().invoke(cli, ["run-cycle", "--cycle", "84"])
    assert result.exit_code == 1
    assert "REFUSE" in result.output


# ---------------------------------------------------------------------------
# B6: model_gate runs real logic (no PYTEST auto-pass).
# ---------------------------------------------------------------------------
def test_model_gate_runs_without_pytest_shortcircuit(monkeypatch):
    """model_gate.check evaluates the real state instead of returning SKIPPED.

    Source must not auto-pass on PYTEST_CURRENT_TEST; with a non-VERIFIED state
    the gate must FAIL (real evaluation), and with a fully-VERIFIED fresh state
    the model/effort/auto checks must pass.
    """
    import automation.model_gate as mg

    # Source inspection — the auto-pass branch is gone.
    src = inspect.getsource(mg.check)
    assert "SKIPPED (test environment)" not in src
    assert 'environ.get("PYTEST_CURRENT_TEST")' not in src

    # Non-VERIFIED state → real failure (not an auto-pass).
    monkeypatch.setattr(mg, "_load_cursor_state", lambda *a, **k: {"status": "STALE"})
    bad = mg.check(repo_root=None, cycle=75, agent="A")
    assert bad.passed is False
    assert any("VERIFIED" in f for f in bad.failures)

    # Fully-verified fresh state → the model/effort/auto/age checks all pass.
    from datetime import UTC, datetime
    good_state = {
        "status": "VERIFIED",
        "observed_model": "Codex 5.3",
        "observed_effort": "medium",
        "auto_model_disabled": True,
        "verified_at": datetime.now(UTC).isoformat(),
    }
    monkeypatch.setattr(mg, "_load_cursor_state", lambda *a, **k: good_state)
    # repo_root=None skips the git-remote check; the rest is real evaluation.
    good = mg.check(repo_root=None, cycle=75, agent="A")
    assert good.passed is True
    assert good.observed_model == "Codex 5.3"


# ---------------------------------------------------------------------------
# B6: ICV config not force-disabled by PYTEST.
# ---------------------------------------------------------------------------
def test_icv_config_not_force_disabled_by_pytest(monkeypatch):
    """Setting PYTEST_CURRENT_TEST must NOT force-cap/disable the ICV config."""
    import automation.codex_verifier.config as cfgmod

    # Source inspection — the PYTEST force-disable block is gone (we look for
    # the code form, since the explanatory comment names the var).
    src = inspect.getsource(cfgmod.ICVConfig.__post_init__)
    assert 'environ.get("PYTEST_CURRENT_TEST")' not in src
    assert "environ.get('PYTEST_CURRENT_TEST')" not in src

    monkeypatch.setenv("PYTEST_CURRENT_TEST", "present")
    monkeypatch.delenv("ICV_MAX_ATTEMPTS", raising=False)
    monkeypatch.delenv("ICV_DISABLED", raising=False)
    cfg = cfgmod.ICVConfig()
    # Real defaults preserved (not forced to the old test values 1 / 0.0).
    assert cfg.max_attempts == 3
    assert cfg.openai_budget_usd == 2.0


def test_run_agent_refuses_when_frozen(monkeypatch):
    """Codex P1: direct run-agent (real dispatch) must fail closed when frozen."""
    from click.testing import CliRunner
    import automation.ai_cycle_controller as ctrl
    monkeypatch.setattr(ctrl, "_is_frozen", lambda: (True, "test_freeze"))
    r = CliRunner().invoke(ctrl.cli, ["run-agent", "--agent", "A", "--cycle", "82"])
    assert r.exit_code != 0
    assert "FROZEN" in r.output


def test_run_agent_dry_run_allowed_when_frozen(monkeypatch):
    """--dry-run is non-dispatching and is permitted while frozen (no FROZEN refuse)."""
    from click.testing import CliRunner
    import automation.ai_cycle_controller as ctrl
    monkeypatch.setattr(ctrl, "_is_frozen", lambda: (True, "test_freeze"))
    r = CliRunner().invoke(ctrl.cli, ["run-agent", "--agent", "A", "--cycle", "82", "--dry-run"])
    # Dry-run must NOT be refused by the freeze guard (it may still fail later for
    # missing prompt etc., but the FROZEN refuse must not fire).
    assert "Autonomy freeze active" not in r.output


def test_run_agent_refuses_on_leaked_pytest(monkeypatch):
    """Direct run-agent refuses when PYTEST leaked without the test harness."""
    from click.testing import CliRunner
    import automation.ai_cycle_controller as ctrl
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "leaked")
    monkeypatch.delenv("AUTOPILOT_TEST_HARNESS", raising=False)
    r = CliRunner().invoke(ctrl.cli, ["run-agent", "--agent", "A", "--cycle", "82"])
    assert r.exit_code != 0
    assert "REFUSE" in r.output
