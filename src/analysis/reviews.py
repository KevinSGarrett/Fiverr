"""Local deterministic review-theme analysis with redaction."""

from __future__ import annotations

from collections import Counter

from src.analysis.contracts import (
    AnalysisEvidence,
    AnalysisReadinessStatus,
    AnalysisTaskType,
    AnalysisWarning,
    ReviewAnalysisInput,
    ReviewAnalysisResult,
)
from src.llm.validation import redact_sensitive_text

_COMPLAINT_PATTERNS: dict[str, tuple[str, ...]] = {
    "late_delivery": ("late", "overdue", "delayed", "missed deadline"),
    "communication_issue": ("no response", "didn't respond", "hard to reach", "ghosted"),
    "quality_mismatch": ("poor quality", "not what i expected", "buggy", "unusable"),
    "scope_mismatch": ("not as described", "missing features", "scope"),
    "revision_issue": ("revision", "refused to revise", "extra charge"),
}

_PRAISE_PATTERNS: dict[str, tuple[str, ...]] = {
    "fast_delivery": ("quick delivery", "fast delivery", "ahead of schedule"),
    "clear_communication": ("great communication", "responsive", "clear updates"),
    "high_quality": ("excellent quality", "great quality", "clean code", "amazing work"),
    "value_for_money": ("great value", "worth every penny", "affordable"),
    "repeat_intent": ("hire again", "order again", "recommended"),
}


def _count_matches(text: str, patterns: dict[str, tuple[str, ...]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for theme, options in patterns.items():
        if any(option in text for option in options):
            counts[theme] += 1
    return counts


def analyze_reviews(payload: ReviewAnalysisInput) -> ReviewAnalysisResult:
    """Aggregate review themes without preserving reviewer-identifiable content."""
    warnings: list[AnalysisWarning] = []
    missing_data_fields: list[str] = []
    if not payload.reviews:
        warnings.append(
            AnalysisWarning(
                code="reviews_missing",
                message="No review snippets were provided for analysis.",
                source_id=payload.source_id,
                severity="warning",
                source_stage=AnalysisTaskType.REVIEW_ANALYSIS,
                remediation="Provide at least one sanitized review snippet.",
                missing_data_fields=["reviews"],
            )
        )
        return ReviewAnalysisResult(
            source_id=payload.source_id,
            themes={},
            sentiment_hints={"positive": 0, "negative": 0, "neutral": 0},
            sentiment_band="unknown",
            complaint_frequency={},
            praise_frequency={},
            theme_list=[],
            weakness_signals=[],
            positive_signals=[],
            sample_count=0,
            opportunity_gaps=[],
            confidence=0.1,
            warnings=warnings,
            explanation="Review analysis is limited because review snippets are missing.",
            missing_data_fields=["reviews"],
            metadata=payload.metadata,
            status=AnalysisReadinessStatus.SKIPPED,
            source_context={"review_count": 0},
            evidence=[
                AnalysisEvidence(
                    code="review_count",
                    message="No review snippets were provided for deterministic analysis.",
                    metric=0.0,
                    source_ref="reviews",
                )
            ],
            downstream_readiness={"status": "blocked", "reasons": ["reviews_missing"]},
        )

    complaint_counter: Counter[str] = Counter()
    praise_counter: Counter[str] = Counter()
    sentiment_counter: Counter[str] = Counter()
    redacted_any = False

    for review in payload.reviews:
        sanitized_text = redact_sensitive_text(review.text)
        if sanitized_text != review.text:
            redacted_any = True
        normalized = sanitized_text.lower()

        complaint_hits = _count_matches(normalized, _COMPLAINT_PATTERNS)
        praise_hits = _count_matches(normalized, _PRAISE_PATTERNS)
        complaint_counter.update(complaint_hits)
        praise_counter.update(praise_hits)

        if review.rating is not None:
            if review.rating >= 4.0:
                sentiment_counter.update(["positive"])
            elif review.rating <= 2.5:
                sentiment_counter.update(["negative"])
            else:
                sentiment_counter.update(["neutral"])
        else:
            if complaint_hits and not praise_hits:
                sentiment_counter.update(["negative"])
            elif praise_hits and not complaint_hits:
                sentiment_counter.update(["positive"])
            else:
                sentiment_counter.update(["neutral"])

    themes = complaint_counter + praise_counter
    top_complaints = sorted(complaint_counter.items(), key=lambda item: (-item[1], item[0]))[:3]
    top_praise = sorted(praise_counter.items(), key=lambda item: (-item[1], item[0]))[:3]

    opportunity_gaps = [
        f"Address frequent complaint theme: {theme.replace('_', ' ')}"
        for theme, count in top_complaints
        if count >= 2
    ]
    if not opportunity_gaps:
        opportunity_gaps.append(
            "Differentiate with explicit quality guarantees and clearer delivery communication."
        )

    confidence = round(
        max(
            0.2,
            min(
                1.0,
                (len(payload.reviews) / 10.0)
                + (0.2 if bool(complaint_counter or praise_counter) else 0.0)
                - (0.1 if redacted_any else 0.0),
            ),
        ),
        3,
    )

    if redacted_any:
        warnings.append(
            AnalysisWarning(
                code="review_text_redacted",
                message="Sensitive-looking strings were redacted before theme aggregation.",
                source_id=payload.source_id,
                severity="info",
                source_stage=AnalysisTaskType.REVIEW_ANALYSIS,
                remediation="Review redaction-safe snippets if additional context is required.",
            )
        )
    if all(review.rating is None for review in payload.reviews):
        missing_data_fields.append("review.rating")
        warnings.append(
            AnalysisWarning(
                code="review_rating_missing",
                message="Review ratings were missing; sentiment relied on text-only heuristics.",
                source_id=payload.source_id,
                severity="warning",
                source_stage=AnalysisTaskType.REVIEW_ANALYSIS,
                remediation="Include rating values in upstream review fixtures.",
                missing_data_fields=["review.rating"],
            )
        )

    negative_count = sentiment_counter.get("negative", 0)
    positive_count = sentiment_counter.get("positive", 0)
    if negative_count >= positive_count + 2:
        sentiment_band = "negative"
    elif positive_count >= negative_count + 2:
        sentiment_band = "positive"
    else:
        sentiment_band = "mixed"

    theme_list = [
        {"theme": theme, "count": count, "signal": "weakness"}
        for theme, count in top_complaints
    ] + [{"theme": theme, "count": count, "signal": "positive"} for theme, count in top_praise]

    explanation = (
        "Review analysis aggregates complaint and praise themes from sanitized snippets to "
        "highlight exploitable competitor weaknesses and recurring buyer expectations."
    )
    return ReviewAnalysisResult(
        source_id=payload.source_id,
        themes=dict(sorted(themes.items())),
        sentiment_hints={
            "positive": positive_count,
            "negative": negative_count,
            "neutral": sentiment_counter.get("neutral", 0),
        },
        sentiment_band=sentiment_band,
        complaint_frequency=dict(top_complaints),
        praise_frequency=dict(top_praise),
        theme_list=theme_list,
        weakness_signals=[theme for theme, _count in top_complaints],
        positive_signals=[theme for theme, _count in top_praise],
        sample_count=len(payload.reviews),
        opportunity_gaps=opportunity_gaps,
        confidence=confidence,
        warnings=warnings,
        explanation=explanation,
        missing_data_fields=missing_data_fields,
        metadata=payload.metadata,
        status=(
            AnalysisReadinessStatus.READY
            if len(payload.reviews) >= 3
            else AnalysisReadinessStatus.PARTIAL
        ),
        source_context={
            "review_count": len(payload.reviews),
            "redacted": redacted_any,
            "theme_count": len(themes),
        },
        evidence=[
            AnalysisEvidence(
                code="negative_sentiment_count",
                message="Negative sentiment hints derived from reviews.",
                metric=float(sentiment_counter.get("negative", 0)),
                source_ref="reviews",
            ),
            AnalysisEvidence(
                code="theme_count",
                message="Combined complaint and praise theme count.",
                metric=float(len(themes)),
                source_ref="reviews",
            ),
        ],
        downstream_readiness={
            "status": "ready" if len(payload.reviews) >= 3 else "partial",
            "reasons": [] if len(payload.reviews) >= 3 else ["limited_review_sample"],
        },
    )
