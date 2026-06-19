"""Unit tests for automation/repo_janitor.py.

Each test builds a real temp git repo so the janitor's git plumbing runs for
real (no mocks). The merged-PR head set is injected via `pr_heads=` so the
squash-merge path is exercised deterministically without touching the network.
Covers: clean-tree detection, CI-path exclusion, ancestry vs squash branch
selection, protected-branch safety, recovery-tagging on force-delete, stash
allow-list + age gating, dry-run no-mutation, and execute semantics.
"""
from __future__ import annotations

import subprocess
import time

import pytest

from automation import repo_janitor as rj


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    _git(["init", "-b", "develop"], r)
    _git(["config", "user.email", "t@t.com"], r)
    _git(["config", "user.name", "tester"], r)
    (r / "a.txt").write_text("1")
    _git(["add", "."], r)
    _git(["commit", "-m", "init"], r)
    return r


def test_verify_clean_tree(repo):
    assert rj.verify_clean_tree(repo) is True
    (repo / "b.txt").write_text("x")
    assert rj.verify_clean_tree(repo) is False


def test_is_ci_path():
    assert rj._is_ci_path("C:/actions-runner/_work/fiverr-cycle-079")
    assert rj._is_ci_path(r"C:\actions-runner\_work\x")
    assert rj._is_ci_path("/home/runner/_work/repo")
    assert not rj._is_ci_path("C:/Fiverr/Fiverr")
    assert not rj._is_ci_path("C:/Fiverr/Fiverr_wt103")


def test_find_prunable_local_ancestry(repo):
    _git(["branch", "cycle/077/integration"], repo)  # merged: points at develop tip
    _git(["checkout", "-b", "feature/x"], repo)
    (repo / "c.txt").write_text("y")
    _git(["add", "."], repo)
    _git(["commit", "-m", "c"], repo)
    _git(["checkout", "develop"], repo)

    res = dict(rj.find_prunable_local_branches(repo, base="develop", pr_heads=set()))
    assert res.get("cycle/077/integration") == "ancestry"
    assert "feature/x" not in res   # unmerged AND not a merged-PR head
    assert "develop" not in res
    assert "main" not in res


def test_find_prunable_local_squash_via_pr_heads(repo):
    # own commit -> NOT ancestry-merged; but listed as a merged-PR head -> squash
    _git(["checkout", "-b", "feature/squashed"], repo)
    (repo / "s.txt").write_text("s")
    _git(["add", "."], repo)
    _git(["commit", "-m", "s"], repo)
    _git(["checkout", "develop"], repo)

    res = dict(rj.find_prunable_local_branches(repo, base="develop",
                                               pr_heads={"feature/squashed"}))
    assert res.get("feature/squashed") == "squash"


def test_find_stale_stashes_allowlist_and_age(repo):
    (repo / "a.txt").write_text("changed-1")
    _git(["stash", "push", "-m", "agent-a preflight preserve"], repo)
    (repo / "a.txt").write_text("changed-2")
    _git(["stash", "push", "-m", "manual important keep"], repo)

    stale = rj.find_stale_stashes(repo, min_age_h=0, now=time.time() + 10)
    msgs = [s["msg"].lower() for s in stale]
    assert any("preflight" in m for m in msgs)
    assert not any("manual important" in m for m in msgs)
    assert rj.find_stale_stashes(repo, min_age_h=10_000) == []


def test_run_dry_run_makes_no_changes(repo):
    _git(["branch", "cycle/077/integration"], repo)
    before = _git(["branch"], repo).stdout
    rep = rj.run(execute=False, base="develop", cwd=repo, pr_heads=set())
    after = _git(["branch"], repo).stdout
    assert before == after
    assert rep.execute is False
    assert any(a.kind == "branch_local" and a.target == "cycle/077/integration"
               for a in rep.actions)
    assert all(a.executed is False for a in rep.actions)


def test_run_execute_deletes_ancestry_merged_only(repo):
    _git(["branch", "cycle/077/integration"], repo)   # merged
    _git(["checkout", "-b", "feature/keep"], repo)     # unmerged, no PR
    (repo / "d.txt").write_text("z")
    _git(["add", "."], repo)
    _git(["commit", "-m", "d"], repo)
    _git(["checkout", "develop"], repo)

    rep = rj.run(execute=True, base="develop", cwd=repo, do_stashes=False, pr_heads=set())
    branches = _git(["branch"], repo).stdout
    assert "cycle/077/integration" not in branches
    assert "feature/keep" in branches
    assert any(a.executed and a.target == "cycle/077/integration" for a in rep.actions)


def test_run_execute_squash_delete_writes_recovery_tag(repo):
    _git(["checkout", "-b", "cycle/078/integration"], repo)  # own commit -> squash path
    (repo / "e.txt").write_text("e")
    _git(["add", "."], repo)
    _git(["commit", "-m", "e"], repo)
    _git(["checkout", "develop"], repo)

    rep = rj.run(execute=True, base="develop", cwd=repo, do_stashes=False,
                 pr_heads={"cycle/078/integration"})
    branches = _git(["branch"], repo).stdout
    tags = _git(["tag"], repo).stdout
    assert "cycle/078/integration" not in branches      # force-deleted (PR-confirmed)
    assert "branch-janitor-backup-" in tags             # recoverable
    assert any(a.executed and a.target == "cycle/078/integration" and "squash" in a.detail
               for a in rep.actions)


def test_report_summary_and_dict(repo):
    rep = rj.run(execute=False, base="develop", cwd=repo, pr_heads=set())
    assert "repo_janitor DRY-RUN" in rep.summary()
    d = rep.to_dict()
    assert d["execute"] is False and d["base"] == "develop"
    assert "counts" in d and "actions" in d


def test_prune_worktrees_removes_obsolete_clean(repo, tmp_path):
    wt = tmp_path / "wt"
    _git(["worktree", "add", str(wt), "-b", "scratch/wt"], repo)
    assert wt.exists()
    obs = rj.find_obsolete_worktrees(repo)
    wtn = str(wt).replace("\\", "/").lower()
    assert any(wtn == w["path"].replace("\\", "/").lower() for w in obs)
    rep = rj.run(execute=True, base="develop", cwd=repo, do_stashes=False, pr_heads=set())
    assert any(a.kind == "worktree" and a.executed for a in rep.actions)
    assert not wt.exists()


def test_drop_stashes_execute_writes_recovery_tag(repo):
    (repo / "a.txt").write_text("stash-me")
    _git(["stash", "push", "-m", "agent-a preflight auto"], repo)
    rep = rj.JanitorReport(execute=True, base="develop")
    rj.drop_stashes(rep, cwd=repo, min_age_h=0)
    assert rj.list_stashes(repo) == []                              # dropped
    assert "stash-janitor-backup-" in _git(["tag"], repo).stdout    # recoverable
    assert any(a.kind == "stash" and a.executed for a in rep.actions)


def test_merged_pr_heads_empty_on_gh_failure(repo):
    # nonexistent repo -> gh errors -> graceful empty set (degrade to ancestry-only)
    assert rj.merged_pr_heads(repo, repo="KevinSGarrett/__no_such_repo__zzz") == set()


def test_find_prunable_remote_no_origin_is_empty(repo):
    assert rj.find_prunable_remote_cycle_branches(repo, base="develop", pr_heads=set()) == []


def test_list_worktrees_includes_main(repo):
    wts = rj.list_worktrees(repo)
    rn = str(repo).replace("\\", "/").lower().rstrip("/")
    assert any(rn == w["path"].replace("\\", "/").lower().rstrip("/") for w in wts)
