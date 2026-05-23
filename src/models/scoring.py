"""Scoring and recommendation persistence models."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, UniqueConstraint
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
    run_id_text: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    final_score_id: Mapped[int | None] = mapped_column(ForeignKey("final_scores.id"), nullable=True, index=True)
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"), nullable=True, index=True)
    gig_id: Mapped[int | None] = mapped_column(ForeignKey("gigs.id"), nullable=True, index=True)
    niche_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    tag: Mapped[str | None] = mapped_column(String(32), nullable=True)
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    generation_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    llm_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    gig_titles: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    tag_sets: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    package_structure: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    description_outline: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    faq_entries: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    differentiation_angle: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    buyer_persona: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    thumbnail_direction: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    upsell_structure: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    red_flags: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    niche_viability: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[Any | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score_at_generation: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommendation_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    recommendation_text: Mapped[str] = mapped_column(String(4096), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
