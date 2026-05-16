"""Deterministic saturation scoring for dry-run analysis."""

from __future__ import annotations

from statistics import mean, pstdev

from src.analysis.contracts import (
    AnalysisEvidence,
    AnalysisReadinessStatus,
    AnalysisTaskType,
    AnalysisWarning,
    SaturationInput,
    SaturationLevel,
    SaturationResult,
)


def _bounded(value: float) -> float:
    return max(0.0, min(100.0, round(value, 2)))


def _compute_price_crowding(prices: list[float]) -> float:
    if len(prices) < 3:
        return 45.0
    avg_price = mean(prices)
    if avg_price <= 0:
        return 45.0
    spread = pstdev(prices)
    coeff_var = spread / avg_price
    crowding = 100.0 - (coeff_var * 140.0)
    return _bounded(crowding)


def _compute_quality_similarity(gig_quality_scores: list[float]) -> float:
    if len(gig_quality_scores) < 2:
        return 45.0
    spread = pstdev(gig_quality_scores)
    similarity = 100.0 - (spread * 2.4)
    return _bounded(similarity)


def _compute_strength_concentration(seller_strength_scores: list[float]) -> float:
    if not seller_strength_scores:
        return 45.0
    sorted_scores = sorted(seller_strength_scores, reverse=True)
    top_slice = sorted_scores[: max(1, len(sorted_scores) // 3)]
    if not top_slice:
        return 45.0
    top_avg = mean(top_slice)
    population_avg = mean(sorted_scores)
    concentration = ((top_avg * 0.7) + ((top_avg - population_avg + 50.0) * 0.3))
    return _bounded(concentration)


def analyze_saturation(payload: SaturationInput) -> SaturationResult:
    """Compute market saturation from deterministic local signals."""
    warnings: list[AnalysisWarning] = []
    missing_data_fields: list[str] = []

    if payload.keyword_count is None:
        missing_data_fields.append("keyword_count")
        keyword_density = 40.0
    else:
        keyword_density = _bounded(min(100.0, (payload.keyword_count / 25.0) * 100.0))

    if payload.search_result_count is None:
        missing_data_fields.append("search_result_count")
        search_density = 40.0
    else:
        search_density = _bounded(min(100.0, (payload.search_result_count / 1200.0) * 100.0))

    if payload.competitor_count is None:
        missing_data_fields.append("competitor_count")
        competitor_density = 40.0
    else:
        competitor_density = _bounded(min(100.0, (payload.competitor_count / 35.0) * 100.0))

    if not payload.seller_strength_scores:
        missing_data_fields.append("seller_strength_scores")
    if not payload.prices:
        missing_data_fields.append("prices")
    if not payload.gig_quality_scores:
        missing_data_fields.append("gig_quality_scores")

    components = {
        "keyword_density": keyword_density,
        "search_result_density": search_density,
        "competitor_density": competitor_density,
        "seller_strength_concentration": _compute_strength_concentration(
            payload.seller_strength_scores
        ),
        "price_crowding": _compute_price_crowding(payload.prices),
        "gig_quality_similarity": _compute_quality_similarity(payload.gig_quality_scores),
    }
    weights = {
        "keyword_density": 0.16,
        "search_result_density": 0.18,
        "competitor_density": 0.21,
        "seller_strength_concentration": 0.17,
        "price_crowding": 0.14,
        "gig_quality_similarity": 0.14,
    }
    score = _bounded(sum(components[name] * weights[name] for name in components))

    available_signals = 6 - len(set(missing_data_fields))
    completeness_ratio = round(available_signals / 6.0, 3)
    completeness_status = (
        "ready" if completeness_ratio >= 0.75 else "partial" if completeness_ratio >= 0.35 else "blocked"
    )
    confidence = round(max(0.12, min(1.0, available_signals / 6.0)), 3)

    if available_signals <= 2:
        saturation_level = SaturationLevel.UNKNOWN
    elif score >= 70.0:
        saturation_level = SaturationLevel.HIGH
    elif score >= 45.0:
        saturation_level = SaturationLevel.MEDIUM
    else:
        saturation_level = SaturationLevel.LOW

    if missing_data_fields:
        warnings.append(
            AnalysisWarning(
                code="saturation_missing_fields",
                message="Saturation used fallback values for missing market inputs.",
                source_id=payload.source_id,
                severity="warning",
                source_stage=AnalysisTaskType.SATURATION,
                remediation="Populate missing keyword, competitor, seller, price, and quality signals.",
                missing_data_fields=sorted(set(missing_data_fields)),
            )
        )

    if score >= 70.0:
        threshold_band = "high"
    elif score >= 45.0:
        threshold_band = "medium"
    elif available_signals <= 2:
        threshold_band = "unknown"
    else:
        threshold_band = "low"

    supply_depth = _bounded((competitor_density * 0.6) + (components["seller_strength_concentration"] * 0.4))
    demand_proxy = _bounded((keyword_density * 0.55) + (search_density * 0.45))
    rationale = (
        f"Threshold band '{threshold_band}' is based on saturation_score={score}, "
        f"supply_depth={supply_depth}, demand_proxy={demand_proxy}."
    )

    explanation = (
        "Saturation score combines density, incumbent concentration, price crowding, and "
        "quality similarity where higher values indicate a more crowded market."
    )
    return SaturationResult(
        source_id=payload.source_id,
        saturation_level=saturation_level,
        score=score,
        saturation_score=score,
        supply_depth=supply_depth,
        demand_proxy=demand_proxy,
        threshold_band=threshold_band,
        thresholds={"high": 70.0, "medium": 45.0, "low": 0.0},
        supply_counts={
            "competitor_count": payload.competitor_count or 0,
            "seller_strength_count": len(payload.seller_strength_scores),
            "gig_quality_count": len(payload.gig_quality_scores),
        },
        opportunity_interpretation=(
            "Lower differentiation and stronger incumbents; prioritize micro-niches."
            if saturation_level == SaturationLevel.HIGH
            else "Competitive but still tractable with clear positioning."
            if saturation_level == SaturationLevel.MEDIUM
            else "Lower competitive pressure; entry opportunity remains favorable."
            if saturation_level == SaturationLevel.LOW
            else "Signal coverage is too sparse for a reliable opportunity interpretation."
        ),
        warning_codes=sorted({warning.code for warning in warnings}),
        rationale=rationale,
        source_context={
            "keyword_count": payload.keyword_count,
            "search_result_count": payload.search_result_count,
            "competitor_count": payload.competitor_count,
            "seller_strength_count": len(payload.seller_strength_scores),
            "price_count": len(payload.prices),
            "gig_quality_count": len(payload.gig_quality_scores),
            "completeness_ratio": completeness_ratio,
            "completeness_status": completeness_status,
        },
        confidence=confidence,
        components=components,
        warnings=warnings,
        explanation=explanation,
        missing_data_fields=sorted(set(missing_data_fields)),
        metadata=payload.metadata,
        status=(
            AnalysisReadinessStatus.READY
            if confidence >= 0.75
            else AnalysisReadinessStatus.PARTIAL
            if confidence >= 0.35
            else AnalysisReadinessStatus.BLOCKED
        ),
        evidence=[
            AnalysisEvidence(
                code="saturation_score",
                message="Deterministic saturation score derived from market density signals.",
                metric=score,
                source_ref="market_signals",
            ),
            AnalysisEvidence(
                code="signal_confidence",
                message="Confidence based on available saturation signal count.",
                metric=confidence,
                source_ref="market_signals",
            ),
        ],
        downstream_readiness={
            "status": completeness_status,
            "reasons": [] if not missing_data_fields else ["missing_saturation_inputs"],
            "completeness": {
                "available_signal_count": available_signals,
                "expected_signal_count": 6,
                "completeness_ratio": completeness_ratio,
            },
        },
    )
