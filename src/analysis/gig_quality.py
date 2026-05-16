"""Heuristic gig quality rubric scoring for dry-run analysis."""

from __future__ import annotations

from collections.abc import Callable

from src.analysis.contracts import (
    AnalysisEvidence,
    AnalysisReadinessStatus,
    AnalysisTaskType,
    AnalysisWarning,
    GigQualityInput,
    GigQualityResult,
)

ScoreFn = Callable[[GigQualityInput], float]


def _title_score(payload: GigQualityInput) -> float:
    title = (payload.title or "").strip()
    if not title:
        return 20.0
    length = len(title)
    word_count = len(title.split())
    score = 40.0
    if 20 <= length <= 80:
        score += 35.0
    if word_count >= 4:
        score += 25.0
    return min(score, 100.0)


def _description_score(payload: GigQualityInput) -> float:
    description = (payload.description or "").strip()
    if not description:
        return 15.0
    length = len(description)
    if length < 80:
        return 35.0
    if length < 200:
        return 60.0
    if length < 400:
        return 80.0
    return 95.0


def _package_score(payload: GigQualityInput) -> float:
    if payload.package_count is None:
        return 30.0
    if payload.package_count <= 0:
        return 10.0
    if payload.package_count == 1:
        return 55.0
    if payload.package_count == 2:
        return 75.0
    return 95.0


def _social_proof_score(payload: GigQualityInput) -> float:
    rating = payload.rating if payload.rating is not None else 0.0
    review_count = payload.review_count if payload.review_count is not None else 0
    rating_component = (rating / 5.0) * 70.0
    review_component = min(30.0, (review_count / 200.0) * 30.0)
    return round(rating_component + review_component, 2)


def _assets_score(payload: GigQualityInput) -> float:
    image_count = payload.image_count if payload.image_count is not None else 0
    has_faq = bool(payload.has_faq)

    image_component = min(75.0, image_count * 15.0)
    faq_component = 25.0 if has_faq else 0.0
    return min(100.0, image_component + faq_component)


def _metadata_completeness_score(payload: GigQualityInput) -> float:
    checks = {
        "title": bool(payload.title and payload.title.strip()),
        "description": bool(payload.description and payload.description.strip()),
        "package_count": payload.package_count is not None,
        "rating": payload.rating is not None,
        "review_count": payload.review_count is not None,
        "image_count": payload.image_count is not None,
        "has_faq": payload.has_faq is not None,
    }
    completion_ratio = sum(1 for state in checks.values() if state) / len(checks)
    return round(completion_ratio * 100.0, 2)


def score_gig_quality(payload: GigQualityInput) -> GigQualityResult:
    """Compute deterministic gig quality score from local rubric signals."""
    score_functions: dict[str, ScoreFn] = {
        "title_quality": _title_score,
        "description_quality": _description_score,
        "package_completeness": _package_score,
        "social_proof": _social_proof_score,
        "asset_richness": _assets_score,
        "metadata_completeness": _metadata_completeness_score,
    }
    weights: dict[str, float] = {
        "title_quality": 0.15,
        "description_quality": 0.20,
        "package_completeness": 0.20,
        "social_proof": 0.25,
        "asset_richness": 0.10,
        "metadata_completeness": 0.10,
    }

    component_scores = {name: round(fn(payload), 2) for name, fn in score_functions.items()}
    weighted_score = sum(component_scores[name] * weights[name] for name in component_scores)
    overall_score = max(0.0, min(100.0, round(weighted_score, 2)))

    strengths = [name for name, score in component_scores.items() if score >= 75.0]
    weaknesses = [name for name, score in component_scores.items() if score < 45.0]

    missing_data_fields = [
        field_name
        for field_name, value in {
            "title": payload.title,
            "description": payload.description,
            "package_count": payload.package_count,
            "rating": payload.rating,
            "review_count": payload.review_count,
            "image_count": payload.image_count,
            "has_faq": payload.has_faq,
        }.items()
        if value is None or (isinstance(value, str) and not value.strip())
    ]

    warnings: list[AnalysisWarning] = []
    if missing_data_fields:
        warnings.append(
            AnalysisWarning(
                code="gig_quality_missing_fields",
                message="Some rubric fields were missing; score confidence reduced.",
                source_id=payload.source_id,
                severity="warning",
                source_stage=AnalysisTaskType.GIG_QUALITY,
                remediation="Populate missing gig rubric fields to improve scoring confidence.",
                missing_data_fields=missing_data_fields,
                metadata={"gig_id": payload.gig_id},
            )
        )

    completeness_ratio = 1.0 - (len(missing_data_fields) / 7.0)
    confidence = max(0.2, min(1.0, round(completeness_ratio, 3)))
    explanation = (
        "Gig quality score is a weighted heuristic across title, description, packages, "
        "social proof, assets, and metadata completeness."
    )

    return GigQualityResult(
        source_id=payload.source_id,
        gig_id=payload.gig_id,
        overall_score=overall_score,
        quality_score=overall_score,
        component_scores=component_scores,
        rubric_components=component_scores,
        strengths=strengths,
        weaknesses=weaknesses,
        source_references=[f"gig:{payload.gig_id}"],
        confidence=confidence,
        explanation=explanation,
        missing_data_fields=missing_data_fields,
        warnings=warnings,
        metadata=payload.metadata,
        status=(
            AnalysisReadinessStatus.READY
            if completeness_ratio >= 0.85
            else AnalysisReadinessStatus.PARTIAL
            if completeness_ratio >= 0.45
            else AnalysisReadinessStatus.BLOCKED
        ),
        source_context={
            "gig_id": payload.gig_id,
            "provided_fields": 7 - len(missing_data_fields),
            "expected_fields": 7,
        },
        evidence=[
            AnalysisEvidence(
                code="overall_score",
                message="Weighted deterministic rubric score for gig quality.",
                metric=overall_score,
                source_ref=payload.gig_id,
            ),
            AnalysisEvidence(
                code="completeness_ratio",
                message="Completeness of required quality rubric fields.",
                metric=round(completeness_ratio, 3),
                source_ref="gig",
            ),
        ],
        downstream_readiness={
            "status": "ready" if completeness_ratio >= 0.85 else "partial",
            "reasons": [] if not missing_data_fields else ["missing_rubric_fields"],
        },
    )
