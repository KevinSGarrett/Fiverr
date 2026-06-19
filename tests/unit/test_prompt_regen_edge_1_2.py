"""Item 1.2 — bounded regenerate edge on PROMPT_VALIDATION_FAILED.

Proves the wedge is gone: a rejected prompt no longer pins the loop in
PROMPT_VALIDATION_FAILED forever. Instead the tick forces a *bounded* number of
regeneration attempts (env ``PROMPT_REGEN_MAX_ATTEMPTS``, default 3) and then
FAILS CLOSED into ``PROMPT_REGEN_EXHAUSTED`` with an alert — never an infinite
auto-retry. ``recover --regen`` resets the attempt counter and clears the
exhausted state back to COMPILED so the next tick re-attempts.

No real Claude / network: the regeneration call is monkeypatched and
``validate_all`` is monkeypatched to drive pass/fail deterministically.

Relies on the global conftest: ``AUTOPILOT_RUNNER_ROOT`` is redirected to a
per-session tmp root, ``AUTOPILOT_TEST_HARNESS=1`` is set, ``_run_and_stream``
is faked, and all runner writes land under tmp.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest
from click.testing import CliRunner

import automation.ai_cycle_controller as ctrl
import automation.prompt_validator as pv
from automation import runner_paths
from automation.ai_cycle_controller import cli
from automation.state_writer import write_controller_state


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------
_AGENTS = ["A", "B", "E", "C", "F", "D"]


@dataclass
class _FakeResult:
    passed: bool


def _all_pass() -> dict:
    return {a: _FakeResult(passed=True) for a in _AGENTS}


def _some_fail(failing: list[str]) -> dict:
    return {a: _FakeResult(passed=a not in failing) for a in _AGENTS}


@pytest.fixture(autouse=True)
def _quiet_notifications(monkeypatch):
    """No-op the notification writers so the per-test write-guard isn't tripped.

    ``notification_router`` is imported lazily inside ``cmd_tick`` (after the
    conftest path-isolation fixture has run), so its real-root Path constants may
    not be redirected — its file writes would hit the live runner root and the
    write-guard would (correctly) raise. Tests that assert on a notification
    re-patch the specific function they care about.
    """
    import automation.notification_router as nr
    monkeypatch.setattr(nr, "notify_info", lambda *a, **k: None, raising=False)
    monkeypatch.setattr(nr, "notify_blocked", lambda *a, **k: None, raising=False)
    monkeypatch.setattr(nr, "notify", lambda *a, **k: None, raising=False)


@pytest.fixture(autouse=True)
def _clean_state():
    """Clear tick lock, pause sentinel and regen-state file between tests."""
    state_dir = runner_paths.state_dir()
    (runner_paths.locks_dir() / "tick.lock").unlink(missing_ok=True)
    (state_dir / "autopilot_paused.json").unlink(missing_ok=True)
    (state_dir / "prompt_regen_state.json").unlink(missing_ok=True)
    (state_dir / "controller_state.json").unlink(missing_ok=True)
    yield
    (runner_paths.locks_dir() / "tick.lock").unlink(missing_ok=True)
    (state_dir / "autopilot_paused.json").unlink(missing_ok=True)
    (state_dir / "prompt_regen_state.json").unlink(missing_ok=True)
    (state_dir / "controller_state.json").unlink(missing_ok=True)


def _set_status(status: str, cycle: int = 84) -> None:
    write_controller_state(status, cycle=cycle)


def _read_status() -> dict:
    return ctrl._read_runner_state()


# ---------------------------------------------------------------------------
# test_regen_attempt_increments
# ---------------------------------------------------------------------------
def test_regen_attempt_increments(monkeypatch):
    """One tick from PROMPT_VALIDATION_FAILED with regen kept failing:
    attempt counter increments, status stays PROMPT_VALIDATION_FAILED, and the
    regen call was invoked for the failing agents."""
    _set_status("PROMPT_VALIDATION_FAILED", cycle=84)
    monkeypatch.setenv("PROMPT_REGEN_MAX_ATTEMPTS", "3")

    # validate_all always reports B + D failing (both before and after regen).
    monkeypatch.setattr(pv, "validate_all",
                        lambda *a, **k: _some_fail(["B", "D"]))

    regen_calls: list[tuple[int, list[str]]] = []

    def _fake_regen(cycle, failing):
        regen_calls.append((cycle, list(failing)))
        return 0

    monkeypatch.setattr(ctrl, "_force_regenerate_failing_prompts", _fake_regen)

    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output

    # Counter incremented to 1.
    st = ctrl._read_prompt_regen_state(84)
    assert st["attempts"] == 1, result.output

    # Status stays blocked (still failing after regen).
    assert _read_status()["status"] == "PROMPT_VALIDATION_FAILED", result.output

    # Regen was called for the failing agents only.
    assert regen_calls, "regen not called"
    assert regen_calls[0][0] == 84
    assert set(regen_calls[0][1]) == {"B", "D"}


# ---------------------------------------------------------------------------
# test_regen_heals_when_revalidation_passes
# ---------------------------------------------------------------------------
def test_regen_heals_when_revalidation_passes(monkeypatch):
    """Regen fixes the prompts → post-regen validation passes → PLANNED, and the
    attempt counter is reset to 0."""
    _set_status("PROMPT_VALIDATION_FAILED", cycle=84)
    monkeypatch.setenv("PROMPT_REGEN_MAX_ATTEMPTS", "3")

    # First validate_all call (pre-regen): fail. After regen runs: pass.
    calls = {"n": 0}
    healed = {"done": False}

    def _validate(*a, **k):
        calls["n"] += 1
        if healed["done"]:
            return _all_pass()
        return _some_fail(["B"])

    def _fake_regen(cycle, failing):
        healed["done"] = True  # regeneration "fixes" the prompts
        return 0

    monkeypatch.setattr(pv, "validate_all", _validate)
    monkeypatch.setattr(ctrl, "_force_regenerate_failing_prompts", _fake_regen)

    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output

    assert _read_status()["status"] == "PLANNED", result.output
    # Counter reset to 0 after a successful heal.
    assert ctrl._read_prompt_regen_state(84)["attempts"] == 0, result.output


def test_external_fix_heals_without_regen(monkeypatch):
    """If validation already passes (external fix), heal to PLANNED without
    calling regeneration at all (external-fix path preserved)."""
    _set_status("PROMPT_VALIDATION_FAILED", cycle=84)
    monkeypatch.setattr(pv, "validate_all", lambda *a, **k: _all_pass())

    regen_called = {"n": 0}
    monkeypatch.setattr(
        ctrl, "_force_regenerate_failing_prompts",
        lambda c, f: regen_called.__setitem__("n", regen_called["n"] + 1) or 0,
    )

    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _read_status()["status"] == "PLANNED", result.output
    assert regen_called["n"] == 0, "regen should not run when validation passes"


# ---------------------------------------------------------------------------
# test_regen_exhausts_and_fails_closed
# ---------------------------------------------------------------------------
def test_regen_exhausts_and_fails_closed(monkeypatch):
    """Driving attempts to MAX with regen failing → PROMPT_REGEN_EXHAUSTED
    (not infinite), a blocked incident is emitted, and a FURTHER tick does NOT
    call regen again (bounded)."""
    _set_status("PROMPT_VALIDATION_FAILED", cycle=84)
    monkeypatch.setenv("PROMPT_REGEN_MAX_ATTEMPTS", "2")

    monkeypatch.setattr(pv, "validate_all",
                        lambda *a, **k: _some_fail(["B", "D"]))

    regen_calls: list[int] = []
    monkeypatch.setattr(
        ctrl, "_force_regenerate_failing_prompts",
        lambda c, f: regen_calls.append(c) or 0,
    )

    blocked: list[dict] = []

    def _fake_notify_blocked(title, body="", incident_code="", cycle=None):
        blocked.append({"title": title, "incident_code": incident_code, "cycle": cycle})

    import automation.notification_router as nr
    monkeypatch.setattr(nr, "notify_blocked", _fake_notify_blocked)

    runner = CliRunner()

    # Tick 1: attempts 0 -> 1, still failing → stays PROMPT_VALIDATION_FAILED.
    r1 = runner.invoke(cli, ["tick"])
    assert r1.exit_code == 0, r1.output
    assert _read_status()["status"] == "PROMPT_VALIDATION_FAILED", r1.output
    assert ctrl._read_prompt_regen_state(84)["attempts"] == 1

    # Tick 2: attempts 1 -> 2 (== MAX), still failing → stays blocked.
    r2 = runner.invoke(cli, ["tick"])
    assert r2.exit_code == 0, r2.output
    assert _read_status()["status"] == "PROMPT_VALIDATION_FAILED", r2.output
    assert ctrl._read_prompt_regen_state(84)["attempts"] == 2

    assert len(regen_calls) == 2, "regen should have run exactly MAX times"

    # Tick 3: attempts == MAX → fail closed, NO further regen.
    r3 = runner.invoke(cli, ["tick"])
    assert r3.exit_code == 0, r3.output
    assert _read_status()["status"] == "PROMPT_REGEN_EXHAUSTED", r3.output
    assert len(regen_calls) == 2, "regen must NOT run after exhaustion (bounded)"

    # A blocked incident with the right code was emitted.
    assert any(b["incident_code"] == "PROMPT_REGEN_EXHAUSTED" for b in blocked), blocked

    # Tick 4: still exhausted, still failing → no regen, stays exhausted.
    r4 = runner.invoke(cli, ["tick"])
    assert r4.exit_code == 0, r4.output
    assert _read_status()["status"] == "PROMPT_REGEN_EXHAUSTED", r4.output
    assert len(regen_calls) == 2, "no regen in the exhausted branch"


def test_exhausted_auto_heals_on_external_fix(monkeypatch):
    """From PROMPT_REGEN_EXHAUSTED, if validation now passes (external fix), the
    tick auto-heals to PLANNED and resets the counter."""
    _set_status("PROMPT_REGEN_EXHAUSTED", cycle=84)
    ctrl._write_prompt_regen_state(84, 3)
    monkeypatch.setattr(pv, "validate_all", lambda *a, **k: _all_pass())

    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _read_status()["status"] == "PLANNED", result.output
    assert ctrl._read_prompt_regen_state(84)["attempts"] == 0


# ---------------------------------------------------------------------------
# test_recover_resets_regen
# ---------------------------------------------------------------------------
def test_recover_resets_regen(monkeypatch):
    """recover --regen resets attempts to 0 and clears PROMPT_REGEN_EXHAUSTED
    back to COMPILED."""
    _set_status("PROMPT_REGEN_EXHAUSTED", cycle=84)
    ctrl._write_prompt_regen_state(84, 3)

    result = CliRunner().invoke(cli, ["recover", "--regen"])
    assert result.exit_code == 0, result.output

    assert ctrl._read_prompt_regen_state(84)["attempts"] == 0, result.output
    assert _read_status()["status"] == "COMPILED", result.output
    assert "reset to 0" in result.output
    assert "COMPILED" in result.output


def test_recover_reset_prompts_alias(monkeypatch):
    """The --reset-prompts alias behaves identically to --regen."""
    _set_status("PROMPT_REGEN_EXHAUSTED", cycle=84)
    ctrl._write_prompt_regen_state(84, 3)

    result = CliRunner().invoke(cli, ["recover", "--reset-prompts"])
    assert result.exit_code == 0, result.output
    assert ctrl._read_prompt_regen_state(84)["attempts"] == 0
    assert _read_status()["status"] == "COMPILED"


# ---------------------------------------------------------------------------
# test_failing_prompt_moved_not_reused
# ---------------------------------------------------------------------------
def test_failing_prompt_moved_not_reused(monkeypatch, tmp_path):
    """A rejected prompt file is moved out of the canonical location (into
    .rejected/) before regen, so resume-from-partial cannot reuse it."""
    # Redirect the prompts dir into tmp so we don't touch the repo.
    fake_prompts = tmp_path / "prompts"
    fake_prompts.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ctrl, "REPO_ROOT", tmp_path)

    # NOTE: _quarantine reads REPO_ROOT / "PM_Pack/automation/prompts".
    real_prompts = tmp_path / "PM_Pack/automation/prompts"
    real_prompts.mkdir(parents=True, exist_ok=True)
    rejected_file = real_prompts / "CYCLE_084_AGENT_B_PROMPT.md"
    rejected_file.write_text("# degenerate rejected prompt\n" * 50, encoding="utf-8")
    assert rejected_file.exists()

    moved = ctrl._quarantine_failing_prompts(84, ["B"])

    assert moved == ["B"]
    # Canonical location no longer has the rejected file.
    assert not rejected_file.exists(), "rejected prompt was NOT removed/moved"
    # It now lives under the RUNNER STATE root (outside the repo worktree) — not
    # under PM_Pack/automation/prompts — so quarantining never dirties the tree
    # (Codex P2 on #114).
    from automation import runner_paths
    rejected_dir = runner_paths.state_dir() / "rejected_prompts" / "CYCLE_084"
    assert rejected_dir.exists()
    survivors = list(rejected_dir.glob("CYCLE_084_AGENT_B_PROMPT_*.md"))
    assert survivors, "rejected prompt was not preserved under runner-state rejected_prompts/"
    # And nothing was written into the repo worktree's prompts dir.
    assert not (real_prompts / ".rejected").exists()


def test_quarantine_missing_file_is_noop(monkeypatch, tmp_path):
    """Quarantining an agent with no prompt file is a safe no-op."""
    monkeypatch.setattr(ctrl, "REPO_ROOT", tmp_path)
    (tmp_path / "PM_Pack/automation/prompts").mkdir(parents=True, exist_ok=True)
    moved = ctrl._quarantine_failing_prompts(84, ["A"])
    assert moved == []


# ---------------------------------------------------------------------------
# state-file helper unit coverage
# ---------------------------------------------------------------------------
def test_regen_state_resets_on_cycle_change():
    """A counter recorded for one cycle reads as 0 attempts for a new cycle."""
    ctrl._write_prompt_regen_state(84, 3)
    assert ctrl._read_prompt_regen_state(84)["attempts"] == 3
    # Different cycle → fresh budget.
    assert ctrl._read_prompt_regen_state(85)["attempts"] == 0


def test_max_attempts_env_tunable(monkeypatch):
    monkeypatch.setenv("PROMPT_REGEN_MAX_ATTEMPTS", "7")
    assert ctrl._prompt_regen_max_attempts() == 7
    monkeypatch.setenv("PROMPT_REGEN_MAX_ATTEMPTS", "not_an_int")
    assert ctrl._prompt_regen_max_attempts() == 3
    monkeypatch.delenv("PROMPT_REGEN_MAX_ATTEMPTS", raising=False)
    assert ctrl._prompt_regen_max_attempts() == 3
