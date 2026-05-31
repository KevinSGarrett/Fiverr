"""Keyword scoring persistence model and query helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, UniqueConstraint, desc
from sqlalchemy.orm import Mapped, Session, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin, utc_now


class KeywordScore(IntegerPrimaryKeyMixin, Base):
    """Persisted score payload for a keyword/profile/depth calculation."""

    __tablename__ = "keyword_scores"
    __table_args__ = (
        UniqueConstraint(
            "keyword_id",
            "scoring_profile",
            "scored_at",
            name="uq_keyword_scores_keyword_profile_scored_at",
        ),
        Index("ix_keyword_scores_keyword_scored_at", "keyword_id", desc("scored_at")),
    )

    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False, index=True)
    scoring_profile: Mapped[str] = mapped_column(String(64), nullable=False, default="default")
    score_depth: Mapped[str] = mapped_column(String(32), nullable=False, default="standard")
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    data_as_of: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    demand_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    competition_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    opportunity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feasibility_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    profitability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    intent_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    saturation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    weakness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    trend_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_modifier: Mapped[float | None] = mapped_column(Float, nullable=True)
    trc_reliability: Mapped[float | None] = mapped_column(Float, nullable=True)
    opportunity_relevance_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_outliers_excluded: Mapped[int | None] = mapped_column(nullable=True)
    clean_gig_count: Mapped[int | None] = mapped_column(nullable=True)
    competitor_profile_source: Mapped[str | None] = mapped_column(String(32), nullable=True)

    tag: Mapped[str | None] = mapped_column(String(32), nullable=True)
    score_components: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    confidence_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    explanation_text: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    red_flags: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    missing_data_warnings: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    source_evidence: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    llm_inputs_used: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    niche_tier: Mapped[str | None] = mapped_column(String(64), nullable=True)


def get_latest_keyword_score(keyword_id: int, db: Any) -> KeywordScore | None:
    """Return the latest score row for a keyword id."""

    if not isinstance(db, Session):
        return None
    return (
        db.query(KeywordScore)
        .filter(KeywordScore.keyword_id == keyword_id)
        .order_by(KeywordScore.scored_at.desc())
        .first()
    )
