"""
schemas.py -- Core dataclasses for the Inter-Agent Codex Verifier (ICV).

ICV-ARCH-1: All data structures defined here; no circular imports.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChecklistStatus(str, Enum):
    SATISFIED    = "satisfied"
    PARTIAL      = "partial"
    MISSING      = "missing"
    UNVERIFIABLE = "unverifiable"


class ItemClassification(str, Enum):
    FIXABLE_IN_SCOPE  = "FIXABLE_IN_SCOPE"
    OUT_OF_SCOPE      = "OUT_OF_SCOPE"
    BLOCKED_EXTERNAL  = "BLOCKED_EXTERNAL"
    NON_ISSUE         = "NON_ISSUE"
    AMBIGUOUS         = "AMBIGUOUS"


class VerificationStatus(str, Enum):
    PASS           = "PASS"
    PARTIAL_PASS   = "PARTIAL_PASS"
    FAIL           = "FAIL"
    UNVERIFIABLE   = "UNVERIFIABLE"


class OutcomeStatus(str, Enum):
    VERIFIED_PASS       = "VERIFIED_PASS"
    PASS_WITH_DEFERRALS = "PASS_WITH_DEFERRALS"
    BLOCKED             = "BLOCKED"
    SKIPPED_BUDGET      = "SKIPPED_BUDGET"
    SKIPPED_DISABLED    = "SKIPPED_DISABLED"
    ERROR_FALLBACK      = "ERROR_FALLBACK"


class GovernorDecisionKind(str, Enum):
    ACCEPT_PASS = "ACCEPT_PASS"
    REPAIR      = "REPAIR"
    STOP        = "STOP"


class StopReason(str, Enum):
    ATTEMPT_CAP          = "ATTEMPT_CAP"
    NO_PROGRESS          = "NO_PROGRESS"
    REGRESSION           = "REGRESSION"
    NOTHING_FIXABLE      = "NOTHING_FIXABLE"
    BUDGET_EXHAUSTED     = "BUDGET_EXHAUSTED"
    WALL_CLOCK_EXCEEDED  = "WALL_CLOCK_EXCEEDED"
    DETERMINISTIC_PASS   = "DETERMINISTIC_PASS"
    LLM_UNAVAILABLE      = "LLM_UNAVAILABLE"
    OPERATOR_STOP        = "OPERATOR_STOP"


@dataclass
class ChecklistItem:
    id: str                                          # e.g. "AC-SCRUM-205-1"
    source: str                                      # "contract.jirascope", "prompt.task", "validation_command"
    description: str
    status: ChecklistStatus = ChecklistStatus.UNVERIFIABLE
    classification: ItemClassification = ItemClassification.AMBIGUOUS
    evidence: str = ""                               # machine-verifiable evidence citation
    is_blocking: bool = True                         # non-blocking = deferrable without BLOCKED outcome


@dataclass
class EvidenceBundle:
    cycle: str
    agent: str
    branch: str
    prompt_text: str
    contract: dict                                   # parsed contract JSON
    head_sha: str | None = None
    committed_this_run: bool = False
    changed_files: list[str] = field(default_factory=list)
    out_of_lane_files: list[str] = field(default_factory=list)
    report_exists: bool = False
    report_text: str = ""
    report_has_complete_marker: bool = False
    validation_command_results: list[dict] = field(default_factory=list)   # [{cmd, rc, stdout, stderr}]
    deliverable_exists: dict[str, bool] = field(default_factory=dict)      # path -> exists
    ci_passed: bool | None = None
    github_pr_number: int | None = None
    jira_statuses: dict[str, str] = field(default_factory=dict)            # key -> status
    elapsed_minutes: float = 0.0
    dispatch_exit_code: int | None = None
    suspiciously_fast: bool = False
    run_dir: str = ""
    errors: list[str] = field(default_factory=list)


@dataclass
class VerificationResult:
    status: VerificationStatus
    completion_score: float                          # 0.0-1.0
    checklist: list[ChecklistItem] = field(default_factory=list)
    unmet_items: list[ChecklistItem] = field(default_factory=list)
    reasoning: str = ""
    confidence: float = 0.0
    tokens_used: int = 0
    cost_usd: float = 0.0
    deterministic_only: bool = False                 # True if LLM was skipped

    @property
    def has_blocking_unmet(self) -> bool:
        return any(i.is_blocking for i in self.unmet_items
                   if i.status != ChecklistStatus.SATISFIED)


@dataclass
class RepairDirective:
    prompt_text: str
    prompt_path: str
    target_items: list[ChecklistItem] = field(default_factory=list)
    estimated_tokens: int = 0


@dataclass
class GovernorDecision:
    kind: GovernorDecisionKind
    stop_reason: StopReason | None = None
    rolled_back: bool = False
    snapshot_ref: str = ""
    explanation: str = ""


@dataclass
class AttemptRecord:
    attempt: int
    timestamp: str
    verdict_status: str
    completion_score: float
    decision_kind: str
    stop_reason: str | None
    cost_usd: float
    tokens_used: int
    unmet_count: int
    deterministic_only: bool


@dataclass
class AgentVerificationOutcome:
    cycle: str
    agent: str
    status: OutcomeStatus
    completion_score: float = 0.0
    attempts: int = 0
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    unmet_items: list[ChecklistItem] = field(default_factory=list)
    stop_reason: StopReason | None = None
    icv_report_path: str = ""
    errors: list[str] = field(default_factory=list)
    skipped_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle": self.cycle,
            "agent": self.agent,
            "status": self.status.value,
            "completion_score": self.completion_score,
            "attempts": self.attempts,
            "total_cost_usd": self.total_cost_usd,
            "total_tokens": self.total_tokens,
            "unmet_count": len(self.unmet_items),
            "stop_reason": self.stop_reason.value if self.stop_reason else None,
            "icv_report_path": self.icv_report_path,
            "errors": self.errors,
        }
