"""Wave 9 Phase 3 model for revenue gate milestone records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin


class RevenueGateRecord(IntegerPrimaryKeyMixin, Base):
    """Persist milestone-based pricing gate checks for revenue tracking."""

    __tablename__ = "revenue_gate_records"

    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False, index=True)
    niche_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    milestone_reviews: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gate_triggered: Mapped[bool] = mapped_column(nullable=False, default=False)
    recommended_price_at_gate: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_price_at_gate: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_delta_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    monthly_orders_estimate: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    gate_alert_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
