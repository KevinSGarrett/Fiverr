"""Dispatch-hardening regression tests (fixes #1, #4, #5).

These pin the ownership-attribution contract that, when broken, produced cycle-83's
0/6 OWNERSHIP_VIOLATION cascade:

  #1 _get_changed_files must attribute ONLY the agent's own deltas — pre-existing
     dirty/untracked files (leftovers, regenerated runner artifacts, the input
     prompt) are subtracted via pre_existing_dirty.
  #4 _check_ownership must exempt runner-generated artifact dirs (reports, prompts,
     reviews, catalogs, cycle-logs) for every agent.
  #5 the lane loader must read BOTH `prohibited` and `prohibited_without_explicit_task`.

The real git calls in _get_changed_files are skipped under PYTEST_CURRENT_TEST, so the
git-path tests delete that env var (matching test_branch_determinism_5_4.py) and run
against a throwaway repo seeded with subprocess.
"""
from __future__ import annotations

import subprocess

import automation.run_agent_lifecycle as ral


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True)


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t.t")
    _git(repo, "config", "user.name", "t")
    (repo / "base.py").write_text("x = 1\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    return repo


# ── Fix #1: attribution scoping ────────────────────────────────────────────────

def test_get_changed_files_subtracts_pre_existing_untracked(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    # Pre-existing leftover (NOT the agent's work) + the agent's own new file.
    (repo / "leftover_artifact.json").write_text("{}\n")
    pre_existing = {"leftover_artifact.json"}
    (repo / "agent_new.py").write_text("y = 2\n")

    monkeypatch.setattr(ral, "REPO_ROOT", repo)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    changed = ral._get_changed_files(pre_dispatch_sha=head, pre_existing_dirty=pre_existing)

    assert "agent_new.py" in changed, "agent's own new file must be attributed"
    assert "leftover_artifact.json" not in changed, "pre-existing leftover must NOT be attributed"


def test_get_changed_files_keeps_committed_since_snapshot(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    # The agent commits work AFTER the snapshot.
    (repo / "committed_by_agent.py").write_text("z = 3\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "agent work")

    monkeypatch.setattr(ral, "REPO_ROOT", repo)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    changed = ral._get_changed_files(pre_dispatch_sha=head, pre_existing_dirty=set())
    assert "committed_by_agent.py" in changed


def test_get_changed_files_clean_tree_returns_empty(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    monkeypatch.setattr(ral, "REPO_ROOT", repo)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    assert ral._get_changed_files(pre_dispatch_sha=head, pre_existing_dirty=set()) == []


# ── Fix #4: runner-artifact ownership exemption ────────────────────────────────

def test_ownership_exempts_runner_artifacts():
    # Agent B owns src/**, tests/** — but runner artifacts must never trip it.
    artifacts = [
        "PM_Pack/automation/post_cycle_reviews/CYCLE_084_review.md",
        "PM_Pack/automation/ref_catalogs/cycle_reports.json",
        "PM_Pack/automation/prompts/CYCLE_084_AGENT_B_PROMPT.md",
        "PM_Pack/10_cycle_log/CYCLE_075.md",
        "docs/cycle_reports/CYCLE_084_AGENT_B.md",
    ]
    assert ral._check_ownership("B", artifacts) == []


def test_ownership_still_flags_real_cross_lane_write():
    # A genuine out-of-lane source write must still be flagged (exemption is narrow).
    viol = ral._check_ownership("E", ["src/pipeline/collector.py"])  # E forbids src/**
    assert "src/pipeline/collector.py" in viol


# ── Fix #5: lane loader reads both denylist keys ───────────────────────────────

def test_lane_loader_reads_prohibited_key(monkeypatch):
    # Force a fresh load (clear the module cache).
    monkeypatch.setattr(ral, "_OWNERSHIP_CACHE", None)
    rules = ral._get_ownership_rules("E")
    # Lane E uses `prohibited: [src/**]`; the loader previously dropped it.
    assert any("src" in f for f in rules.get("forbidden", [])), \
        "lane E's `prohibited` src/** denylist must be loaded"
