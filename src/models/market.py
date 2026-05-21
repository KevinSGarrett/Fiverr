"""Core market and research entity models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from src.models.base import (
    Base,
    ExternalSourceMixin,
    IntegerPrimaryKeyMixin,
    MetadataJSONMixin,
    SoftStatusMixin,
    TimestampMixin,
)
from src.models.gig import Gig
from src.models.search_result import SearchResult
from src.models.seller import Seller as Seller  # noqa: F401

if TYPE_CHECKING:
    from src.models.external_signal import ExternalSignal
    from src.models.niche import Niche


class Keyword(
    IntegerPrimaryKeyMixin, TimestampMixin, ExternalSourceMixin, MetadataJSONMixin, SoftStatusMixin, Base
):
    __tablename__ = "keywords"
    __table_args__ = (UniqueConstraint("niche_id", "keyword", name="uq_keywords_niche_keyword"),)

    niche_id: Mapped[int] = mapped_column(ForeignKey("niches.id"), nullable=False, index=True)
    keyword: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    normalized_keyword: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    intent_class: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    embedding_vector: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    cluster_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True, default=None)
    search_volume_hint: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Discovery fields — AC-1.3.8
    is_discovery: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    discovery_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hypothesis_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    niche: Mapped[Niche] = relationship(back_populates="keywords")
    search_results: Mapped[list[SearchResult]] = relationship(back_populates="keyword_ref")
    gigs: Mapped[list[Gig]] = relationship(back_populates="keyword_ref")
    external_signals: Mapped[list[ExternalSignal]] = relationship("ExternalSignal", back_populates="keyword_ref")


class ClusterAssignment(IntegerPrimaryKeyMixin, Base):
    """Persist Stage 9 keyword-to-cluster assignments."""

    __tablename__ = "cluster_assignments"
    __table_args__ = (
        UniqueConstraint("keyword_id", "run_id", name="uq_cluster_assignments_keyword_run"),
    )

    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False, index=True)
    niche_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    cluster_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    algorithm: Mapped[str] = mapped_column(String(16), nullable=False, default="kmeans")
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )


class ClusterLabel(IntegerPrimaryKeyMixin, Base):
    """Persist Stage 9 cluster-level labels and narratives."""

    __tablename__ = "cluster_labels"
    __table_args__ = (
        UniqueConstraint("niche_id", "cluster_id", "run_id", name="uq_cluster_labels_niche_cluster_run"),
    )

    niche_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    cluster_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    label_text: Mapped[str | None] = mapped_column(String(256), nullable=True)
    opportunity_narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    keyword_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )


class CompetitorProfile(IntegerPrimaryKeyMixin, Base):
    """Persist Stage 10 per-niche competitor benchmark snapshots."""

    __tablename__ = "competitor_profiles"
    __table_args__ = (
        UniqueConstraint("niche_id", "run_id", name="uq_competitor_profiles_niche_run"),
    )

    niche_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    top_gig_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    median_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    mean_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_std: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    mean_reviews: Mapped[float | None] = mapped_column(Float, nullable=True)
    seller_level_distribution: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False, default=dict)
    min_delivery_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_delivery_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_present_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    portfolio_present_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_seller_gap: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )


class GigQualityAnalysis(IntegerPrimaryKeyMixin, Base):
    """Persist Stage 11 gig rubric analysis rows."""

    __tablename__ = "gig_quality_analyses"
    __table_args__ = (
        UniqueConstraint("gig_url", "run_id", name="uq_gig_quality_analyses_gig_url_run"),
    )

    gig_url: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    niche_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rubric_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    video_absent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    portfolio_absent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description_thin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    faq_absent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    thumbnail_quality_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    weakness_flags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )


class ReviewAnalysis(IntegerPrimaryKeyMixin, Base):
    """Persist Stage 12 per-gig review signal analysis rows."""

    __tablename__ = "review_analyses"
    __table_args__ = (
        UniqueConstraint("gig_url", "run_id", name="uq_review_analyses_gig_url_run"),
    )

    gig_url: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    niche_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_velocity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    recurring_complaints: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )


class AutocompleteSuggestion(IntegerPrimaryKeyMixin, TimestampMixin, Base):
    """Persist Stage-8 Fiverr autocomplete suggestions per keyword/run."""

    __tablename__ = "autocomplete_suggestions"
    tablename = __tablename__
    __table_args__ = (
        UniqueConstraint(
            "keyword_id",
            "suggestion_text",
            "run_id",
            name="uq_autocomplete_suggestion",
        ),
    )

    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False, index=True)
    niche_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    suggestion_text: Mapped[str] = mapped_column(String(256), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="fiverr_autocomplete")
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )

    keyword_ref: Mapped[Keyword] = relationship("Keyword")


class Review(IntegerPrimaryKeyMixin, TimestampMixin, ExternalSourceMixin, MetadataJSONMixin, Base):
    __tablename__ = "reviews"

    gig_id: Mapped[int | None] = mapped_column(ForeignKey("gigs.id"), nullable=True, index=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_text: Mapped[str | None] = mapped_column(String(4096), nullable=True)
    reviewer_handle: Mapped[str | None] = mapped_column(String(128), nullable=True)
    review_date_text: Mapped[str | None] = mapped_column(String(128), nullable=True)

    gig: Mapped[Gig | None] = relationship(back_populates="reviews")


def write_autocomplete_suggestion(
    *,
    keyword_id: int,
    niche_id: str,
    suggestion_text: str,
    position: int,
    run_id: str,
    db: Any,
    source: str = "fiverr_autocomplete",
) -> AutocompleteSuggestion | None:
    """Upsert autocomplete suggestion row by keyword/suggestion/run key."""
    if not isinstance(db, Session):
        return None

    normalized_text = suggestion_text.strip()
    if not normalized_text:
        return None

    row = (
        db.query(AutocompleteSuggestion)
        .filter(
            AutocompleteSuggestion.keyword_id == keyword_id,
            AutocompleteSuggestion.suggestion_text == normalized_text,
            AutocompleteSuggestion.run_id == run_id,
        )
        .one_or_none()
    )
    if row is None:
        row = AutocompleteSuggestion(
            keyword_id=keyword_id,
            niche_id=niche_id,
            suggestion_text=normalized_text,
            run_id=run_id,
        )

    row.niche_id = niche_id
    row.position = position
    row.source = source
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        row = (
            db.query(AutocompleteSuggestion)
            .filter(
                AutocompleteSuggestion.keyword_id == keyword_id,
                AutocompleteSuggestion.suggestion_text == normalized_text,
                AutocompleteSuggestion.run_id == run_id,
            )
            .one_or_none()
        )
        if row is None:
            return None
    db.refresh(row)
    return row


def write_cluster_assignment(
    *,
    keyword_id: int,
    niche_id: str,
    cluster_id: int,
    run_id: str,
    db: Any,
    algorithm: str = "kmeans",
    commit: bool = True,
) -> ClusterAssignment | None:
    """Upsert a cluster assignment keyed by keyword/run."""
    if not isinstance(db, Session):
        return None

    row = (
        db.query(ClusterAssignment)
        .filter(
            ClusterAssignment.keyword_id == keyword_id,
            ClusterAssignment.run_id == run_id,
        )
        .one_or_none()
    )
    if row is None:
        row = ClusterAssignment(
            keyword_id=keyword_id,
            niche_id=niche_id,
            cluster_id=cluster_id,
            run_id=run_id,
            algorithm=algorithm,
        )
    else:
        row.niche_id = niche_id
        row.cluster_id = cluster_id
        row.algorithm = algorithm

    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    return row


def write_cluster_label(
    *,
    niche_id: str,
    cluster_id: int,
    run_id: str,
    db: Any,
    label_text: str | None = None,
    opportunity_narrative: str | None = None,
    keyword_count: int = 0,
    commit: bool = True,
) -> ClusterLabel | None:
    """Upsert a cluster label keyed by niche/cluster/run."""
    if not isinstance(db, Session):
        return None

    row = (
        db.query(ClusterLabel)
        .filter(
            ClusterLabel.niche_id == niche_id,
            ClusterLabel.cluster_id == cluster_id,
            ClusterLabel.run_id == run_id,
        )
        .one_or_none()
    )
    if row is None:
        row = ClusterLabel(
            niche_id=niche_id,
            cluster_id=cluster_id,
            run_id=run_id,
            label_text=label_text,
            opportunity_narrative=opportunity_narrative,
            keyword_count=keyword_count,
        )
    else:
        row.label_text = label_text
        row.opportunity_narrative = opportunity_narrative
        row.keyword_count = keyword_count

    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    return row


def write_competitor_profile(
    *,
    niche_id: str,
    run_id: str,
    db: Any,
    top_gig_count: int = 0,
    median_price: float | None = None,
    mean_price: float | None = None,
    price_std: float | None = None,
    median_rating: float | None = None,
    mean_reviews: float | None = None,
    seller_level_distribution: dict[str, float] | None = None,
    min_delivery_days: int | None = None,
    max_delivery_days: int | None = None,
    video_present_rate: float | None = None,
    portfolio_present_rate: float | None = None,
    new_seller_gap: dict[str, Any] | None = None,
    commit: bool = True,
) -> CompetitorProfile | None:
    """Upsert a competitor benchmark profile keyed by niche/run."""
    if not isinstance(db, Session):
        return None

    row = (
        db.query(CompetitorProfile)
        .filter(
            CompetitorProfile.niche_id == niche_id,
            CompetitorProfile.run_id == run_id,
        )
        .one_or_none()
    )
    if row is None:
        row = CompetitorProfile(
            niche_id=niche_id,
            run_id=run_id,
        )

    row.top_gig_count = int(top_gig_count)
    row.median_price = median_price
    row.mean_price = mean_price
    row.price_std = price_std
    row.median_rating = median_rating
    row.mean_reviews = mean_reviews
    row.seller_level_distribution = dict(seller_level_distribution or {"UNKNOWN": 1.0})
    row.min_delivery_days = min_delivery_days
    row.max_delivery_days = max_delivery_days
    row.video_present_rate = video_present_rate
    row.portfolio_present_rate = portfolio_present_rate
    row.new_seller_gap = dict(new_seller_gap or {})

    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    return row


def write_gig_quality_analysis(
    *,
    gig_url: str,
    niche_id: str,
    run_id: str,
    db: Any,
    rubric_score: float,
    video_absent: bool,
    portfolio_absent: bool,
    description_thin: bool,
    faq_absent: bool,
    thumbnail_quality_flag: bool,
    weakness_flags: list[str] | None = None,
    commit: bool = True,
) -> GigQualityAnalysis | None:
    """Upsert Stage 11 gig quality analysis by gig/run key."""
    if not isinstance(db, Session):
        return None

    row = (
        db.query(GigQualityAnalysis)
        .filter(
            GigQualityAnalysis.gig_url == gig_url,
            GigQualityAnalysis.run_id == run_id,
        )
        .one_or_none()
    )
    if row is None:
        row = GigQualityAnalysis(gig_url=gig_url, run_id=run_id)

    row.niche_id = niche_id
    row.rubric_score = float(rubric_score)
    row.video_absent = bool(video_absent)
    row.portfolio_absent = bool(portfolio_absent)
    row.description_thin = bool(description_thin)
    row.faq_absent = bool(faq_absent)
    row.thumbnail_quality_flag = bool(thumbnail_quality_flag)
    row.weakness_flags = sorted(set(str(flag) for flag in (weakness_flags or [])))

    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    return row


def write_review_analysis(
    *,
    gig_url: str,
    niche_id: str,
    run_id: str,
    db: Any,
    review_count: int,
    avg_rating: float | None,
    review_velocity: float,
    sentiment_score: float | None,
    recurring_complaints: list[str] | None = None,
    commit: bool = True,
) -> ReviewAnalysis | None:
    """Upsert Stage 12 review analysis by gig/run key."""
    if not isinstance(db, Session):
        return None

    row = (
        db.query(ReviewAnalysis)
        .filter(
            ReviewAnalysis.gig_url == gig_url,
            ReviewAnalysis.run_id == run_id,
        )
        .one_or_none()
    )
    if row is None:
        row = ReviewAnalysis(gig_url=gig_url, run_id=run_id)

    row.niche_id = niche_id
    row.review_count = max(0, int(review_count))
    row.avg_rating = avg_rating
    row.review_velocity = max(0.0, float(review_velocity))
    row.sentiment_score = sentiment_score
    row.recurring_complaints = sorted(set(str(item) for item in (recurring_complaints or [])))

    db.add(row)
    if commit:
        db.commit()
        db.refresh(row)
    return row


