"""Discovery outcome persistence model.

Supports both legacy relevance-gate fields and S7.6 scoring-feedback fields.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin


class DiscoveryOutcome(IntegerPrimaryKeyMixin, Base):
    __tablename__ = "discovery_outcomes"

    # S7.6 canonical fields
    keyword_id: Mapped[int | None] = mapped_column(
        ForeignKey("keywords.id"),
        nullable=True,
        index=True,
    )
    discovery_mode: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    hypothesis_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_tag: Mapped[str | None] = mapped_column(String(32), nullable=True)
    score_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_gold: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_hit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_miss: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )

    # Legacy fields kept for backward compatibility
    run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    niche_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    keyword_text: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    is_invalid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_contaminated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    contamination_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
