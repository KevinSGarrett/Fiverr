"""Audit rank-1 (BLOCKER) + rank-5: never silently abandon committed agent work.

rank-1: when a post-cycle review PASSES but there is NO active PR, the controller
used to write POST_CYCLE_PASS and advance — silently abandoning any committed work
on the integration branch that never reached develop (the exact state cycle 84 was
in). The fix preserves the work as a durable recovery tag and routes to the bounded
PR_CREATE_FAILED recovery (re-attempt open_cycle_pr) instead of advancing.

rank-5: the post-cycle review's `gh pr list` had no timeout — a hang wedged
run_review forever with no exception for the controller's error-counter to bound.
"""
from __future__ import annotations

import subprocess

import automation.ai_cycle_controller as ctrl
import automation.post_cycle_review as pcr


# ---- rank-1: _finalize_post_cycle_pass work-preservation guard --------------

def _patch_state_writer(monkeypatch):
    """Capture write_controller_state calls without touching disk."""
    written = []
    import automation.state_writer as sw
    monkeypatch.setattr(sw, "write_controller_state",
                        lambda status, **kw: written.append((status, kw)))
    return written


def test_open_pr_routes_to_awaiting_ci(monkeypatch):
    """Unchanged behavior: an open PR routes to AWAITING_CI_GREEN."""
    _patch_state_writer(monkeypatch)
    monkeypatch.setattr(ctrl, "_read_runner_state", lambda: {"active_pr": 77})
    assert ctrl._finalize_post_cycle_pass(85) == "AWAITING_CI_GREEN"


def test_no_pr_no_work_advances(monkeypatch):
    """No PR and NO un-merged work → POST_CYCLE_PASS (safe to advance)."""
    _patch_state_writer(monkeypatch)
    monkeypatch.setattr(ctrl, "_read_runner_state", lambda: {})
    monkeypatch.setattr(ctrl, "_integration_branch_ahead_of_develop", lambda c: (0, ""))
    assert ctrl._finalize_post_cycle_pass(85) == "POST_CYCLE_PASS"


def test_no_pr_with_work_preserves_and_recovers(monkeypatch):
    """No PR but the integration branch is AHEAD → must NOT silently advance.
    Routes to PR_CREATE_FAILED (bounded open_cycle_pr recovery) and preserves the
    work as a recovery tag — never POST_CYCLE_PASS."""
    written = _patch_state_writer(monkeypatch)
    monkeypatch.setattr(ctrl, "_read_runner_state", lambda: {})
    monkeypatch.setattr(ctrl, "_integration_branch_ahead_of_develop",
                        lambda c: (2, "deadbeefcafe"))
    tagged = {}
    monkeypatch.setattr(ctrl, "_preserve_cycle_work_tag",
                        lambda c, sha: tagged.setdefault("call", (c, sha)) or f"cycle-{c:03d}-checkpoint")

    result = ctrl._finalize_post_cycle_pass(84)

    assert result == "PR_CREATE_FAILED", "un-PR'd work must route to recovery, not advance"
    assert ("PR_CREATE_FAILED", {"cycle": 84}) in written
    assert ("POST_CYCLE_PASS", {"cycle": 84}) not in [(s, k) for s, k in written]
    assert tagged["call"] == (84, "deadbeefcafe"), "work must be preserved as a recovery tag"


# ---- rank-1: _integration_branch_ahead_of_develop measurement ---------------

def test_ahead_zero_when_branch_missing(monkeypatch):
    """No local integration branch ⇒ (0, "") — nothing to lose, safe to advance."""
    def fake_git(args):
        if args[:2] == ["rev-parse", "--verify"]:
            return (1, "")  # branch does not exist
        return (0, "")
    monkeypatch.setattr(ctrl, "_git_cmd", fake_git)
    assert ctrl._integration_branch_ahead_of_develop(84) == (0, "")


def test_ahead_count_parsed(monkeypatch):
    """Reports the rev-list ahead count + head sha when the branch exists."""
    def fake_git(args):
        if args[:2] == ["rev-parse", "--verify"]:
            return (0, "ok")
        if args[0] == "rev-parse":            # head sha
            return (0, "abc123def456\n")
        if args[0] == "rev-list":             # ahead count
            return (0, "3\n")
        return (0, "")
    monkeypatch.setattr(ctrl, "_git_cmd", fake_git)
    assert ctrl._integration_branch_ahead_of_develop(84) == (3, "abc123def456")


def test_ahead_zero_for_no_cycle(monkeypatch):
    assert ctrl._integration_branch_ahead_of_develop(None) == (0, "")


# ---- rank-5: gh pr list timeout is non-fatal --------------------------------

def test_github_facts_gh_timeout_degrades(monkeypatch, tmp_path):
    """A hung `gh pr list` (TimeoutExpired) degrades to gh_unavailable, never raises."""
    monkeypatch.setattr(pcr.subprocess, "run",
                        lambda *a, **k: (_ for _ in ()).throw(
                            subprocess.TimeoutExpired(cmd="gh", timeout=30)))
    fc = pcr.FactCollector(cycle=84) if hasattr(pcr, "FactCollector") else None
    # Resolve the collector class generically (name may differ); fall back to the
    # object that owns _verify_github_facts.
    collector = fc
    if collector is None:
        import inspect
        owner = None
        for _name, obj in inspect.getmembers(pcr, inspect.isclass):
            if hasattr(obj, "_verify_github_facts"):
                owner = obj
                break
        assert owner is not None, "could not locate the _verify_github_facts owner class"
        collector = owner.__new__(owner)
    collector.current_run_dir = tmp_path
    payload = collector._verify_github_facts()
    assert payload["merged_prs"] == []
    assert payload["error"] == "gh_unavailable"


def test_github_facts_has_timeout_in_source():
    """Regression: the gh call must pass a timeout and catch TimeoutExpired."""
    import inspect
    src = inspect.getsource(pcr)
    i = src.index("def _verify_github_facts")
    seg = src[i:i + 1400]
    assert "POST_CYCLE_GH_TIMEOUT" in seg
    assert "subprocess.TimeoutExpired" in seg
