"""Auto-promotion log model — task 1.3.27."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin, TimestampMixin


class AutoPromotionLog(IntegerPrimaryKeyMixin, TimestampMixin, Base):
    """Records niche depth changes triggered by the auto-promotion evaluator.

    Each row captures a single promotion or demotion event for a niche,
    including the before/after depth values and the score that triggered the change.
    """

    __tablename__ = "auto_promotion_logs"

    niche_id: Mapped[int] = mapped_column(
        ForeignKey("niches.id"), nullable=False, index=True
    )
    run_id: Mapped[int | None] = mapped_column(
        ForeignKey("run_logs.id"), nullable=True, index=True
    )
    previous_depth: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_depth: Mapped[str] = mapped_column(String(32), nullable=False)
    trigger_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    trigger_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    evaluation_run_count: Mapped[int | None] = mapped_column(nullable=True)
    approved_by: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # "auto" or manual override
