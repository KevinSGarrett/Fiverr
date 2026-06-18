"""
automation/report_synthesis/evidence_crosscheck.py
RSF-6 through RSF-12: Cross-check claimed report against deterministic sources.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from automation.report_synthesis.schemas import AgentVerdict, AgentReportSynthesis, ClaimedAgentReport

log = logging.getLogger(__name__)

# ── Discrepancy constants ─────────────────────────────────────────────────────
FLAG_NO_COMMIT = "COMPLETION_CLAIMED_NO_COMMIT"
FLAG_CLAIMED_FILES = "CLAIMED_FILES_NOT_IN_DIFF"
FLAG_CI_RED = "TESTS_CLAIMED_PASS_CI_RED"
FLAG_AC_UNMET = "AC_CLAIMED_MET_DETERMINISTIC_UNMET"
FLAG_JIRA_MISSING = "JIRA_TRANSITION_CLAIMED_NOT_FOUND"
FLAG_EVIDENCE_UNAVAILABLE = "EVIDENCE_UNAVAILABLE"

REPO_ROOT = Path(__file__).resolve().parents[2]


# ── Actual-evidence gatherer (RSF-6) ─────────────────────────────────────────

@dataclass
class ActualEvidence:
    actual_commits: list[str] = field(default_factory=list)
    actual_files: list[str] = field(default_factory=list)
    ci_status: str = "unknown"
    coverage_pct: Optional[float] = None
    jira_transitions: dict[str, list[str]] = field(default_factory=dict)


def gather_actual_evidence(cycle: int, branch: str = "", _git_adapter=None, _ci_reader=None, _jira_client=None) -> ActualEvidence:
    """Collect the deterministic (non-claimed) view. Never raises."""
    ev = ActualEvidence()

    # --- Git commits ----------------------------------------------------------
    try:
        if _git_adapter is not None:
            ev.actual_commits = _git_adapter.get_commits(branch) or []
        else:
            import subprocess
            result = subprocess.run(
                ["git", "log", f"origin/develop..{branch}", "--format=%H", "--no-merges"],
                capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=15,
            )
            if result.returncode == 0:
                ev.actual_commits = [c.strip() for c in result.stdout.splitlines() if c.strip()]
    except Exception as exc:
        log.warning("gather_actual_evidence: git lookup failed: %s", exc)
        ev.actual_commits = []

    # --- Changed files -------------------------------------------------------
    try:
        if _git_adapter is not None:
            ev.actual_files = _git_adapter.get_diff_files(branch) or []
        else:
            import subprocess
            result = subprocess.run(
                ["git", "diff", "--name-only", f"origin/develop...{branch}"],
                capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=15,
            )
            if result.returncode == 0:
                ev.actual_files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except Exception as exc:
        log.warning("gather_actual_evidence: file diff failed: %s", exc)
        ev.actual_files = []

    # --- CI status -----------------------------------------------------------
    try:
        if _ci_reader is not None:
            ev.ci_status = _ci_reader.get_status(branch) or "unknown"
        else:
            # Try reading from cached CI artifact if present
            ci_cache = REPO_ROOT / "PM_Pack/automation/post_cycle_reviews/current_run/github_verification.json"
            if ci_cache.exists():
                import json
                data = json.loads(ci_cache.read_text(encoding="utf-8"))
                ev.ci_status = "green" if data.get("checks_passing") else "red"
    except Exception:
        ev.ci_status = "unknown"

    return ev


# ── Cross-checker: claimed vs actual ─────────────────────────────────────────

def crosscheck_agent(
    claimed: ClaimedAgentReport,
    cycle: int,
    *,
    actual: Optional[ActualEvidence] = None,
    _git_adapter=None,
    _ci_reader=None,
    _jira_client=None,
) -> AgentReportSynthesis:
    """Build an AgentReportSynthesis for one agent by cross-checking claims."""
    synth = AgentReportSynthesis(agent=claimed.agent, claimed=claimed)
    synth.carryover = list(claimed.carryover)

    branch = claimed.branch or f"cycle/{cycle:03d}/integration"
    if actual is None:
        try:
            actual = gather_actual_evidence(
                cycle, branch,
                _git_adapter=_git_adapter, _ci_reader=_ci_reader, _jira_client=_jira_client,
            )
        except Exception as exc:
            log.warning("crosscheck_agent: evidence gather failed: %s", exc)
            actual = ActualEvidence()
            synth.discrepancies.append(FLAG_EVIDENCE_UNAVAILABLE)

    synth.actual_commits = actual.actual_commits
    synth.actual_files = actual.actual_files
    synth.ci_status = actual.ci_status

    # RSF-7: No-commit flag
    _check_no_commit(claimed, actual, synth)

    # RSF-8: Claimed files not in diff
    _check_claimed_files(claimed, actual, synth)

    # RSF-9: Tests claimed pass but CI is red
    _check_ci_mismatch(claimed, actual, synth)

    # RSF-10: AC claimed met but not deterministically proven
    _check_ac_claims(claimed, synth)

    # RSF-11: Jira transitions
    _check_jira_transitions(claimed, actual, synth)

    # RSF-12: Compute verdict
    synth.verdict = _compute_verdict(claimed, synth.discrepancies)

    return synth


# ── Individual flag checks ────────────────────────────────────────────────────

def _check_no_commit(claimed: ClaimedAgentReport, actual: ActualEvidence, synth: AgentReportSynthesis) -> None:
    """RSF-7: committed:true + 0 actual commits → COMPLETION_CLAIMED_NO_COMMIT."""
    completion_claimed = (
        claimed.committed
        or claimed.self_status in ("COMPLETE",)
        or claimed.verdict in ("PASS",)
    )
    no_commit_admitted = bool(
        re.search(r"No\s+git\s+commit", claimed.raw_text, re.IGNORECASE)
        if claimed.raw_text else False
    )
    if completion_claimed and not actual.actual_commits and not no_commit_admitted:
        synth.discrepancies.append(FLAG_NO_COMMIT)


def _check_claimed_files(claimed: ClaimedAgentReport, actual: ActualEvidence, synth: AgentReportSynthesis) -> None:
    """RSF-8: files claimed as created/modified but absent from real diff."""
    if not actual.actual_files:
        return
    actual_set = {Path(f).as_posix() for f in actual.actual_files}
    all_claimed = claimed.files_created + claimed.files_modified
    missing = [
        f for f in all_claimed
        if f and Path(f).name not in {Path(p).name for p in actual_set}
        and Path(f).as_posix() not in actual_set
    ]
    if missing:
        synth.discrepancies.append(f"{FLAG_CLAIMED_FILES}: {missing[:5]}")


def _check_ci_mismatch(claimed: ClaimedAgentReport, actual: ActualEvidence, synth: AgentReportSynthesis) -> None:
    """RSF-9: validation says pytest pass but CI is red."""
    pytest_claimed_pass = (
        claimed.validation.get("ruff") == "pass"
        or str(claimed.validation.get("pytest_passed", "")).isdigit()
    )
    if pytest_claimed_pass and actual.ci_status == "red":
        synth.discrepancies.append(FLAG_CI_RED)


def _check_ac_claims(claimed: ClaimedAgentReport, synth: AgentReportSynthesis) -> None:
    """RSF-10: AC marked met without deterministic evidence."""
    for ac in claimed.ac_status:
        if ac.get("met") and not ac.get("evidence"):
            key = ac.get("key", "?")
            synth.unmet_ac.append(key)
            synth.discrepancies.append(f"{FLAG_AC_UNMET}: {key}")


def _check_jira_transitions(claimed: ClaimedAgentReport, actual: ActualEvidence, synth: AgentReportSynthesis) -> None:
    """RSF-11: claimed Jira transition not found in actual."""
    if not actual.jira_transitions:
        return
    for ja in claimed.jira_actions:
        if ja.transition and ja.transition != "none":
            real = actual.jira_transitions.get(ja.key, [])
            if ja.transition not in real:
                synth.discrepancies.append(f"{FLAG_JIRA_MISSING}: {ja.key} ({ja.transition})")


# ── Verdict ladder (RSF-12) ───────────────────────────────────────────────────

_HARD_DISCREPANCIES = {FLAG_NO_COMMIT, FLAG_CI_RED}


def _compute_verdict(claimed: ClaimedAgentReport, discrepancies: list[str]) -> str:
    """Map (claims, discrepancies) → AgentVerdict per the documented ladder."""
    # NO_REPORT: nothing was parsed at all
    if not claimed.verdict and not claimed.tasks:
        return AgentVerdict.NO_REPORT.value

    # Any hard discrepancy that means the agent lied about completing
    hard_hits = [d for d in discrepancies if any(h in d for h in _HARD_DISCREPANCIES)]
    if hard_hits:
        return AgentVerdict.CLAIMED_ONLY.value

    # Agent itself said BLOCKED/FAILED
    uv = (claimed.verdict or "").upper()
    if "BLOCKED" in uv:
        return AgentVerdict.BLOCKED.value
    if "FAIL" in uv:
        return AgentVerdict.FAILED.value

    # Partial: soft discrepancies or incomplete tasks
    soft = [d for d in discrepancies if d not in hard_hits]
    if soft or claimed.tasks_partial or claimed.tasks_failed:
        return AgentVerdict.PARTIAL.value

    # Everything lines up
    if claimed.committed and not discrepancies:
        return AgentVerdict.DELIVERED.value

    return AgentVerdict.PARTIAL.value


import re  # noqa: E402 (placed here to avoid circular at top)
