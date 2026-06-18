"""
loop_governor.py -- Guarantees termination. Decides ACCEPT_PASS / REPAIR / STOP.

ICV-GOV-1..8: Monotonic progress, attempt cap, budget, wall-clock, regression.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from automation.codex_verifier.schemas import (
    GovernorDecision,
    GovernorDecisionKind,
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
    Pure logic — no I/O. Decides what to do given the current verdict and history.
    Guarantees termination by construction.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        wall_clock_max_s: float = 1800.0,
        openai_budget_usd: float = 2.0,
        min_score: float = 0.80,
    ) -> None:
        self.max_attempts = max_attempts
        self.wall_clock_max_s = wall_clock_max_s
        self.openai_budget_usd = openai_budget_usd
        self.min_score = min_score
        self._history: list[_AttemptHistory] = []
        self._start_time = time.time()
        self._total_cost = 0.0

    def note_attempt(self, score: float, cost_usd: float, snapshot_ref: str = "") -> None:
        """Record the result of one attempt (call before decide)."""
        self._history.append(_AttemptHistory(score=score, cost_usd=cost_usd, snapshot_ref=snapshot_ref))
        self._total_cost += cost_usd

    def decide(
        self,
        verdict: VerificationResult,
        attempt: int,
    ) -> GovernorDecision:
        """
        Returns the decision for this attempt.
        Must be called after note_attempt().
        """
        elapsed = time.time() - self._start_time

        # ── ACCEPT: deterministic full pass ──────────────────────────
        if verdict.deterministic_only and verdict.status == VerificationStatus.PASS:
            return GovernorDecision(
                kind=GovernorDecisionKind.ACCEPT_PASS,
                stop_reason=StopReason.DETERMINISTIC_PASS,
                explanation="All blocking items satisfied deterministically",
            )

        # ── ACCEPT: LLM verdict PASS above threshold ─────────────────
        if (verdict.status == VerificationStatus.PASS
                and verdict.completion_score >= self.min_score):
            return GovernorDecision(
                kind=GovernorDecisionKind.ACCEPT_PASS,
                explanation=f"Verified PASS  score={verdict.completion_score:.2f}",
            )

        # ── STOP: hard cap on attempts ────────────────────────────────
        if attempt >= self.max_attempts:
            return GovernorDecision(
                kind=GovernorDecisionKind.STOP,
                stop_reason=StopReason.ATTEMPT_CAP,
                explanation=f"Attempt cap reached ({attempt}/{self.max_attempts})",
            )

        # ── STOP: wall-clock exceeded ─────────────────────────────────
        if elapsed > self.wall_clock_max_s:
            return GovernorDecision(
                kind=GovernorDecisionKind.STOP,
                stop_reason=StopReason.WALL_CLOCK_EXCEEDED,
                explanation=f"Wall clock {elapsed:.0f}s > cap {self.wall_clock_max_s:.0f}s",
            )

        # ── STOP: budget exhausted ────────────────────────────────────
        if self._total_cost >= self.openai_budget_usd:
            return GovernorDecision(
                kind=GovernorDecisionKind.STOP,
                stop_reason=StopReason.BUDGET_EXHAUSTED,
                explanation=f"Budget ${self._total_cost:.4f} >= cap ${self.openai_budget_usd:.2f}",
            )

        # ── STOP: no progress (score did not improve) ─────────────────
        if len(self._history) >= 2:
            prev_score = self._history[-2].score
            curr_score = self._history[-1].score
            if curr_score <= prev_score - 0.01:  # regression (allowed small epsilon)
                prev_snap = self._history[-2].snapshot_ref
                return GovernorDecision(
                    kind=GovernorDecisionKind.STOP,
                    stop_reason=StopReason.REGRESSION,
                    rolled_back=bool(prev_snap),
                    snapshot_ref=prev_snap,
                    explanation=(
                        f"Score regressed from {prev_score:.2f} to {curr_score:.2f} "
                        "(repair made things worse)"
                    ),
                )
            if curr_score <= prev_score + 0.01:  # no meaningful improvement
                return GovernorDecision(
                    kind=GovernorDecisionKind.STOP,
                    stop_reason=StopReason.NO_PROGRESS,
                    explanation=f"Score flat: {prev_score:.2f} -> {curr_score:.2f}",
                )

        # ── STOP: no fixable items remain ─────────────────────────────
        from automation.codex_verifier.schemas import ItemClassification
        fixable = [
            i for i in verdict.unmet_items
            if i.classification == ItemClassification.FIXABLE_IN_SCOPE
        ]
        if not fixable:
            return GovernorDecision(
                kind=GovernorDecisionKind.STOP,
                stop_reason=StopReason.NOTHING_FIXABLE,
                explanation=(
                    f"{len(verdict.unmet_items)} unmet items but none are FIXABLE_IN_SCOPE"
                ),
            )

        # ── REPAIR: more attempts available and fixable items exist ───
        return GovernorDecision(
            kind=GovernorDecisionKind.REPAIR,
            explanation=(
                f"Attempt {attempt + 1}/{self.max_attempts}: "
                f"{len(fixable)} fixable items, score={verdict.completion_score:.2f}"
            ),
        )
