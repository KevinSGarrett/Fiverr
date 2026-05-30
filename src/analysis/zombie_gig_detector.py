"""SRDI R3.3 zombie detector with non-destructive NULL semantics."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

ZOMBIE_THRESHOLD = 0.50
MIN_ACCOUNT_AGE_DAYS = 180


def _to_utc_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        for fmt in ("%b %Y", "%B %Y", "%Y-%m-%d", "%Y/%m/%d"):
            try:
                parsed = datetime.strptime(candidate, fmt)
                return parsed.replace(tzinfo=UTC)
            except ValueError:
                continue
    return None


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        raw = value.strip().replace("%", "")
        if not raw:
            return None
        try:
            return float(raw)
        except ValueError:
            return None
    return None


def _to_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        raw = value.strip().replace(",", "")
        if not raw:
            return None
        try:
            return int(float(raw))
        except ValueError:
            return None
    return None


def compute_zombie_score(
    gig: Any,
    seller: Any,
    *,
    reference_date: datetime | None = None,
    min_account_age_days: int = MIN_ACCOUNT_AGE_DAYS,
) -> tuple[float, dict[str, Any]]:
    ref = reference_date or datetime.now(UTC)

    member_since = _to_utc_datetime(getattr(seller, "member_since", None))
    if member_since is not None:
        account_age_days = (ref - member_since).days
        if account_age_days < min_account_age_days:
            return 0.0, {"new_seller": True, "account_age_days": account_age_days}

    score = 0.0
    signals: dict[str, Any] = {}
    review_count = _to_int(getattr(gig, "review_count", None))
    if review_count is None:
        review_count = _to_int(getattr(gig, "review_count_exact", None))
    if review_count is not None and review_count < 10:
        score += 0.30
        signals["low_review_count"] = review_count

    last_reviewed_at = _to_utc_datetime(getattr(gig, "last_reviewed_at", None))
    if last_reviewed_at is None:
        score += 0.20
        signals["never_reviewed"] = True
    else:
        stale_days = (ref - last_reviewed_at).days
        if stale_days > 365:
            score += 0.25
            signals["stale_reviews_days"] = stale_days

    response_rate = _to_float(getattr(seller, "response_rate", None))
    if response_rate is not None and response_rate < 30.0:
        score += 0.15
        signals["low_response_rate"] = response_rate

    orders_in_queue = _to_int(getattr(gig, "orders_in_queue", None))
    if orders_in_queue == 0 and review_count is not None and review_count < 5:
        score += 0.10
        signals["no_queue_low_reviews"] = True

    return min(score, 1.0), signals


def is_zombie_gig(
    gig: Any,
    seller: Any,
    *,
    reference_date: datetime | None = None,
    zombie_threshold: float = ZOMBIE_THRESHOLD,
    min_account_age_days: int = MIN_ACCOUNT_AGE_DAYS,
) -> bool:
    score, _ = compute_zombie_score(
        gig,
        seller,
        reference_date=reference_date,
        min_account_age_days=min_account_age_days,
    )
    return score >= zombie_threshold
