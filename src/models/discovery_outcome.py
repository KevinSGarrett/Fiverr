"""Discovery outcome persistence model for relevance-gated decisions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin


class DiscoveryOutcome(IntegerPrimaryKeyMixin, Base):
    __tablename__ = "discovery_outcomes"

    run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    niche_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    keyword_text: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    is_invalid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_contaminated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    contamination_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )
