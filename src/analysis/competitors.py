"""Competitor profiling and early seller-strength heuristics."""

from __future__ import annotations

from collections import Counter
from statistics import median

from src.analysis.contracts import (
    AnalysisEvidence,
    AnalysisReadinessStatus,
    AnalysisWarning,
    CompetitorProfileInput,
    CompetitorProfileResult,
)


def _band_for_price(price: float) -> str:
    if price < 50:
        return "low"
    if price <= 150:
        return "mid"
    return "high"


def profile_competitors(payload: CompetitorProfileInput) -> CompetitorProfileResult:
    """Generate deterministic competitor profile from local competitor snapshots."""
    competitors = payload.competitors
    warnings: list[AnalysisWarning] = []

    if not competitors:
        warnings.append(
            AnalysisWarning(
                code="no_competitors",
                message="No competitors were provided for profile analysis.",
                source_id=payload.source_id,
                missing_data_fields=["competitors"],
            )
        )
        return CompetitorProfileResult(
            source_id=payload.source_id,
            competition_intensity_score=0.0,
            dominant_seller_levels={},
            pricing_bands={},
            rating_review_concentration="insufficient_data",
            high_authority_sellers=[],
            weak_competitors=[],
            opportunity_signals=["Very sparse competitor landscape."],
            confidence=0.2,
            explanation="Insufficient competitor data for reliable market profile.",
            missing_data_fields=["competitors"],
            warnings=warnings,
            metadata=payload.metadata,
            status=AnalysisReadinessStatus.SKIPPED,
            source_context={"competitor_count": 0},
            evidence=[
                AnalysisEvidence(
                    code="competitor_count",
                    message="No competitor rows were available for profiling.",
                    metric=0.0,
                    source_ref="competitors",
                )
            ],
            downstream_readiness={"status": "blocked", "reasons": ["competitors_missing"]},
        )

    level_counter = Counter((entry.seller_level or "unknown").lower() for entry in competitors)
    price_counter = Counter(
        _band_for_price(entry.starting_price)
        for entry in competitors
        if entry.starting_price is not None
    )

    high_authority = [
        entry.seller_id
        for entry in competitors
        if (entry.rating or 0.0) >= 4.8 and (entry.review_count or 0) >= 200
    ]
    weak_competitors = [
        entry.seller_id
        for entry in competitors
        if (entry.rating or 0.0) < 4.5 or (entry.review_count or 0) < 20
    ]

    ratings = [entry.rating for entry in competitors if entry.rating is not None]
    reviews = [entry.review_count for entry in competitors if entry.review_count is not None]
    prices = [entry.starting_price for entry in competitors if entry.starting_price is not None]

    median_rating = round(median(ratings), 2) if ratings else 0.0
    median_reviews = int(median(reviews)) if reviews else 0
    median_price = round(float(median(prices)), 2) if prices else 0.0

    strong_ratio = len(high_authority) / len(competitors)
    weak_ratio = len(weak_competitors) / len(competitors)
    new_seller_ratio = level_counter.get("new", 0) / len(competitors)

    competition_intensity = (
        strong_ratio * 55.0
        + min(30.0, median_reviews / 10.0)
        + (15.0 if median_rating >= 4.8 else 5.0 if median_rating >= 4.6 else 0.0)
    )
    competition_intensity_score = max(0.0, min(100.0, round(competition_intensity, 2)))

    opportunity_signals: list[str] = []
    if weak_ratio >= 0.4:
        opportunity_signals.append("Large share of weak competitors indicates entry opportunity.")
    if new_seller_ratio >= 0.3:
        opportunity_signals.append(
            "New-seller feasibility is favorable due to meaningful early-stage seller presence."
        )
    if median_price >= 120:
        opportunity_signals.append("Higher median pricing suggests premium-positioning space.")
    if not opportunity_signals:
        opportunity_signals.append("Market appears efficient; focus on micro-differentiation.")

    concentration = (
        f"median_rating={median_rating}, median_reviews={median_reviews}, median_price={median_price}"
    )

    if strong_ratio >= 0.35:
        warnings.append(
            AnalysisWarning(
                code="high_competition",
                message="Strong incumbent concentration detected in market snapshot.",
                source_id=payload.source_id,
                metadata={"strong_ratio": round(strong_ratio, 3)},
            )
        )

    missing_data_fields: list[str] = []
    if not prices:
        missing_data_fields.append("starting_price")
    if not ratings:
        missing_data_fields.append("rating")
    if not reviews:
        missing_data_fields.append("review_count")

    confidence = max(
        0.25,
        min(
            1.0,
            round(
                0.45
                + (0.2 if bool(ratings) else 0.0)
                + (0.2 if bool(reviews) else 0.0)
                + (0.15 if bool(prices) else 0.0),
                3,
            ),
        ),
    )

    return CompetitorProfileResult(
        source_id=payload.source_id,
        competition_intensity_score=competition_intensity_score,
        dominant_seller_levels=dict(level_counter),
        pricing_bands=dict(price_counter),
        rating_review_concentration=concentration,
        high_authority_sellers=sorted(high_authority),
        weak_competitors=sorted(set(weak_competitors)),
        opportunity_signals=opportunity_signals,
        confidence=confidence,
        explanation="Profile derived from local seller level, pricing, rating, and review heuristics.",
        missing_data_fields=missing_data_fields,
        warnings=warnings,
        metadata=payload.metadata,
        status=(
            AnalysisReadinessStatus.READY
            if len(competitors) >= 3
            else AnalysisReadinessStatus.PARTIAL
        ),
        source_context={
            "competitor_count": len(competitors),
            "has_rating_signals": bool(ratings),
            "has_review_signals": bool(reviews),
            "has_price_signals": bool(prices),
        },
        evidence=[
            AnalysisEvidence(
                code="competition_intensity_score",
                message="Deterministic competition intensity from seller, rating, and review signals.",
                metric=competition_intensity_score,
                source_ref="competitors",
            ),
            AnalysisEvidence(
                code="high_authority_ratio",
                message="Ratio of high-authority sellers in competitor sample.",
                metric=round(strong_ratio, 3),
                source_ref="competitors",
            ),
        ],
        downstream_readiness={
            "status": "ready" if len(competitors) >= 3 else "partial",
            "reasons": [] if len(competitors) >= 3 else ["limited_competitor_sample"],
        },
    )
