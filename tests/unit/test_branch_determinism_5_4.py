"""Item 5.4 (determinism): the per-cycle integration branch must contain current
origin/develop BEFORE prompt-gen or dispatch, so a RESUMED cycle never runs stale
pre-merge code (the 2026-06-21 milestone failure: cycle/083/integration was 3 behind
develop and the runner checked it out as-is, reverting merged fixes).

These tests pin ensure_integration_branch_current()'s four cases + fail-closed
behavior, and _sync_or_block()'s transient-retry-in-place vs conflict-block policy.
The helper's PYTEST guard is removed per-test (monkeypatch) so the git logic runs;
git is simulated by mocking _run_shell_command.
"""
from __future__ import annotations

import automation.ai_cycle_controller as c

DEV = "DEVSHA"


def _runner(script):
    """Build a _run_shell_command replacement. `script` = list of (predicate, (rc,out));
    first matching predicate wins; unmatched git calls default to (0, "")."""
    def run(args):
        run.calls.append(list(args))
        for pred, result in script:
            if pred(args):
                return result
        return (0, "")
    run.calls = []
    return run


def _joined(a):
    return " ".join(a)


# Common predicate helpers
_clean = (lambda a: a[1] == "status", (0, ""))
_dirty = (lambda a: a[1] == "status", (0, " M src/x.py"))
_fetch_ok = (lambda a: a[1] == "fetch" and "develop" in a, (0, ""))
_devsha = (lambda a: a[1:4] == ["rev-parse", "--verify", "origin/develop"], (0, DEV + "\n"))
_local_exists = (lambda a: a[1] == "rev-parse" and "refs/heads/" in _joined(a), (0, "LOCAL\n"))
_local_absent = (lambda a: a[1] == "rev-parse" and "refs/heads/" in _joined(a), (1, ""))
_checkout_ok = (lambda a: a[1] == "checkout", (0, ""))


def _setup(monkeypatch, script):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)  # let the git logic run
    monkeypatch.setattr(c, "_run_shell_command", _runner(script))


def test_case_b_behind_zero_ahead_hard_aligns(monkeypatch):
    # The cycle-83 case: branch 3 behind develop, 0 ahead, clean -> reset --hard.
    script = [
        _clean, _fetch_ok, _devsha, _local_exists, _checkout_ok,
        (lambda a: a[1] == "rev-list" and f"HEAD..{DEV}" in _joined(a), (0, "3\n")),   # behind
        (lambda a: a[1] == "rev-list" and f"{DEV}..HEAD" in _joined(a), (0, "0\n")),   # ahead
        (lambda a: a[1] == "reset", (0, "")),
    ]
    run = _runner(script)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(c, "_run_shell_command", run)
    res = c.ensure_integration_branch_current(83)
    assert res["action"] == "fast_forwarded"
    assert res["behind"] == 3 and res["ahead"] == 0
    assert any(a[1] == "reset" and "--hard" in a and DEV in a for a in run.calls), \
        "must hard-align to develop"


def test_case_c_behind_with_work_merges_develop(monkeypatch):
    # Agent commits present (ahead>0) -> merge develop IN, preserving work.
    script = [
        _clean, _fetch_ok, _devsha, _local_exists, _checkout_ok,
        (lambda a: a[1] == "rev-list" and f"HEAD..{DEV}" in _joined(a), (0, "2\n")),
        (lambda a: a[1] == "rev-list" and f"{DEV}..HEAD" in _joined(a), (0, "4\n")),   # 4 ahead
        (lambda a: "merge" in a, (0, "Merge made")),
    ]
    run = _runner(script)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(c, "_run_shell_command", run)
    res = c.ensure_integration_branch_current(84)
    assert res["action"] == "merged_develop"
    assert any("merge" in a and "--no-ff" in a for a in run.calls)
    assert not any(a[1] == "reset" for a in run.calls), "must NOT reset when work exists"


def test_case_d_merge_conflict_aborts_and_raises_nontransient(monkeypatch):
    script = [
        _clean, _fetch_ok, _devsha, _local_exists, _checkout_ok,
        (lambda a: a[1] == "rev-list" and f"HEAD..{DEV}" in _joined(a), (0, "1\n")),
        (lambda a: a[1] == "rev-list" and f"{DEV}..HEAD" in _joined(a), (0, "1\n")),
        (lambda a: "merge" in a and "--abort" not in a, (1, "CONFLICT (content): merge conflict")),
        (lambda a: "merge" in a and "--abort" in a, (0, "")),
    ]
    run = _runner(script)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(c, "_run_shell_command", run)
    import pytest
    with pytest.raises(c.BranchSyncError) as ei:
        c.ensure_integration_branch_current(84)
    assert ei.value.transient is False
    assert any("merge" in a and "--abort" in a for a in run.calls), "must abort the conflicted merge"


def test_case_a_fresh_creates_from_develop(monkeypatch):
    script = [
        _clean, _fetch_ok, _devsha,
        _local_absent,                                                  # no local branch
        (lambda a: a[1] == "rev-parse" and "refs/remotes/origin/" in _joined(a), (1, "")),  # no remote
        (lambda a: a[1] == "checkout" and "-B" in a and "origin/develop" in a, (0, "")),
    ]
    run = _runner(script)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(c, "_run_shell_command", run)
    res = c.ensure_integration_branch_current(90)
    assert res["action"] == "created_from_develop"
    assert res["behind"] == 0 and res["ahead"] == 0
    assert any(a[1] == "checkout" and "-B" in a and "origin/develop" in a for a in run.calls)


def test_already_current_is_noop(monkeypatch):
    script = [
        _clean, _fetch_ok, _devsha, _local_exists, _checkout_ok,
        (lambda a: a[1] == "rev-list" and f"HEAD..{DEV}" in _joined(a), (0, "0\n")),   # behind 0
        (lambda a: a[1] == "rev-list" and f"{DEV}..HEAD" in _joined(a), (0, "0\n")),
    ]
    run = _runner(script)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(c, "_run_shell_command", run)
    res = c.ensure_integration_branch_current(84)
    assert res["action"] == "already_current"
    assert not any(a[1] in ("reset", "merge") for a in run.calls), "no mutation when current"


def test_dirty_tree_is_stashed_not_blocked(monkeypatch):
    # Crashed-mid-run resume: dirty tree must be STASHED (preserved), not fail-closed.
    script = [
        _dirty,
        (lambda a: a[1] == "stash", (0, "Saved working directory")),
        _fetch_ok, _devsha, _local_exists, _checkout_ok,
        (lambda a: a[1] == "rev-list" and f"HEAD..{DEV}" in _joined(a), (0, "1\n")),
        (lambda a: a[1] == "rev-list" and f"{DEV}..HEAD" in _joined(a), (0, "0\n")),
        (lambda a: a[1] == "reset", (0, "")),
    ]
    run = _runner(script)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(c, "_run_shell_command", run)
    res = c.ensure_integration_branch_current(83)
    assert res["stashed"] is True
    assert any(a[1] == "stash" and "--include-untracked" in a for a in run.calls)
    assert res["action"] == "fast_forwarded"  # proceeds after stashing


def test_behind_count_tolerates_stderr_warning(monkeypatch):
    # Bug fix: _run_shell_command concatenates stdout+stderr; a git warning line must
    # NOT break int() parsing of the rev-list count (which would crash the tick).
    script = [
        _clean, _fetch_ok, _devsha, _local_exists, _checkout_ok,
        (lambda a: a[1] == "rev-list" and f"HEAD..{DEV}" in _joined(a),
         (0, "3\nwarning: refname 'origin/develop' is ambiguous.\n")),   # count + stderr warning
        (lambda a: a[1] == "rev-list" and f"{DEV}..HEAD" in _joined(a), (0, "0\n")),
        (lambda a: a[1] == "reset", (0, "")),
    ]
    run = _runner(script)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(c, "_run_shell_command", run)
    res = c.ensure_integration_branch_current(83)  # must NOT raise ValueError
    assert res["behind"] == 3 and res["ahead"] == 0
    assert res["action"] == "fast_forwarded"


def test_unparsable_count_raises_transient(monkeypatch):
    script = [
        _clean, _fetch_ok, _devsha, _local_exists, _checkout_ok,
        (lambda a: a[1] == "rev-list" and f"HEAD..{DEV}" in _joined(a), (0, "fatal: garbage\n")),
    ]
    run = _runner(script)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(c, "_run_shell_command", run)
    import pytest
    with pytest.raises(c.BranchSyncError) as ei:
        c.ensure_integration_branch_current(83)
    assert ei.value.transient is True


def test_stash_name_avoids_janitor_gc_patterns(monkeypatch):
    # The parked-work stash must NOT match any repo_janitor STALE_STASH_PATTERNS,
    # else the janitor GCs it after 72h (silent data loss).
    from automation.repo_janitor import STALE_STASH_PATTERNS
    captured = {}
    script = [
        _dirty,
        (lambda a: a[1] == "stash" and (captured.update(name=a[-1]) or True), (0, "Saved")),
        _fetch_ok, _devsha, _local_exists, _checkout_ok,
        (lambda a: a[1] == "rev-list" and f"HEAD..{DEV}" in _joined(a), (0, "2\n")),   # behind>0 -> mutates -> stashes
        (lambda a: a[1] == "rev-list" and f"{DEV}..HEAD" in _joined(a), (0, "0\n")),
        (lambda a: a[1] == "reset", (0, "")),
    ]
    run = _runner(script)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(c, "_run_shell_command", run)
    res = c.ensure_integration_branch_current(83)
    assert res["stashed"] is True
    name = captured["name"].lower()
    assert not any(p in name for p in STALE_STASH_PATTERNS), \
        f"stash name '{name}' matches a janitor GC pattern -> would be silently dropped"


def test_current_branch_with_dirty_tree_is_NOT_stashed(monkeypatch):
    # Codex P1: at READY_TO_DISPATCH the dirty tree is the freshly-validated prompts.
    # When already current (behind==0) the helper must NOT stash them (would break
    # dispatch — run-agent would find no prompts).
    stash_calls = []
    script = [
        _dirty,                                                  # tree dirty (the prompts)
        (lambda a: a[1] == "stash" and (stash_calls.append(a) or True), (0, "Saved")),
        _fetch_ok, _devsha, _local_exists, _checkout_ok,
        (lambda a: a[1] == "rev-list" and f"HEAD..{DEV}" in _joined(a), (0, "0\n")),   # behind==0
        (lambda a: a[1] == "rev-list" and f"{DEV}..HEAD" in _joined(a), (0, "0\n")),
    ]
    run = _runner(script)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(c, "_run_shell_command", run)
    res = c.ensure_integration_branch_current(83)
    assert res["action"] == "already_current"
    assert res["stashed"] is False, "must NOT stash when already current"
    assert not stash_calls, "no git stash when behind==0 (prompts preserved)"


def test_sync_or_block_unexpected_exception_is_failclosed(monkeypatch):
    # A non-BranchSyncError must NOT propagate out of the guard (would crash cmd_tick
    # before the tick.lock release). It is treated as transient -> retry/block.
    def _boom(cycle):
        raise RuntimeError("unexpected git glitch")
    monkeypatch.setattr(c, "ensure_integration_branch_current", _boom)
    monkeypatch.setattr("automation.state_writer.write_controller_state", lambda *a, **k: None)
    monkeypatch.setattr("automation.notification_router.notify_blocked", lambda *a, **k: None)
    monkeypatch.setattr(c, "_SYNC_MAX_TRANSIENT", 2, raising=False)
    c._tick_counter("develop_sync_retry_55", reset=True)
    assert c._sync_or_block(55, "dispatch agents") is None  # does not raise
    assert c._sync_or_block(55, "dispatch agents") is None  # 2nd -> exhausted -> block, still no raise


def test_transient_fetch_failure_raises_transient(monkeypatch):
    script = [
        _clean,
        (lambda a: a[1] == "fetch" and "develop" in a, (1, "fatal: unable to access ... timed out")),
    ]
    run = _runner(script)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setattr(c, "_run_shell_command", run)
    import pytest
    with pytest.raises(c.BranchSyncError) as ei:
        c.ensure_integration_branch_current(83)
    assert ei.value.transient is True


def test_pytest_guard_skips(monkeypatch):
    # Under pytest (env set) the helper is a no-op so the suite never touches git.
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "yes")
    res = c.ensure_integration_branch_current(83)
    assert res["action"] == "skipped_pytest"


def test_sync_or_block_returns_skipped_under_pytest_not_an_advance(monkeypatch):
    # Regression (CI #129): under pytest the real _sync_or_block returns
    # "skipped_pytest". READY_TO_DISPATCH must treat that like "already_current"
    # (proceed to dispatch), NOT as a branch-advance that bounces back to COMPILED
    # (which broke test_tick_preserves_pr_create_failed_state). Pin the value so the
    # call site's membership check (already_current/skipped_pytest -> proceed) holds.
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "yes")
    assert c._sync_or_block(83, "dispatch agents") == "skipped_pytest"


# ── _sync_or_block policy ─────────────────────────────────────────────────────

def test_sync_or_block_conflict_writes_blocked(monkeypatch):
    def _raise(cycle):
        raise c.BranchSyncError("merge conflicted", transient=False)
    monkeypatch.setattr(c, "ensure_integration_branch_current", _raise)
    writes = []
    monkeypatch.setattr("automation.state_writer.write_controller_state",
                        lambda status, **k: writes.append((status, k)))
    monkeypatch.setattr("automation.notification_router.notify_blocked",
                        lambda *a, **k: None)
    ok = c._sync_or_block(83, "dispatch agents")
    assert ok is None  # conflict -> None (caller must not proceed)
    assert any(w[0] == "DEVELOP_SYNC_BLOCKED" for w in writes)


def test_sync_or_block_transient_retries_in_place_then_blocks(monkeypatch):
    def _raise(cycle):
        raise c.BranchSyncError("fetch timed out", transient=True)
    monkeypatch.setattr(c, "ensure_integration_branch_current", _raise)
    writes = []
    monkeypatch.setattr("automation.state_writer.write_controller_state",
                        lambda status, **k: writes.append(status))
    monkeypatch.setattr("automation.notification_router.notify_blocked",
                        lambda *a, **k: None)
    # First _SYNC_MAX_TRANSIENT-1 calls: retry in place (no BLOCKED write); last: block.
    monkeypatch.setattr(c, "_SYNC_MAX_TRANSIENT", 3, raising=False)
    c._tick_counter("develop_sync_retry_77", reset=True)  # isolate from prior tests
    r1 = c._sync_or_block(77, "generate prompts")
    r2 = c._sync_or_block(77, "generate prompts")
    assert r1 is None and r2 is None
    assert "DEVELOP_SYNC_BLOCKED" not in writes, "transient retries must NOT block early"
    r3 = c._sync_or_block(77, "generate prompts")  # 3rd -> exhausted -> block
    assert r3 is None
    assert "DEVELOP_SYNC_BLOCKED" in writes


def test_sync_or_block_returns_action_string(monkeypatch):
    # Returns the ACTION (truthy) on success so READY_TO_DISPATCH can tell apart
    # "already_current" (dispatch) from an advance (regenerate — Codex P2).
    monkeypatch.setattr(c, "ensure_integration_branch_current",
                        lambda cycle: {"branch": f"cycle/{cycle:03d}/integration",
                                       "action": "already_current", "behind": 0, "ahead": 0})
    assert c._sync_or_block(83, "dispatch agents") == "already_current"
    monkeypatch.setattr(c, "ensure_integration_branch_current",
                        lambda cycle: {"branch": f"cycle/{cycle:03d}/integration",
                                       "action": "fast_forwarded", "behind": 3, "ahead": 0})
    assert c._sync_or_block(83, "dispatch agents") == "fast_forwarded"


# ── Item 5.4-T5: dirty-repo guard blocks only on uncommitted TRACKED source ───
from automation.ai_cycle_controller import _dirty_blocking_lines as _dbl  # noqa: E402

_PREFIXES_T5 = (
    "PM_Pack/automation/runs/",
    "PM_Pack/automation/post_cycle_reviews/",
    "PM_Pack/10_cycle_log/",
)


def test_untracked_runner_output_never_blocks():
    # The exact wedge: pre-existing untracked cycle-logs + a synthesis-json artifact
    # must NOT trip BLOCKED_DIRTY_REPO (they are the loop's own output, not source).
    raw = (
        "?? PM_Pack/10_cycle_log/CYCLE_075.md\n"
        "?? PM_Pack/10_cycle_log/CYCLE_075_scrum_1072_spec.md\n"
        "?? docs/cycle_reports/CYCLE_083_SYNTHESIS.json\n"
    )
    assert _dbl(raw, _PREFIXES_T5) == [], "untracked runner output must not block"


def test_tracked_source_change_still_blocks():
    raw = " M src/pipeline/collector.py\n"
    assert _dbl(raw, _PREFIXES_T5) == [" M src/pipeline/collector.py"]


def test_tracked_cycle_log_modification_is_exempt():
    # One of the 353 tracked cycle-log files modified -> exempt via the prefix.
    raw = " M PM_Pack/10_cycle_log/00_index/MASTER_INDEX.md\n"
    assert _dbl(raw, _PREFIXES_T5) == []


def test_tracked_artifact_path_modification_is_exempt():
    raw = " M PM_Pack/automation/runs/CYCLE_099/run.json\n"
    assert _dbl(raw, _PREFIXES_T5) == []


def test_mixed_only_tracked_source_blocks():
    raw = (
        "?? PM_Pack/10_cycle_log/CYCLE_075.md\n"          # untracked log -> ignore
        " M PM_Pack/10_cycle_log/00_index/QUICK_NAV.md\n"  # tracked log -> exempt
        " M PM_Pack/automation/runs/x.json\n"             # tracked artifact -> exempt
        " M src/scoring/ranker.py\n"                       # tracked SOURCE -> blocks
        "A  automation/new_real_module.py\n"               # tracked add SOURCE -> blocks
    )
    blocking = _dbl(raw, _PREFIXES_T5)
    assert blocking == [" M src/scoring/ranker.py", "A  automation/new_real_module.py"]


def test_untracked_source_file_also_does_not_block():
    # Even an untracked .py is the runner's transient output at the guard point
    # (agents commit their work); only TRACKED uncommitted source blocks.
    raw = "?? src/experimental/scratch.py\n"
    assert _dbl(raw, _PREFIXES_T5) == []
