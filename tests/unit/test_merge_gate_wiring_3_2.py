"""ITEM 3.2 — wiring the autonomous merge gate into the tick state machine.

After 3.1 opens a PR (state AGENT_COMPLETE + active_pr), the loop must:
  AGENT_COMPLETE --(local review PASS, PR open)--> AWAITING_CI_GREEN
  AWAITING_CI_GREEN --(required CI GREEN + gate pass)--> MERGED
  MERGED --> POST_CYCLE_PASS (active_pr cleared) -> existing advance machinery
and fail-closed to MERGE_BLOCKED on CI failure / gate fail / missing PR / timeout,
never advancing the cycle while a PR is open.

All gh/git/CI/merge seams are mocked.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from automation import runner_paths
from automation.ai_cycle_controller import cli
from automation.state_writer import write_controller_state


@pytest.fixture(autouse=True)
def _clean_state():
    """Keep tests order-independent: clear persistent state between them."""
    def _wipe():
        for name in ("controller_state.json", "tick_counters.json"):
            try:
                (runner_paths.state_dir() / name).unlink()
            except OSError:
                pass
    _wipe()
    yield
    _wipe()


@pytest.fixture
def no_drift(monkeypatch):
    """Stop the tick's cycle-authority pre/post reconcile from aborting the tick."""
    import automation.cycle_authority as ca
    monkeypatch.setattr(ca, "reconcile",
                        lambda **k: {"action": "OK", "consensus": None})
    return monkeypatch


@pytest.fixture
def caps(monkeypatch):
    blocked: list[dict] = []
    info: list[str] = []
    import automation.notification_router as nr
    monkeypatch.setattr(nr, "notify_blocked",
                        lambda title, body="", incident_code="", cycle=None:
                        blocked.append({"title": title, "incident_code": incident_code, "cycle": cycle}))
    monkeypatch.setattr(nr, "notify_info", lambda *a, **k: info.append(a[0] if a else ""))
    return SimpleNamespace(blocked=blocked, info=info)


def _state() -> dict:
    return json.loads((runner_paths.state_dir() / "controller_state.json").read_text())


def _fake_ci(monkeypatch, disposition: str, gh_ok: bool = True):
    import automation.ci_status_reader as csr

    class _CS:
        def __init__(self):
            self.gh_ok = gh_ok
            self.checks = []

        def disposition(self, required=None):
            return disposition

    monkeypatch.setattr(csr, "read_pr_ci_status", lambda *a, **k: _CS())
    # avoid the live gh call for the required set
    import automation.required_checks as rc
    monkeypatch.setattr(rc, "get_required_contexts", lambda *a, **k: set(rc.REQUIRED_CONTEXTS))


def _fake_gate(monkeypatch, *, passed: bool, merge_sha="sha_merged", already=False,
               merged=None):
    import automation.merge_gate as mg
    calls = {"n": 0, "execute": None, "dry_run": None}
    merged_flag = passed if merged is None else merged

    def _run(pr_number, repo=mg.REPO, *, dry_run=True, execute=False):
        calls["n"] += 1
        calls["execute"] = execute
        calls["dry_run"] = dry_run
        return SimpleNamespace(
            passed=passed, merge_sha=(merge_sha if passed else None),
            already_merged=already, merged=merged_flag,
            failed_checks=lambda: ([] if passed else
                [SimpleNamespace(name="ci::CI / tests-coverage")]),
        )

    monkeypatch.setattr(mg, "run", _run)
    return calls


# ── AGENT_COMPLETE -> AWAITING_CI_GREEN (PR open) ─────────────────────────────
def test_agent_complete_with_pr_goes_to_awaiting_ci(no_drift, caps, monkeypatch):
    import automation.post_cycle_review as pcr
    monkeypatch.setattr(
        pcr, "run_review",
        lambda cycle, mode: SimpleNamespace(
            result=SimpleNamespace(value="PASS"), blocks_dispatch=False, facts=None),
    )
    write_controller_state("AGENT_COMPLETE", cycle=410, pr=1410)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    st = _state()
    assert st["status"] == "AWAITING_CI_GREEN"
    assert st["active_pr"] == 1410  # PR preserved for the merge path


def test_agent_complete_without_pr_keeps_legacy_post_cycle_pass(no_drift, caps, monkeypatch):
    import automation.post_cycle_review as pcr
    monkeypatch.setattr(
        pcr, "run_review",
        lambda cycle, mode: SimpleNamespace(
            result=SimpleNamespace(value="PASS"), blocks_dispatch=False, facts=None),
    )
    write_controller_state("AGENT_COMPLETE", cycle=411)  # no active_pr
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "POST_CYCLE_PASS"


# ── AWAITING_CI_GREEN transitions ─────────────────────────────────────────────
def test_awaiting_ci_green_merges_when_green(no_drift, caps, monkeypatch):
    _fake_ci(monkeypatch, "GREEN")
    calls = _fake_gate(monkeypatch, passed=True, merge_sha="abc999")
    write_controller_state("AWAITING_CI_GREEN", cycle=420, pr=1420)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "MERGED"
    assert any("merged PR #1420" in m for m in caps.info)
    # #10: prove the irreversible merge was actually triggered (execute=True).
    assert calls["execute"] is True
    assert calls["dry_run"] is False


def test_awaiting_ci_green_but_gate_passed_no_sha_blocks(no_drift, caps, monkeypatch):
    # #11: passed=True but no merge_sha AND not already_merged AND not merged -> block.
    _fake_ci(monkeypatch, "GREEN")
    _fake_gate(monkeypatch, passed=True, merge_sha=None, already=False, merged=False)
    write_controller_state("AWAITING_CI_GREEN", cycle=426, pr=1426)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "MERGE_BLOCKED"


def test_awaiting_ci_gh_error_treated_as_pending(no_drift, caps, monkeypatch):
    # #17: gh read failure (gh_ok=False) must be treated as PENDING (fail-closed,
    # stay waiting), never merged even if disposition() would say GREEN.
    _fake_ci(monkeypatch, "GREEN", gh_ok=False)
    calls = _fake_gate(monkeypatch, passed=True)
    write_controller_state("AWAITING_CI_GREEN", cycle=427, pr=1427)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "AWAITING_CI_GREEN"
    assert calls["n"] == 0, "merge gate must not run on a gh-errored CI read"


def test_awaiting_ci_pending_stays(no_drift, caps, monkeypatch):
    _fake_ci(monkeypatch, "PENDING")
    write_controller_state("AWAITING_CI_GREEN", cycle=421, pr=1421)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "AWAITING_CI_GREEN"  # bounded wait, still waiting


def test_awaiting_ci_failed_blocks(no_drift, caps, monkeypatch):
    _fake_ci(monkeypatch, "FAILED")
    write_controller_state("AWAITING_CI_GREEN", cycle=422, pr=1422)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "MERGE_BLOCKED"
    assert any(b["incident_code"] == "MERGE_BLOCKED" for b in caps.blocked)


def test_awaiting_ci_green_but_gate_fails_blocks(no_drift, caps, monkeypatch):
    _fake_ci(monkeypatch, "GREEN")
    _fake_gate(monkeypatch, passed=False)
    write_controller_state("AWAITING_CI_GREEN", cycle=423, pr=1423)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "MERGE_BLOCKED"


def test_awaiting_ci_no_pr_fails_closed(no_drift, caps, monkeypatch):
    write_controller_state("AWAITING_CI_GREEN", cycle=424)  # no active_pr
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "MERGE_BLOCKED"


def test_ci_wait_timeout_blocks(no_drift, caps, monkeypatch):
    _fake_ci(monkeypatch, "PENDING")
    monkeypatch.setenv("AUTOPILOT_CI_WAIT_MAX_TICKS", "2")
    write_controller_state("AWAITING_CI_GREEN", cycle=425, pr=1425)
    # tick 1 -> still waiting (count 1)
    CliRunner().invoke(cli, ["tick"])
    assert _state()["status"] == "AWAITING_CI_GREEN"
    # tick 2 -> count reaches cap -> MERGE_BLOCKED
    CliRunner().invoke(cli, ["tick"])
    assert _state()["status"] == "MERGE_BLOCKED"


# ── MERGING crash-recovery ────────────────────────────────────────────────────
def test_merging_recovers_idempotently(no_drift, caps, monkeypatch):
    # A tick that wrote MERGING then crashed must recover: re-attempt the merge
    # (idempotent) rather than leaking to IDLE.
    calls = _fake_gate(monkeypatch, passed=True, already=True, merge_sha=None)
    write_controller_state("MERGING", cycle=428, pr=1428)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "MERGED"
    assert calls["execute"] is True


def test_merging_no_pr_fails_closed(no_drift, caps, monkeypatch):
    write_controller_state("MERGING", cycle=429)  # no active_pr
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "MERGE_BLOCKED"


# ── MERGED -> advance ─────────────────────────────────────────────────────────
def test_merged_clears_pr_and_routes_to_post_cycle_pass(no_drift, caps, monkeypatch):
    write_controller_state("MERGED", cycle=430, pr=1430)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    st = _state()
    assert st["status"] == "POST_CYCLE_PASS"
    assert "active_pr" not in st  # cleared so the next cycle doesn't inherit it


# ── MERGE_BLOCKED bounded recovery ────────────────────────────────────────────
def test_merge_blocked_retries_into_awaiting(no_drift, caps, monkeypatch):
    write_controller_state("MERGE_BLOCKED", cycle=440, pr=1440)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "AWAITING_CI_GREEN"  # bounded auto-retry


def test_merge_blocked_exhausted_stays_and_notifies(no_drift, caps, monkeypatch):
    monkeypatch.setenv("AUTOPILOT_MERGE_RETRY_MAX", "1")
    write_controller_state("MERGE_BLOCKED", cycle=441, pr=1441)
    CliRunner().invoke(cli, ["tick"])   # retry 1 -> AWAITING_CI_GREEN
    write_controller_state("MERGE_BLOCKED", cycle=441, pr=1441)
    CliRunner().invoke(cli, ["tick"])   # retry 2 > cap -> stays MERGE_BLOCKED + notify
    assert _state()["status"] == "MERGE_BLOCKED"
    assert any(b["incident_code"] == "MERGE_BLOCKED" for b in caps.blocked)


def test_merge_blocked_no_pr_stays_blocked_no_advance(no_drift, caps, monkeypatch):
    # #16: MERGE_BLOCKED with no active_pr must stay blocked and never advance.
    import automation.cycle_authority as ca
    advanced = {"n": 0}
    monkeypatch.setattr(ca, "advance",
                        lambda *a, **k: advanced.__setitem__("n", advanced["n"] + 1) or 999,
                        raising=False)
    write_controller_state("MERGE_BLOCKED", cycle=442)  # no active_pr
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert _state()["status"] == "MERGE_BLOCKED"
    assert advanced["n"] == 0


# ── no advance while a PR is open ─────────────────────────────────────────────
def test_cycle_does_not_advance_while_awaiting_ci(no_drift, caps, monkeypatch):
    import automation.cycle_authority as ca
    advanced = {"n": 0}
    monkeypatch.setattr(ca, "advance",
                        lambda *a, **k: advanced.__setitem__("n", advanced["n"] + 1) or 999,
                        raising=False)
    _fake_ci(monkeypatch, "PENDING")
    write_controller_state("AWAITING_CI_GREEN", cycle=450, pr=1450)
    CliRunner().invoke(cli, ["tick"])
    assert advanced["n"] == 0, "cycle must NOT advance while CI is pending"


# ── state_writer.clear_pr ─────────────────────────────────────────────────────
def test_state_writer_clear_pr_drops_active_pr(no_drift):
    write_controller_state("AGENT_COMPLETE", cycle=460, pr=1460)
    assert _state()["active_pr"] == 1460  # sticky once set
    # A plain write keeps it (sticky).
    write_controller_state("AWAITING_CI_GREEN", cycle=460)
    assert _state()["active_pr"] == 1460
    # clear_pr drops it.
    write_controller_state("POST_CYCLE_PASS", cycle=460, clear_pr=True)
    assert "active_pr" not in _state()


# ── new states recognized (behavioral, not source-text) ───────────────────────
@pytest.fixture
def clean_repo(monkeypatch):
    """status-tick blocks on a dirty repo / freeze before evaluating status; the
    local dev tree is dirty, so neutralize both to test the status ladder itself.
    (In CI the checked-out tree is clean, so this only matters locally.)"""
    import subprocess as _sp
    import automation.freeze_gate as fg
    monkeypatch.setattr(fg, "is_frozen", lambda *a, **k: False)
    _real = _sp.run

    def _fake(cmd, *a, **k):
        if isinstance(cmd, list | tuple) and "status" in cmd and "git" in cmd[0]:
            class _R:
                returncode = 0
                stdout = ""
                stderr = ""
            return _R()
        return _real(cmd, *a, **k)

    monkeypatch.setattr(_sp, "run", _fake)
    return monkeypatch


@pytest.mark.parametrize("status,expected_action", [
    ("AWAITING_CI_GREEN", "WAIT_CI_GREEN"),
    ("MERGING", "MERGING"),
    ("MERGED", "ADVANCE_CYCLE"),
    ("MERGE_BLOCKED", "RETRY_OR_OPERATOR_MERGE"),
])
def test_status_tick_recognizes_new_states(no_drift, clean_repo, status, expected_action, monkeypatch):
    # Behavioral: status-tick (read-only) must classify each new state to its
    # specific next_action, never the UNKNOWN_STATUS_* fallback.
    write_controller_state(status, cycle=470, pr=1470)
    result = CliRunner().invoke(cli, ["status-tick"])
    assert result.exit_code == 0, result.output
    decision = json.loads(
        (runner_paths.state_dir() / "next_action_decision.json").read_text())
    assert decision["next_action"] == expected_action
    assert not decision["next_action"].startswith("UNKNOWN_STATUS")
