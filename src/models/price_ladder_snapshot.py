"""Wave 9 Phase 3 model for price ladder tracking snapshots."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin


class PriceLadderSnapshot(IntegerPrimaryKeyMixin, Base):
    """Track actual seller pricing versus recommended ladder milestones."""

    __tablename__ = "price_ladder_snapshots"

    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False, index=True)
    niche_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    run_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    reviews_at_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ladder_milestone: Mapped[int | None] = mapped_column(Integer, nullable=True)

    actual_basic_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_standard_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_premium_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    recommended_basic_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommended_standard_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommended_premium_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    price_delta_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    on_track: Mapped[bool] = mapped_column(nullable=False, default=True)
    tolerance: Mapped[float] = mapped_column(Float, nullable=False, default=0.15)
