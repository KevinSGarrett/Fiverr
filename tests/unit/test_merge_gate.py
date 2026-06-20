"""Unit tests for merge_gate.py — corrected autonomous merge gate (item 3.2).

All gh/git calls are mocked. Verifies: safe-by-default (no merge without
execute), idempotency, runner_paths isolation, casing-correct CI evaluation,
strict mergeable, fail-closed secret scan, fail-closed merge execution, the
authoritative merge SHA + receipt, and that the merge command is squash-only with
--match-head-commit and NEVER --admin.
"""
from __future__ import annotations

import json
import shutil
from unittest.mock import MagicMock

import pytest

from automation import merge_gate, required_checks, runner_paths


@pytest.fixture(autouse=True)
def _clean_merge_receipts():
    """Merge receipts persist in the session tmp runner root; wipe them per test
    so idempotency short-circuits from one test don't pollute another (PR numbers
    are reused across tests)."""
    def _wipe():
        d = runner_paths.state_dir() / "merge_receipts"
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    _wipe()
    yield
    _wipe()


# ── helpers ──────────────────────────────────────────────────────────────────
def _rollup_green() -> list[dict]:
    return [{"__typename": "CheckRun", "name": n, "conclusion": "SUCCESS",
             "status": "COMPLETED"} for n in required_checks.REQUIRED_CONTEXTS]


def _pr_data(**overrides) -> dict:
    base = {
        "headRefName": "cycle/075/integration",
        "baseRefName": "develop",
        "state": "OPEN",
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "CLEAN",
        "headRefOid": "deadbeef",
        "statusCheckRollup": _rollup_green(),
        "mergeCommit": None,
    }
    base.update(overrides)
    return base


def _seed_model_verified() -> None:
    p = runner_paths.state_dir() / "cursor_model_state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"status": "VERIFIED"}))


def _happy_path(monkeypatch, *, pr_data=None, merge_returns="mergesha123"):
    """Wire all gh-touching seams to a passing happy path; return a dict of mocks."""
    pr_data = pr_data if pr_data is not None else _pr_data()
    merged = {"executed": 0}

    monkeypatch.setattr(merge_gate, "_get_pr", lambda n, r: pr_data)
    monkeypatch.setattr(merge_gate, "read_threads",
                        lambda n, r: MagicMock(merge_blocked=False, threads=[], blockers=[]))
    monkeypatch.setattr(merge_gate.required_checks, "get_required_contexts",
                        lambda *a, **k: set(required_checks.REQUIRED_CONTEXTS))

    def _fake_exec(n, r, head_sha=""):
        merged["executed"] += 1
        merged["head_sha"] = head_sha
        return merge_returns

    monkeypatch.setattr(merge_gate, "_execute_merge", _fake_exec)
    # controller_state not POST_CYCLE_PENDING + model verified
    _seed_model_verified()
    ctrl = runner_paths.state_dir() / "controller_state.json"
    ctrl.write_text(json.dumps({"status": "AWAITING_CI_GREEN"}))
    return merged


# ── dataclasses ──────────────────────────────────────────────────────────────
def test_gate_check_defaults_blocking_true() -> None:
    c = merge_gate.GateCheck(name="x", passed=True, detail="ok")
    assert c.blocking is True


def test_failed_checks_only_blocking() -> None:
    r = merge_gate.MergeGateResult(pr_number=1, branch="b", target="develop",
                                   dry_run=True, passed=False)
    r.checks = [
        merge_gate.GateCheck("a", passed=True, blocking=True),
        merge_gate.GateCheck("b", passed=False, blocking=True),
        merge_gate.GateCheck("c", passed=False, blocking=False),
    ]
    assert [c.name for c in r.failed_checks()] == ["b"]


# ── safe by default ──────────────────────────────────────────────────────────
def test_default_does_not_merge(monkeypatch) -> None:
    merged = _happy_path(monkeypatch)
    result = merge_gate.run(pr_number=1)  # dry_run=True, execute=False defaults
    assert result.passed is True
    assert merged["executed"] == 0
    assert result.merge_sha is None
    assert result.dry_run is True


def test_execute_merges_when_all_green(monkeypatch) -> None:
    merged = _happy_path(monkeypatch)
    result = merge_gate.run(pr_number=42, execute=True, dry_run=False)
    assert result.passed is True
    assert merged["executed"] == 1
    assert result.merge_sha == "mergesha123"
    assert merged["head_sha"] == "deadbeef"  # match-head-commit value passed through
    # receipt written for idempotency
    assert (runner_paths.state_dir() / "merge_receipts" / "pr42.json").exists()


# ── idempotency ──────────────────────────────────────────────────────────────
def test_already_merged_is_idempotent_success(monkeypatch) -> None:
    merged = _happy_path(
        monkeypatch,
        pr_data=_pr_data(state="MERGED", mergeCommit={"oid": "abc123"}),
    )
    result = merge_gate.run(pr_number=7, execute=True, dry_run=False)
    assert result.already_merged is True
    assert result.passed is True
    assert result.merge_sha == "abc123"
    assert merged["executed"] == 0  # never re-merges


def test_receipt_makes_rerun_idempotent(monkeypatch) -> None:
    merged = _happy_path(monkeypatch)
    # Pre-write a receipt for this PR.
    rp = runner_paths.state_dir() / "merge_receipts" / "pr99.json"
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps({"pr_number": 99, "merge_sha": "prior"}))
    result = merge_gate.run(pr_number=99, execute=True, dry_run=False)
    assert result.already_merged is True
    assert result.merge_sha == "prior"
    assert merged["executed"] == 0


# ── blocking conditions ──────────────────────────────────────────────────────
def test_failed_required_ci_blocks(monkeypatch) -> None:
    rollup = [{"name": n, "conclusion": ("FAILURE" if n == "CI / tests-coverage" else "SUCCESS")}
              for n in required_checks.REQUIRED_CONTEXTS]
    merged = _happy_path(monkeypatch, pr_data=_pr_data(statusCheckRollup=rollup))
    result = merge_gate.run(pr_number=1, execute=True, dry_run=False)
    assert result.passed is False
    assert merged["executed"] == 0
    assert any(c.name == "ci::CI / tests-coverage" and not c.passed for c in result.checks)


def test_pending_required_ci_blocks(monkeypatch) -> None:
    rollup = [{"name": n, "conclusion": "SUCCESS"} for n in required_checks.REQUIRED_CONTEXTS
              if n != "Validate PR"]  # missing required check -> pending
    merged = _happy_path(monkeypatch, pr_data=_pr_data(statusCheckRollup=rollup))
    result = merge_gate.run(pr_number=1, execute=True, dry_run=False)
    assert result.passed is False
    assert merged["executed"] == 0


def test_mergeable_unknown_blocks(monkeypatch) -> None:
    merged = _happy_path(monkeypatch, pr_data=_pr_data(mergeable="UNKNOWN"))
    result = merge_gate.run(pr_number=1, execute=True, dry_run=False)
    assert result.passed is False
    assert merged["executed"] == 0
    assert any(c.name == "github_mergeable" and not c.passed for c in result.checks)


def test_conflicting_blocks(monkeypatch) -> None:
    merged = _happy_path(monkeypatch, pr_data=_pr_data(mergeable="CONFLICTING"))
    result = merge_gate.run(pr_number=1, execute=True, dry_run=False)
    assert result.passed is False
    assert merged["executed"] == 0


def test_non_develop_target_blocks(monkeypatch) -> None:
    _happy_path(monkeypatch, pr_data=_pr_data(baseRefName="main"))
    result = merge_gate.run(pr_number=1, execute=True, dry_run=False)
    assert result.passed is False


def test_codex_unresolved_blocks(monkeypatch) -> None:
    _happy_path(monkeypatch)
    monkeypatch.setattr(merge_gate, "read_threads",
                        lambda n, r: MagicMock(merge_blocked=True, threads=[1], blockers=[1]))
    result = merge_gate.run(pr_number=1, execute=True, dry_run=False)
    assert result.passed is False
    assert any(c.name == "codex_review_disposition" and not c.passed for c in result.checks)


# ── runner_paths isolation ───────────────────────────────────────────────────
def test_model_evidence_read_from_runner_paths(monkeypatch) -> None:
    _happy_path(monkeypatch)
    # Overwrite the seeded VERIFIED state with a non-verified one in the SAME
    # (isolated) runner state dir; the gate must read it and block.
    (runner_paths.state_dir() / "cursor_model_state.json").write_text(
        json.dumps({"status": "UNVERIFIED"})
    )
    result = merge_gate.run(pr_number=1, execute=True, dry_run=False)
    assert result.passed is False
    assert any(c.name == "model_evidence_cursor" and not c.passed for c in result.checks)


def test_post_cycle_pending_blocks(monkeypatch) -> None:
    _happy_path(monkeypatch)
    (runner_paths.state_dir() / "controller_state.json").write_text(
        json.dumps({"status": "POST_CYCLE_PENDING"})
    )
    result = merge_gate.run(pr_number=1, execute=True, dry_run=False)
    assert result.passed is False
    assert any(c.name == "post_cycle_gate" and not c.passed for c in result.checks)


# ── secret scanning delegated to required CI ──────────────────────────────────
def test_secret_scanning_delegated_to_required_ci(monkeypatch) -> None:
    # The no-op local staged-file scan was removed; "Secret Scan" must be in the
    # required-CI set so secrets are gated by the server-side CI job instead.
    assert "Secret Scan" in required_checks.REQUIRED_CONTEXTS
    _happy_path(monkeypatch)
    result = merge_gate.run(pr_number=1)
    assert not any(c.name == "no_secret_artifacts" for c in result.checks)


# ── fail-closed ──────────────────────────────────────────────────────────────
def test_gate_error_fails_closed(monkeypatch) -> None:
    # An unexpected error anywhere in run() must fail closed (no merge).
    merged = _happy_path(monkeypatch)
    monkeypatch.setattr(merge_gate, "_get_pr",
                        lambda n, r: (_ for _ in ()).throw(RuntimeError("gh exploded")))
    result = merge_gate.run(pr_number=1, execute=True, dry_run=False)
    assert result.passed is False
    assert result.merge_sha is None
    assert merged["executed"] == 0
    assert any(c.name == "gate_error" and not c.passed for c in result.checks)


def test_merge_success_without_sha_is_not_blocked(monkeypatch) -> None:
    # merged flag (item-3.2 fix #6): a successful merge whose SHA did not resolve
    # must NOT be treated as a failure.
    merged = _happy_path(monkeypatch, merge_returns=None)
    result = merge_gate.run(pr_number=1, execute=True, dry_run=False)
    assert merged["executed"] == 1
    assert result.passed is True
    assert result.merged is True  # success even though merge_sha is None
    assert result.merge_sha is None


def test_merge_execution_failure_is_fail_closed(monkeypatch) -> None:
    _happy_path(monkeypatch)

    def _boom(n, r, head_sha=""):
        raise RuntimeError("gh merge 405")

    monkeypatch.setattr(merge_gate, "_execute_merge", _boom)
    result = merge_gate.run(pr_number=1, execute=True, dry_run=False)  # must NOT raise
    assert result.passed is False
    assert result.merge_sha is None
    assert any(c.name == "merge_execution" and not c.passed for c in result.checks)


def test_result_artifact_always_written(monkeypatch) -> None:
    _happy_path(monkeypatch)
    before = list((runner_paths.reports_dir()).glob("merge_gate_pr*.json")) \
        if runner_paths.reports_dir().exists() else []
    merge_gate.run(pr_number=123)
    after = list((runner_paths.reports_dir()).glob("merge_gate_pr*.json"))
    assert len(after) > len(before)


# ── merge command shape ──────────────────────────────────────────────────────
def test_execute_merge_command_is_squash_no_admin(monkeypatch) -> None:
    captured = {}

    class _R:
        returncode = 0
        stdout = "mergedsha\n"
        stderr = ""

    def _fake_run(cmd, **kwargs):
        captured.setdefault("cmds", []).append(cmd)
        return _R()

    monkeypatch.setattr(merge_gate.subprocess, "run", _fake_run)
    sha = merge_gate._execute_merge(5, "KevinSGarrett/Fiverr", head_sha="abc")
    merge_cmd = captured["cmds"][0]
    assert "merge" in merge_cmd and "--squash" in merge_cmd
    assert "--delete-branch" in merge_cmd
    assert "--match-head-commit" in merge_cmd and "abc" in merge_cmd
    # Squash ONLY — never a merge-commit or rebase, never --admin/CI bypass.
    assert "--admin" not in merge_cmd
    assert "--merge" not in merge_cmd
    assert "--rebase" not in merge_cmd
    assert sha == "mergedsha"


def test_execute_merge_omits_match_head_when_no_sha(monkeypatch) -> None:
    class _R:
        returncode = 0
        stdout = "s\n"
        stderr = ""

    captured = {}

    def _run(cmd, **k):
        captured.setdefault("cmd", cmd)
        return _R()

    monkeypatch.setattr(merge_gate.subprocess, "run", _run)
    merge_gate._execute_merge(5, "KevinSGarrett/Fiverr")  # no head_sha
    assert "--match-head-commit" not in captured["cmd"]


def test_run_threads_head_sha_into_merge_command(monkeypatch) -> None:
    # Item-3.2 #13: the gate-evaluated head SHA (headRefOid) must be the value
    # passed to --match-head-commit, not just any value. Real _execute_merge runs
    # against a mocked subprocess (no _execute_merge mock here).
    pr_data = _pr_data(headRefOid="cafef00d")
    monkeypatch.setattr(merge_gate, "_get_pr", lambda n, r: pr_data)
    monkeypatch.setattr(merge_gate, "read_threads",
                        lambda n, r: MagicMock(merge_blocked=False, threads=[], blockers=[]))
    monkeypatch.setattr(merge_gate.required_checks, "get_required_contexts",
                        lambda *a, **k: set(required_checks.REQUIRED_CONTEXTS))
    _seed_model_verified()
    (runner_paths.state_dir() / "controller_state.json").write_text(
        json.dumps({"status": "AWAITING_CI_GREEN"}))

    captured = {}

    class _R:
        returncode = 0
        stdout = "merged\n"
        stderr = ""

    monkeypatch.setattr(merge_gate.subprocess, "run",
                        lambda cmd, **k: captured.setdefault("cmds", []).append(cmd) or _R())
    result = merge_gate.run(pr_number=77, execute=True, dry_run=False)
    assert result.merged is True
    merge_cmd = next(c for c in captured["cmds"] if "merge" in c)
    assert "--match-head-commit" in merge_cmd
    assert "cafef00d" in merge_cmd


def test_receipt_with_open_state_is_idempotent(monkeypatch) -> None:
    # Item-3.2 #14: a receipt present even with state=OPEN short-circuits to
    # already-merged (trust the receipt; never attempt a second merge).
    merged = _happy_path(monkeypatch, pr_data=_pr_data(state="OPEN"))
    rp = runner_paths.state_dir() / "merge_receipts" / "pr88.json"
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps({"pr_number": 88, "merge_sha": "fromreceipt"}))
    result = merge_gate.run(pr_number=88, execute=True, dry_run=False)
    assert result.already_merged is True
    assert result.merge_sha == "fromreceipt"
    assert merged["executed"] == 0


def test_execute_merge_raises_on_failure(monkeypatch) -> None:
    class _R:
        returncode = 1
        stdout = ""
        stderr = "not mergeable"

    monkeypatch.setattr(merge_gate.subprocess, "run", lambda *a, **k: _R())
    try:
        merge_gate._execute_merge(5, "KevinSGarrett/Fiverr")
        raised = False
    except RuntimeError:
        raised = True
    assert raised
