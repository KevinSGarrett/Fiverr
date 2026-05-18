"""Pricing analysis persistence models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, UniqueConstraint, desc
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin, utc_now


class PriceAnalysis(IntegerPrimaryKeyMixin, Base):
    """Persisted per-keyword price distribution analysis."""

    __tablename__ = "price_analyses"
    __table_args__ = (
        UniqueConstraint("keyword_id", "run_id", name="uq_price_analyses_keyword_run"),
        Index("ix_price_analyses_keyword_analyzed_at", "keyword_id", desc("analyzed_at")),
    )

    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    basic_n: Mapped[int | None] = mapped_column(nullable=True)
    basic_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_cv: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_skewness: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_gaps: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)

    standard_n: Mapped[int | None] = mapped_column(nullable=True)
    standard_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_mean: Mapped[float | None] = mapped_column(Float, nullable=True)

    premium_n: Mapped[int | None] = mapped_column(nullable=True)
    premium_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_mean: Mapped[float | None] = mapped_column(Float, nullable=True)

    market_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    moat_strength: Mapped[str | None] = mapped_column(String(16), nullable=True)
    review_premium: Mapped[float | None] = mapped_column(Float, nullable=True)
