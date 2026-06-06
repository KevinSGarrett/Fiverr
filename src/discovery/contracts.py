"""Discovery engine contracts.

Status: Scaffolded (SCRUM-273). Full implementation in SCRUM-195 through SCRUM-204.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HypothesisMode(str, Enum):
    """Supported discovery hypothesis generation modes for S7.2-S7.5."""

    ADJACENT_KEYWORD = "adjacent_keyword"  # S7.2
    ADJACENT_NICHE = "adjacent_niche"  # S7.3
    GAP_EXPLOIT = "gap_exploit"  # S7.4
    TREND_CHASE = "trend_chase"  # S7.5


class HypothesisStatus(str, Enum):
    """Lifecycle status of a discovery hypothesis."""

    PENDING = "pending"
    TESTING = "testing"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    SKIPPED = "skipped"


@dataclass
class DiscoveryHypothesisResult:
    """Single generated discovery hypothesis."""

    keyword: str
    normalized_keyword: str
    hypothesis_type: str  # matches HypothesisMode value
    rationale: str = ""
    estimated_demand: str = "MEDIUM"
    estimated_competition: str = "MEDIUM"
    confidence: float = 0.0
    status: str = HypothesisStatus.PENDING.value
    raw_json: dict[str, Any] = field(default_factory=dict)


@dataclass
class DiscoveryInput:
    """Input contract for a discovery cycle run."""

    run_id: int | None = None
    niche_id: str | None = None
    niche_name: str = ""
    category_path: str = ""
    active_keywords: list[str] = field(default_factory=list)
    primary_skills: list[str] = field(default_factory=list)
    enabled_modes: list[str] = field(default_factory=list)
    max_hypotheses: int = 12
    budget_usd: float = 7.5
    competitor_weaknesses: list[str] = field(default_factory=list)
    trend_signals: list[dict[str, Any]] = field(default_factory=list)
    llm_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class DiscoveryOutput:
    """Output from a discovery cycle run."""

    run_id: int | None = None
    niche_id: str | None = None
    hypotheses: list[DiscoveryHypothesisResult] = field(default_factory=list)
    cost_usd: float = 0.0
    modes_run: list[str] = field(default_factory=list)
    promoted_keywords: list[str] = field(default_factory=list)
    raw_json: dict[str, Any] = field(default_factory=dict)

    @property
    def hypothesis_count(self) -> int:
        return len(self.hypotheses)

    @property
    def promoted_count(self) -> int:
        return len(self.promoted_keywords)
