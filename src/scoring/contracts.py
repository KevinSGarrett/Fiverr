"""Scoring engine contracts — input/output dataclasses.

Status: Scaffolded (SCRUM-273). Full implementation in SCRUM-165 through SCRUM-177.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
    """Input contract for the scoring orchestrator.

    All fields are optional to allow partial scoring during development.
    """

    run_id: int | None = None
    niche_id: str | None = None
    keyword_id: int | None = None
    gig_id: int | None = None
    seller_id: int | None = None
    profile_name: str = "default"

    # Raw signal inputs — populated by upstream analysis stages
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

    # GO/NO-GO threshold classification
    verdict: str = "UNSCORED"  # GO | CONDITIONAL_GO | MONITOR | CAUTION | NO_GO

    explanation: str = ""
    raw_json: dict[str, Any] = field(default_factory=dict)

    @property
    def is_go(self) -> bool:
        return self.verdict in ("GO", "CONDITIONAL_GO")
