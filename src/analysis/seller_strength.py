"""Deterministic seller-strength scoring for dry-run analysis."""

from __future__ import annotations

import re

from src.analysis.contracts import (
    AnalysisEvidence,
    AnalysisReadinessStatus,
    AnalysisTaskType,
    AnalysisWarning,
    SellerStrengthInput,
    SellerStrengthResult,
)

_LEVEL_SCORES: dict[str, float] = {
    "no level": 20.0,
    "new": 28.0,
    "level 1": 52.0,
    "level one": 52.0,
    "level 2": 72.0,
    "level two": 72.0,
    "top rated": 90.0,
    "pro": 96.0,
}


def _normalize_level(level: str | None) -> str:
    if not level:
        return "no level"
    return level.strip().lower()


def _response_time_score(response_time: str | None) -> float:
    if not response_time:
        return 45.0
    text = response_time.strip().lower()
    if "minute" in text:
        return 95.0
    if "hour" in text:
        hours = _extract_numeric(text)
        if hours <= 1:
            return 90.0
        if hours <= 3:
            return 80.0
        if hours <= 12:
            return 70.0
        return 55.0
    if "day" in text:
        days = _extract_numeric(text)
        if days <= 1:
            return 55.0
        if days <= 2:
            return 35.0
        return 20.0
    return 45.0


def _extract_numeric(text: str) -> int:
    match = re.search(r"(\d+)", text)
    if match is None:
        return 1
    return int(match.group(1))


def score_seller_strength(payload: SellerStrengthInput) -> SellerStrengthResult:
    """Compute deterministic seller strength from local seller profile fields."""
    missing_data_fields: list[str] = []
    warnings: list[AnalysisWarning] = []

    level = _normalize_level(payload.level)
    level_score = _LEVEL_SCORES.get(level, 30.0)
    if payload.level is None:
        missing_data_fields.append("level")

    if payload.rating is None:
        rating_score = 45.0
        missing_data_fields.append("rating")
    else:
        rating_score = round((payload.rating / 5.0) * 100.0, 2)

    if payload.review_count is None:
        review_score = 20.0
        missing_data_fields.append("review_count")
    else:
        review_score = min(100.0, round((payload.review_count / 400.0) * 100.0, 2))

    response_time_score = _response_time_score(payload.response_time)
    if payload.response_time is None:
        missing_data_fields.append("response_time")

    if payload.delivery_consistency is None:
        delivery_score = 50.0
        missing_data_fields.append("delivery_consistency")
    else:
        delivery_score = round(payload.delivery_consistency * 100.0, 2)

    if payload.active_gig_count is None:
        gig_score = 45.0
        missing_data_fields.append("active_gig_count")
    elif payload.active_gig_count <= 2:
        gig_score = 55.0
    elif payload.active_gig_count <= 8:
        gig_score = 85.0
    elif payload.active_gig_count <= 15:
        gig_score = 70.0
    else:
        gig_score = 50.0

    language_count = len([language for language in payload.languages if language.strip()])
    if not payload.languages:
        language_score = 40.0
        missing_data_fields.append("languages")
    else:
        language_score = min(100.0, 35.0 + (language_count * 22.0))

    if payload.account_tenure_months is None:
        tenure_score = 30.0
        missing_data_fields.append("account_tenure_months")
    else:
        tenure_score = min(100.0, round((payload.account_tenure_months / 60.0) * 100.0, 2))

    components = {
        "level": round(level_score, 2),
        "rating": round(rating_score, 2),
        "review_count": round(review_score, 2),
        "response_time": round(response_time_score, 2),
        "delivery_consistency": round(delivery_score, 2),
        "active_gig_count": round(gig_score, 2),
        "language_breadth": round(language_score, 2),
        "account_tenure": round(tenure_score, 2),
    }
    weights = {
        "level": 0.22,
        "rating": 0.18,
        "review_count": 0.18,
        "response_time": 0.08,
        "delivery_consistency": 0.12,
        "active_gig_count": 0.08,
        "language_breadth": 0.06,
        "account_tenure": 0.08,
    }
    weighted_score = sum(components[name] * weights[name] for name in components)
    score = round(max(0.0, min(100.0, weighted_score)), 2)

    completeness_ratio = 1.0 - (len(missing_data_fields) / len(components))
    completeness_ratio = round(completeness_ratio, 3)
    completeness_status = (
        "ready" if completeness_ratio >= 0.75 else "partial" if completeness_ratio >= 0.35 else "blocked"
    )
    confidence = round(max(0.15, min(1.0, completeness_ratio)), 3)
    if missing_data_fields:
        warnings.append(
            AnalysisWarning(
                code="seller_strength_missing_fields",
                message="Seller strength used fallback values for missing fields.",
                source_id=payload.source_id,
                severity="warning",
                source_stage=AnalysisTaskType.SELLER_STRENGTH,
                remediation="Populate missing seller profile fields to increase strength confidence.",
                missing_data_fields=sorted(missing_data_fields),
                metadata={"seller_id": payload.seller_id},
            )
        )

    reliability_signals = {
        "response_time": round(response_time_score, 2),
        "delivery_consistency": round(delivery_score, 2),
        "rating": round(rating_score, 2),
    }
    experience_indicators = {
        "level": level,
        "review_count": payload.review_count or 0,
        "active_gig_count": payload.active_gig_count or 0,
        "account_tenure_months": payload.account_tenure_months or 0,
    }
    weakness_markers = sorted(
        set(missing_data_fields + [name for name, value in components.items() if value < 45.0])
    )

    explanation = (
        "Seller strength combines level, social proof, responsiveness, delivery reliability, "
        "gig activity, language breadth, and tenure using deterministic weighted heuristics."
    )
    return SellerStrengthResult(
        source_id=payload.source_id,
        seller_id=payload.seller_id,
        score=score,
        authority_score=round((components["level"] * 0.45) + (components["review_count"] * 0.55), 2),
        normalized_score=round(score / 100.0, 4),
        confidence=confidence,
        components=components,
        reliability_signals=reliability_signals,
        authority_indicators={
            "level_signal": components["level"],
            "review_signal": components["review_count"],
            "rating_signal": components["rating"],
        },
        input_signals={
            "review_count": payload.review_count,
            "rating": payload.rating,
            "account_tenure_months": payload.account_tenure_months,
            "active_gig_count": payload.active_gig_count,
        },
        experience_indicators=experience_indicators,
        weakness_markers=weakness_markers,
        reasons=[
            "missing_profile_fields" if missing_data_fields else "profile_complete",
            "high_authority" if score >= 75.0 else "developing_authority",
        ],
        warnings=warnings,
        explanation=explanation,
        missing_data_fields=sorted(missing_data_fields),
        metadata=payload.metadata,
        status=(
            AnalysisReadinessStatus.READY
            if confidence >= 0.75
            else AnalysisReadinessStatus.PARTIAL
            if confidence >= 0.35
            else AnalysisReadinessStatus.BLOCKED
        ),
        source_context={
            "seller_id": payload.seller_id,
            "provided_component_count": len(components) - len(missing_data_fields),
            "expected_component_count": len(components),
            "completeness_ratio": completeness_ratio,
            "completeness_status": completeness_status,
        },
        evidence=[
            AnalysisEvidence(
                code="seller_strength_score",
                message="Deterministic seller strength score from weighted rubric components.",
                metric=score,
                source_ref=payload.seller_id,
            ),
            AnalysisEvidence(
                code="seller_confidence",
                message="Confidence degrades when fallback values replace missing fields.",
                metric=confidence,
                source_ref=payload.seller_id,
            ),
        ],
        downstream_readiness={
            "status": completeness_status,
            "reasons": [] if not missing_data_fields else ["missing_seller_profile_fields"],
            "completeness": {
                "required_components": sorted(components.keys()),
                "missing_fields": sorted(missing_data_fields),
                "completeness_ratio": completeness_ratio,
            },
        },
    )
