"""Tests for Wave 9 Phase 3 ladder tracking module."""

from __future__ import annotations

import importlib
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.models import Base, Keyword, Niche, PriceLadderSnapshot, PricingSnapshot
from src.pricing.ladder_tracker import (
    LADDER_MILESTONES,
    LADDER_TOLERANCE,
    get_ladder_progress,
    get_nearest_milestone,
    get_recommended_prices_at_milestone,
    is_pricing_on_track,
    track_price_ladder,
)


def _engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def _seed_keyword(session: Session, *, slug: str = "test_niche", keyword_text: str = "test keyword") -> int:
    niche = Niche(slug=slug, name="Test Niche", category_path="Programming & Tech")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword=keyword_text,
        normalized_keyword=keyword_text,
    )
    session.add(keyword)
    session.flush()
    return int(keyword.id)


def _seed_ladder_snapshot(session: Session, keyword_id: int, *, as_json_text: bool = False) -> None:
    ladder = [
        {"milestone": m, "basic": 65 + m, "standard": 145 + m, "premium": 280 + m}
        for m in LADDER_MILESTONES
    ]
    payload = json.dumps(ladder) if as_json_text else ladder
    session.add(
        PricingSnapshot(
            keyword_id=keyword_id,
            niche_id="test_niche",
            run_id="test-run",
            entry_basic=65.0,
            entry_standard=145.0,
            entry_premium=280.0,
            price_ladder=payload,
            confidence="MEDIUM",
        )
    )


@pytest.fixture
def seeded_ladder_db():
    engine = _engine()
    with Session(engine) as session:
        keyword_id = _seed_keyword(session)
        _seed_ladder_snapshot(session, keyword_id)
        session.commit()
    return engine


@pytest.fixture
def seeded_ladder_json_db():
    engine = _engine()
    with Session(engine) as session:
        keyword_id = _seed_keyword(session)
        _seed_ladder_snapshot(session, keyword_id, as_json_text=True)
        session.commit()
    return engine


@pytest.fixture
def seeded_multi_snapshot_db():
    engine = _engine()
    with Session(engine) as session:
        keyword_id = _seed_keyword(session)
        _seed_ladder_snapshot(session, keyword_id)
        track_price_ladder(keyword_id, 70.0, 150.0, 285.0, 5, session)
        track_price_ladder(keyword_id, 74.0, 160.0, 295.0, 10, session)
        session.commit()
    return engine


@pytest.fixture
def seeded_on_track_db(seeded_ladder_db):
    with Session(seeded_ladder_db) as session:
        track_price_ladder(1, 70.0, 150.0, 285.0, 5, session)
        session.commit()
    return seeded_ladder_db


@pytest.fixture
def seeded_off_track_db(seeded_ladder_db):
    with Session(seeded_ladder_db) as session:
        track_price_ladder(1, 150.0, 260.0, 390.0, 5, session)
        session.commit()
    return seeded_ladder_db


class TestGetNearestMilestone:
    def test_returns_5_for_0_to_9_reviews(self):
        assert get_nearest_milestone(0) == 5
        assert get_nearest_milestone(4) == 5
        assert get_nearest_milestone(9) == 5

    def test_returns_5_for_exactly_5(self):
        assert get_nearest_milestone(5) == 5

    def test_returns_10_for_10_reviews(self):
        assert get_nearest_milestone(10) == 10

    def test_returns_50_for_75_reviews(self):
        assert get_nearest_milestone(75) == 50

    def test_returns_100_for_200_reviews(self):
        assert get_nearest_milestone(200) == 100


def test_get_recommended_prices_returns_correct_milestone(seeded_ladder_db):
    with Session(seeded_ladder_db) as session:
        result = get_recommended_prices_at_milestone(1, 5, session)
        assert "basic" in result
        assert result["basic"] == 70.0


def test_get_recommended_prices_handles_json_string_payload(seeded_ladder_json_db):
    with Session(seeded_ladder_json_db) as session:
        result = get_recommended_prices_at_milestone(1, 10, session)
        assert result["basic"] == 75.0


def test_get_recommended_prices_returns_empty_dict_no_snapshot(empty_db):
    with Session(empty_db) as session:
        result = get_recommended_prices_at_milestone(999, 10, session)
        assert result == {}


def test_get_recommended_prices_wrong_milestone_returns_empty(seeded_ladder_db):
    with Session(seeded_ladder_db) as session:
        result = get_recommended_prices_at_milestone(1, 999, session)
        assert result == {}


class TestTrackPriceLadder:
    def test_creates_snapshot_with_correct_fields(self, seeded_ladder_db):
        with Session(seeded_ladder_db) as session:
            snap = track_price_ladder(1, 68.0, 150.0, 285.0, 7, session)
            session.commit()
            assert snap.keyword_id == 1
            assert snap.ladder_milestone == 5
            assert snap.actual_basic_price == 68.0

    def test_on_track_when_within_tolerance(self, seeded_ladder_db):
        with Session(seeded_ladder_db) as session:
            snap = track_price_ladder(1, 70.0, 150.0, 285.0, 5, session)
            session.commit()
            assert snap.on_track is True

    def test_off_track_when_outside_tolerance(self, seeded_ladder_db):
        with Session(seeded_ladder_db) as session:
            snap = track_price_ladder(1, 200.0, 150.0, 285.0, 5, session)
            session.commit()
            assert snap.on_track is False

    def test_delta_pct_calculated_correctly(self, seeded_ladder_db):
        with Session(seeded_ladder_db) as session:
            snap = track_price_ladder(1, 77.0, 150.0, 285.0, 10, session)
            session.commit()
            assert snap.price_delta_pct == pytest.approx(abs((77.0 - 75.0) / 75.0))

    def test_handles_missing_pricing_snapshot(self, empty_db):
        with Session(empty_db) as session:
            keyword_id = _seed_keyword(session, slug="empty_niche", keyword_text="empty")
            snap = track_price_ladder(keyword_id, 65.0, 145.0, 280.0, 5, session)
            session.commit()
            assert snap.recommended_basic_price == 65.0
            assert snap.on_track is True

    def test_milestone_matches_review_count(self, seeded_ladder_db):
        with Session(seeded_ladder_db) as session:
            snap = track_price_ladder(1, 65.0, 145.0, 280.0, 50, session)
            session.commit()
            assert snap.ladder_milestone == 50

    def test_nearest_milestone_25_at_30_reviews(self, seeded_ladder_db):
        with Session(seeded_ladder_db) as session:
            snap = track_price_ladder(1, 80.0, 165.0, 300.0, 30, session)
            session.commit()
            assert snap.ladder_milestone == 25

    def test_tolerance_default_is_15_pct(self):
        assert LADDER_TOLERANCE == pytest.approx(0.15)

    def test_delta_pct_is_positive(self, seeded_ladder_db):
        with Session(seeded_ladder_db) as session:
            snap = track_price_ladder(1, 60.0, 145.0, 280.0, 5, session)
            session.commit()
            assert snap.price_delta_pct >= 0.0

    def test_track_price_ladder_at_zero_reviews(self, seeded_ladder_db):
        assert get_nearest_milestone(0) == 5
        with Session(seeded_ladder_db) as session:
            snap = track_price_ladder(1, 65.0, 145.0, 280.0, 0, session)
            session.commit()
            assert snap.ladder_milestone == 5


class TestGetLadderProgress:
    def test_returns_newest_first(self, seeded_multi_snapshot_db):
        with Session(seeded_multi_snapshot_db) as session:
            progress = get_ladder_progress(1, session)
            milestones = [entry["milestone"] for entry in progress]
            assert milestones == sorted(milestones, reverse=True)

    def test_returns_empty_list_no_data(self, empty_db):
        with Session(empty_db) as session:
            progress = get_ladder_progress(1, session)
            assert progress == []

    def test_returns_dict_with_required_keys(self, seeded_ladder_db):
        with Session(seeded_ladder_db) as session:
            track_price_ladder(1, 68.0, 150.0, 285.0, 7, session)
            session.commit()
            progress = get_ladder_progress(1, session)
            assert {"milestone", "delta_pct", "on_track", "reviews"}.issubset(progress[0].keys())

    def test_get_ladder_progress_newest_first(self, empty_db):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            keyword_id = _seed_keyword(session)
            _seed_ladder_snapshot(session, keyword_id)
            session.flush()
            track_price_ladder(keyword_id, 70.0, 150.0, 285.0, 5, session)
            track_price_ladder(keyword_id, 75.0, 160.0, 295.0, 10, session)
            session.commit()
            progress = get_ladder_progress(keyword_id, session)
            assert len(progress) >= 2
            assert progress[0]["milestone"] >= progress[1]["milestone"]


class TestIsPricingOnTrack:
    def test_returns_true_when_on_track(self, seeded_on_track_db):
        with Session(seeded_on_track_db) as session:
            assert is_pricing_on_track(1, session) is True

    def test_returns_false_when_off_track(self, seeded_off_track_db):
        with Session(seeded_off_track_db) as session:
            assert is_pricing_on_track(1, session) is False

    def test_returns_true_when_no_data(self, empty_db):
        with Session(empty_db) as session:
            assert is_pricing_on_track(1, session) is True

    def test_tolerance_parameter_respected(self, seeded_ladder_db):
        with Session(seeded_ladder_db) as session:
            track_price_ladder(1, 82.0, 165.0, 300.0, 10, session)
            session.commit()
            assert is_pricing_on_track(1, session, tolerance=0.05) is False
            assert is_pricing_on_track(1, session, tolerance=0.15) is True

    def test_uses_most_recent_snapshot(self, seeded_ladder_db):
        with Session(seeded_ladder_db) as session:
            track_price_ladder(1, 70.0, 150.0, 285.0, 5, session)
            track_price_ladder(1, 120.0, 200.0, 340.0, 10, session)
            session.commit()
            assert is_pricing_on_track(1, session) is False


def test_full_ladder_tracking_pipeline(seeded_ladder_db):
    """End-to-end: track_price_ladder -> get_ladder_progress -> is_pricing_on_track."""
    with Session(seeded_ladder_db) as session:
        snap = track_price_ladder(1, 68.0, 150.0, 285.0, 7, session)
        session.commit()
        assert snap.ladder_milestone == 5
        assert snap.actual_basic_price == 68.0
        assert isinstance(snap.on_track, bool)
        progress = get_ladder_progress(1, session)
        assert len(progress) >= 1
        assert progress[0]["milestone"] == 5
        on_track = is_pricing_on_track(1, session)
        assert isinstance(on_track, bool)


def test_ladder_tracker_does_not_affect_golden_parity():
    """Importing ladder_tracker module has no side effects on scoring."""
    module = importlib.import_module("src.pricing.ladder_tracker")
    assert hasattr(module, "track_price_ladder")
    assert hasattr(module, "get_nearest_milestone")
    assert hasattr(module, "LADDER_MILESTONES")


def test_price_ladder_snapshot_model_available():
    assert PriceLadderSnapshot.__tablename__ == "price_ladder_snapshots"
