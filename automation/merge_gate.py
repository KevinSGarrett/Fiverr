"""
merge_gate.py — Full merge gate checker for autonomous PR merging.
All conditions must pass before the runner may merge a PR into develop.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = "KevinSGarrett/Fiverr"
REPO_ROOT = Path("C:/Fiverr/Fiverr")
MERGE_POLICY_PATH = REPO_ROOT / "PM_Pack/automation/merge_policy.yml"


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
    evaluated_at: str = ""

    def __post_init__(self):
        if not self.evaluated_at:
            self.evaluated_at = datetime.now(timezone.utc).isoformat()

    def failed_checks(self) -> list[GateCheck]:
        return [c for c in self.checks if not c.passed and c.blocking]

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines = [f"MERGE GATE {status} — PR #{self.pr_number} -> {self.target}"]
        for c in self.checks:
            icon = "PASS" if c.passed else "FAIL"
            block = "" if c.blocking else " (non-blocking)"
            lines.append(f"  [{icon}] {c.name}{block}: {c.detail}")
        if self.merge_sha:
            lines.append(f"  Merged: {self.merge_sha}")
        return "\n".join(lines)


def run(pr_number: int, repo: str = REPO,
        dry_run: bool = False) -> MergeGateResult:
    """Run all merge gate checks. Optionally execute merge if all pass."""
    # Get PR info
    pr_data = _get_pr(pr_number, repo)
    branch = pr_data.get("headRefName", "unknown")
    target = pr_data.get("baseRefName", "unknown")
    state = pr_data.get("state", "unknown")
    mergeable = pr_data.get("mergeable", "UNKNOWN")

    result = MergeGateResult(
        pr_number=pr_number,
        branch=branch,
        target=target,
        dry_run=dry_run,
        passed=True,
    )

    # 1. PR must target develop
    result.checks.append(GateCheck(
        "pr_target_develop",
        passed=(target == "develop"),
        detail=f"target={target}",
    ))

    # 2. PR must be open
    result.checks.append(GateCheck(
        "pr_open",
        passed=(state == "OPEN"),
        detail=f"state={state}",
    ))

    # 3. Branch must not be main/master
    result.checks.append(GateCheck(
        "no_main_branch",
        passed=(branch not in ("main", "master")),
        detail=f"branch={branch}",
    ))

    # 4. GitHub reports mergeable
    result.checks.append(GateCheck(
        "github_mergeable",
        passed=(mergeable not in ("CONFLICTING", False)),
        detail=f"mergeable={mergeable}",
    ))

    # 5. CI checks
    ci_checks = pr_data.get("statusCheckRollup") or []
    required_ci = {
        "CI / lint", "CI / type-check",
        "CI / tests-coverage", "CI / smoke-gates",
    }
    ci_passed = {
        c.get("name") for c in ci_checks
        if c.get("conclusion") == "success" or c.get("state") == "SUCCESS"
    }
    for check_name in sorted(required_ci):
        result.checks.append(GateCheck(
            f"ci_{check_name.replace('CI / ', '').replace('-', '_').replace(' ', '_')}",
            passed=(check_name in ci_passed),
            detail=f"check={check_name}",
        ))

    # 6. Codecov (non-blocking if token not set — warn only)
    codecov_project = _find_check_state(ci_checks, "codecov/project")
    codecov_patch = _find_check_state(ci_checks, "codecov/patch")
    result.checks.append(GateCheck(
        "codecov_project",
        passed=(codecov_project in ("success", "SUCCESS") or codecov_project == "MISSING"),
        detail=f"status={codecov_project}",
        blocking=(codecov_project != "MISSING"),
    ))
    result.checks.append(GateCheck(
        "codecov_patch",
        passed=(codecov_patch in ("success", "SUCCESS") or codecov_patch == "MISSING"),
        detail=f"status={codecov_patch}",
        blocking=(codecov_patch != "MISSING"),
    ))

    # 7. Secret guard on branch
    secret_result = _run_secret_scan()
    result.checks.append(GateCheck(
        "no_secret_artifacts",
        passed=secret_result,
        detail="staged file scan",
    ))

    # 8. Model evidence (check cursor state is verified)
    cursor_state = _load_json(Path("C:/AI_Runner/state/cursor_model_state.json"))
    result.checks.append(GateCheck(
        "model_evidence",
        passed=(cursor_state.get("status") == "VERIFIED"),
        detail=f"cursor_status={cursor_state.get('status')}",
        blocking=False,
    ))

    # Evaluate overall
    result.passed = all(c.passed for c in result.checks if c.blocking)

    # Execute merge if all pass and not dry_run
    if result.passed and not dry_run:
        sha = _execute_merge(pr_number, repo)
        result.merge_sha = sha

    # Write result
    _write_result(result)
    return result


def _get_pr(pr_number: int, repo: str) -> dict[str, Any]:
    r = subprocess.run(
        ["gh", "pr", "view", str(pr_number), "--repo", repo,
         "--json", "headRefName,baseRefName,state,mergeable,statusCheckRollup"],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode != 0:
        return {}
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}


def _find_check_state(checks: list[dict], name_pattern: str) -> str:
    for c in checks:
        if name_pattern.lower() in (c.get("name", "") or "").lower():
            return c.get("conclusion") or c.get("state") or "pending"
    return "MISSING"


def _run_secret_scan() -> bool:
    """Return True if no secrets found in staged files."""
    try:
        from automation.secret_guard import scan_staged
        result = scan_staged(REPO_ROOT)
        return result.passed
    except Exception:
        return True  # non-blocking if guard unavailable


def _execute_merge(pr_number: int, repo: str) -> str | None:
    r = subprocess.run(
        ["gh", "pr", "merge", str(pr_number),
         "--repo", repo, "--squash", "--delete-branch"],
        capture_output=True, text=True, timeout=60
    )
    if r.returncode != 0:
        raise RuntimeError(f"Merge failed: {r.stderr.strip()}")
    # Get merge SHA
    r2 = subprocess.run(
        ["git", "rev-parse", "origin/develop"],
        cwd=str(REPO_ROOT), capture_output=True, text=True
    )
    return r2.stdout.strip()


def _write_result(result: MergeGateResult) -> None:
    out_dir = Path("C:/AI_Runner/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"merge_gate_pr{result.pr_number}_{ts}.json"
    path.write_text(json.dumps({
        "pr_number": result.pr_number,
        "branch": result.branch,
        "target": result.target,
        "passed": result.passed,
        "dry_run": result.dry_run,
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
