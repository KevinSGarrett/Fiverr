"""Dashboard display schema for ranked keyword opportunities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.models.keyword_score import KeywordScore


class ScoreBreakdown(BaseModel):
    """Score detail values shown on an opportunity card."""

    demand: float | None = None
    competition: float | None = None
    opportunity: float | None = None
    feasibility: float | None = None
    profitability: float | None = None
    confidence_modifier: float | None = None


class OpportunityCardSchema(BaseModel):
    """Display schema for a single keyword opportunity card in the dashboard."""

    keyword_id: int
    keyword_text: str
    niche_id: str
    niche_name: str | None = None
    tag: str  # STRONG_GO / CONDITIONAL_GO / MONITOR / CAUTION / PASS
    final_score: float = Field(..., ge=0.0, le=100.0)
    confidence_modifier: float = Field(..., ge=0.0, le=1.0)
    score_breakdown: ScoreBreakdown
    red_flags: list[str] = Field(default_factory=list)
    missing_data_warnings: list[str] = Field(default_factory=list)
    explanation_text: str | None = None
    scored_at: str | None = None  # ISO datetime string for serialization
    rank: int | None = None
    percentile: float | None = None  # 0-100

    @classmethod
    def from_keyword_score(
        cls,
        ks: KeywordScore,
        rank: int | None = None,
    ) -> OpportunityCardSchema:
        """Build OpportunityCardSchema from a KeywordScore ORM row."""

        breakdown = ScoreBreakdown(
            demand=ks.demand_score,
            competition=ks.competition_score,
            opportunity=ks.opportunity_score,
            feasibility=ks.feasibility_score,
            profitability=ks.profitability_score,
            confidence_modifier=ks.confidence_modifier,
        )
        return cls(
            keyword_id=ks.keyword_id,
            keyword_text="",  # caller populates from Keyword table
            niche_id="",
            tag=ks.tag or "MONITOR",
            final_score=ks.final_score or 0.0,
            confidence_modifier=ks.confidence_modifier or 0.0,
            score_breakdown=breakdown,
            red_flags=[flag.get("flag", "") for flag in (ks.red_flags or []) if isinstance(flag, dict)],
            missing_data_warnings=ks.missing_data_warnings or [],
            explanation_text=ks.explanation_text,
            scored_at=ks.scored_at.isoformat() if ks.scored_at else None,
            rank=rank,
        )
