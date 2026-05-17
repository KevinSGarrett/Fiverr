"""Discovery cycle log model — task 1.3.25."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin, TimestampMixin


class DiscoveryCycleLog(IntegerPrimaryKeyMixin, TimestampMixin, Base):
    """Tracks each discovery cycle's hypotheses, costs, and outcomes.

    One row per discovery cycle run, recording aggregate statistics and
    configuration used for that cycle.
    """

    __tablename__ = "discovery_cycle_logs"

    run_id: Mapped[int | None] = mapped_column(
        ForeignKey("run_logs.id"), nullable=True, index=True
    )
    niche_id: Mapped[int | None] = mapped_column(
        ForeignKey("niches.id"), nullable=True, index=True
    )
    cycle_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hypotheses_generated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hypotheses_promoted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hypotheses_rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_llm_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    enabled_modes: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)
    error_message: Mapped[str | None] = mapped_column(nullable=True)
