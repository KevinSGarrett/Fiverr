"""Scoring and recommendation persistence models."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin, SoftStatusMixin, TimestampMixin


class ScoreComponent(IntegerPrimaryKeyMixin, TimestampMixin, SoftStatusMixin, Base):
    __tablename__ = "score_components"
    __table_args__ = (UniqueConstraint("run_id", "score_name", "gig_id", name="uq_score_components_key"),)

    run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True, index=True)
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"), nullable=True, index=True)
    gig_id: Mapped[int | None] = mapped_column(ForeignKey("gigs.id"), nullable=True, index=True)
    seller_id: Mapped[int | None] = mapped_column(ForeignKey("sellers.id"), nullable=True, index=True)
    score_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    score_value: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    explanation: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class FinalScore(IntegerPrimaryKeyMixin, TimestampMixin, SoftStatusMixin, Base):
    __tablename__ = "final_scores"
    __table_args__ = (UniqueConstraint("run_id", "gig_id", name="uq_final_scores_run_gig"),)

    run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True, index=True)
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"), nullable=True, index=True)
    gig_id: Mapped[int | None] = mapped_column(ForeignKey("gigs.id"), nullable=True, index=True)
    seller_id: Mapped[int | None] = mapped_column(ForeignKey("sellers.id"), nullable=True, index=True)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    profile_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rank_in_run: Mapped[int | None] = mapped_column(nullable=True)
    explanation: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class Recommendation(IntegerPrimaryKeyMixin, TimestampMixin, SoftStatusMixin, Base):
    __tablename__ = "recommendations"

    run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"), nullable=True, index=True)
    final_score_id: Mapped[int | None] = mapped_column(ForeignKey("final_scores.id"), nullable=True, index=True)
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"), nullable=True, index=True)
    gig_id: Mapped[int | None] = mapped_column(ForeignKey("gigs.id"), nullable=True, index=True)
    recommendation_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    recommendation_text: Mapped[str] = mapped_column(String(4096), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
