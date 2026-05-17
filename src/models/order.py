"""Order / revenue tracking model — task 1.3.28."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, ExternalSourceMixin, IntegerPrimaryKeyMixin, TimestampMixin


class Order(IntegerPrimaryKeyMixin, TimestampMixin, ExternalSourceMixin, Base):
    """Revenue order record for the gate tracker (E06 Story 6.5).

    Tracks individual orders on gigs being monitored, enabling the Revenue
    Gate Tracker to calculate monthly revenue velocity and gate thresholds.
    """

    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("external_order_id", name="uq_orders_external_order_id"),
    )

    external_order_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True
    )
    gig_id: Mapped[int | None] = mapped_column(
        ForeignKey("gigs.id"), nullable=True, index=True
    )
    seller_id: Mapped[int | None] = mapped_column(
        ForeignKey("sellers.id"), nullable=True, index=True
    )
    niche_id: Mapped[int | None] = mapped_column(
        ForeignKey("niches.id"), nullable=True, index=True
    )
    order_value_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    package_tier: Mapped[str | None] = mapped_column(String(32), nullable=True)
    order_date_text: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False
    )
    review_left: Mapped[bool] = mapped_column(default=False, nullable=False)
    repeat_buyer: Mapped[bool] = mapped_column(default=False, nullable=False)
    run_id: Mapped[int | None] = mapped_column(
        ForeignKey("run_logs.id"), nullable=True, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
