"""Seller model and Stage-5 persistence helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.models.base import (
    Base,
    ExternalSourceMixin,
    IntegerPrimaryKeyMixin,
    MetadataJSONMixin,
    SoftStatusMixin,
    TimestampMixin,
)

if TYPE_CHECKING:
    from src.models.gig import Gig


class Seller(IntegerPrimaryKeyMixin, TimestampMixin, ExternalSourceMixin, MetadataJSONMixin, SoftStatusMixin, Base):
    """Persist seller profile fields collected from Fiverr profile pages."""

    __tablename__ = "sellers"
    tablename = __tablename__
    __table_args__ = (
        Index("ix_sellers_seller_level", "seller_level"),
        Index("ix_sellers_run_id", "run_id"),
    )

    seller_username: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    seller_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    member_since: Mapped[str | None] = mapped_column(String(32), nullable=True)
    response_time: Mapped[str | None] = mapped_column(String(64), nullable=True)
    response_rate: Mapped[str | None] = mapped_column(String(16), nullable=True)
    languages: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    bio_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_reviews: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_gigs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gig_titles: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    portfolio_item_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    badges: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    profile_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    profile_collected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    profile_collected_at: Mapped[Any] = mapped_column(DateTime(timezone=True), nullable=True)
    ttl_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=720)

    # Legacy compatibility fields used by older tests/analysis flows.
    display_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    response_time_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    gigs: Mapped[list[Gig]] = relationship(back_populates="seller")

    def __init__(self, **kwargs: Any) -> None:
        # Keep legacy call sites (seller_handle/level) compatible with new schema.
        if kwargs.get("seller_username") is None and kwargs.get("seller_handle") is not None:
            kwargs["seller_username"] = kwargs.pop("seller_handle")
        if kwargs.get("seller_level") is None and kwargs.get("level") is not None:
            kwargs["seller_level"] = kwargs.pop("level")
        if kwargs.get("profile_collected") is None:
            kwargs["profile_collected"] = False
        if kwargs.get("ttl_hours") is None:
            kwargs["ttl_hours"] = 720
        super().__init__(**kwargs)

    @property
    def seller_handle(self) -> str:
        return self.seller_username

    @seller_handle.setter
    def seller_handle(self, value: str) -> None:
        self.seller_username = value

    @property
    def level(self) -> str | None:
        return self.seller_level

    @level.setter
    def level(self, value: str | None) -> None:
        self.seller_level = value

    @property
    def active_gig_titles(self) -> list[str] | None:
        return self.gig_titles

    @active_gig_titles.setter
    def active_gig_titles(self, value: list[str] | None) -> None:
        self.gig_titles = value

    @property
    def portfolio_count(self) -> int | None:
        return self.portfolio_item_count

    @portfolio_count.setter
    def portfolio_count(self, value: int | None) -> None:
        self.portfolio_item_count = value


def write_seller_profile(
    seller_username: str,
    run_id: str,
    seller_level: str | None,
    member_since: str | None,
    response_time: str | None,
    total_reviews: int | None,
    total_gigs: int | None,
    db: object,
) -> Seller | None:
    """Upsert a Seller row for a collected profile; return None for non-Session db."""
    if not isinstance(db, Session):
        return None

    existing = db.query(Seller).filter(Seller.seller_username == seller_username).one_or_none()
    row = Seller(
        id=existing.id if existing is not None else None,
        seller_username=seller_username,
        run_id=run_id,
        seller_level=seller_level,
        member_since=member_since,
        response_time=response_time,
        total_reviews=total_reviews,
        total_gigs=total_gigs,
        profile_collected=True,
        profile_collected_at=datetime.now(UTC),
    )
    merged = db.merge(row)
    db.commit()
    db.refresh(merged)
    return merged


def get_seller(seller_username: str, db: object) -> Seller | None:
    """Return a seller by username, or None for non-Session db."""
    if not isinstance(db, Session):
        return None
    return db.query(Seller).filter(Seller.seller_username == seller_username).first()
