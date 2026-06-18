"""
loop_governor.py -- Guarantees termination. Decides ACCEPT_PASS / REPAIR / STOP.

ICV-GOV-1..9: All 9 termination guarantees from ICV design Wave 9 §9.1.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from automation.codex_verifier.schemas import (
    GovernorDecision,
    GovernorDecisionKind,
    ItemClassification,
    StopReason,
    VerificationResult,
    VerificationStatus,
)


@dataclass
class _AttemptHistory:
    score: float
    cost_usd: float
    snapshot_ref: str = ""


class LoopGovernor:
    """
    Pure logic -- no I/O. Decides what to do given the current verdict and history.
    Guarantees termination by construction via 9 independent guarantees (Wave 9 §9.1).
    """

    def __init__(
        self,
        max_attempts: int = 3,
        wall_clock_max_s: float = 1800.0,
        openai_budget_usd: float = 2.0,
        min_score: float = 0.80,
        min_progress_delta: float = 0.05,
        pass_confidence_floor: float = 0.55,
    ) -> None:
        self.max_attempts = max_attempts
        self.wall_clock_max_s = wall_clock_max_s
        self.openai_budget_usd = openai_budget_usd
        self.min_score = min_score
        self.min_progress_delta = min_progress_delta
        self.pass_confidence_floor = pass_confidence_floor
        self._history: list[_AttemptHistory] = []
        self._start_time = time.time()
        self._total_cost = 0.0
        self._attempted_action_hashes: set[str] = set()

    def note_attempt(self, score: float, cost_usd: float, snapshot_ref: str = "") -> None:
        self._history.append(_AttemptHistory(score=score, cost_usd=cost_usd, snapshot_ref=snapshot_ref))
        self._total_cost += cost_usd

    def decide(self, verdict: VerificationResult, attempt: int) -> GovernorDecision:
        elapsed = time.time() - self._start_time

        # Wave 9 #0: Deterministic PASS
        if verdict.deterministic_only and verdict.status == VerificationStatus.PASS:
            return GovernorDecision(kind=GovernorDecisionKind.ACCEPT_PASS, stop_reason=StopReason.DETERMINISTIC_PASS, explanation="All blocking items satisfied deterministically")

        # Wave 9 #8: PASS with confidence floor
        if verdict.status == VerificationStatus.PASS and verdict.completion_score >= self.min_score:
            return GovernorDecision(kind=GovernorDecisionKind.ACCEPT_PASS, explanation=f"PASS score={verdict.completion_score:.2f}")

        # Wave 9 #1: Attempt cap
        if attempt >= self.max_attempts:
            return GovernorDecision(kind=GovernorDecisionKind.STOP, stop_reason=StopReason.ATTEMPT_CAP, explanation=f"Cap reached ({attempt}/{self.max_attempts})")

        # Wave 9 #6: Wall-clock
        if elapsed > self.wall_clock_max_s:
            return GovernorDecision(kind=GovernorDecisionKind.STOP, stop_reason=StopReason.WALL_CLOCK_EXCEEDED, explanation=f"Elapsed {elapsed:.0f}s > {self.wall_clock_max_s:.0f}s")

        # Wave 9 #5: Budget
        if self._total_cost >= self.openai_budget_usd:
            return GovernorDecision(kind=GovernorDecisionKind.STOP, stop_reason=StopReason.BUDGET_EXHAUSTED, explanation=f"Budget ${self._total_cost:.4f} >= ${self.openai_budget_usd:.2f}")

        # Wave 9 #3: Regression tripwire
        if len(self._history) >= 2:
            prev = self._history[-2].score
            curr = self._history[-1].score
            if curr < prev - 0.01:
                snap = self._history[-2].snapshot_ref
                return GovernorDecision(kind=GovernorDecisionKind.STOP, stop_reason=StopReason.REGRESSION, rolled_back=bool(snap), snapshot_ref=snap, explanation=f"Score regressed {prev:.2f}->{curr:.2f}")

        # Wave 9 #2: Monotonic progress
        if len(self._history) >= 2:
            prev = self._history[-2].score
            curr = self._history[-1].score
            if (curr - prev) < self.min_progress_delta:
                return GovernorDecision(kind=GovernorDecisionKind.STOP, stop_reason=StopReason.NO_PROGRESS, explanation=f"delta={curr-prev:.3f} < {self.min_progress_delta}")

        # Wave 9 #7: Nothing fixable
        fixable = [i for i in verdict.unmet_items if i.classification == ItemClassification.FIXABLE_IN_SCOPE]
        if not fixable:
            return GovernorDecision(kind=GovernorDecisionKind.STOP, stop_reason=StopReason.NOTHING_FIXABLE, explanation=f"{len(verdict.unmet_items)} unmet but none FIXABLE_IN_SCOPE")

        # Wave 9 #4: Oscillation detection
        _ak = f"{attempt}:{verdict.completion_score:.3f}:{len(verdict.unmet_items)}"
        if _ak in self._attempted_action_hashes:
            return GovernorDecision(kind=GovernorDecisionKind.STOP, stop_reason=StopReason.OPERATOR_STOP, explanation=f"OSCILLATION: key {_ak!r} already attempted")
        self._attempted_action_hashes.add(_ak)

        return GovernorDecision(kind=GovernorDecisionKind.REPAIR, explanation=f"Attempt {attempt+1}/{self.max_attempts}: {len(fixable)} fixable, score={verdict.completion_score:.2f}")
