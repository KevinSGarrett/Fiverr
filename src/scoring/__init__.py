"""Scoring engine — E04 implementation module.

Provides composite opportunity scoring across demand, competition, feasibility,
profitability, intent, saturation, weakness, and trend dimensions.

Status: Scaffolded (SCRUM-273). Full implementation tracked in SCRUM-165 through SCRUM-177.
"""

from __future__ import annotations

from src.scoring.contracts import ScoringInput, ScoringOutput
from src.scoring.orchestrator import ScoringOrchestrator
from src.scoring.pipeline import (
    SCORING_PROFILES,
    assign_tag,
    calculate_final_score,
    calculate_weighted_composite,
    detect_red_flags_from_scores,
    score_keyword,
    score_keyword_batch,
    write_keyword_score,
)

__all__ = [
    "SCORING_PROFILES",
    "ScoringInput",
    "ScoringOutput",
    "ScoringOrchestrator",
    "assign_tag",
    "calculate_final_score",
    "calculate_weighted_composite",
    "detect_red_flags_from_scores",
    "score_keyword",
    "score_keyword_batch",
    "write_keyword_score",
]
