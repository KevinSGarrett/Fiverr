"""Wave 9 pricing analysis persistence models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin, utc_now


class PriceAnalysis(IntegerPrimaryKeyMixin, Base):
    """Per-keyword price distribution analysis."""

    __tablename__ = "price_analysis"
    __table_args__ = (UniqueConstraint("keyword_id", "run_id", name="uq_price_analysis_keyword_run"),)

    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False, index=True)
    niche_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    basic_n: Mapped[int | None] = mapped_column(Integer, nullable=True)
    basic_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_mode: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_std: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_q1: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_q3: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_p10: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_p90: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_skewness: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_cv: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_clusters: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    basic_gaps: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)

    standard_n: Mapped[int | None] = mapped_column(Integer, nullable=True)
    standard_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_mode: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_std: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_q1: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_q3: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_p10: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_p90: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_skewness: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_cv: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_clusters: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    standard_gaps: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)

    premium_n: Mapped[int | None] = mapped_column(Integer, nullable=True)
    premium_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_mode: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_std: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_q1: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_q3: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_p10: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_p90: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_skewness: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_cv: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_clusters: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    premium_gaps: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)

    price_review_correlation: Mapped[float | None] = mapped_column(Float, nullable=True)
    moat_strength: Mapped[str | None] = mapped_column(String(16), nullable=True)
    review_premium_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_seller_avg_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_seller_discount_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_type: Mapped[str | None] = mapped_column(String(32), nullable=True)

    avg_extras_count: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_extras_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    extras_price_range: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class NichePriceAnalysis(IntegerPrimaryKeyMixin, Base):
    """Niche-level aggregate price analysis."""

    __tablename__ = "niche_price_analysis"

    niche_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True, unique=True)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    keywords_analyzed: Mapped[int | None] = mapped_column(Integer, nullable=True)

    basic_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_p25: Mapped[float | None] = mapped_column(Float, nullable=True)
    basic_p75: Mapped[float | None] = mapped_column(Float, nullable=True)

    standard_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_p25: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_p75: Mapped[float | None] = mapped_column(Float, nullable=True)

    premium_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_p25: Mapped[float | None] = mapped_column(Float, nullable=True)
    premium_p75: Mapped[float | None] = mapped_column(Float, nullable=True)

    avg_price_review_correlation: Mapped[float | None] = mapped_column(Float, nullable=True)
    moat_strength: Mapped[str | None] = mapped_column(String(16), nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class PricingSnapshot(IntegerPrimaryKeyMixin, Base):
    """New seller pricing recommendation snapshot per keyword."""

    __tablename__ = "pricing_snapshots"

    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False, index=True)
    niche_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    entry_basic: Mapped[float | None] = mapped_column(Float, nullable=True)
    entry_standard: Mapped[float | None] = mapped_column(Float, nullable=True)
    entry_premium: Mapped[float | None] = mapped_column(Float, nullable=True)

    acquisition_basic: Mapped[float | None] = mapped_column(Float, nullable=True)
    acquisition_standard: Mapped[float | None] = mapped_column(Float, nullable=True)
    acquisition_premium: Mapped[float | None] = mapped_column(Float, nullable=True)

    target_basic: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_standard: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_premium: Mapped[float | None] = mapped_column(Float, nullable=True)

    price_ladder: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    undercut_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    moat_adjustment: Mapped[float | None] = mapped_column(Float, nullable=True)
    gap_pricing_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    gap_target: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
