"""Audit BLOCKER #2 — merge gate auto-updates a PR that fell BEHIND develop.

Once any cycle merges to develop, branch protection makes every OTHER open cycle PR
BEHIND, and `gh pr merge` fails "not up to date" on every retry → the merge gate
dead-ends → operator. The MERGE_BLOCKED handler now updates the branch when BEHIND so
CI re-runs on the merged result. Routine in a multi-cycle run.
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
    import automation.notification_router as nr
    monkeypatch.setattr(nr, "notify_blocked", lambda *a, **k: None)
    monkeypatch.setattr(nr, "notify_info", lambda *a, **k: None)
    import automation.cycle_authority as ca
    monkeypatch.setattr(ca, "reconcile", lambda **k: {"action": "OK", "consensus": None})
    yield
    _wipe()


def _state() -> dict:
    return json.loads((runner_paths.state_dir() / "controller_state.json").read_text())


# ── the helper ─────────────────────────────────────────────────────────────────
def test_update_pr_branch_if_behind_updates_when_behind(monkeypatch):
    import automation.ai_cycle_controller as ctl
    calls = []

    def fake_run(args, **k):
        calls.append(list(args))
        if "view" in args:
            return SimpleNamespace(returncode=0, stdout='{"mergeStateStatus":"BEHIND"}', stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")  # update-branch

    monkeypatch.setattr("subprocess.run", fake_run)
    assert ctl._update_pr_branch_if_behind(140) is True
    assert any("update-branch" in c for c in calls), "must call gh pr update-branch when BEHIND"


def test_update_pr_branch_noop_when_clean(monkeypatch):
    import automation.ai_cycle_controller as ctl
    calls = []

    def fake_run(args, **k):
        calls.append(list(args))
        return SimpleNamespace(returncode=0, stdout='{"mergeStateStatus":"CLEAN"}', stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)
    assert ctl._update_pr_branch_if_behind(140) is False
    assert not any("update-branch" in c for c in calls), "must NOT update a non-BEHIND PR"


def test_update_pr_branch_fail_safe_on_gh_error(monkeypatch):
    import automation.ai_cycle_controller as ctl
    monkeypatch.setattr("subprocess.run",
                        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="boom"))
    assert ctl._update_pr_branch_if_behind(140) is False  # never raises


# ── wiring: MERGE_BLOCKED retry updates a BEHIND branch ─────────────────────────
def test_merge_blocked_retry_updates_behind_branch(monkeypatch):
    import automation.ai_cycle_controller as ctl
    called = {"n": 0}
    monkeypatch.setattr(ctl, "_update_pr_branch_if_behind",
                        lambda pr: (called.__setitem__("n", called["n"] + 1) or True))
    write_controller_state("MERGE_BLOCKED", cycle=450, pr=1450)
    result = CliRunner().invoke(cli, ["tick"])
    assert result.exit_code == 0, result.output
    assert called["n"] == 1, "MERGE_BLOCKED retry must attempt the behind-branch update"
    assert _state()["status"] == "AWAITING_CI_GREEN"  # re-enters to re-check CI on the update
