"""
automation/report_synthesis/schemas.py
RSF-1.1: Dataclasses + enums for the ARSF layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AgentVerdict(str, Enum):
    DELIVERED = "DELIVERED"
    PARTIAL = "PARTIAL"
    CLAIMED_ONLY = "CLAIMED_ONLY"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    NO_REPORT = "NO_REPORT"


# ---------------------------------------------------------------------------
# Per-agent claim structures (parsed from the report)
# ---------------------------------------------------------------------------

@dataclass
class TaskClaim:
    id: str = ""
    title: str = ""
    status: str = ""   # DONE | PARTIAL | FAILED | DEFERRED
    evidence: str = ""


@dataclass
class GateClaim:
    id: str = ""
    result: str = ""   # PASS | FAIL
    evidence: str = ""


@dataclass
class JiraActionClaim:
    key: str = ""
    comment: bool = False
    worklog: str = "none"
    transition: str = "none"
    transition_id: str = "none"


# ---------------------------------------------------------------------------
# ClaimedAgentReport  — the parsed view of ONE agent's report
# ---------------------------------------------------------------------------

@dataclass
class ClaimedAgentReport:
    cycle: int = 0
    agent: str = ""
    role: str = ""
    branch: str = ""
    base_sha: str = ""
    verdict: str = ""
    verdict_qualifier: str = ""
    summary: str = ""
    tasks: list[TaskClaim] = field(default_factory=list)
    tasks_total: int = 0
    tasks_done: int = 0
    tasks_partial: int = 0
    tasks_failed: int = 0
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    commits: list[str] = field(default_factory=list)
    committed: bool = False
    validation: dict[str, Any] = field(default_factory=dict)
    gates: list[GateClaim] = field(default_factory=list)
    ac_status: list[dict[str, Any]] = field(default_factory=list)
    jira_actions: list[JiraActionClaim] = field(default_factory=list)
    governance_updates: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    non_claims: list[str] = field(default_factory=list)
    carryover: list[str] = field(default_factory=list)
    self_status: str = ""
    # parse metadata
    parse_source: str = "unknown"   # "manifest" | "markdown" | "none"
    format_violations: list[str] = field(default_factory=list)
    raw_text: str = ""

    def is_empty(self) -> bool:
        """True when the report carries no real claimed content.

        A report is empty only when there are NO claimed files, NO summary,
        NO task claims, and NO verdict. Used to decide NO_REPORT — a missing
        file or a title-only stub is empty; a real markdown report is not.
        """
        return not (
            self.files_created
            or self.files_modified
            or self.summary.strip()
            or self.tasks
            or self.verdict.strip()
        )


# ---------------------------------------------------------------------------
# AgentReportSynthesis — the cross-checked view (claimed + actual)
# ---------------------------------------------------------------------------

@dataclass
class AgentReportSynthesis:
    agent: str = ""
    claimed: ClaimedAgentReport | None = None
    verdict: str = AgentVerdict.NO_REPORT.value
    discrepancies: list[str] = field(default_factory=list)
    actual_commits: list[str] = field(default_factory=list)
    actual_files: list[str] = field(default_factory=list)
    ci_status: str = "unknown"
    unmet_ac: list[str] = field(default_factory=list)
    carryover: list[str] = field(default_factory=list)
    summary_for_pm: str = ""
    # ICV fold
    icv_status: str = ""
    icv_score: float = 0.0


# ---------------------------------------------------------------------------
# CycleSynthesis — the top-level artifact
# ---------------------------------------------------------------------------

@dataclass
class CycleSynthesis:
    cycle: int = 0
    agents: dict[str, AgentReportSynthesis] = field(default_factory=dict)
    cycle_verdict: str = ""
    carryover: list[str] = field(default_factory=list)
    top_risks: list[str] = field(default_factory=list)
    format_health: str = ""   # e.g. "5/6" (manifest-conforming reports)
    parsed_ok: str = ""       # e.g. "6/6" (reports that parsed to real content, not NO_REPORT)
    pm_markdown: str = ""
