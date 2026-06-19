"""Item 0.1 — cycle-number oscillation (82<->84) regression tests.

These exercise the five fixes:
  T1 atomic + monotonic write_controller_state
  T2 trust-ordered consensus (NOT max())
  T3 (covered indirectly) end-of-run re-stamp removed
  T4 force_set persists BOTH ledger and controller_state
  T5 get_active_cycle() single accessor

All probe readings are injected via monkeypatch so no real git/network/disk
state is consulted. Writes land under the per-session tmp runner root (the
autouse conftest fixtures redirect AUTOPILOT_RUNNER_ROOT and re-point the
hardcoded Path constants in cycle_authority/state_writer).
"""

from __future__ import annotations

import json

import pytest

from automation import cycle_authority, state_writer


# ---------------------------------------------------------------------------
# T2 — trust-ordered consensus
# ---------------------------------------------------------------------------
def test_trust_ordered_prefers_controller_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """controller_state=82 (trust 10) must win over git=84/prompt=84 (lower trust).

    The OLD max() returned 84 (negative reproduction). Trust-ordered returns 82.
    """
    monkeypatch.setattr(cycle_authority, "_probe_controller_state", lambda: 82)
    monkeypatch.setattr(cycle_authority, "_probe_git_branches", lambda: 84)
    monkeypatch.setattr(cycle_authority, "_probe_prompt_files", lambda: 84)
    monkeypatch.setattr(cycle_authority, "_probe_local_hydration", lambda: None)
    monkeypatch.setattr(cycle_authority, "_probe_policy_snapshot", lambda: None)
    monkeypatch.setattr(cycle_authority, "_probe_runner_hydration", lambda: None)

    result = cycle_authority.determine_correct_cycle()
    assert result["cycle"] == 82
    assert result["method"] == "trust_ordered"


def test_trust_ordered_falls_to_next_when_controller_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No controller_state -> highest trust present (git_branch=84) wins, not max."""
    monkeypatch.setattr(cycle_authority, "_probe_controller_state", lambda: None)
    monkeypatch.setattr(cycle_authority, "_probe_git_branches", lambda: 84)
    monkeypatch.setattr(cycle_authority, "_probe_prompt_files", lambda: 83)
    monkeypatch.setattr(cycle_authority, "_probe_local_hydration", lambda: None)
    monkeypatch.setattr(cycle_authority, "_probe_policy_snapshot", lambda: None)
    monkeypatch.setattr(cycle_authority, "_probe_runner_hydration", lambda: None)

    result = cycle_authority.determine_correct_cycle()
    assert result["cycle"] == 84
    assert result["method"] == "trust_ordered"


# ---------------------------------------------------------------------------
# T1 — monotonic + atomic write_controller_state
# ---------------------------------------------------------------------------
def test_write_controller_state_monotonic() -> None:
    """A lower cycle is ignored unless allow_lower=True."""
    path = state_writer._controller_state_path()

    state_writer.write_controller_state("RUNNING", cycle=84)
    assert json.loads(path.read_text(encoding="utf-8"))["active_cycle"] == 84

    # Lower write with default allow_lower=False -> stays 84.
    state_writer.write_controller_state("RUNNING", cycle=82)
    assert json.loads(path.read_text(encoding="utf-8"))["active_cycle"] == 84

    # Explicit override lowers it.
    state_writer.write_controller_state("RUNNING", cycle=82, allow_lower=True)
    assert json.loads(path.read_text(encoding="utf-8"))["active_cycle"] == 82


def test_write_controller_state_monotonic_preserves_other_fields() -> None:
    """A rejected lower cycle still applies the other field updates."""
    path = state_writer._controller_state_path()
    state_writer.write_controller_state("RUNNING", cycle=84, branch="cycle/084")
    # Lower cycle is rejected, but status/branch updates still apply.
    state_writer.write_controller_state("AGENT_COMPLETE", cycle=82, branch="cycle/082")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["active_cycle"] == 84  # kept
    assert data["status"] == "AGENT_COMPLETE"  # applied
    assert data["active_branch"] == "cycle/082"  # applied


def test_write_controller_state_atomic() -> None:
    """File is always valid JSON with the expected value after a write."""
    path = state_writer._controller_state_path()
    state_writer.write_controller_state("RUNNING", cycle=84)
    # No partial writes: file parses cleanly and holds the value.
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["active_cycle"] == 84
    assert data["status"] == "RUNNING"


# ---------------------------------------------------------------------------
# T4 — force_set persists BOTH ledger and controller_state
# ---------------------------------------------------------------------------
def test_force_set_persists_both() -> None:
    cycle_authority.force_set(90, "op")

    ledger = cycle_authority.get_ledger(5)
    assert ledger, "ledger should have at least one entry"
    last = ledger[-1]
    assert last["event"] == "FORCE_SET"
    assert last["to"] == 90

    state = json.loads(
        state_writer._controller_state_path().read_text(encoding="utf-8")
    )
    assert state["active_cycle"] == 90


def test_force_set_can_lower() -> None:
    """force_set is an explicit override -> may lower active_cycle."""
    state_writer.write_controller_state("RUNNING", cycle=95)
    cycle_authority.force_set(90, "operator-rollback")
    state = json.loads(
        state_writer._controller_state_path().read_text(encoding="utf-8")
    )
    assert state["active_cycle"] == 90


# ---------------------------------------------------------------------------
# T5 — get_active_cycle single accessor
# ---------------------------------------------------------------------------
def test_get_active_cycle_uses_controller_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cycle_authority, "_probe_controller_state", lambda: 77)
    assert cycle_authority.get_active_cycle() == 77
    # get_current is a thin alias.
    assert cycle_authority.get_current() == 77


def test_get_active_cycle_falls_back_to_consensus(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cycle_authority, "_probe_controller_state", lambda: None)
    monkeypatch.setattr(cycle_authority, "_probe_git_branches", lambda: 84)
    monkeypatch.setattr(cycle_authority, "_probe_prompt_files", lambda: 83)
    monkeypatch.setattr(cycle_authority, "_probe_local_hydration", lambda: None)
    monkeypatch.setattr(cycle_authority, "_probe_policy_snapshot", lambda: None)
    monkeypatch.setattr(cycle_authority, "_probe_runner_hydration", lambda: None)
    assert cycle_authority.get_active_cycle() == 84


# ---------------------------------------------------------------------------
# Core oscillation regression — reconcile must NOT correct 82 -> 84
# ---------------------------------------------------------------------------
def test_reconcile_no_oscillation(monkeypatch: pytest.MonkeyPatch) -> None:
    """controller=82 with a stale git_branch=84: consensus must equal 82.

    With trust-ordered selection the authoritative controller_state wins, so
    reconcile() takes no action (no "CORRECTED 82 -> 84" churn).
    """
    monkeypatch.setattr(cycle_authority, "_probe_controller_state", lambda: 82)
    monkeypatch.setattr(cycle_authority, "_probe_git_branches", lambda: 84)  # stale
    monkeypatch.setattr(cycle_authority, "_probe_prompt_files", lambda: 84)
    monkeypatch.setattr(cycle_authority, "_probe_local_hydration", lambda: None)
    monkeypatch.setattr(cycle_authority, "_probe_policy_snapshot", lambda: None)
    monkeypatch.setattr(cycle_authority, "_probe_runner_hydration", lambda: None)

    # Let reconcile() actually run (it short-circuits under PYTEST_CURRENT_TEST).
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    report = cycle_authority.reconcile()

    assert report["consensus"] == 82
    assert report["action"] == "none"
    assert "CORRECTED" not in report["action"]
