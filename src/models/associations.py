"""Many-to-many association tables — AC-1.3.5."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin, TimestampMixin


class KeywordGigAssociation(IntegerPrimaryKeyMixin, TimestampMixin, Base):
    """Many-to-many junction between keywords and gigs — AC-1.3.5.

    Records the relationship between a keyword search result and a gig,
    capturing the rank position and collection run that observed it.
    """

    __tablename__ = "keyword_gig_associations"
    __table_args__ = (
        UniqueConstraint(
            "keyword_id", "gig_id", "run_id",
            name="uq_kga_keyword_gig_run",
        ),
    )

    keyword_id: Mapped[int] = mapped_column(
        ForeignKey("keywords.id"), nullable=False, index=True
    )
    gig_id: Mapped[int] = mapped_column(
        ForeignKey("gigs.id"), nullable=False, index=True
    )
    run_id: Mapped[int | None] = mapped_column(
        ForeignKey("run_logs.id"), nullable=True, index=True
    )
    rank_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    search_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    collection_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
