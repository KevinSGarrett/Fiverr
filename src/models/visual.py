"""Gig visual analysis model — AC-1.3.9."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, IntegerPrimaryKeyMixin, TimestampMixin


class GigVisualAnalysis(IntegerPrimaryKeyMixin, TimestampMixin, Base):
    """Thumbnail and gallery visual classification for a gig — AC-1.3.9.

    Records the result of Wave 11 visual analysis on a gig's thumbnail,
    gallery images, and video presence.
    """

    __tablename__ = "gig_visual_analyses"

    gig_id: Mapped[int] = mapped_column(
        ForeignKey("gigs.id"), nullable=False, index=True
    )
    run_id: Mapped[int | None] = mapped_column(
        ForeignKey("run_logs.id"), nullable=True, index=True
    )
    # Thumbnail classification
    thumbnail_type: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # e.g. branded, stock_photo, illustration, text_only, screenshot
    thumbnail_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    has_face: Mapped[bool | None] = mapped_column(nullable=True)
    has_logo: Mapped[bool | None] = mapped_column(nullable=True)
    dominant_color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    text_overlay_present: Mapped[bool | None] = mapped_column(nullable=True)
    # Gallery
    gallery_item_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_video: Mapped[bool | None] = mapped_column(nullable=True)
    # Aggregate assessment
    visual_strength_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    visual_style_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    analysis_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_analysis_json: Mapped[str | None] = mapped_column(nullable=True)
