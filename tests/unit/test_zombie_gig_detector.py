from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from src.analysis.zombie_gig_detector import compute_zombie_score, is_zombie_gig


def _gig(**kwargs):
    return SimpleNamespace(**kwargs)


def _seller(**kwargs):
    return SimpleNamespace(**kwargs)


def test_zombie_score_low_reviews_new_account() -> None:
    ref = datetime(2026, 1, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2025, 12, 1, tzinfo=UTC), response_rate=10)
    gig = _gig(review_count=2, orders_in_queue=0, last_reviewed_at=None)
    score, signals = compute_zombie_score(gig, seller, reference_date=ref)
    assert score == 0.0
    assert signals["new_seller"] is True
    assert is_zombie_gig(gig, seller, reference_date=ref) is False


def test_new_seller_guard_returns_zero_before_any_signal() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2026, 1, 15, tzinfo=UTC), response_rate=0)
    gig = _gig(review_count=0, orders_in_queue=0, last_reviewed_at=None)
    score, signals = compute_zombie_score(gig, seller, reference_date=ref)
    assert score == 0.0
    assert "low_review_count" not in signals


def test_signal_low_review_count_adds_0_30() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2020, 1, 1, tzinfo=UTC), response_rate=100)
    gig = _gig(review_count=3, orders_in_queue=5, last_reviewed_at=ref)
    score, signals = compute_zombie_score(gig, seller, reference_date=ref)
    assert score == 0.30
    assert signals["low_review_count"] == 3


def test_signal_never_reviewed_adds_0_20() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2020, 1, 1, tzinfo=UTC), response_rate=100)
    gig = _gig(review_count=50, orders_in_queue=1, last_reviewed_at=None)
    score, signals = compute_zombie_score(gig, seller, reference_date=ref)
    assert score == 0.20
    assert signals["never_reviewed"] is True


def test_signal_stale_reviews_over_365_days_adds_0_25() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2020, 1, 1, tzinfo=UTC), response_rate=100)
    gig = _gig(review_count=50, orders_in_queue=1, last_reviewed_at=ref - timedelta(days=366))
    score, signals = compute_zombie_score(gig, seller, reference_date=ref)
    assert score == 0.25
    assert signals["stale_reviews_days"] == 366


def test_signal_low_response_rate_adds_0_15() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2020, 1, 1, tzinfo=UTC), response_rate=29)
    gig = _gig(review_count=50, orders_in_queue=1, last_reviewed_at=ref)
    score, signals = compute_zombie_score(gig, seller, reference_date=ref)
    assert score == 0.15
    assert signals["low_response_rate"] == 29


def test_signal_no_queue_and_low_reviews_adds_0_10() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2020, 1, 1, tzinfo=UTC), response_rate=100)
    gig = _gig(review_count=3, orders_in_queue=0, last_reviewed_at=ref)
    score, signals = compute_zombie_score(gig, seller, reference_date=ref)
    assert score == 0.40
    assert signals["no_queue_low_reviews"] is True


def test_combined_signals_capped_at_1_0() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2020, 1, 1, tzinfo=UTC), response_rate=0)
    gig = _gig(review_count=0, orders_in_queue=0, last_reviewed_at=ref - timedelta(days=800))
    score, _ = compute_zombie_score(gig, seller, reference_date=ref)
    assert score <= 1.0


def test_is_zombie_true_at_threshold_050() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2020, 1, 1, tzinfo=UTC), response_rate=100)
    gig = _gig(review_count=9, orders_in_queue=1, last_reviewed_at=None)
    assert is_zombie_gig(gig, seller, reference_date=ref) is True


def test_is_zombie_false_below_threshold() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2020, 1, 1, tzinfo=UTC), response_rate=100)
    gig = _gig(review_count=50, orders_in_queue=1, last_reviewed_at=None)
    assert is_zombie_gig(gig, seller, reference_date=ref) is False


def test_missing_response_rate_does_not_fire_signal() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2020, 1, 1, tzinfo=UTC), response_rate=None)
    gig = _gig(review_count=50, orders_in_queue=1, last_reviewed_at=None)
    _score, signals = compute_zombie_score(gig, seller, reference_date=ref)
    assert "low_response_rate" not in signals


def test_missing_orders_in_queue_does_not_raise() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2020, 1, 1, tzinfo=UTC), response_rate=100)
    gig = _gig(review_count=3, orders_in_queue=None, last_reviewed_at=ref)
    score, _ = compute_zombie_score(gig, seller, reference_date=ref)
    assert score == 0.30


def test_reference_date_defaults_to_now_utc() -> None:
    seller = _seller(member_since="Jan 2020", response_rate="25%")
    gig = _gig(review_count=2, orders_in_queue=0, last_reviewed_at=None)
    score, signals = compute_zombie_score(gig, seller)
    assert score >= 0.0
    assert isinstance(signals, dict)


def test_detector_coerces_string_and_float_inputs() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since="2020/01/01", response_rate="29%")
    gig = _gig(
        review_count=None,
        review_count_exact="4.0",
        orders_in_queue="0",
        last_reviewed_at="2022/01/15",
    )
    score, signals = compute_zombie_score(gig, seller, reference_date=ref)
    assert score >= 0.55
    assert signals["low_review_count"] == 4
    assert signals["low_response_rate"] == 29.0
    assert signals["no_queue_low_reviews"] is True


def test_detector_ignores_unparseable_values_and_empty_strings() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since="   ", response_rate="n/a")
    gig = _gig(review_count="N/A", review_count_exact=" ", orders_in_queue="unknown", last_reviewed_at="bad")
    score, signals = compute_zombie_score(gig, seller, reference_date=ref)
    assert score == 0.20
    assert signals == {"never_reviewed": True}


def test_new_seller_guard_boundary_179_vs_180_days() -> None:
    ref = datetime(2026, 1, 1, tzinfo=UTC)
    gig = _gig(review_count=2, orders_in_queue=0, last_reviewed_at=None)
    new_seller = _seller(member_since=ref - timedelta(days=179), response_rate=10)
    old_enough_seller = _seller(member_since=ref - timedelta(days=180), response_rate=10)

    score_new, signals_new = compute_zombie_score(gig, new_seller, reference_date=ref)
    score_old, signals_old = compute_zombie_score(gig, old_enough_seller, reference_date=ref)

    assert score_new == 0.0
    assert signals_new.get("new_seller") is True
    assert score_old >= 0.50
    assert "new_seller" not in signals_old


def test_stale_boundary_365_not_stale_but_366_is_stale() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2020, 1, 1, tzinfo=UTC), response_rate=100)
    gig_365 = _gig(review_count=50, orders_in_queue=1, last_reviewed_at=ref - timedelta(days=365))
    gig_366 = _gig(review_count=50, orders_in_queue=1, last_reviewed_at=ref - timedelta(days=366))

    score_365, signals_365 = compute_zombie_score(gig_365, seller, reference_date=ref)
    score_366, signals_366 = compute_zombie_score(gig_366, seller, reference_date=ref)

    assert score_365 == 0.0
    assert "stale_reviews_days" not in signals_365
    assert score_366 == 0.25
    assert signals_366["stale_reviews_days"] == 366


def test_no_queue_signal_requires_review_count_below_five() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2020, 1, 1, tzinfo=UTC), response_rate=100)
    gig = _gig(review_count=5, orders_in_queue=0, last_reviewed_at=ref)
    score, signals = compute_zombie_score(gig, seller, reference_date=ref)
    assert score == 0.30
    assert "no_queue_low_reviews" not in signals


def test_detector_is_deterministic_with_fixed_reference_date() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2020, 1, 1, tzinfo=UTC), response_rate=29)
    gig = _gig(review_count=4, orders_in_queue=0, last_reviewed_at=ref - timedelta(days=400))
    first = compute_zombie_score(gig, seller, reference_date=ref)
    second = compute_zombie_score(gig, seller, reference_date=ref)
    assert first == second


def test_is_zombie_false_at_just_below_threshold_04999() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    seller = _seller(member_since=datetime(2020, 1, 1, tzinfo=UTC), response_rate=100)
    gig = _gig(review_count=10, orders_in_queue=0, last_reviewed_at=None)
    score, _signals = compute_zombie_score(gig, seller, reference_date=ref)
    assert score == 0.20
    assert is_zombie_gig(gig, seller, reference_date=ref, zombie_threshold=0.4999) is False


def test_compute_zombie_score_with_seller_none_skips_guard_and_scores() -> None:
    ref = datetime(2026, 2, 1, tzinfo=UTC)
    gig = _gig(review_count=4, orders_in_queue=0, last_reviewed_at=None)
    score, signals = compute_zombie_score(gig, None, reference_date=ref)
    assert score == 0.60
    assert "new_seller" not in signals
    assert signals["low_review_count"] == 4
