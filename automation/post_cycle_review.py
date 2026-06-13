"""
post_cycle_review.py â€” Post-cycle PM review automation.

Implements the gate between a merged cycle and next-cycle dispatch.
Source prompt: PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md

Two modes:
  POST_AGENT_CYCLE_REVIEW  â€” agents done, PR open, not yet merged (draft preview)
  POST_CYCLE_PM_REVIEW     â€” PR merged to develop (canonical closeout, blocks next dispatch)
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from automation import claude_post_cycle_adapter, claude_sub_gate, state_writer

REPO_ROOT = Path(__file__).parent.parent
RUNNER_ROOT = Path("C:/AI_Runner")
POLICY_PATH = REPO_ROOT / "PM_Pack/automation/post_cycle_review_policy.yml"
SOURCE_PROMPT = REPO_ROOT / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md"
REVIEWS_DIR = REPO_ROOT / "PM_Pack/automation/post_cycle_reviews"
QUEUE_DIR = RUNNER_ROOT / "queue/post_cycle"


class ReviewMode(str, Enum):
    POST_AGENT = "POST_AGENT_CYCLE_REVIEW"
    POST_MERGE = "POST_CYCLE_PM_REVIEW"


class ReviewResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ADVISORY_ONLY = "ADVISORY_ONLY"
    DRAFT_UNMERGED_PREVIEW = "DRAFT_UNMERGED_PREVIEW"
    BLOCKED_SOURCE_PROMPT_MISSING = "BLOCKED_SOURCE_PROMPT_MISSING"
    BLOCKED_MODEL_UNVERIFIED = "BLOCKED_MODEL_UNVERIFIED"


@dataclass
class PostCycleFacts:
    cycle: int
    mode: ReviewMode
    collected_at: str = ""

    # Git facts
    head_sha: str = ""
    develop_sha: str = ""
    pr_number: int | None = None
    pr_merged: bool = False
    merge_sha: str = ""

    # Validation facts
    ci_passed: bool = False
    codecov_project: str = "UNKNOWN"
    codecov_patch: str = "UNKNOWN"
    codex_threads_resolved: bool = False
    local_ruff: bool = False
    local_mypy: bool = False
    local_pytest: bool = False
    local_coverage_pct: float = 0.0
    baseline_db_mtime_unchanged: bool = False
    scrapfly_enabled_false: bool = True

    # Jira facts
    cycle_control_done: bool = False
    next_cycle_control_created: bool = False

    # Agent report facts
    agent_reports_present: dict[str, bool] = field(default_factory=dict)

    # Scoring
    score1_internal_pct: float = 0.0
    score2_e2e_pct: float = 0.0
    tierd2_stages: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = {k: v for k, v in self.__dict__.items()}
        d["mode"] = self.mode.value
        return d


@dataclass
class PostCycleReviewResult:
    cycle: int
    mode: ReviewMode
    result: ReviewResult
    facts: PostCycleFacts
    status: str = ""
    review_result: str = ""
    reason: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    next_scope_decision: str = ""
    prompt_package_valid: bool = False
    artifact_paths: list[str] = field(default_factory=list)

    @property
    def blocks_dispatch(self) -> bool:
        if self.mode == ReviewMode.POST_AGENT and self.review_result in ("PASS", ""):
            return False
        return (self.review_result or self.result.value) != ReviewResult.PASS.value

    def summary(self) -> str:
        lines = [f"POST-CYCLE REVIEW {self.result.value} â€” Cycle {self.cycle:03d} [{self.mode.value}]"]
        for e in self.errors:
            lines.append(f"  ERROR: {e}")
        for w in self.warnings:
            lines.append(f"  WARN:  {w}")
        if self.blocks_dispatch:
            lines.append("  DISPATCH BLOCKED until this review passes")
        return "\n".join(lines)


def collect_facts(
    cycle: int,
    mode_or_repo_root: ReviewMode | Path,
    pr_number_or_runner_root: int | Path | None = None,
) -> PostCycleFacts:
    """Collect facts (legacy + new signatures supported)."""
    if isinstance(mode_or_repo_root, ReviewMode):
        mode = mode_or_repo_root
        repo_root = REPO_ROOT
        runner_root = RUNNER_ROOT
        pr_number = pr_number_or_runner_root if isinstance(pr_number_or_runner_root, int) else None
    else:
        mode = ReviewMode.POST_MERGE
        repo_root = mode_or_repo_root
        runner_root = (
            pr_number_or_runner_root if isinstance(pr_number_or_runner_root, Path) else RUNNER_ROOT
        )
        pr_number = None

    facts = PostCycleFacts(cycle=cycle, mode=mode, collected_at=datetime.now(UTC).isoformat())
    facts.head_sha = _git("rev-parse", "HEAD")
    facts.develop_sha = _git("rev-parse", "origin/develop")
    if pr_number:
        facts.pr_number = pr_number

    collectors = [
        ("local", lambda: _collect_local_code_verification(cycle, repo_root)),
        ("github", lambda: _collect_github_facts(cycle, repo_root)),
        ("jira", lambda: _collect_jira_facts(cycle)),
    ]
    collected: dict[str, Any] = {}
    for key, collector in collectors:
        try:
            collected[key] = collector()
        except Exception:
            collected[key] = {}

    github = collected.get("github", {})
    facts.pr_merged = bool(github.get("pr_merged"))
    facts.merge_sha = str(github.get("merge_sha", ""))
    facts.ci_passed = bool(github.get("ci_passed", False))
    facts.codecov_project = str(github.get("codecov_project", "UNKNOWN"))
    facts.codecov_patch = str(github.get("codecov_patch", "UNKNOWN"))

    local = collected.get("local", {})
    facts.local_ruff = bool(local.get("ruff_passed", False))
    facts.local_mypy = bool(local.get("mypy_passed", False))
    facts.local_pytest = bool(local.get("pytest_passed", False))
    facts.local_coverage_pct = float(local.get("coverage_pct", 0.0))
    facts.baseline_db_mtime_unchanged = not bool(local.get("baseline_db_modified", False))
    facts.scrapfly_enabled_false = not bool(local.get("scrapfly_enabled", True))

    jira = collected.get("jira", {})
    facts.cycle_control_done = jira.get("cycle_control_status") == "Done"

    reports_dir = repo_root / "docs/cycle_reports"
    for agent in ["A", "B", "E", "C", "F", "D"]:
        facts.agent_reports_present[agent] = (reports_dir / f"CYCLE_{cycle:03d}_AGENT_{agent}.md").exists()
    _ = runner_root
    return facts


def _collect_local_code_verification(cycle: int, repo_root: Path) -> dict[str, Any]:
    _ = cycle
    # Use _run_check so tests can monkeypatch it without spawning real subprocesses
    ruff_passed = _run_check(["python", "-m", "ruff", "check", "automation/", "src/"])
    mypy_passed = _run_check(
        ["python", "-m", "mypy", "automation/", "--ignore-missing-imports"]
    )
    pytest_passed = _run_check(
        ["python", "-m", "pytest", "tests/unit/", "-q", "--tb=short"]
    )
    baseline_db = repo_root / "data/cycle037_live.db"
    baseline_db_modified = baseline_db.exists() and (
        datetime.now(UTC).timestamp() - baseline_db.stat().st_mtime
    ) < 24 * 3600
    config = repo_root / "config.yaml"
    config_text = config.read_text(encoding="utf-8", errors="replace") if config.exists() else ""
    return {
        "ruff_passed": ruff_passed,
        "mypy_passed": mypy_passed,
        "pytest_passed": pytest_passed,
        "coverage_pct": 0.0,
        "baseline_db_modified": baseline_db_modified,
        "scrapfly_enabled": "scrapfly.enabled: true" in config_text,
    }


def _collect_github_facts(cycle: int, repo_root: Path) -> dict[str, Any]:
    """Collect PR/CI facts via _gh (patchable) instead of raw subprocess calls."""
    _ = repo_root
    try:
        pr_info = json.loads(_gh("pr", "view", "--json", "state,mergeCommit,headRefName"))
    except Exception:
        return {"pr_merged": False}

    if pr_info.get("state") != "MERGED":
        return {"pr_merged": False}

    merge_sha = (pr_info.get("mergeCommit") or {}).get("oid", "")

    try:
        checks_raw = json.loads(_gh("pr", "view", "--json", "statusCheckRollup"))
    except Exception:
        checks_raw = {}

    rollup = checks_raw.get("statusCheckRollup", [])
    # ci_passed: all non-codecov checks must succeed; codecov/patch is advisory only
    core_checks = [c for c in rollup if not c.get("name", "").startswith("codecov/")]
    ci_passed = bool(core_checks) and all(
        c.get("conclusion") == "success" for c in core_checks
    )
    codecov_project = next(
        (c.get("conclusion", "UNKNOWN").upper()
         for c in rollup if c.get("name") == "codecov/project"),
        "UNKNOWN",
    )
    codecov_patch = next(
        (c.get("conclusion", "UNKNOWN").upper()
         for c in rollup if c.get("name") == "codecov/patch"),
        "UNKNOWN",
    )
    return {
        "pr_merged": True,
        "merge_sha": merge_sha,
        "ci_passed": ci_passed,
        "codecov_project": codecov_project,
        "codecov_patch": codecov_patch,
    }
def _collect_jira_facts(cycle: int) -> dict[str, Any]:
    from automation.jira_client import JiraClient

    client = JiraClient()
    issues = client.search_issues(f'project = SCRUM AND text ~ "cycle {cycle}"', max_results=100)
    return {
        "cycle_control_status": issues[0]["fields"]["status"]["name"] if issues else "UNKNOWN",
        "in_review_stories": [i["key"] for i in issues if i["fields"]["status"]["name"] == "In Review"],
        "done_stories": [i["key"] for i in issues if i["fields"]["status"]["name"] == "Done"],
    }


def calculate_score2_with_cap(score1: float, tierd2_evidence: dict[str, Any]) -> float:
    base_cap = 50.0
    passes = sum(1 for value in tierd2_evidence.values() if str(value).upper() == "PASS")
    cap = base_cap + (passes * 2.0)
    return min(score1, cap)


def update_tierd2_tracker(evidence_dir: Path) -> dict[str, str]:
    statuses = {f"V{i}": "NOT_STARTED" for i in range(1, 10)}
    evidence = evidence_dir / "data/live_validation_evidence.json"
    if not evidence.exists():
        return statuses
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    allowed = {"NOT_STARTED", "IN_PROGRESS", "CONDITIONAL_GO", "PASS", "BLOCKED"}
    for stage in statuses:
        value = payload.get(stage)
        if value in allowed:
            statuses[stage] = value
    return statuses


def generate_post_cycle_github_bundle(cycle: int, merge_sha: str, client: Any) -> dict[str, Any]:
    return {
        "cycle": cycle,
        "merge_sha": merge_sha,
        "checks": client.get_check_runs(merge_sha),
    }


def generate_post_cycle_jira_bundle(cycle: int, jira_client: Any) -> dict[str, Any]:
    facts = _collect_jira_facts(cycle)
    return {
        "cycle": cycle,
        "done_stories": facts["done_stories"],
        "in_review_stories": facts["in_review_stories"],
        "cycle_control_status": facts["cycle_control_status"],
    }


def _legacy_run_review(cycle: int, mode: ReviewMode,
                       pr_number: int | None = None) -> PostCycleReviewResult:
    """Run a post-cycle review. Returns result with dispatch gate decision."""
    result = PostCycleReviewResult(
        cycle=cycle, mode=mode,
        result=ReviewResult.FAIL,
        facts=PostCycleFacts(cycle=cycle, mode=mode),
    )

    # â”€â”€ GATE 1: Source prompt must exist â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if not SOURCE_PROMPT.exists():
        result.result = ReviewResult.BLOCKED_SOURCE_PROMPT_MISSING
        result.errors.append(f"Source prompt missing: {SOURCE_PROMPT}")
        _write_result(result)
        return result

    # â”€â”€ GATE 2: Write queue request â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _write_queue_request(cycle, mode, pr_number)

    # â”€â”€ GATE 3: Collect deterministic facts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    result.facts = collect_facts(cycle, mode, pr_number)

    # â”€â”€ GATE 4: Validate facts (POST_MERGE requires merge) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if mode == ReviewMode.POST_MERGE and not result.facts.pr_merged:
        result.errors.append("PR not merged â€” cannot run POST_CYCLE_PM_REVIEW")
        _write_result(result)
        return result

    # â”€â”€ GATE 5: Agent reports audit â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # V5-010: missing reports are HARD ERRORS for official POST_MERGE review
    missing_reports = [a for a, present in result.facts.agent_reports_present.items()
                       if not present]
    if missing_reports:
        if mode == ReviewMode.POST_MERGE:
            result.errors.append(
                f"Missing agent reports (official review requires all 6): {missing_reports}"
            )
        else:
            result.warnings.append(f"Missing agent reports: {missing_reports}")

    # â”€â”€ GATE 6: Baseline DB integrity â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if not result.facts.baseline_db_mtime_unchanged:
        result.errors.append("cycle037_live.db mtime changed â€” baseline tampered")

    # â”€â”€ GATE 7: ScrapFly config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if not result.facts.scrapfly_enabled_false:
        result.errors.append("config.yaml has scrapfly.enabled:true â€” not allowed in commits")

    # â”€â”€ GATE 8: Claude subscription PM review (V5-010 fix) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Official POST_MERGE review MUST invoke Claude adapter.
    # If Claude is not available â†’ ADVISORY_ONLY, dispatch blocked.
    # If model/effort/adaptive thinking unverified â†’ ADVISORY_ONLY.
    if mode == ReviewMode.POST_MERGE and not result.errors:
        from automation.claude_post_cycle_adapter import run_post_cycle_review as _claude_review
        run_dir = REVIEWS_DIR / f"cycle_{result.cycle:03d}_runs" / "current"
        run_dir.mkdir(parents=True, exist_ok=True)

        # Load source prompt fresh from disk every time
        review_prompt = SOURCE_PROMPT.read_text(encoding="utf-8", errors="replace")
        facts_json = json.dumps(result.facts.to_dict(), indent=2, default=str)

        claude_result = _claude_review(
            cycle=result.cycle,
            run_dir=run_dir,
            review_prompt_text=review_prompt,
            facts_json=facts_json,
        )

        # Record Claude artifacts in result
        if claude_result.request_path:
            result.artifact_paths.append(claude_result.request_path)
        if claude_result.response_path:
            result.artifact_paths.append(claude_result.response_path)

        if claude_result.status == "BLOCKED":
            result.result = ReviewResult.BLOCKED_MODEL_UNVERIFIED
            result.errors.append(f"Claude blocked: {claude_result.error}")
        elif claude_result.status == "ADVISORY_ONLY":
            result.result = ReviewResult.ADVISORY_ONLY
            result.warnings.append(
                "Claude PM review is advisory-only: "
                + str(claude_result.error)
                + "  Next dispatch BLOCKED until official review completes."
            )
        elif claude_result.status == "PASS":
            result.result = ReviewResult.PASS
        else:
            # FAIL or ERROR from Claude
            result.result = ReviewResult.ADVISORY_ONLY
            result.warnings.append(
                f"Claude review status: {claude_result.status}. Treating as advisory."
            )

    # â”€â”€ RESULT: POST_AGENT is always preview â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif mode == ReviewMode.POST_AGENT:
        result.result = ReviewResult.DRAFT_UNMERGED_PREVIEW
    elif not result.errors:
        result.result = ReviewResult.PASS
    else:
        result.result = ReviewResult.FAIL

    _write_result(result)
    _legacy_write_artifacts(result)
    return result


def write_queue_request_for_agent_d(cycle: int) -> Path:
    """Called when Agent D completes â€” writes review queue request."""
    return _write_queue_request(cycle, ReviewMode.POST_AGENT, None)


def _write_queue_request(cycle: int, mode: ReviewMode,
                          pr_number: int | None) -> Path:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    path = QUEUE_DIR / f"CYCLE_{cycle:03d}_POST_CYCLE_REVIEW_REQUEST.json"
    path.write_text(json.dumps({
        "cycle": cycle,
        "mode": mode.value,
        "pr_number": pr_number,
        "requested_at": datetime.now(UTC).isoformat(),
        "status": "PENDING",
    }, indent=2))
    return path


def _write_result(result: PostCycleReviewResult) -> None:
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    name = f"CYCLE_{result.cycle:03d}_{result.mode.value}_{ts}"
    json_path = REVIEWS_DIR / f"{name}.json"
    md_path   = REVIEWS_DIR / f"{name}.md"

    payload = {
        "cycle": result.cycle,
        "mode": result.mode.value,
        "result": result.result.value,
        "blocks_dispatch": result.blocks_dispatch,
        "errors": result.errors,
        "warnings": result.warnings,
        "facts": result.facts.to_dict(),
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
    json_path.write_text(json.dumps(payload, indent=2))

    lines = [
        f"# Post-Cycle Review â€” Cycle {result.cycle:03d}",
        f"Mode: {result.mode.value}  Result: **{result.result.value}**",
        f"Blocks dispatch: {result.blocks_dispatch}",
        "", "## Errors",
    ]
    for e in result.errors:
        lines.append(f"- {e}")
    lines += ["", "## Warnings"]
    for w in result.warnings:
        lines.append(f"- {w}")
    lines += ["", "## Facts summary",
              f"- PR merged: {result.facts.pr_merged}",
              f"- CI passed: {result.facts.ci_passed}",
              f"- Codecov project: {result.facts.codecov_project}",
              f"- Baseline DB intact: {result.facts.baseline_db_mtime_unchanged}",
              f"- ScrapFly disabled: {result.facts.scrapfly_enabled_false}",
              f"- Agent reports: {result.facts.agent_reports_present}"]
    md_path.write_text("\n".join(lines))
    result.artifact_paths.extend([str(json_path), str(md_path)])


def _legacy_write_artifacts(result: PostCycleReviewResult) -> None:
    """Write sub-artifact files for individual audit sections."""
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    cycle = result.cycle

    # Agent report audit
    agent_audit = REVIEWS_DIR / f"CYCLE_{cycle:03d}_agent_report_audit.json"
    agent_audit.write_text(json.dumps({
        "cycle": cycle,
        "agent_reports": result.facts.agent_reports_present,
        "all_present": all(result.facts.agent_reports_present.values()),
    }, indent=2))

    # GitHub verification
    gh_verify = REVIEWS_DIR / f"CYCLE_{cycle:03d}_github_verification.json"
    gh_verify.write_text(json.dumps({
        "cycle": cycle,
        "pr_number": result.facts.pr_number,
        "pr_merged": result.facts.pr_merged,
        "merge_sha": result.facts.merge_sha,
        "ci_passed": result.facts.ci_passed,
        "codecov_project": result.facts.codecov_project,
        "codecov_patch": result.facts.codecov_patch,
        "codex_threads_resolved": result.facts.codex_threads_resolved,
    }, indent=2))

    # Jira verification
    jira_verify = REVIEWS_DIR / f"CYCLE_{cycle:03d}_jira_verification.json"
    jira_verify.write_text(json.dumps({
        "cycle": cycle,
        "cycle_control_done": result.facts.cycle_control_done,
    }, indent=2))


def _git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=str(REPO_ROOT),
                       capture_output=True, text=True, check=False)
    return r.stdout.strip()


def _gh(*args: str) -> str:
    r = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.strip()


def _run_check(cmd: list[str]) -> bool:
    r = subprocess.run(cmd, cwd=str(REPO_ROOT),
                       capture_output=True, text=True, check=False, timeout=120)
    return r.returncode == 0


def run_review(
    cycle: int,
    mode: ReviewMode,
    pr_number: int | None = None,
    repo_root: Path = REPO_ROOT,
    runner_root: Path = RUNNER_ROOT,
) -> PostCycleReviewResult:
    """Delegate to the versioned implementation which uses patchable module constants."""
    _ = (repo_root, runner_root)
    return _legacy_run_review(cycle, mode, pr_number)


def _run_review_impl_unused(
    cycle: int,
    mode: ReviewMode,
    pr_number: int | None,
    repo_root: Path,
    runner_root: Path,
) -> PostCycleReviewResult:
    """Kept for reference — run_review now delegates to _legacy_run_review."""
    _ = pr_number
    source_prompt = repo_root / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md"
    if not source_prompt.exists():
        facts = PostCycleFacts(cycle=cycle, mode=mode)
        result = PostCycleReviewResult(
            cycle=cycle,
            mode=mode,
            result=ReviewResult.FAIL,
            facts=facts,
            status="BLOCKED_MISSING_SOURCE_PROMPT",
            review_result="FAIL",
            reason="Missing source prompt",
        )
        _write_dispatch_decision(result, runner_root)
        _write_post_cycle_result(result, runner_root)
        return result

    preflight = claude_sub_gate.verify_subscription_preflight()
    if not preflight.get("passed", False):
        incident = preflight.get("incident_code", "")
        status = (
            "BLOCKED_CLAUDE_API_KEY_PRESENT"
            if incident == "BLOCKED_CLAUDE_API_KEY_PRESENT"
            else "BLOCKED_CLAUDE_NOT_LOGGED_IN"
        )
        facts = PostCycleFacts(cycle=cycle, mode=mode)
        result = PostCycleReviewResult(
            cycle=cycle,
            mode=mode,
            result=ReviewResult.FAIL,
            facts=facts,
            status=status,
            review_result="FAIL",
            reason=incident or "preflight failed",
        )
        _write_dispatch_decision(result, runner_root)
        _write_post_cycle_result(result, runner_root)
        return result

    facts = collect_facts(cycle, mode)
    facts.agent_reports_present = {
        agent: (repo_root / "docs/cycle_reports" / f"CYCLE_{cycle:03d}_AGENT_{agent}.md").exists()
        for agent in ["A", "B", "E", "C", "F", "D"]
    }
    missing = [agent for agent, present in facts.agent_reports_present.items() if not present]
    if mode == ReviewMode.POST_MERGE and missing:
        result = PostCycleReviewResult(
            cycle=cycle,
            mode=mode,
            result=ReviewResult.FAIL,
            facts=facts,
            status="BLOCKED_MISSING_AGENT_REPORT",
            review_result="FAIL",
            reason=f"Missing reports: {missing}",
            warnings=[f"Missing reports: {missing}"],
        )
        _write_dispatch_decision(result, runner_root)
        _write_post_cycle_result(result, runner_root)
        return result

    prompt_text = source_prompt.read_text(encoding="utf-8", errors="replace")
    prompt = f"{prompt_text}\n\n## Facts\n```json\n{json.dumps(facts.to_dict(), indent=2)}\n```"
    try:
        claude_result = claude_post_cycle_adapter.submit_for_review(prompt, facts.to_dict())
    except Exception as exc:
        result = PostCycleReviewResult(
            cycle=cycle,
            mode=mode,
            result=ReviewResult.ADVISORY_ONLY,
            facts=facts,
            status="ADVISORY_ONLY_ADAPTER_ERROR",
            review_result="ADVISORY_ONLY",
            reason=str(exc),
            errors=[str(exc)],
        )
        _write_dispatch_decision(result, runner_root)
        _write_post_cycle_result(result, runner_root)
        return result

    if claude_result.status != "PASS":
        result = PostCycleReviewResult(
            cycle=cycle,
            mode=mode,
            result=ReviewResult.ADVISORY_ONLY,
            facts=facts,
            status="ADVISORY_ONLY_ADAPTER_ERROR",
            review_result="ADVISORY_ONLY",
            reason=claude_result.error or claude_result.status,
            warnings=[claude_result.error or claude_result.status],
        )
    else:
        result = PostCycleReviewResult(
            cycle=cycle,
            mode=mode,
            result=ReviewResult.PASS,
            facts=facts,
            status="PASS",
            review_result="PASS",
            reason="Post-cycle review passed",
        )

    _write_artifacts(cycle, facts.to_dict(), claude_result, runner_root)
    state_writer.write_cycle_log_entry(
        cycle=cycle,
        run_id=datetime.now(UTC).strftime("%Y%m%dT%H%M%S"),
        commit_shas=[],
        agents_complete=[a for a, present in facts.agent_reports_present.items() if present],
        scores={"s1": 0, "s2": 0},
        repo_root=repo_root,
    )
    _write_dispatch_decision(result, runner_root)
    _write_post_cycle_result(result, runner_root)
    return result


def get_review_result(cycle: int, runner_root: Path) -> PostCycleReviewResult | None:
    path = runner_root / "runs" / f"CYCLE_{cycle:03d}_post_cycle_result.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    facts_payload = data.get("facts", {})
    facts = PostCycleFacts(
        cycle=data["cycle"],
        mode=ReviewMode(data["mode"]),
    )
    if isinstance(facts_payload, dict):
        for key, value in facts_payload.items():
            if hasattr(facts, key):
                setattr(facts, key, value)
    return PostCycleReviewResult(
        cycle=data["cycle"],
        mode=ReviewMode(data["mode"]),
        result=ReviewResult(data.get("review_result", "FAIL")),
        facts=facts,
        status=data["status"],
        review_result=data["review_result"],
        reason=data.get("reason", ""),
    )


def _write_dispatch_decision(result: PostCycleReviewResult, runner_root: Path) -> None:
    path = runner_root / "state/next_cycle_dispatch_decision.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "cycle": result.cycle,
                "review_result": result.review_result,
                "blocks_dispatch": result.blocks_dispatch,
                "next_action": f"DISPATCH_CYCLE_{result.cycle + 1:03d}",
                "reason": result.reason,
                "timestamp": datetime.now(UTC).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_post_cycle_result(result: PostCycleReviewResult, runner_root: Path) -> None:
    path = runner_root / "runs" / f"CYCLE_{result.cycle:03d}_post_cycle_result.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "cycle": result.cycle,
                "mode": result.mode.value,
                "status": result.status,
                "review_result": result.review_result,
                "blocks_dispatch": result.blocks_dispatch,
                "reason": result.reason,
                "facts": result.facts.to_dict(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_artifacts(
    cycle: int,
    facts: dict[str, Any],
    claude_result: Any,
    runner_root: Path,
) -> None:
    run_dir = runner_root / "runs" / f"CYCLE_{cycle:03d}"
    run_dir.mkdir(parents=True, exist_ok=True)
    common = {
        "cycle": cycle,
        "timestamp": datetime.now(UTC).isoformat(),
        "billing_mode": "claude_subscription_only",
        "anthropic_api_key_present": False,
    }
    payloads = {
        "agent_report_audit.json": {
            **common,
            "agent_reports": facts.get("agent_reports_present", facts.get("agent_reports", {})),
        },
        "github_verification.json": {
            **common,
            "pr_merged": facts.get("pr_merged", False),
            "merge_sha": facts.get("merge_sha", ""),
            "ci_passed": facts.get("ci_passed", False),
            "codecov_project": facts.get("codecov_project", "UNKNOWN"),
            "codecov_patch": facts.get("codecov_patch", "UNKNOWN"),
        },
        "jira_verification.json": {
            **common,
            "cycle_control_done": facts.get("cycle_control_done", False),
            "in_review_stories": facts.get("in_review_stories", []),
            "done_stories": facts.get("done_stories", []),
        },
        "post_cycle_result.json": {
            **common,
            "claude_status": str(getattr(claude_result, "status", "UNKNOWN")),
            "claude_error": str(getattr(claude_result, "error", "")),
        },
    }
    for name, payload in payloads.items():
        (run_dir / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
