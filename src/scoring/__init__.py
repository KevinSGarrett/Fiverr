"""Scoring engine — E04 implementation module.

Provides composite opportunity scoring across demand, competition, feasibility,
profitability, intent, saturation, weakness, and trend dimensions.

Status: Scaffolded (SCRUM-273). Full implementation tracked in SCRUM-165 through SCRUM-177.
"""

from __future__ import annotations

from src.scoring.contracts import ScoringInput, ScoringOutput
from src.scoring.orchestrator import ScoringOrchestrator

__all__ = [
    "ScoringInput",
    "ScoringOutput",
    "ScoringOrchestrator",
]
