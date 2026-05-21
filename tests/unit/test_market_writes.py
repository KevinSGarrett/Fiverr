"""Unit tests for market upsert helper edge paths."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from src.models.database import create_session_factory, initialize_database
from src.models.market import (
    CompetitorProfile,
    GigQualityAnalysis,
    Keyword,
    ReviewAnalysis,
    SaturationScore,
    write_autocomplete_suggestion,
    write_cluster_assignment,
    write_cluster_label,
    write_competitor_profile,
    write_gig_quality_analysis,
    write_review_analysis,
    write_saturation_score,
)
from src.models.niche import Niche


def _build_session() -> tuple[Any, Niche, Keyword]:
    engine = initialize_database("sqlite:///:memory:")
    session_factory = create_session_factory(engine)
    session = session_factory()

    niche = Niche(slug="market-test", name="Market Test", category_path="programming-tech/testing")
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automation",
        normalized_keyword="python automation",
        external_source="seed",
        metadata_json={},
    )
    session.add(keyword)
    session.commit()
    session.refresh(niche)
    session.refresh(keyword)
    return session, niche, keyword


def test_write_helpers_return_none_when_db_is_not_session() -> None:
    assert write_autocomplete_suggestion(
        keyword_id=1,
        niche_id="niche",
        suggestion_text="value",
        position=1,
        run_id="run-1",
        db=object(),
    ) is None
    assert write_cluster_assignment(
        keyword_id=1,
        niche_id="niche",
        cluster_id=0,
        run_id="run-1",
        db=object(),
    ) is None
    assert write_cluster_label(
        niche_id="niche",
        cluster_id=0,
        run_id="run-1",
        db=object(),
    ) is None
    assert write_competitor_profile(
        niche_id="niche",
        run_id="run-1",
        db=object(),
    ) is None
    assert write_gig_quality_analysis(
        gig_url="https://example.com/gig/1",
        niche_id="niche",
        run_id="run-1",
        db=object(),
        rubric_score=80.0,
        video_absent=False,
        portfolio_absent=False,
        description_thin=False,
        faq_absent=False,
        thumbnail_quality_flag=False,
    ) is None
    assert write_review_analysis(
        gig_url="https://example.com/gig/1",
        niche_id="niche",
        run_id="run-1",
        db=object(),
        review_count=10,
        avg_rating=4.5,
        review_velocity=0.2,
        sentiment_score=9.0,
    ) is None
    assert write_saturation_score(
        keyword_id=1,
        niche_id="niche",
        run_id="run-1",
        saturation_score=50.0,
        count_score=10.0,
        title_dup_score=20.0,
        price_score=30.0,
        overlap_score=40.0,
        llm_class_score=50.0,
        title_duplication_rate=0.2,
        price_compression_rate=0.3,
        seller_overlap_rate=0.4,
        explanation_text="none",
        db=object(),
    ) is None


def test_write_autocomplete_suggestion_upserts_and_handles_integrity_retry(
    monkeypatch,
) -> None:
    session, _niche, keyword = _build_session()
    try:
        created = write_autocomplete_suggestion(
            keyword_id=keyword.id,
            niche_id="market-test",
            suggestion_text=" python automation ",
            position=1,
            run_id="run-autocomplete",
            db=session,
        )
        assert created is not None
        assert created.suggestion_text == "python automation"

        updated = write_autocomplete_suggestion(
            keyword_id=keyword.id,
            niche_id="market-test",
            suggestion_text="python automation",
            position=3,
            run_id="run-autocomplete",
            db=session,
            source="fiverr-autocomplete-v2",
        )
        assert updated is not None
        assert updated.id == created.id
        assert updated.position == 3

        original_commit = session.commit

        def _raise_once() -> None:
            monkeypatch.setattr(session, "commit", original_commit)
            raise IntegrityError("INSERT", {}, Exception("unique_violation"))

        monkeypatch.setattr(session, "commit", _raise_once)
        fallback = write_autocomplete_suggestion(
            keyword_id=keyword.id,
            niche_id="market-test",
            suggestion_text="python automation",
            position=5,
            run_id="run-autocomplete",
            db=session,
        )
        assert fallback is not None
        assert fallback.id == created.id
    finally:
        session.close()


def test_write_cluster_assignment_and_label_update_existing_rows() -> None:
    session, _niche, keyword = _build_session()
    try:
        assignment = write_cluster_assignment(
            keyword_id=keyword.id,
            niche_id="market-test",
            cluster_id=1,
            run_id="run-cluster",
            db=session,
            algorithm="kmeans",
        )
        assert assignment is not None

        assignment_update = write_cluster_assignment(
            keyword_id=keyword.id,
            niche_id="market-test",
            cluster_id=2,
            run_id="run-cluster",
            db=session,
            algorithm="dbscan",
        )
        assert assignment_update is not None
        assert assignment_update.id == assignment.id
        assert assignment_update.cluster_id == 2
        assert assignment_update.algorithm == "dbscan"

        label = write_cluster_label(
            niche_id="market-test",
            cluster_id=2,
            run_id="run-cluster",
            db=session,
            label_text="Initial Label",
            opportunity_narrative="Initial narrative",
            keyword_count=1,
        )
        assert label is not None

        label_update = write_cluster_label(
            niche_id="market-test",
            cluster_id=2,
            run_id="run-cluster",
            db=session,
            label_text="Updated Label",
            opportunity_narrative="Updated narrative",
            keyword_count=3,
        )
        assert label_update is not None
        assert label_update.id == label.id
        assert label_update.keyword_count == 3
    finally:
        session.close()


def test_write_profile_quality_and_review_analysis_upsert_paths() -> None:
    session, _niche, _keyword = _build_session()
    try:
        profile = write_competitor_profile(
            niche_id="market-test",
            run_id="run-analysis",
            db=session,
            top_gig_count=2,
            median_price=50.0,
            mean_price=60.0,
            price_std=10.0,
            median_rating=4.8,
            mean_reviews=120.0,
            seller_level_distribution={"LEVEL_2": 0.5, "TOP_RATED": 0.5},
            min_delivery_days=2,
            max_delivery_days=6,
            video_present_rate=0.5,
            portfolio_present_rate=0.6,
        )
        assert profile is not None

        profile_update = write_competitor_profile(
            niche_id="market-test",
            run_id="run-analysis",
            db=session,
            top_gig_count=4,
            seller_level_distribution={"UNKNOWN": 1.0},
        )
        assert profile_update is not None
        assert profile_update.id == profile.id
        assert profile_update.top_gig_count == 4

        quality = write_gig_quality_analysis(
            gig_url="https://example.com/gig/qa-1",
            niche_id="market-test",
            run_id="run-analysis",
            db=session,
            rubric_score=88.0,
            video_absent=False,
            portfolio_absent=False,
            description_thin=False,
            faq_absent=False,
            thumbnail_quality_flag=False,
            weakness_flags=["faq_absent", "faq_absent"],
        )
        assert quality is not None
        assert quality.weakness_flags == ["faq_absent"]

        quality_update = write_gig_quality_analysis(
            gig_url="https://example.com/gig/qa-1",
            niche_id="market-test",
            run_id="run-analysis",
            db=session,
            rubric_score=44.0,
            video_absent=True,
            portfolio_absent=True,
            description_thin=True,
            faq_absent=True,
            thumbnail_quality_flag=True,
            weakness_flags=["video_absent", "portfolio_absent"],
        )
        assert quality_update is not None
        assert quality_update.id == quality.id
        assert quality_update.video_absent is True

        review = write_review_analysis(
            gig_url="https://example.com/gig/ra-1",
            niche_id="market-test",
            run_id="run-analysis",
            db=session,
            review_count=12,
            avg_rating=4.5,
            review_velocity=0.3,
            sentiment_score=9.0,
            recurring_complaints=["late_delivery", "late_delivery"],
        )
        assert review is not None
        assert review.recurring_complaints == ["late_delivery"]

        review_update = write_review_analysis(
            gig_url="https://example.com/gig/ra-1",
            niche_id="market-test",
            run_id="run-analysis",
            db=session,
            review_count=-3,
            avg_rating=3.0,
            review_velocity=-1.2,
            sentiment_score=6.0,
            recurring_complaints=["quality_mismatch", "revision_dispute"],
        )
        assert review_update is not None
        assert review_update.id == review.id
        assert review_update.review_count == 0
        assert review_update.review_velocity == 0.0

        assert len(session.scalars(select(CompetitorProfile)).all()) == 1
        assert len(session.scalars(select(GigQualityAnalysis)).all()) == 1
        assert len(session.scalars(select(ReviewAnalysis)).all()) == 1
    finally:
        session.close()


def test_write_saturation_score_upserts_and_supports_commit_false() -> None:
    session, niche, keyword = _build_session()
    try:
        created = write_saturation_score(
            keyword_id=keyword.id,
            niche_id=niche.slug,
            run_id="run-saturation",
            saturation_score=66.0,
            count_score=50.0,
            title_dup_score=60.0,
            price_score=40.0,
            overlap_score=30.0,
            llm_class_score=55.0,
            title_duplication_rate=0.4,
            price_compression_rate=0.25,
            seller_overlap_rate=0.2,
            explanation_text="initial",
            db=session,
            commit=False,
        )
        assert created is not None
        session.commit()
        session.refresh(created)

        updated = write_saturation_score(
            keyword_id=keyword.id,
            niche_id=niche.slug,
            run_id="run-saturation",
            saturation_score=72.5,
            count_score=52.0,
            title_dup_score=62.0,
            price_score=42.0,
            overlap_score=32.0,
            llm_class_score=58.0,
            title_duplication_rate=0.45,
            price_compression_rate=0.3,
            seller_overlap_rate=0.25,
            explanation_text="updated",
            db=session,
            commit=True,
        )
        assert updated is not None
        assert updated.id == created.id
        assert updated.saturation_score == 72.5
        rows = session.scalars(select(SaturationScore)).all()
        assert len(rows) == 1
    finally:
        session.close()
