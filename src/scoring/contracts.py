"""Scoring engine contracts for calculators and orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class ScoreComponent:
    """Single component contribution to a score calculation."""

    value: float
    weight: float
    raw: Any
    note: str = ""


@dataclass
class ScoreResult:
    """Common payload used by score calculators."""

    score_value: float | None
    score_components: dict[str, ScoreComponent] = field(default_factory=dict)
    confidence_modifier: float = 1.0
    confidence_breakdown: dict[str, float] = field(default_factory=dict)
    confidence_reason: str = ""
    missing_data_warnings: list[str] = field(default_factory=list)
    source_evidence: list[str] = field(default_factory=list)
    scored_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    explanation_text: str = ""


@dataclass
class DemandScoreResult(ScoreResult):
    """Result payload for S4.1 demand scoring."""

    keyword_id: int | None = None
    total_weight_available: float = 0.0


@dataclass
class CompetitionScoreResult(ScoreResult):
    """Result payload for S4.2 competition scoring."""

    keyword_id: int | None = None
    total_weight_available: float = 0.0


@dataclass
class OpportunityScoreResult(ScoreResult):
    """Result payload for S4.3 opportunity scoring."""

    keyword_id: int | None = None
    demand_score: float | None = None
    competition_score: float | None = None
    default_weight: float = 0.25


@dataclass
class ScoreDimension:
    """Single scored dimension with value, weight, and explanation."""

    name: str
    value: float
    weight: float = 0.0
    explanation: str = ""
    raw_data: dict[str, Any] = field(default_factory=dict)

    def weighted_contribution(self) -> float:
        """Return this dimension's weighted contribution to composite score."""
        return self.value * self.weight


@dataclass
class ScoringInput:
    """Input contract for the scoring orchestrator."""

    run_id: int | None = None
    niche_id: str | None = None
    keyword_id: int | None = None
    gig_id: int | None = None
    seller_id: int | None = None
    profile_name: str = "default"

    demand_signals: dict[str, Any] = field(default_factory=dict)
    competition_signals: dict[str, Any] = field(default_factory=dict)
    opportunity_signals: dict[str, Any] = field(default_factory=dict)
    feasibility_signals: dict[str, Any] = field(default_factory=dict)
    profitability_signals: dict[str, Any] = field(default_factory=dict)
    intent_signals: dict[str, Any] = field(default_factory=dict)
    saturation_signals: dict[str, Any] = field(default_factory=dict)
    weakness_signals: dict[str, Any] = field(default_factory=dict)
    trend_signals: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoringOutput:
    """Output contract for a completed scoring run."""

    run_id: int | None = None
    keyword_id: int | None = None
    gig_id: int | None = None
    seller_id: int | None = None
    profile_name: str = "default"
    dimensions: list[ScoreDimension] = field(default_factory=list)
    composite_score: float = 0.0
    rank_in_run: int | None = None
    verdict: str = "UNSCORED"
    explanation: str = ""
    raw_json: dict[str, Any] = field(default_factory=dict)

    @property
    def is_go(self) -> bool:
        return self.verdict in ("GO", "CONDITIONAL_GO")
