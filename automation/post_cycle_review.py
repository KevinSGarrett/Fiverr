"""
post_cycle_review.py — Post-cycle PM review automation.

Implements the gate between a merged cycle and next-cycle dispatch.
Source prompt: PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md

Two modes:
  POST_AGENT_CYCLE_REVIEW  — agents done, PR open, not yet merged (draft preview)
  POST_CYCLE_PM_REVIEW     — PR merged to develop (canonical closeout, blocks next dispatch)
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path("C:/Fiverr/Fiverr")
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
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    next_scope_decision: str = ""
    prompt_package_valid: bool = False
    artifact_paths: list[str] = field(default_factory=list)

    @property
    def blocks_dispatch(self) -> bool:
        if self.mode == ReviewMode.POST_AGENT:
            return False
        return self.result != ReviewResult.PASS

    def summary(self) -> str:
        lines = [f"POST-CYCLE REVIEW {self.result.value} — Cycle {self.cycle:03d} [{self.mode.value}]"]
        for e in self.errors:
            lines.append(f"  ERROR: {e}")
        for w in self.warnings:
            lines.append(f"  WARN:  {w}")
        if self.blocks_dispatch:
            lines.append("  DISPATCH BLOCKED until this review passes")
        return "\n".join(lines)


def collect_facts(cycle: int, mode: ReviewMode,
                  pr_number: int | None = None) -> PostCycleFacts:
    """Collect all deterministic facts before any PM review runs."""
    facts = PostCycleFacts(cycle=cycle, mode=mode,
                           collected_at=datetime.now(UTC).isoformat())

    # ── Git facts ─────────────────────────────────────────────────────
    facts.head_sha = _git("rev-parse", "HEAD")
    facts.develop_sha = _git("rev-parse", "origin/develop")

    # ── PR merge state ────────────────────────────────────────────────
    if pr_number:
        facts.pr_number = pr_number
        try:
            pr = json.loads(_gh("pr", "view", str(pr_number),
                                "--repo", "KevinSGarrett/Fiverr",
                                "--json", "state,mergeCommit,headRefName"))
            facts.pr_merged = pr.get("state") == "MERGED"
            mc = pr.get("mergeCommit") or {}
            facts.merge_sha = mc.get("oid", "")
        except Exception:
            pass

    # ── CI status ─────────────────────────────────────────────────────
    if pr_number:
        try:
            checks = json.loads(_gh("pr", "view", str(pr_number),
                                    "--repo", "KevinSGarrett/Fiverr",
                                    "--json", "statusCheckRollup"))
            rollup = checks.get("statusCheckRollup") or []
            required = {"CI / lint", "CI / type-check",
                        "CI / tests-coverage", "CI / smoke-gates"}
            passed = {c.get("name") for c in rollup
                      if c.get("conclusion") == "success"}
            facts.ci_passed = required.issubset(passed)
            for c in rollup:
                name = (c.get("name") or "").lower()
                state = c.get("conclusion") or c.get("state") or "pending"
                if "codecov/project" in name:
                    facts.codecov_project = state.upper()
                elif "codecov/patch" in name:
                    facts.codecov_patch = state.upper()
        except Exception:
            pass

    # ── Agent reports ─────────────────────────────────────────────────
    reports_dir = REPO_ROOT / "docs/cycle_reports"
    for agent in ["A", "B", "E", "C", "F", "D"]:
        pattern = f"CYCLE_{cycle:03d}_AGENT_{agent}.md"
        found = list(reports_dir.glob(pattern))
        facts.agent_reports_present[agent] = bool(found)

    # ── Local validation ──────────────────────────────────────────────
    py = str(REPO_ROOT / ".venv/Scripts/python.exe")
    facts.local_ruff = _run_check([py, "-m", "ruff", "check", "."])
    facts.local_mypy = _run_check([py, "-m", "mypy", "src"])

    # ── Baseline DB mtime ─────────────────────────────────────────────
    baseline_db = REPO_ROOT / "data/cycle037_live.db"
    if baseline_db.exists():
        mtime = baseline_db.stat().st_mtime
        facts.baseline_db_mtime_unchanged = (round(mtime) == 1780553758)

    # ── ScrapFly config check ─────────────────────────────────────────
    config_path = REPO_ROOT / "config.yaml"
    if config_path.exists():
        content = config_path.read_text(encoding="utf-8", errors="replace")
        facts.scrapfly_enabled_false = "scrapfly.enabled: false" in content or \
                                        "enabled: false" in content

    # ── Jira cycle control ────────────────────────────────────────────
    try:
        import base64

        import requests

        from automation.config_loader import get_secret
        jira_url = get_secret("JIRA_BASE_URL")
        email = get_secret("JIRA_EMAIL")
        token = get_secret("JIRA_API_TOKEN")
        if jira_url and email and token:
            creds = base64.b64encode(f"{email}:{token}".encode()).decode()
            headers = {"Authorization": f"Basic {creds}", "Accept": "application/json"}
            jql = f"project=SCRUM AND labels='cycle:{cycle:03d}' AND issuetype=Story ORDER BY created ASC"
            r = requests.get(f"{jira_url}/rest/api/3/search/jql",
                             headers=headers,
                             params={"jql": jql, "maxResults": "5", "fields": "summary,status"},
                             timeout=10)
            if r.status_code == 200:
                issues = r.json().get("issues", [])
                for issue in issues:
                    status = issue["fields"]["status"]["name"]
                    if status == "Done":
                        facts.cycle_control_done = True
    except Exception:
        pass

    reviewer = PostCycleReview(cycle=cycle)
    reviewer._verify_github_facts()
    jira_facts = reviewer._verify_jira_facts()
    if jira_facts.get("done_stories"):
        facts.cycle_control_done = True
    return facts


def run_review(cycle: int, mode: ReviewMode,
               pr_number: int | None = None) -> PostCycleReviewResult:
    """Run a post-cycle review. Returns result with dispatch gate decision."""
    result = PostCycleReviewResult(
        cycle=cycle, mode=mode,
        result=ReviewResult.FAIL,
        facts=PostCycleFacts(cycle=cycle, mode=mode),
    )

    # ── GATE 1: Source prompt must exist ──────────────────────────────
    if not SOURCE_PROMPT.exists():
        result.result = ReviewResult.BLOCKED_SOURCE_PROMPT_MISSING
        result.errors.append(f"Source prompt missing: {SOURCE_PROMPT}")
        _write_result(result)
        return result

    # ── GATE 2: Write queue request ───────────────────────────────────
    _write_queue_request(cycle, mode, pr_number)

    # ── GATE 3: Collect deterministic facts ───────────────────────────
    result.facts = collect_facts(cycle, mode, pr_number)

    # ── GATE 4: Validate facts (POST_MERGE requires merge) ────────────
    if mode == ReviewMode.POST_MERGE and not result.facts.pr_merged:
        result.errors.append("PR not merged — cannot run POST_CYCLE_PM_REVIEW")
        _write_result(result)
        return result

    # ── GATE 5: Agent reports audit ───────────────────────────────────
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

    # ── GATE 6: Baseline DB integrity ────────────────────────────────
    if not result.facts.baseline_db_mtime_unchanged:
        result.errors.append("cycle037_live.db mtime changed — baseline tampered")

    # ── GATE 7: ScrapFly config ───────────────────────────────────────
    if not result.facts.scrapfly_enabled_false:
        result.errors.append("config.yaml has scrapfly.enabled:true — not allowed in commits")

    # ── GATE 8: Claude subscription PM review (V5-010 fix) ───────────
    # Official POST_MERGE review MUST invoke Claude adapter.
    # If Claude is not available → ADVISORY_ONLY, dispatch blocked.
    # If model/effort/adaptive thinking unverified → ADVISORY_ONLY.
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

    # ── RESULT: POST_AGENT is always preview ──────────────────────────
    elif mode == ReviewMode.POST_AGENT:
        result.result = ReviewResult.DRAFT_UNMERGED_PREVIEW
    elif not result.errors:
        result.result = ReviewResult.PASS
    else:
        result.result = ReviewResult.FAIL

    _write_result(result)
    _write_artifacts(result)
    return result


def write_queue_request_for_agent_d(cycle: int) -> Path:
    """Called when Agent D completes — writes review queue request."""
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
        f"# Post-Cycle Review — Cycle {result.cycle:03d}",
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


def _write_artifacts(result: PostCycleReviewResult) -> None:
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


class JiraAuthError(Exception):
    """Raised when Jira authentication fails for post-cycle collection."""


class _JiraClientProxy:
    def search_issues(self, jql: str) -> list[dict[str, Any]]:
        import requests

        from automation.jira_client import _base_url, _headers

        response = requests.get(
            f"{_base_url()}/rest/api/3/search/jql",
            headers=_headers(),
            params={"jql": jql, "maxResults": "100", "fields": "key"},
            timeout=20,
        )
        if response.status_code in {401, 403}:
            raise JiraAuthError("JIRA_AUTH_FAILED")
        response.raise_for_status()
        payload = response.json()
        return payload.get("issues", [])


class PostCycleReview:
    """Post-cycle fact collector helpers for GitHub and Jira verification."""

    def __init__(self, cycle: int | None = None, jira_client: Any | None = None) -> None:
        self.cycle = cycle
        self.jira_client = jira_client or _JiraClientProxy()
        self.current_run_dir = REPO_ROOT / "PM_Pack/automation/post_cycle_reviews/current_run"

    def collect_facts(self) -> dict[str, Any]:
        github_facts = self._verify_github_facts()
        jira_facts = self._verify_jira_facts()
        return {"github": github_facts, "jira": jira_facts}

    def _verify_github_facts(self) -> dict[str, Any]:
        try:
            result = subprocess.run(
                ["gh", "pr", "list", "--state", "merged", "--limit", "5", "--json", "number,title,mergedAt"],
                capture_output=True,
                text=True,
                check=True,
            )
            merged_prs = json.loads(result.stdout or "[]")
            payload = {"merged_prs": merged_prs, "collected_at": datetime.now(UTC).isoformat()}
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            payload = {"merged_prs": [], "error": "gh_unavailable"}
        self.current_run_dir.mkdir(parents=True, exist_ok=True)
        (self.current_run_dir / "github_verification.json").write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
        return payload

    def _verify_jira_facts(self) -> dict[str, Any]:
        try:
            issues = self.jira_client.search_issues(
                "project=SCRUM AND status=Done AND sprint in openSprints()"
            )
            done_stories = [str(issue.get("key", "")) for issue in issues if issue.get("key")]
            payload = {"done_stories": done_stories, "collected_at": datetime.now(UTC).isoformat()}
        except (JiraAuthError, ConnectionError):
            payload = {"done_stories": [], "auth_error": "JIRA_AUTH_FAILED"}
        except Exception:
            payload = {"done_stories": [], "auth_error": "JIRA_AUTH_FAILED"}
        self.current_run_dir.mkdir(parents=True, exist_ok=True)
        (self.current_run_dir / "jira_verification.json").write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
        return payload
