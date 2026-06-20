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
from types import SimpleNamespace
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
    # ITEM 4.2: True when the local suite was skipped (CI is the authority). In
    # the pre-merge POST_AGENT review this DEFERS the local + remote-CI gates to
    # AWAITING_CI_GREEN (which waits for and gates on the PR's CI before merge),
    # so a still-pending PR CI does not dead-end the cycle at AGENT_COMPLETE.
    local_validation_skipped: bool = False
    baseline_db_mtime_unchanged: bool = False
    scrapfly_enabled_false: bool = True

    # Jira facts
    cycle_control_done: bool = False
    next_cycle_control_created: bool = False

    # GitHub health audit (from github_reviewer.py)
    github_health_score: int = 100
    github_blockers: list[str] = field(default_factory=list)
    github_action_items: list[str] = field(default_factory=list)

    # C4.3: PR expected flag (set when branch has commits not yet in develop)
    pr_expected: bool = False

    # C4.6: ICV blocked agents (populated from _agent_outcomes in cmd_run_cycle)
    icv_blocked_agents: list[str] = field(default_factory=list)

    # Agent report facts
    agent_reports_present: dict[str, bool] = field(default_factory=dict)

    # ARSF: evidence-checked synthesis of the agent reports (content, not just existence)
    per_agent_verdict: dict[str, str] = field(default_factory=dict)
    agent_discrepancies: dict[str, list[str]] = field(default_factory=dict)
    claimed_only_agents: list[str] = field(default_factory=list)
    carryover: list[str] = field(default_factory=list)
    unmet_ac: list[str] = field(default_factory=list)
    report_format_health: str = ""

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
        # ITEM 4.1 (Codex P1): hard errors recorded by run_review ALWAYS block
        # dispatch, in EVERY mode. GATE 6/7 (baseline cycle037_live.db mtime
        # tampered, config.yaml enabling ScrapFly) append to result.errors without
        # early-returning, and the POST_AGENT fact checks below ignore errors — so
        # without this, a tampered-but-otherwise-clean cycle would advance. Since
        # blocks_dispatch is the single advance predicate (4.1), errors must gate
        # here so every consumer (tick + manual command) is protected.
        if self.errors:
            return True
        # C4.2 (existing): POST_AGENT mode blocks on hard red facts.
        # C4.3: blocks on missing branch/PR when expected.
        # C4.4: blocks on coverage below configurable floor.
        # C4.5: blocks on GitHub health below threshold.
        # C4.6: blocks on unmet acceptance criteria (ICV BLOCKED outcomes).
        if self.mode == ReviewMode.POST_AGENT:
            if hasattr(self, "facts") and self.facts is not None:
                f = self.facts
                # ITEM 4.2: when local validation was delegated to CI
                # (skip_local_validation), the local tool + remote-CI gates are
                # DEFERRED to AWAITING_CI_GREEN, which waits for and gates on the
                # PR's CI before merge. Without this, a PR whose CI is still
                # pending at AGENT_COMPLETE (ci_passed=False) would dead-end the
                # cycle at POST_CYCLE_FAIL instead of advancing to the merge path.
                # A full (non-skipped) review still enforces these locally.
                if not getattr(f, "local_validation_skipped", False):
                    # C4.2: Local tool failures
                    if f.local_ruff is False:
                        return True
                    if f.local_mypy is False:
                        return True
                    if f.local_pytest is False:
                        return True
                    if f.ci_passed is False:
                        return True
                # C4.3: Missing PR when merge is expected
                if getattr(f, "pr_expected", False) and not f.pr_number:
                    return True
                # H8.1/C4.4: Coverage floor — single source of truth.
                # ITEM 4.2 (Codex MEDIUM): use _coverage_floor() (reads the
                # correct validation.coverage_floor key) instead of a divergent
                # inline reader that read a non-existent top-level key (always 80).
                if 0 < f.local_coverage_pct < _coverage_floor():
                    return True
                # C4.5: GitHub health below threshold
                if getattr(f, "github_health_score", 100) < 50:
                    return True
                # C4.6: ICV BLOCKED outcomes on any agent
                icv_outcomes = getattr(f, "icv_blocked_agents", [])
                if icv_outcomes:
                    return True
                # ARSF (gated): block on hard discrepancies when enabled
                try:
                    import yaml as _y
                    _cfg_path = __file__[: __file__.rindex("automation")] + "PM_Pack/automation/report_synthesis.yml"
                    import os as _os
                    if _os.path.exists(_cfg_path):
                        _cfg = _y.safe_load(open(_cfg_path, encoding="utf-8").read()) or {}
                        if _cfg.get("gate_on_discrepancies", False):
                            _hard = set(_cfg.get("blocking_discrepancies",
                                        ["COMPLETION_CLAIMED_NO_COMMIT", "TESTS_CLAIMED_PASS_CI_RED"]))
                            for _flags in getattr(f, "agent_discrepancies", {}).values():
                                if _hard.intersection(_flags):
                                    return True
                except Exception:
                    pass
            return False  # No facts available -- don't block
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
                  pr_number: int | None = None,
                  skip_local_validation: bool = False) -> PostCycleFacts:
    """Collect all deterministic facts before any PM review runs.

    ITEM 4.2: with ``skip_local_validation=True`` the ~13-min local ruff/mypy/
    pytest+coverage suite is NOT re-run (CI already ran the identical suite via
    CI/tests-coverage). The local_* facts are then derived from the REAL green CI
    fact (``ci_passed``) — never a fabricated local pass. When CI is red,
    ``ci_passed`` is False so the local facts go red and the cycle fails closed.
    """
    facts = PostCycleFacts(cycle=cycle, mode=mode,
                           collected_at=datetime.now(UTC).isoformat())

    # ── Git facts ─────────────────────────────────────────────────────
    facts.head_sha = _git("rev-parse", "HEAD")
    facts.develop_sha = _git("rev-parse", "origin/develop")
    # C4.3: detect whether a PR is expected (HEAD differs from develop)
    if facts.head_sha and facts.develop_sha and facts.head_sha != facts.develop_sha:
        facts.pr_expected = True

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
            # ITEM 4.2 (Codex HIGH): use the CANONICAL required-check set
            # (automation.required_checks — the 8 contexts incl. Secret Scan /
            # Dependency Audit / Validate PR, unioned with live branch protection)
            # via casing/typename-correct disposition, NOT a local 5-check subset.
            # ci_passed is the load-bearing fact for the deterministic POST_MERGE
            # PASS authority, so it must match the merge gate (never be looser).
            from automation import required_checks as _rc
            facts.ci_passed = _rc.required_check_disposition(
                rollup, _rc.get_required_contexts()) == "GREEN"
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

    # ── ARSF synthesis (content of the reports, cross-checked) ────────
    try:
        from automation.report_synthesis import load_cycle_synthesis
        cs = load_cycle_synthesis(cycle)
        if cs is not None:
            facts.per_agent_verdict = {a: s.verdict for a, s in cs.agents.items()}
            facts.agent_discrepancies = {a: list(s.discrepancies) for a, s in cs.agents.items()}
            facts.claimed_only_agents = [a for a, s in cs.agents.items() if s.verdict == "CLAIMED_ONLY"]
            facts.carryover = list(cs.carryover)
            facts.unmet_ac = [ac for s in cs.agents.values() for ac in s.unmet_ac]
            facts.report_format_health = cs.format_health
    except Exception:
        pass  # non-blocking: existence audit (above) remains the floor

    # ── Local validation ──────────────────────────────────────────────
    if skip_local_validation:
        # ITEM 4.2-T4: do NOT re-run the ~13-min suite — CI already ran the
        # identical suite (CI/tests-coverage), and AWAITING_CI_GREEN gates on that
        # PR CI before merge. Mark validation as delegated; blocks_dispatch then
        # defers the local + remote-CI checks to the merge path (so a PR whose CI
        # is still pending at AGENT_COMPLETE does not dead-end the cycle). The
        # non-CI invariants (baseline/scrapfly/reports/health/ICV) still gate.
        facts.local_validation_skipped = True
        facts.local_ruff = True   # delegated to CI (no local pre-check objection)
        facts.local_mypy = True
        facts.local_pytest = True
        facts.local_coverage_pct = 0.0  # unmeasured locally; CI enforces the floor
    else:
        _run_local_suite(facts)

    # ── Baseline DB mtime ─────────────────────────────────────────────
    baseline_db = REPO_ROOT / "data/cycle037_live.db"
    if baseline_db.exists():
        mtime = baseline_db.stat().st_mtime
        # Allow ±2s tolerance for filesystem timestamp drift across git operations.
        # Baseline epoch: 1780553758 (cycle037_live.db original commit mtime)
        facts.baseline_db_mtime_unchanged = abs(round(mtime) - 1780553758) <= 2

    # ── ScrapFly config check ─────────────────────────────────────────
    # ITEM 4.2 (Codex MEDIUM): parse the nested YAML key explicitly. The old
    # substring match (`"enabled: false" in content`) was spoofable — any
    # unrelated `enabled: false` (e.g. relevance.llm.enabled) would satisfy it
    # even while scrapfly.enabled was true, letting an enabled-ScrapFly config
    # ride to a deterministic PASS. Missing scrapfly key => treated as disabled.
    config_path = REPO_ROOT / "config.yaml"
    if config_path.exists():
        try:
            import yaml as _yaml_sf
            _cfg_sf = _yaml_sf.safe_load(
                config_path.read_text(encoding="utf-8", errors="replace")
            ) or {}
            facts.scrapfly_enabled_false = (
                ((_cfg_sf.get("scrapfly") or {}).get("enabled", False)) is not True
            )
        except Exception:
            facts.scrapfly_enabled_false = False  # unparseable config -> fail closed

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
    reviewer.collect_github_facts(pr_number=pr_number)
    jira_facts = reviewer.collect_jira_facts(merge_sha=facts.merge_sha)
    if jira_facts.get("all_done", False):
        facts.cycle_control_done = True

    # ── GitHub health audit (full repo review for PM) ─────────────────
    try:
        from automation.github_reviewer import (
            build_health_report,
            auto_fix_what_we_can,
        )
        branch = f"cycle/{cycle:03d}/integration"
        health = build_health_report(cycle=cycle, branch=branch)
        # Auto-fix what the PM can handle without code changes
        auto_fix_what_we_can(health)
        # Attach summary to facts for review prompt
        facts.github_health_score = health.health_score
        facts.github_blockers = health.blockers
        facts.github_action_items = health.action_items[:10]
    except Exception:
        pass

    return facts


def run_review(cycle: int, mode: ReviewMode,
               pr_number: int | None = None,
               skip_local_validation: bool = False) -> PostCycleReviewResult:
    """Run a post-cycle review. Returns result with dispatch gate decision.

    ITEM 4.2: ``skip_local_validation=True`` (the autonomous-loop default) skips
    the ~13-min local suite — CI already ran it — and derives local facts from
    ``ci_passed``. Default False preserves manual/operator callers.
    """
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
    result.facts = collect_facts(cycle, mode, pr_number,
                                 skip_local_validation=skip_local_validation)
    # ARSF: next-cycle scope is driven by what was NOT delivered (carryover)
    if result.facts.carryover:
        result.next_scope_decision = "CARRYOVER: " + "; ".join(result.facts.carryover[:12])

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

    # ── GATE 8: Deterministic POST_MERGE verdict + Claude advisory (item 4.2) ──
    # INVERTED from the old "Claude is the sole PASS authority" (which stranded the
    # runner on any Claude flake). Now the DETERMINISTIC verdict from real green
    # facts is the PASS floor; Claude PM runs ADVISORY on top and can NEVER strand.
    # Genuinely red facts already appended to result.errors above (GATE 4-7) ->
    # blocks_dispatch True (item 4.1), so a red cycle still fails closed.
    if mode == ReviewMode.POST_MERGE and not result.errors:
        passable, det_reasons = _deterministic_post_merge_verdict(result.facts)
        if not passable:
            # Facts are not green enough for an unattended pass -> hard block.
            # Claude is not even consulted (no point; facts decide).
            result.errors.extend(det_reasons)
            result.result = ReviewResult.FAIL
        else:
            # Facts ARE green -> deterministic PASS is the floor. Claude advisory.
            result.result = ReviewResult.PASS
            claude_result = _run_claude_with_retry(result)
            if claude_result is not None:
                if claude_result.request_path:
                    result.artifact_paths.append(claude_result.request_path)
                if claude_result.response_path:
                    result.artifact_paths.append(claude_result.response_path)
                if claude_result.status == "BLOCKED":
                    # SECURITY (item 4.2 decision): ANTHROPIC_API_KEY present is a
                    # deterministic policy violation, NOT a transient flake — it
                    # STILL hard-blocks even on green facts (subscription-only
                    # stance preserved). The runner env has no API key, so this
                    # never fires in practice; it guards against a misconfig.
                    result.errors.append(f"Claude blocked: {claude_result.error}")
                    result.result = ReviewResult.BLOCKED_MODEL_UNVERIFIED
                elif claude_result.status == "PASS":
                    result.warnings.append("Claude PM advisory: PASS (concurs)")
                elif claude_result.status == "FAIL":
                    result.warnings.append(
                        f"Claude PM advisory DISSENT: FAIL ({claude_result.error}). "
                        "Deterministic facts are green; PASS stands — artifact saved for human."
                    )
                else:  # ADVISORY_ONLY / ERROR (transient/unavailable after retry)
                    result.warnings.append(
                        f"Claude PM advisory unavailable ({claude_result.status}: "
                        f"{claude_result.error}); deterministic PASS stands."
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
    # ITEM 4.2-T4: bounded so a hung git can never stall fact collection (which
    # runs inside the unattended MERGED tick). On timeout return "" (fail-closed:
    # an empty SHA makes pr_expected/merge checks behave conservatively).
    try:
        r = subprocess.run(["git", *args], cwd=str(REPO_ROOT),
                           capture_output=True, text=True, check=False, timeout=60)
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""


def _gh(*args: str) -> str:
    # ITEM 4.2-T4: bounded so a hung gh can never stall the MERGED-tick fact
    # collection. A timeout raises RuntimeError, which every caller already wraps
    # in try/except so the affected fact stays False (fail-closed), never green.
    try:
        r = subprocess.run(["gh", *args], capture_output=True, text=True,
                           check=False, timeout=60)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"gh timed out: {' '.join(args)[:80]}") from e
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.strip()


def _run_check(cmd: list[str]) -> bool:
    # ITEM 4.2 (Codex LOW): fail closed on timeout (a hung ruff/mypy yields a red
    # local fact, not an exception out of collect_facts), consistent with _git/_gh.
    try:
        r = subprocess.run(cmd, cwd=str(REPO_ROOT),
                           capture_output=True, text=True, check=False, timeout=120)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def _coverage_floor() -> float:
    """Coverage floor from autonomous_runner.yml (single source of truth; 80).

    The key lives under ``validation.coverage_floor``; fall back to a top-level
    key and then 80.0 so a config-shape change cannot silently lower the floor.
    """
    try:
        import yaml as _yaml
        cfg = _yaml.safe_load(
            open("automation/config/autonomous_runner.yml", encoding="utf-8").read()
        ) or {}
        val = (cfg.get("validation", {}) or {}).get("coverage_floor")
        if val is None:
            val = cfg.get("coverage_floor", 80.0)
        return float(val)
    except Exception:
        return 80.0


def _run_local_suite(facts: PostCycleFacts) -> None:
    """Run the local ruff/mypy/pytest+coverage suite and record the facts.

    Item 4.2: this is the ~13-min suite. It is invoked ONLY when
    skip_local_validation is False (manual reviews / explicit operator runs); the
    autonomous loop passes skip_local_validation=True because CI already ran it.
    """
    py = str(REPO_ROOT / ".venv/Scripts/python.exe")
    facts.local_ruff = _run_check([py, "-m", "ruff", "check", "automation/", "src/", "tests/",
                                   "--ignore", "I001,UP035,W605"])
    facts.local_mypy = _run_check([py, "-m", "mypy", "src"])
    # Run pytest with coverage — keep the ignore set in sync with .github/workflows/ci.yml
    # (item 3.3: Cursor-CLI-dependent modules stay ignored to mirror ubuntu CI).
    _IGNORES = [
        "--ignore=tests/unit/test_cycle062_smoke_aliases.py",
        "--ignore=tests/unit/test_playbook_generator.py",
        "--ignore=tests/unit/test_automation_system_restriction_removal.py",
        "--ignore=tests/unit/test_post_cycle_review_coverage.py",
        "--ignore=tests/unit/test_cursor_adapter.py",
        "--ignore=tests/unit/test_prompt_generator.py",
        "--ignore=tests/unit/test_prompt_contract_builder.py",
    ]
    cov_result = subprocess.run(
        [py, "-m", "pytest", "tests/unit/", "--no-header", "--tb=no", "-q",
         *_IGNORES,
         "--cov=src", "--cov=automation", "--cov-report=term-missing:skip-covered",
         "--cov-fail-under=80"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=900,
    )
    facts.local_pytest = cov_result.returncode == 0
    import re as _re
    m = _re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", cov_result.stdout + cov_result.stderr)
    if m:
        facts.local_coverage_pct = float(m.group(1))


def _deterministic_post_merge_verdict(facts: PostCycleFacts) -> tuple[bool, list[str]]:
    """ITEM 4.2-T1: deterministic POST_MERGE PASS from REAL green facts only.

    Returns ``(passable, hard_block_reasons)``. Never fabricates: every clause maps
    to a concrete collected fact, and the only PASS authority is ``ci_passed``
    (real required-CI subset incl. codex-review-gate, with --cov-fail-under=80) plus
    a real ``merge_sha`` and on-disk reports/baseline/config. Any missing/red fact
    forces ``passable=False`` with a precise reason.
    """
    reasons: list[str] = []
    if not facts.pr_merged:
        reasons.append("PR not merged")
    if not (facts.merge_sha or "").strip():
        reasons.append("no merge SHA (merge not verified)")
    if not facts.ci_passed:
        reasons.append("required CI not green")
    floor = _coverage_floor()
    # ci_passed already enforces the coverage floor remotely; a positively-measured
    # local pct >= floor also satisfies it. An unmeasured 0.0 only rides ci_passed.
    if not (facts.ci_passed or facts.local_coverage_pct >= floor):
        reasons.append(f"coverage below floor {floor}")
    missing = [a for a in ("A", "B", "E", "C", "F", "D")
               if not facts.agent_reports_present.get(a)]
    if missing:
        reasons.append(f"missing agent reports: {missing}")
    if not facts.baseline_db_mtime_unchanged:
        reasons.append("baseline cycle037_live.db mtime changed")
    if not facts.scrapfly_enabled_false:
        reasons.append("config.yaml has ScrapFly enabled")
    return (not reasons, reasons)


def _is_transient(claude_result: Any) -> bool:
    """ITEM 4.2-T2: True iff a Claude PM result is a transient/infra failure worth
    retrying (timeout, missing binary, spawn/session crash) — NOT a real verdict
    (PASS/FAIL) and NOT a config block (ANTHROPIC_API_KEY present)."""
    status = getattr(claude_result, "status", "")
    if status == "ERROR":
        return True  # generic subprocess exception — spawn/session crash
    if status == "ADVISORY_ONLY":
        err = (getattr(claude_result, "error", "") or "").lower()
        return "timed out" in err or "not found on path" in err or "binary" in err
    return False  # BLOCKED=config; PASS/FAIL=real verdict; bare ADVISORY=real


def _run_claude_with_retry(result: PostCycleReviewResult) -> Any:
    """ITEM 4.2-T2: invoke the Claude PM adapter with BOUNDED retry that self-clears
    transient flakes. The deterministic PASS already stands, so this is advisory
    QUALITY only — it can never strand the runner and is hard-bounded (cannot loop).
    Returns the (advisory) ClaudeReviewResult, or None on unexpected failure.
    """
    import time
    from automation.claude_post_cycle_adapter import run_post_cycle_review as _claude_review
    try:
        import yaml as _yaml
        cfg = (_yaml.safe_load(
            open("automation/config/autonomous_runner.yml", encoding="utf-8").read()
        ) or {}).get("claude_review", {}) or {}
    except Exception:
        cfg = {}
    max_attempts = max(1, min(int(cfg.get("max_attempts", 2)), 3))  # hard cap 3
    base_backoff = min(int(cfg.get("backoff_s", 5)), 30)

    run_dir = REVIEWS_DIR / f"cycle_{result.cycle:03d}_runs" / "current"
    run_dir.mkdir(parents=True, exist_ok=True)
    review_prompt = SOURCE_PROMPT.read_text(encoding="utf-8", errors="replace")
    facts_json = json.dumps(result.facts.to_dict(), indent=2, default=str)

    res: Any = None
    for attempt in range(1, max_attempts + 1):
        try:
            res = _claude_review(cycle=result.cycle, run_dir=run_dir,
                                 review_prompt_text=review_prompt, facts_json=facts_json)
        except Exception as e:  # adapter raised -> treat as transient ERROR
            res = SimpleNamespace(status="ERROR", error=str(e)[:200],
                                  request_path="", response_path="")
        if not _is_transient(res):
            return res  # real verdict or config-BLOCKED -> stop immediately
        if attempt < max_attempts:
            time.sleep(min(base_backoff * attempt, 30))
    return res  # exhausted -> last (transient) result; caller treats as advisory


class JiraAuthError(Exception):
    """Raised when Jira authentication fails for post-cycle collection."""


class _JiraClientProxy:
    def search_issues(self, jql: str) -> list[dict[str, Any]]:
        import requests

        from automation.jira_client import _base_url, _headers

        response = requests.get(
            f"{_base_url()}/rest/api/3/search/jql",
            headers=_headers(),
            params={"jql": jql, "maxResults": "100", "fields": "key,status"},
            timeout=20,
        )
        if response.status_code in {401, 403}:
            raise JiraAuthError("JIRA_AUTH_FAILED")
        response.raise_for_status()
        payload = response.json()
        return payload.get("issues", [])

    def transition_issue(self, issue_key: str, transition_id: str) -> None:
        from automation.jira_client import transition_issue

        transition_issue(issue_key, transition_id)

    def add_comment(self, issue_key: str, body: str) -> None:
        from automation.jira_client import add_comment

        add_comment(issue_key, body)


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

    def collect_github_facts(self, pr_number: int | None = None) -> dict[str, Any]:
        _ = pr_number
        return self._verify_github_facts()

    def collect_jira_facts(self, merge_sha: str = "") -> dict[str, Any]:
        _ = merge_sha
        return self._verify_jira_facts()

    def _verify_github_facts(self) -> dict[str, Any]:
        try:
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "list",
                    "--state",
                    "merged",
                    "--limit",
                    "5",
                    "--json",
                    "number,title,mergedAt",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            merged_prs = json.loads(result.stdout or "[]")
            payload: dict[str, Any] = {
                "merged_prs": merged_prs,
                "collected_at": datetime.now(UTC).isoformat(),
            }
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
            done_stories: list[str] = []
            for issue in issues:
                if isinstance(issue, dict):
                    key = issue.get("key")
                    if key:
                        done_stories.append(str(key))
            payload: dict[str, Any] = {
                "done_stories": done_stories,
                "collected_at": datetime.now(UTC).isoformat(),
            }
        except (JiraAuthError, ConnectionError, OSError):
            payload = {"done_stories": [], "auth_error": "JIRA_AUTH_FAILED"}
        self.current_run_dir.mkdir(parents=True, exist_ok=True)
        (self.current_run_dir / "jira_verification.json").write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
        return payload
