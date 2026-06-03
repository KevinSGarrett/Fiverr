"""Unit tests for R7 External Signal Integrity."""

from __future__ import annotations

import math
from collections.abc import Generator
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.analysis.external_signals import (
    _apply_youtube_confidence_gate,
    _classify_autocomplete_absence,
    _compute_fiverr_relevance_qualifier,
    _qualify_reddit_score,
    compute_signal_freshness_quality,
    estimate_buyer_intent_ratio,
)
from src.config.models import ExternalSignalsConfig
from src.models.base import Base
from src.models.external_signal import ExternalSignal, write_external_signal


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def test_external_signal_raw_value_column_nullable(db_session: Session) -> None:
    row = ExternalSignal(keyword_id=1, signal_type="google_trends")
    db_session.add(row)
    db_session.commit()
    assert row.raw_value is None


def test_external_signal_raw_value_stored_and_retrieved(db_session: Session) -> None:
    row = ExternalSignal(keyword_id=1, signal_type="google_trends", raw_value=0.75)
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    reloaded = db_session.query(ExternalSignal).filter_by(id=row.id).first()
    assert reloaded is not None
    assert reloaded.raw_value == 0.75


def test_external_signal_raw_value_zero_stored(db_session: Session) -> None:
    row = ExternalSignal(keyword_id=1, signal_type="google_trends", raw_value=0.0)
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    assert row.raw_value == 0.0


def test_external_signal_relevance_score_defaults_none(db_session: Session) -> None:
    row = ExternalSignal(keyword_id=1, signal_type="reddit_demand")
    db_session.add(row)
    db_session.commit()
    assert row.relevance_score is None


@pytest.mark.parametrize("score", [0.0, 0.5, 1.0])
def test_external_signal_relevance_score_full_range(db_session: Session, score: float) -> None:
    row = ExternalSignal(keyword_id=1, signal_type="reddit_demand", relevance_score=score)
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    assert row.relevance_score == score


def test_external_signal_trend_direction_rising(db_session: Session) -> None:
    row = ExternalSignal(keyword_id=1, signal_type="google_trends", trend_direction="RISING")
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    assert row.trend_direction == "RISING"


def test_external_signal_trend_direction_stable(db_session: Session) -> None:
    row = ExternalSignal(keyword_id=1, signal_type="google_trends", trend_direction="STABLE")
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    assert row.trend_direction == "STABLE"


def test_external_signal_trend_direction_falling(db_session: Session) -> None:
    row = ExternalSignal(keyword_id=1, signal_type="google_trends", trend_direction="FALLING")
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    assert row.trend_direction == "FALLING"


def test_external_signal_trend_direction_unknown(db_session: Session) -> None:
    row = ExternalSignal(keyword_id=1, signal_type="google_trends", trend_direction="UNKNOWN")
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    assert row.trend_direction == "UNKNOWN"


def test_external_signal_trend_direction_none(db_session: Session) -> None:
    row = ExternalSignal(keyword_id=1, signal_type="google_trends")
    db_session.add(row)
    db_session.commit()
    assert row.trend_direction is None


def test_external_signal_write_helper_accepts_tc1_fields(db_session: Session) -> None:
    row = write_external_signal(
        keyword_id=1,
        signal_type="google_trends",
        signal_value=0.6,
        signal_json=None,
        run_id="run_001",
        collection_method="api",
        db=db_session,
        raw_value=0.8,
        relevance_score=0.9,
        trend_direction="RISING",
    )
    assert row is not None
    assert row.raw_value == 0.8
    assert row.relevance_score == 0.9
    assert row.trend_direction == "RISING"


def test_external_signal_backward_compat_aliases_unchanged(db_session: Session) -> None:
    row = ExternalSignal(
        keyword_id=1,
        signal_type="test",
        signal_value=0.5,
        signal_json={"key": "val"},
        collection_method="test",
    )
    db_session.add(row)
    db_session.commit()
    assert row.normalized_value == 0.5
    assert row.raw_value_json == {"key": "val"}
    assert row.source_name == "test"


def test_autocomplete_emerging_keyword_gets_neutral_not_zero_score() -> None:
    """REG-28: emerging autocomplete -> 50, not 0."""
    result = _classify_autocomplete_absence(
        "python agent",
        "python_automation",
        {"status": "emerging"},
    )
    assert result == 50, f"Expected 50 for emerging, got {result}"


def test_reddit_qualified_score_lower_than_raw_when_buyer_intent_low() -> None:
    """REG-29: qualified < raw when buyer_intent_ratio < 1.0."""
    cfg = ExternalSignalsConfig()
    raw = 75.0
    result = _qualify_reddit_score(raw, buyer_intent_ratio=0.20, config=cfg)
    assert result < raw, f"Expected qualified ({result}) < raw ({raw})"
    expected = raw * (0.40 + 0.60 * 0.20)
    assert abs(result - expected) < 0.01


def test_trends_platform_qualifier_applied_before_demand_score_calculation() -> None:
    """REG-30: trends qualifier clamped [0.20, 0.95] and applied pre-demand."""
    cfg = ExternalSignalsConfig()
    qualifier = _compute_fiverr_relevance_qualifier(
        0.7,
        True,
        "STRONGLY_RISING",
        "n8n workflow",
        cfg,
    )
    assert 0.20 <= qualifier <= 0.95, f"Qualifier {qualifier} out of clamp range"
    assert qualifier > cfg.trends_base_qualifier


def test_trends_qualifier_single_word_breadth_penalty() -> None:
    cfg = ExternalSignalsConfig()
    single_word = _compute_fiverr_relevance_qualifier(0.7, True, "FLAT", "python", cfg)
    phrase = _compute_fiverr_relevance_qualifier(0.7, True, "FLAT", "python automation", cfg)
    assert single_word < phrase, "Single-word should get breadth penalty"


def test_reddit_qualified_equals_raw_at_full_intent() -> None:
    cfg = ExternalSignalsConfig()
    result = _qualify_reddit_score(80.0, buyer_intent_ratio=1.0, config=cfg)
    assert abs(result - 80.0) < 0.01, "At full intent, qualified == raw"


def test_youtube_confidence_deduction_below_threshold() -> None:
    cfg = ExternalSignalsConfig()
    result = _apply_youtube_confidence_gate(0.80, youtube_video_count=5, config=cfg)
    assert result < 0.80, "< 10 videos should reduce confidence"


def test_youtube_confidence_boost_above_threshold() -> None:
    cfg = ExternalSignalsConfig()
    result = _apply_youtube_confidence_gate(0.80, youtube_video_count=600, config=cfg)
    assert result > 0.80, ">= 500 videos should boost confidence"


def test_freshness_relevance_low_when_irrelevant() -> None:
    quality = compute_signal_freshness_quality(signal_age_days=5, relevance_score=0.10)
    assert quality < 0.40, f"Fresh+irrelevant should be low, got {quality}"


def test_freshness_relevance_high_when_fresh_and_relevant() -> None:
    quality = compute_signal_freshness_quality(signal_age_days=5, relevance_score=0.90)
    assert quality >= 0.85, f"Fresh+relevant should be high, got {quality}"


def test_autocomplete_absent_returns_zero() -> None:
    result = _classify_autocomplete_absence(
        "generic",
        "python_automation",
        {"status": "not_searched"},
    )
    assert result == 0


def test_youtube_mid_range_no_adjustment() -> None:
    cfg = ExternalSignalsConfig()
    result = _apply_youtube_confidence_gate(0.75, youtube_video_count=250, config=cfg)
    assert result == 0.75


def test_youtube_boundary_exactly_10_no_deduction() -> None:
    cfg = ExternalSignalsConfig()
    result = _apply_youtube_confidence_gate(0.75, youtube_video_count=10, config=cfg)
    assert result == 0.75


def test_youtube_boundary_exactly_9_deducts() -> None:
    cfg = ExternalSignalsConfig()
    result = _apply_youtube_confidence_gate(0.75, youtube_video_count=9, config=cfg)
    assert result < 0.75


def test_youtube_boundary_exactly_499_no_boost() -> None:
    cfg = ExternalSignalsConfig()
    result = _apply_youtube_confidence_gate(0.75, youtube_video_count=499, config=cfg)
    assert result == 0.75


def test_youtube_boundary_exactly_500_boosts() -> None:
    cfg = ExternalSignalsConfig()
    result = _apply_youtube_confidence_gate(0.75, youtube_video_count=500, config=cfg)
    assert result > 0.75


def test_trends_qualifier_clamps_at_minimum() -> None:
    cfg = ExternalSignalsConfig()
    result = _compute_fiverr_relevance_qualifier(0.0, False, "DECLINING", "ai", cfg)
    assert result == cfg.trends_clamp_low


def test_trends_qualifier_clamps_at_maximum_with_custom_base() -> None:
    cfg = ExternalSignalsConfig(trends_base_qualifier=0.95)
    result = _compute_fiverr_relevance_qualifier(1.0, True, "STRONGLY_RISING", "n8n workflow", cfg)
    assert result == cfg.trends_clamp_high


def test_trends_rising_direction_applies_partial_boost() -> None:
    cfg = ExternalSignalsConfig()
    rising = _compute_fiverr_relevance_qualifier(0.9, True, "RISING", "python automation", cfg)
    flat = _compute_fiverr_relevance_qualifier(0.9, True, "FLAT", "python automation", cfg)
    assert rising > flat


def test_reddit_qualified_at_zero_intent() -> None:
    cfg = ExternalSignalsConfig()
    result = _qualify_reddit_score(100.0, buyer_intent_ratio=0.0, config=cfg)
    assert abs(result - 40.0) < 0.01


def test_reddit_qualified_zero_raw_stays_zero() -> None:
    cfg = ExternalSignalsConfig()
    result = _qualify_reddit_score(0.0, buyer_intent_ratio=0.5, config=cfg)
    assert result == 0.0


def test_freshness_quality_zero_age_matches_sqrt_relevance() -> None:
    relevance = 0.80
    quality = compute_signal_freshness_quality(signal_age_days=0, relevance_score=relevance)
    assert abs(quality - math.sqrt(relevance)) < 0.01


def test_freshness_quality_expired_signal_zero() -> None:
    quality = compute_signal_freshness_quality(signal_age_days=200, relevance_score=0.80, max_age_days=90)
    assert quality == 0.0


def test_freshness_quality_zero_when_max_age_non_positive() -> None:
    quality = compute_signal_freshness_quality(signal_age_days=5, relevance_score=0.80, max_age_days=0)
    assert quality == 0.0


def test_autocomplete_returns_unknown_on_none_data() -> None:
    result = _classify_autocomplete_absence("keyword", "python_automation", None)
    assert result == 20


def test_autocomplete_returns_unknown_on_unrecognized_status() -> None:
    result = _classify_autocomplete_absence(
        "keyword",
        "python_automation",
        {"status": "insufficient_data"},
    )
    assert result == 20


def test_estimate_buyer_intent_ratio_uses_explicit_ratio() -> None:
    ratio = estimate_buyer_intent_ratio({"buyer_intent_ratio": 0.25})
    assert abs(ratio - 0.25) < 0.001


def test_estimate_buyer_intent_ratio_from_posts_phrases() -> None:
    ratio = estimate_buyer_intent_ratio(
        {
            "posts": [
                {"title": "Need help building an automation", "body": "budget approved"},
                {"title": "Showcase only", "body": "no buyer intent here"},
            ]
        }
    )
    assert 0.4 < ratio < 0.6


def test_estimate_buyer_intent_ratio_non_mapping_defaults_zero() -> None:
    assert estimate_buyer_intent_ratio(None) == 0.0


def test_estimate_buyer_intent_ratio_empty_posts_defaults_zero() -> None:
    assert estimate_buyer_intent_ratio({"posts": []}) == 0.0


def test_estimate_buyer_intent_ratio_non_mapping_entries_defaults_zero() -> None:
    ratio = estimate_buyer_intent_ratio({"posts": ["not-a-dict", 123]})
    assert ratio == 0.0
