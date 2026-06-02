"""R7 external signal integrity qualifiers and helpers."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from src.config.models import ExternalSignalsConfig

_BUYER_INTENT_PHRASES: tuple[str, ...] = (
    "looking for",
    "need help",
    "hire",
    "hiring",
    "budget",
    "price",
    "quote",
    "freelancer",
)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _compute_fiverr_relevance_qualifier(
    rsv: float,
    is_fiverr_relevant: bool,
    trend_direction: str,
    keyword: str,
    config: ExternalSignalsConfig,
) -> float:
    """Compute Google Trends platform relevance qualifier, clamped [0.20, 0.95]."""
    base = float(config.trends_base_qualifier)
    modifier = 0.0

    normalized_direction = trend_direction.strip().upper()
    if normalized_direction == "STRONGLY_RISING":
        modifier += 0.10
    elif normalized_direction == "RISING":
        modifier += 0.05
    elif normalized_direction == "DECLINING":
        modifier -= 0.05

    # Single-word keywords are usually broader and lower-intent on Fiverr.
    if len([part for part in keyword.split(" ") if part.strip()]) == 1:
        modifier -= 0.10

    if not is_fiverr_relevant:
        modifier -= 0.15

    if rsv < 0.80:
        modifier -= min(0.15, (0.80 - max(0.0, rsv)) * 0.5)

    raw = base + modifier
    return _clamp(raw, float(config.trends_clamp_low), float(config.trends_clamp_high))


def _qualify_reddit_score(
    raw_score: float,
    buyer_intent_ratio: float,
    config: ExternalSignalsConfig,
) -> float:
    """Qualify Reddit score with buyer-intent weighting."""
    normalized_ratio = _clamp(buyer_intent_ratio, 0.0, 1.0)
    intent_multiplier = float(config.reddit_baseline_weight) + (
        float(config.reddit_intent_weight) * normalized_ratio
    )
    return float(raw_score) * intent_multiplier


def _apply_youtube_confidence_gate(
    current_confidence: float,
    youtube_video_count: int,
    config: ExternalSignalsConfig,
) -> float:
    """Apply category-legitimacy confidence gate from YouTube counts."""
    confidence = _clamp(current_confidence, 0.0, 1.0)
    if youtube_video_count < int(config.youtube_confidence_threshold_low):
        return max(0.20, confidence - float(config.youtube_confidence_delta))
    if youtube_video_count >= int(config.youtube_confidence_threshold_high):
        return min(1.0, confidence + float(config.youtube_confidence_delta))
    return confidence


def _classify_autocomplete_absence(
    keyword: str,
    niche: str,
    autocomplete_data: dict[str, Any] | None,
) -> int:
    """Classify autocomplete signal status: emerging=50, not_searched=0, unknown=20."""
    del keyword, niche
    if autocomplete_data is None:
        return 20
    status = str(autocomplete_data.get("status", "unknown")).strip().lower()
    if status == "emerging":
        return 50
    if status == "not_searched":
        return 0
    return 20


def estimate_buyer_intent_ratio(payload: Mapping[str, Any] | None) -> float:
    """Estimate buyer intent ratio from payload posts when explicit ratio is unavailable."""
    if not isinstance(payload, Mapping):
        return 0.0
    explicit = payload.get("buyer_intent_ratio")
    if isinstance(explicit, int | float):
        return _clamp(float(explicit), 0.0, 1.0)

    raw_posts = payload.get("posts")
    if not isinstance(raw_posts, list) or not raw_posts:
        return 0.0

    matched = 0
    total = 0
    for entry in raw_posts:
        if not isinstance(entry, Mapping):
            continue
        text = f"{entry.get('title', '')} {entry.get('body', '')}".lower()
        total += 1
        if any(phrase in text for phrase in _BUYER_INTENT_PHRASES):
            matched += 1
    if total == 0:
        return 0.0
    return _clamp(matched / total, 0.0, 1.0)


def compute_signal_freshness_quality(
    signal_age_days: int,
    relevance_score: float,
    max_age_days: int = 90,
) -> float:
    """Compute freshness×relevance quality as geometric mean."""
    if max_age_days <= 0:
        return 0.0
    freshness = _clamp(1.0 - (float(signal_age_days) / float(max_age_days)), 0.0, 1.0)
    relevance = _clamp(relevance_score, 0.0, 1.0)
    return _clamp(math.sqrt(freshness * relevance), 0.0, 1.0)
