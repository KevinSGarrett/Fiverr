"""Gig quality score ORM model and helper functions."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, Session, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin, TimestampMixin


class GigQualityScore(IntegerPrimaryKeyMixin, TimestampMixin, Base):
    """LLM/collection quality signal row per gig and run."""

    __tablename__ = "gig_quality_scores"
    tablename = __tablename__
    __table_args__ = (
        UniqueConstraint("gig_url", "run_id", name="uq_gig_quality_scores_gig_url_run_id"),
        Index("ix_gig_quality_scores_keyword_analysis_complete", "keyword_id", "analysis_complete"),
    )

    gig_id: Mapped[int | None] = mapped_column(ForeignKey("gigs.id"), nullable=True)
    gig_url: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    analysis_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    description_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    weakness_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    thumbnail_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    faq_completeness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    package_differentiation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    niche_specificity_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    video_present: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    portfolio_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    llm_model_used: Mapped[str | None] = mapped_column(String(128), nullable=True)
    llm_prompt_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    analysis_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ttl_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=720)


def write_gig_quality_score(
    gig_url: str,
    keyword_id: int,
    run_id: str,
    video_present: bool | None,
    portfolio_count: int | None,
    analysis_complete: bool,
    description_quality_score: float | None,
    weakness_count: int | None,
    db: Any,
) -> GigQualityScore | None:
    """Upsert a GigQualityScore row. Returns None when db is not a Session."""
    if not isinstance(db, Session):
        return None

    row = (
        db.query(GigQualityScore)
        .filter(
            GigQualityScore.gig_url == gig_url,
            GigQualityScore.run_id == run_id,
        )
        .one_or_none()
    )
    if row is None:
        row = GigQualityScore(gig_url=gig_url, run_id=run_id)
        db.add(row)

    row.keyword_id = keyword_id
    row.video_present = video_present
    row.portfolio_count = portfolio_count
    row.analysis_complete = analysis_complete
    row.description_quality_score = description_quality_score
    row.weakness_count = weakness_count
    row.analysed_at = datetime.now(UTC) if analysis_complete else None

    db.commit()
    db.refresh(row)
    return row


def get_gig_quality_scores(keyword_id: int, db: Any) -> list[GigQualityScore]:
    """Return all GigQualityScore rows for a keyword."""
    if not isinstance(db, Session):
        return []
    return db.query(GigQualityScore).filter(GigQualityScore.keyword_id == keyword_id).all()


def get_analysis_complete_count(keyword_id: int, db: Any) -> int:
    """Return count of rows with analysis_complete=True for a keyword."""
    if not isinstance(db, Session):
        return 0
    return (
        db.query(GigQualityScore)
        .filter(
            GigQualityScore.keyword_id == keyword_id,
            GigQualityScore.analysis_complete.is_(True),
        )
        .count()
    )
