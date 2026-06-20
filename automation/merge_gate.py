"""
merge_gate.py — Full merge gate for autonomous PR merging into ``develop``.

All BLOCKING conditions must pass before the runner may squash-merge a PR. The
Controller is the sole git authority (G1); the merge uses ``gh pr merge --squash
--delete-branch`` and NEVER ``--admin`` or any CI bypass — CI gates via branch
protection.

Item 3.2 corrections vs the original:
  * Portable ``REPO_ROOT`` (derived from ``__file__``) and all runner-state reads
    go through ``automation.runner_paths`` (test-isolatable; works on ubuntu CI).
  * The impossible ``codecov/*`` blocking checks are removed — this repo has no
    codecov checks; coverage is enforced by the required ``CI / tests-coverage``
    context (pytest ``--cov-fail-under=80``). The dead break-glass loader is gone.
  * CI success parsing + the required-check set are centralized in
    ``automation.required_checks`` (casing-correct; union with live branch
    protection, fail-closed to the known set).
  * ``mergeable`` must be ``MERGEABLE`` (``UNKNOWN``/``CONFLICTING`` block).
  * Safe by default: ``run(dry_run=True, execute=False)`` evaluates without
    merging; an irreversible merge requires an explicit ``execute=True``.
  * Merge execution is wrapped (fail-closed, never crashes the loop), idempotent
    (receipt-guarded; an already-merged PR is treated as success), records the
    authoritative merge SHA from ``mergeCommit.oid``, and uses
    ``--match-head-commit`` to abort on a race-push. A result artifact is always
    written (``finally``).
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from automation import required_checks, runner_paths
from automation.codex_thread_reader import read_threads

REPO = "KevinSGarrett/Fiverr"
REPO_ROOT = Path(__file__).resolve().parent.parent  # automation/ -> repo root


@dataclass
class GateCheck:
    name: str
    passed: bool
    detail: str = ""
    blocking: bool = True


@dataclass
class MergeGateResult:
    pr_number: int
    branch: str
    target: str
    dry_run: bool
    passed: bool
    checks: list[GateCheck] = field(default_factory=list)
    merge_sha: str | None = None
    already_merged: bool = False
    merged: bool = False  # the merge was performed (or PR already merged) this run
    evaluated_at: str = ""

    def __post_init__(self) -> None:
        if not self.evaluated_at:
            self.evaluated_at = datetime.now(UTC).isoformat()

    def failed_checks(self) -> list[GateCheck]:
        return [c for c in self.checks if not c.passed and c.blocking]

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines = [f"MERGE GATE {status} — PR #{self.pr_number} -> {self.target}"]
        for c in self.checks:
            icon = "PASS" if c.passed else "FAIL"
            block = "" if c.blocking else " (non-blocking)"
            lines.append(f"  [{icon}] {c.name}{block}: {c.detail}")
        if self.already_merged:
            lines.append("  (idempotent: PR already merged)")
        if self.merge_sha:
            lines.append(f"  Merged: {self.merge_sha}")
        return "\n".join(lines)


def _state_dir() -> Path:
    return runner_paths.state_dir()


def run(pr_number: int, repo: str = REPO, *,
        dry_run: bool = True, execute: bool = False) -> MergeGateResult:
    """Evaluate every blocking merge gate; squash-merge ONLY when ``execute`` is
    True and all blocking gates pass.

    Safe by default (``dry_run=True`` / ``execute=False``): the gate is evaluated
    and a result artifact written, but no merge is performed. A merge into
    ``develop`` is irreversible, so a caller must opt in explicitly with
    ``execute=True``. A merge failure never raises out of ``run`` — it is recorded
    as a failed ``merge_execution`` check (fail-closed) so the loop can recover.
    """
    # gh honours only GH_TOKEN — export it so gh calls here are authenticated even
    # in a fresh tick process (idempotent; the controller also calls this).
    try:
        from automation.pr_builder import _ensure_gh_token
        _ensure_gh_token()
    except Exception:
        pass

    result = MergeGateResult(
        pr_number=pr_number, branch="unknown", target="unknown",
        dry_run=(not execute), passed=True,
    )
    try:
        pr_data = _get_pr(pr_number, repo)
        result.branch = pr_data.get("headRefName", "unknown")
        result.target = pr_data.get("baseRefName", "unknown")
        state = pr_data.get("state", "UNKNOWN")
        mergeable = pr_data.get("mergeable", "UNKNOWN")
        head_sha = pr_data.get("headRefOid", "") or ""

        # ── Idempotency: already-merged PR (or a recorded receipt) is success ──
        receipt = _read_receipt(pr_number)
        if state == "MERGED" or receipt:
            result.already_merged = True
            result.merged = True
            result.passed = True
            merge_commit = (pr_data.get("mergeCommit") or {}).get("oid")
            result.merge_sha = merge_commit or (receipt or {}).get("merge_sha")
            result.checks.append(GateCheck(
                "already_merged", True,
                detail=f"state={state} receipt={bool(receipt)}",
                blocking=False,
            ))
            return result

        # 1. PR must target develop
        result.checks.append(GateCheck(
            "pr_target_develop", passed=(result.target == "develop"),
            detail=f"target={result.target}",
        ))
        # 2. PR must be open
        result.checks.append(GateCheck(
            "pr_open", passed=(state == "OPEN"), detail=f"state={state}",
        ))
        # 3. Branch must not be main/master
        result.checks.append(GateCheck(
            "no_main_branch", passed=(result.branch not in ("main", "master")),
            detail=f"branch={result.branch}",
        ))
        # 4. GitHub must report MERGEABLE (UNKNOWN/CONFLICTING/False block).
        #    UNKNOWN is GitHub still computing — fail-closed; a later tick retries.
        result.checks.append(GateCheck(
            "github_mergeable", passed=(mergeable in ("MERGEABLE", True)),
            detail=f"mergeable={mergeable}",
        ))

        # 5. Required CI checks green (casing-correct; required set = union of the
        #    known contexts with live branch protection, fail-closed).
        rollup = pr_data.get("statusCheckRollup") or []
        required = required_checks.get_required_contexts(repo)
        # Observability (non-blocking): record the required set actually used. If a
        # live branch-protection fetch failed, this falls back to the known floor
        # (still safe — GitHub enforces protection server-side at merge time).
        result.checks.append(GateCheck(
            "required_ci_set", passed=True, blocking=False,
            detail=f"{len(required)} contexts: {','.join(sorted(required))}",
        ))
        states = required_checks.latest_by_name(rollup)
        for ctx in sorted(required):
            st = states.get(ctx)
            result.checks.append(GateCheck(
                f"ci::{ctx}", passed=(st == "SUCCESS"),
                detail=f"state={st or 'MISSING'}",
            ))

        # 6. Secret scanning is enforced by the REQUIRED "Secret Scan" CI context
        # (in the required-CI set above), which scans the PR's actual diff on the
        # server. A local staged-file scan here would be a no-op at merge time (the
        # Controller's working tree has nothing staged for a remote PR merge), so
        # it is intentionally NOT performed — relying on a no-op gate would be
        # false confidence. See automation/required_checks.REQUIRED_CONTEXTS.

        # 7. Model evidence — cannot merge without verified model state.
        cursor_state = _load_json(_state_dir() / "cursor_model_state.json")
        result.checks.append(GateCheck(
            "model_evidence_cursor",
            passed=(cursor_state.get("status") == "VERIFIED"),
            detail=f"cursor_status={cursor_state.get('status', 'MISSING')}",
        ))

        # 8. Codex review disposition — all review THREADS resolved/non-blocking.
        codex_result = read_threads(pr_number, repo)
        result.checks.append(GateCheck(
            "codex_review_disposition",
            passed=not codex_result.merge_blocked,
            detail=f"threads={len(codex_result.threads)} blockers={len(codex_result.blockers)}",
        ))

        # 9. Post-cycle gate — block only if controller explicitly says pending.
        ctrl_state = _load_json(_state_dir() / "controller_state.json")
        last_status = ctrl_state.get("status", "UNKNOWN")
        result.checks.append(GateCheck(
            "post_cycle_gate", passed=(last_status != "POST_CYCLE_PENDING"),
            detail=f"controller_status={last_status}",
        ))

        # ── Evaluate ──
        result.passed = all(c.passed for c in result.checks if c.blocking)

        # ── Execute (explicit opt-in only) ──
        if result.passed and execute:
            try:
                sha = _execute_merge(pr_number, repo, head_sha)
                # The merge itself SUCCEEDED if _execute_merge did not raise; the
                # SHA is best-effort (mergeCommit may not have resolved yet). Do
                # not treat an unresolved SHA as a failure (would spuriously block
                # an already-merged PR until the idempotent retry).
                result.merged = True
                result.merge_sha = sha
                _write_receipt(pr_number, sha, result.branch)
            except Exception as e:  # fail-closed: never crash the loop
                result.passed = False
                result.checks.append(GateCheck(
                    "merge_execution", passed=False, detail=str(e)[:300],
                ))
    except Exception as e:  # any unexpected error → fail-closed
        result.passed = False
        result.checks.append(GateCheck("gate_error", passed=False, detail=str(e)[:300]))
    finally:
        _write_result(result)
    return result


def _get_pr(pr_number: int, repo: str) -> dict[str, Any]:
    r = subprocess.run(
        ["gh", "pr", "view", str(pr_number), "--repo", repo,
         "--json", "headRefName,baseRefName,state,mergeable,mergeStateStatus,"
                   "statusCheckRollup,headRefOid,mergeCommit"],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode != 0:
        return {}
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}


def _execute_merge(pr_number: int, repo: str, head_sha: str = "") -> str | None:
    cmd = ["gh", "pr", "merge", str(pr_number),
           "--repo", repo, "--squash", "--delete-branch"]
    if head_sha:
        # Abort the merge if the PR head advanced since gate evaluation (TOCTOU).
        cmd += ["--match-head-commit", head_sha]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"Merge failed: {r.stderr.strip() or r.stdout.strip()}")
    # Authoritative merge SHA from GitHub (not a possibly-stale local rev-parse).
    r2 = subprocess.run(
        ["gh", "pr", "view", str(pr_number), "--repo", repo,
         "--json", "mergeCommit", "-q", ".mergeCommit.oid"],
        capture_output=True, text=True, timeout=30,
    )
    return r2.stdout.strip() or None


# ── Idempotency receipts ────────────────────────────────────────────────────
def _receipt_path(pr_number: int) -> Path:
    return _state_dir() / "merge_receipts" / f"pr{pr_number}.json"


def _read_receipt(pr_number: int) -> dict | None:
    path = _receipt_path(pr_number)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _write_receipt(pr_number: int, merge_sha: str | None, branch: str) -> None:
    path = _receipt_path(pr_number)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "pr_number": pr_number,
        "merge_sha": merge_sha,
        "branch": branch,
        "merged_at": datetime.now(UTC).isoformat(),
    }, indent=2))


def _write_result(result: MergeGateResult) -> None:
    out_dir = runner_paths.reports_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"merge_gate_pr{result.pr_number}_{ts}.json"
    path.write_text(json.dumps({
        "pr_number": result.pr_number,
        "branch": result.branch,
        "target": result.target,
        "passed": result.passed,
        "dry_run": result.dry_run,
        "already_merged": result.already_merged,
        "evaluated_at": result.evaluated_at,
        "merge_sha": result.merge_sha,
        "checks": [
            {"name": c.name, "passed": c.passed,
             "detail": c.detail, "blocking": c.blocking}
            for c in result.checks
        ],
    }, indent=2))


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}
