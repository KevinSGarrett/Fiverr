"""Dry-run analysis stage orchestrator for local integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from pydantic import ValidationError

from src.analysis.clustering import cluster_keywords
from src.analysis.competitors import profile_competitors
from src.analysis.contracts import (
    AnalysisError,
    AnalysisReadinessStatus,
    AnalysisRunSummary,
    AnalysisStageSummary,
    AnalysisStatus,
    AnalysisTaskType,
    AnalysisWarning,
    CompetitorProfileInput,
    GigQualityInput,
    IntentInput,
    KeywordClusterInput,
    ReviewAnalysisInput,
    SaturationInput,
    SellerStrengthInput,
)
from src.analysis.gig_quality import score_gig_quality
from src.analysis.intent import classify_intent
from src.analysis.registry import build_analysis_output_registry
from src.analysis.reviews import analyze_reviews
from src.analysis.saturation import analyze_saturation
from src.analysis.seller_strength import score_seller_strength

STAGE_EXECUTION_ORDER: tuple[AnalysisTaskType, ...] = (
    AnalysisTaskType.KEYWORD_CLUSTERING,
    AnalysisTaskType.GIG_QUALITY,
    AnalysisTaskType.COMPETITOR_PROFILE,
    AnalysisTaskType.SELLER_STRENGTH,
    AnalysisTaskType.SATURATION,
    AnalysisTaskType.REVIEW_ANALYSIS,
    AnalysisTaskType.INTENT_CLASSIFICATION,
)

_INTENT_SELECTION_CONFIDENCE: dict[str, float] = {
    "explicit_intent_keyword": 1.0,
    "top_level_keyword_text": 0.9,
    "keywords_first_entry": 0.8,
    "source_id_fallback": 0.6,
}

_PLACEHOLDER_STATUS_ORDER: tuple[str, ...] = ("blocked", "empty", "sparse", "ready")

_SCORING_CONTRACT_FIELDS: dict[str, tuple[str, ...]] = {
    "demand_scoring": (
        "intent.selected_keyword",
        "intent.selection_reason",
        "keyword_clustering.cluster_count",
        "keyword_clustering.top_cluster_labels",
    ),
    "competition_scoring": (
        "competitor_profile.competitor_count",
        "competitor_profile.missing_seller_context_count",
        "gig_quality.completeness_ratio",
    ),
    "opportunity_scoring": (
        "saturation.signal_counts",
        "review_analysis.status",
        "seller_strength.readiness_status",
    ),
    "confidence_scoring": (
        "run.warning_count",
        "run.missing_field_count",
        "stage_contracts.*.status",
    ),
}

_SCORING_INTERFACE_REQUIREMENTS: dict[str, tuple[AnalysisTaskType, ...]] = {
    "demand_scoring": (
        AnalysisTaskType.KEYWORD_CLUSTERING,
        AnalysisTaskType.INTENT_CLASSIFICATION,
    ),
    "competition_scoring": (
        AnalysisTaskType.COMPETITOR_PROFILE,
        AnalysisTaskType.GIG_QUALITY,
        AnalysisTaskType.SELLER_STRENGTH,
    ),
    "opportunity_scoring": (
        AnalysisTaskType.SATURATION,
        AnalysisTaskType.REVIEW_ANALYSIS,
        AnalysisTaskType.COMPETITOR_PROFILE,
    ),
    "confidence_scoring": (
        AnalysisTaskType.KEYWORD_CLUSTERING,
        AnalysisTaskType.GIG_QUALITY,
        AnalysisTaskType.COMPETITOR_PROFILE,
        AnalysisTaskType.SELLER_STRENGTH,
        AnalysisTaskType.SATURATION,
        AnalysisTaskType.REVIEW_ANALYSIS,
        AnalysisTaskType.INTENT_CLASSIFICATION,
    ),
    "conversion_intent_scoring": (
        AnalysisTaskType.INTENT_CLASSIFICATION,
        AnalysisTaskType.REVIEW_ANALYSIS,
    ),
    "trend_scoring": (
        AnalysisTaskType.KEYWORD_CLUSTERING,
        AnalysisTaskType.SATURATION,
        AnalysisTaskType.REVIEW_ANALYSIS,
    ),
}


@dataclass(frozen=True)
class _IntentKeywordSelection:
    keyword_text: str
    selection_reason: str
    selection_confidence: float


@dataclass(frozen=True)
class _AnalysisRunContract:
    stage_order: list[str]
    successful_stages: list[str]
    failed_stages: list[str]
    skipped_stages: list[str]
    warning_count: int
    missing_field_count: int
    scoring_readiness: dict[str, Any]

    @classmethod
    def from_stages(
        cls,
        stages: list[AnalysisStageSummary],
        *,
        warning_count: int,
    ) -> _AnalysisRunContract:
        stage_by_type = {stage.stage: stage for stage in stages}
        successful_stages: list[str] = []
        failed_stages: list[str] = []
        skipped_stages: list[str] = []
        missing_field_count = 0
        for stage_type in STAGE_EXECUTION_ORDER:
            stage_summary = stage_by_type.get(stage_type)
            if stage_summary is None:
                skipped_stages.append(stage_type.value)
                continue
            if stage_summary.status == AnalysisStatus.SUCCESS:
                successful_stages.append(stage_type.value)
            elif stage_summary.status == AnalysisStatus.FAILED:
                failed_stages.append(stage_type.value)
            missing_fields = stage_summary.metadata.get("missing_field_count", 0)
            if isinstance(missing_fields, int) and missing_fields >= 0:
                missing_field_count += missing_fields
        return cls(
            stage_order=[stage_type.value for stage_type in STAGE_EXECUTION_ORDER],
            successful_stages=successful_stages,
            failed_stages=failed_stages,
            skipped_stages=skipped_stages,
            warning_count=warning_count,
            missing_field_count=missing_field_count,
            scoring_readiness=summarize_scoring_readiness(
                stages,
                warning_count=warning_count,
                missing_field_count=missing_field_count,
            ),
        )


def _stage_metadata(
    source_id: str,
    *,
    result_count: int = 0,
    warning_count: int = 0,
    missing_field_count: int = 0,
    **extras: Any,
) -> dict[str, Any]:
    """Build stable metadata keys required by dry-run consumers."""
    return {
        "source_id": source_id,
        "result_count": result_count,
        "warning_count": warning_count,
        "missing_field_count": missing_field_count,
        **extras,
    }


def _with_stage_timing(metadata: dict[str, Any], *, started_at: datetime) -> dict[str, Any]:
    finished_at = datetime.now(UTC)
    duration_ms = max(0, int((finished_at - started_at).total_seconds() * 1000))
    return {
        **metadata,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_ms": duration_ms,
    }


def _normalize_readiness_status(stage_status: str) -> AnalysisReadinessStatus:
    if stage_status == "ready":
        return AnalysisReadinessStatus.READY
    if stage_status == "sparse":
        return AnalysisReadinessStatus.PARTIAL
    if stage_status == "empty":
        return AnalysisReadinessStatus.SKIPPED
    return AnalysisReadinessStatus.BLOCKED


def _readiness_reasons(stage_contract: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    missing_fields = stage_contract.get("missing_fields")
    if isinstance(missing_fields, list):
        reasons.extend(str(field_name) for field_name in missing_fields if str(field_name))
    blocking_reasons = stage_contract.get("blocking_reasons")
    if isinstance(blocking_reasons, list):
        reasons.extend(str(reason) for reason in blocking_reasons if str(reason))
    return list(dict.fromkeys(reasons))


def _stage_log_entry(stage: AnalysisStageSummary) -> dict[str, Any]:
    error_code = stage.error.code if stage.error is not None else None
    return {
        "stage": stage.stage.value,
        "status": stage.status.value,
        "readiness_status": stage.readiness_status.value,
        "warning_count": len(stage.warnings),
        "error_code": error_code,
        "duration_ms": stage.metadata.get("duration_ms", 0),
    }


def _build_dashboard_handoff_contract(stages: list[AnalysisStageSummary]) -> dict[str, Any]:
    """Build dashboard-consumable alignment fields for analysis outputs."""
    stage_map = {stage.stage.value: stage for stage in stages}
    saturation_stage = stage_map.get("saturation")
    competitor_stage = stage_map.get("competitor_profile")
    intent_stage = stage_map.get("intent_classification")
    clustering_stage = stage_map.get("keyword_clustering")
    return {
        "opportunity_cards": {
            "saturation_status": (
                saturation_stage.readiness_status.value if saturation_stage is not None else "blocked"
            ),
            "competitor_status": (
                competitor_stage.readiness_status.value if competitor_stage is not None else "blocked"
            ),
            "intent_status": intent_stage.readiness_status.value if intent_stage is not None else "blocked",
        },
        "keyword_table": {
            "cluster_status": (
                clustering_stage.readiness_status.value if clustering_stage is not None else "blocked"
            ),
        },
        "run_history": {
            "stage_count": len(stages),
            "failed_stage_count": sum(1 for stage in stages if stage.status == AnalysisStatus.FAILED),
            "warning_count": sum(len(stage.warnings) for stage in stages),
        },
    }


def _normalized_warning_dict(warning: AnalysisWarning) -> dict[str, Any]:
    affected_field = warning.affected_field
    if affected_field is None and warning.missing_data_fields:
        affected_field = warning.missing_data_fields[0]
    source_stage = warning.source_stage.value if warning.source_stage is not None else "analysis"
    remediation = warning.remediation or "Inspect source data quality and rerun analysis."
    return {
        "code": warning.code,
        "severity": warning.severity,
        "message": warning.message,
        "affected_field": affected_field,
        "source_stage": source_stage,
        "remediation": remediation,
        "source_id": warning.source_id,
    }


def _build_stage_run_summary(stages: list[AnalysisStageSummary]) -> list[dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    for stage in stages:
        contract = stage.metadata.get("readiness_contract", {})
        source_availability = contract.get("source_availability", {})
        inputs_consumed = (
            sorted([name for name, present in source_availability.items() if bool(present)])
            if isinstance(source_availability, dict)
            else []
        )
        outputs_emitted = (
            contract.get("future_contract_fields", [])
            if isinstance(contract, dict) and isinstance(contract.get("future_contract_fields"), list)
            else []
        )
        output_keys = sorted(str(key) for key in outputs_emitted if str(key).strip())
        if stage.status == AnalysisStatus.SUCCESS:
            stage_run_status = "completed" if not stage.warnings else "warning"
        elif stage.status == AnalysisStatus.FAILED:
            stage_run_status = "blocked"
        else:
            stage_run_status = "skipped"
        summary_rows.append(
            {
                "stage": stage.stage.value,
                "status": stage_run_status,
                "started": True,
                "inputs_consumed": inputs_consumed,
                "input_availability": source_availability if isinstance(source_availability, dict) else {},
                "outputs_emitted": outputs_emitted,
                "output_keys": output_keys,
                "warning_count": len(stage.warnings),
            }
        )
    return summary_rows


def _build_analysis_closure_matrix(stages: list[AnalysisStageSummary]) -> list[dict[str, Any]]:
    """Return stage closure evidence rows used for Jira/report handoff."""
    matrix: list[dict[str, Any]] = []
    stage_lookup = {stage.stage: stage for stage in stages}
    for stage_type in STAGE_EXECUTION_ORDER:
        stage = stage_lookup.get(stage_type)
        if stage is None:
            matrix.append(
                {
                    "stage": stage_type.value,
                    "executed": False,
                    "status": "missing",
                    "readiness_status": "blocked",
                    "warning_count": 0,
                    "missing_field_count": 0,
                    "closure_ready": False,
                    "scoring_ready": False,
                }
            )
            continue
        readiness_contract = stage.metadata.get("readiness_contract", {})
        missing_fields = readiness_contract.get("missing_fields", []) if isinstance(readiness_contract, dict) else []
        closure_ready = stage.status == AnalysisStatus.SUCCESS and not missing_fields
        scoring_ready = _stage_contract_status(stage) == "ready"
        matrix.append(
            {
                "stage": stage.stage.value,
                "executed": True,
                "status": stage.status.value,
                "readiness_status": stage.readiness_status.value,
                "warning_count": len(stage.warnings),
                "missing_field_count": int(stage.metadata.get("missing_field_count", 0)),
                "closure_ready": closure_ready,
                "scoring_ready": scoring_ready,
            }
        )
    return matrix


def _build_scoring_readiness_handoff(readiness: dict[str, Any]) -> dict[str, Any]:
    """Build non-implementation handoff for future scoring cycle owners."""
    interfaces = readiness.get("interfaces", {})
    blocked_or_sparse = [
        interface_name
        for interface_name, data in interfaces.items()
        if isinstance(data, dict) and data.get("status") in {"blocked", "sparse", "empty"}
    ]
    return {
        "implementation_status": "handoff_only",
        "ready_for_scoring_epic": not blocked_or_sparse,
        "blocked_or_sparse_interfaces": blocked_or_sparse,
        "next_cycle_focus": (
            "Implement scoring only after blocked/sparse interfaces reach ready."
            if blocked_or_sparse
            else "Scoring contracts are ready for implementation."
        ),
    }


def _failed_stage_summary(
    *,
    stage: AnalysisTaskType,
    source_id: str,
    code: str,
    exc: Exception,
) -> AnalysisStageSummary:
    """Create stable failed-stage summaries without dropping error details."""
    error = AnalysisError.from_exception(exc, code=code)
    started_at = datetime.now(UTC)
    return AnalysisStageSummary(
        stage=stage,
        status=AnalysisStatus.FAILED,
        readiness_status=AnalysisReadinessStatus.BLOCKED,
        readiness_reasons=[code],
        error=error,
        result_type="none",
        metadata=_with_stage_timing(
            _stage_metadata(
                source_id,
                result_count=0,
                warning_count=0,
                missing_field_count=0,
                error_code=error.code,
                failed=True,
            ),
            started_at=started_at,
        ),
    )


def summarize_scoring_readiness(
    stages: list[AnalysisStageSummary],
    *,
    warning_count: int = 0,
    missing_field_count: int = 0,
) -> dict[str, Any]:
    """Summarize which analysis outputs are available for downstream scoring."""
    successful_stages = {stage.stage for stage in stages if stage.status == AnalysisStatus.SUCCESS}
    stage_lookup = {stage.stage: stage for stage in stages}
    demand_inputs = all(
        stage_lookup.get(stage_type) is not None and stage_lookup[stage_type].status == AnalysisStatus.SUCCESS
        for stage_type in _SCORING_INTERFACE_REQUIREMENTS["demand_scoring"]
    )
    readiness: dict[str, Any] = {
        "demand_inputs": demand_inputs,
        "competition_inputs": AnalysisTaskType.COMPETITOR_PROFILE in successful_stages,
        "saturation_inputs": AnalysisTaskType.SATURATION in successful_stages,
        "review_signals": AnalysisTaskType.REVIEW_ANALYSIS in successful_stages,
        "intent_signals": AnalysisTaskType.INTENT_CLASSIFICATION in successful_stages,
        "seller_strength": AnalysisTaskType.SELLER_STRENGTH in successful_stages,
        "gig_quality": AnalysisTaskType.GIG_QUALITY in successful_stages,
    }
    readiness["available_count"] = sum(1 for value in readiness.values() if bool(value))
    readiness["total_expected"] = 7
    readiness["contracts"] = _SCORING_CONTRACT_FIELDS
    readiness["contract_signal_counts"] = {
        "warning_count": warning_count,
        "missing_field_count": missing_field_count,
    }
    readiness["interfaces"] = {
        interface_name: _summarize_scoring_interface(
            interface_name=interface_name,
            required_stages=required_stages,
            stage_lookup=stage_lookup,
            warning_count=warning_count,
            missing_field_count=missing_field_count,
        )
        for interface_name, required_stages in _SCORING_INTERFACE_REQUIREMENTS.items()
    }
    readiness["interface_statuses"] = {
        interface_name: interface_data["status"]
        for interface_name, interface_data in readiness["interfaces"].items()
    }
    readiness["stage_contract_statuses"] = {
        stage_type.value: _stage_contract_status(stage_lookup.get(stage_type))
        for stage_type in STAGE_EXECUTION_ORDER
    }
    return readiness


def _placeholder_status(*, signal_count: int, minimum_ready_signals: int = 1) -> str:
    """Map signal counts to deterministic placeholder readiness buckets."""
    if signal_count <= 0:
        return "empty"
    if signal_count < minimum_ready_signals:
        return "sparse"
    return "ready"


def _status_rank(status: str) -> int:
    try:
        return _PLACEHOLDER_STATUS_ORDER.index(status)
    except ValueError:
        return 0


def _stage_contract_status(stage: AnalysisStageSummary | None) -> str:
    if stage is None:
        return "empty"
    if stage.status == AnalysisStatus.FAILED:
        return "blocked"
    readiness_contract = stage.metadata.get("readiness_contract")
    if isinstance(readiness_contract, dict):
        contract_status = readiness_contract.get("status")
        if isinstance(contract_status, str) and contract_status in _PLACEHOLDER_STATUS_ORDER:
            return contract_status
    stage_status = stage.metadata.get("stage_status")
    if isinstance(stage_status, str) and stage_status in _PLACEHOLDER_STATUS_ORDER:
        return stage_status
    return "ready" if stage.status == AnalysisStatus.SUCCESS else "blocked"


def _summarize_scoring_interface(
    *,
    interface_name: str,
    required_stages: tuple[AnalysisTaskType, ...],
    stage_lookup: dict[AnalysisTaskType, AnalysisStageSummary],
    warning_count: int,
    missing_field_count: int,
) -> dict[str, Any]:
    stage_details: list[dict[str, Any]] = []
    blocked_reasons: list[str] = []
    statuses: list[str] = []
    available_stage_count = 0
    for stage_type in required_stages:
        stage = stage_lookup.get(stage_type)
        if stage is not None:
            available_stage_count += 1
        stage_status = _stage_contract_status(stage)
        statuses.append(stage_status)
        if stage_status != "ready":
            blocked_reasons.append(f"{stage_type.value}:{stage_status}")
        stage_details.append(
            {
                "stage": stage_type.value,
                "present": stage is not None,
                "status": stage_status,
            }
        )
    if not statuses:
        interface_status = "empty"
    elif any(status == "blocked" for status in statuses):
        interface_status = "blocked"
    elif all(status == "empty" for status in statuses):
        interface_status = "empty"
    elif all(status == "ready" for status in statuses):
        interface_status = "ready"
    else:
        interface_status = "sparse"

    if interface_name == "confidence_scoring":
        if warning_count > 6 or missing_field_count > 8:
            interface_status = "blocked"
            blocked_reasons.append("run_signal_counts:blocked")
        elif (
            warning_count > 2 or missing_field_count > 3
        ) and _status_rank(interface_status) > _status_rank("sparse"):
            interface_status = "sparse"
            blocked_reasons.append("run_signal_counts:sparse")

    return {
        "status": interface_status,
        "ready_for_scoring": interface_status == "ready",
        "required_stage_count": len(required_stages),
        "available_stage_count": available_stage_count,
        "required_stages": [stage_type.value for stage_type in required_stages],
        "required_contract_fields": list(_SCORING_CONTRACT_FIELDS.get(interface_name, ())),
        "stage_details": stage_details,
        "blocking_reasons": blocked_reasons,
    }


def _placeholder_summary(
    *,
    stage: str,
    status: str,
    explanation: str,
    source_availability: dict[str, bool],
    warning_count: int,
    missing_fields: list[str],
    future_contract_fields: list[str],
    **extra: Any,
) -> dict[str, Any]:
    """Produce stable stage-level readiness metadata for downstream integration."""
    normalized_status = status if status in _PLACEHOLDER_STATUS_ORDER else "blocked"
    summary: dict[str, Any] = {
        "stage": stage,
        "status": normalized_status,
        "stage_status": normalized_status,
        "source_availability": source_availability,
        "warning_count": warning_count,
        "missing_field_count": len(missing_fields),
        "missing_fields": missing_fields,
        "explanation": explanation,
        "future_contract_fields": future_contract_fields,
    }
    if extra:
        summary.update(extra)
    return summary


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _coerce_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        try:
            return int(float(normalized))
        except ValueError:
            return None
    return None


def _coerce_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        try:
            return float(normalized)
        except ValueError:
            return None
    return None


def _coerce_gig_input_fields(
    gig_payload: dict[str, Any], *, source_id: str
) -> tuple[dict[str, Any], list[AnalysisWarning]]:
    warnings: list[AnalysisWarning] = []
    normalized = dict(gig_payload)
    numeric_fields: dict[str, str] = {
        "package_count": "int",
        "review_count": "int",
        "image_count": "int",
        "rating": "float",
    }
    for field_name, field_type in numeric_fields.items():
        raw_value = gig_payload.get(field_name)
        coerced_value = _coerce_int(raw_value) if field_type == "int" else _coerce_float(raw_value)
        if raw_value is not None and coerced_value is None:
            warnings.append(
                AnalysisWarning(
                    code="gig_numeric_field_invalid",
                    message=f"gig.{field_name} was malformed and replaced with null-safe fallback.",
                    source_id=source_id,
                    missing_data_fields=[field_name],
                    metadata={"field": field_name, "raw_value": str(raw_value)},
                )
            )
        normalized[field_name] = coerced_value
    return normalized, warnings


def _compute_intent_selection_contract(
    payload: dict[str, Any], source_id: str, selection: _IntentKeywordSelection
) -> dict[str, Any]:
    """Expose deterministic intent keyword selection contract for future scoring stages."""
    missing_input_warnings: list[str] = []
    intent_section = payload.get("intent")
    intent_keyword_present = isinstance(intent_section, dict) and (
        _non_empty_text_or_none(intent_section.get("keyword_text")) is not None
    )
    payload_keyword_present = _non_empty_text_or_none(payload.get("keyword_text")) is not None
    keyword_array_present = any(
        _non_empty_text_or_none(keyword) is not None for keyword in _as_list(payload.get("keywords"))
    )

    if not intent_keyword_present:
        missing_input_warnings.append("intent.keyword_text_missing")
    if not payload_keyword_present:
        missing_input_warnings.append("keyword_text_missing")
    if not keyword_array_present:
        missing_input_warnings.append("keywords_array_missing")
    if selection.selection_reason == "source_id_fallback":
        missing_input_warnings.append("source_id_fallback_used")
    if (
        not intent_keyword_present
        and not payload_keyword_present
        and not keyword_array_present
        and _non_empty_text_or_none(source_id) is not None
    ):
        missing_input_warnings.append("all_keyword_sources_missing")

    confidence_bucket = (
        "high"
        if selection.selection_confidence >= 0.9
        else "medium"
        if selection.selection_confidence >= 0.75
        else "low"
    )
    return {
        "selected_keyword": selection.keyword_text,
        "selection_reason": selection.selection_reason,
        "selection_confidence": selection.selection_confidence,
        "confidence_bucket": confidence_bucket,
        "missing_input_warnings": missing_input_warnings,
    }


def _keyword_clustering_placeholder_summary(
    *, keyword_input_count: int, keyword_result_count: int, warning_count: int, missing_fields: list[str]
) -> dict[str, Any]:
    minimum_keywords_for_ready = 2
    blocking_reasons: list[str] = []
    if keyword_input_count <= 0:
        status = "empty"
        blocking_reasons.append("keywords_missing")
    elif keyword_input_count < minimum_keywords_for_ready:
        status = "sparse"
        blocking_reasons.append("keywords_sparse")
    elif keyword_result_count <= 0:
        status = "blocked"
        blocking_reasons.append("cluster_output_empty")
    else:
        status = "ready"
    explanation = {
        "empty": "Keyword clustering readiness is empty because no source keywords were provided.",
        "sparse": "Keyword clustering readiness is sparse because too few keywords were provided.",
        "blocked": "Keyword clustering readiness is blocked because cluster outputs were unavailable.",
        "ready": "Keyword clustering readiness is valid for downstream scoring contracts.",
    }[status]
    return _placeholder_summary(
        stage=AnalysisTaskType.KEYWORD_CLUSTERING.value,
        status=status,
        explanation=explanation,
        source_availability={
            "keywords": keyword_input_count > 0,
            "cluster_outputs": keyword_result_count > 0,
        },
        warning_count=warning_count,
        missing_fields=missing_fields,
        future_contract_fields=[
            "cluster_id",
            "label",
            "member_count",
            "confidence",
            "source_keywords",
        ],
        keyword_input_count=keyword_input_count,
        minimum_keywords_for_ready=minimum_keywords_for_ready,
        cluster_count=keyword_result_count,
        blocking_reasons=blocking_reasons,
        downstream_scoring_status="ready_for_demand_scoring" if status == "ready" else "blocked_for_demand_scoring",
    )


def _gig_quality_placeholder_summary(
    *, gig_data: Any, warning_count: int
) -> dict[str, Any]:
    gig = _as_dict(gig_data)
    required_fields = ("title", "description", "package_count", "rating", "review_count")
    title_present = _non_empty_text_or_none(gig.get("title")) is not None
    description_present = _non_empty_text_or_none(gig.get("description")) is not None
    package_count = gig.get("package_count")
    packages_present = isinstance(package_count, int) and package_count > 0
    rating_present = isinstance(gig.get("rating"), (int | float))
    review_count_value = gig.get("review_count")
    review_count_present = isinstance(review_count_value, int) and review_count_value >= 0
    signal_count = sum([title_present, description_present, packages_present, rating_present, review_count_present])
    completeness = signal_count / len(required_fields)
    missing_fields = [
        field_name
        for field_name, present in (
            ("title", title_present),
            ("description", description_present),
            ("package_count", packages_present),
            ("rating", rating_present),
            ("review_count", review_count_present),
        )
        if not present
    ]
    status = _placeholder_status(signal_count=signal_count, minimum_ready_signals=len(required_fields))
    if not isinstance(gig_data, dict) and gig_data is not None:
        status = "blocked"
        missing_fields.append("gig_fixture_malformed")
    source_counts = {
        "gig_records": 1 if isinstance(gig_data, dict) else 0,
        "required_fields_present": len(required_fields)
        - len([field_name for field_name in missing_fields if field_name in required_fields]),
        "required_fields_expected": len(required_fields),
    }
    return _placeholder_summary(
        stage=AnalysisTaskType.GIG_QUALITY.value,
        status=status,
        explanation=(
            "Gig fixture malformed; quality scoring readiness is blocked."
            if status == "blocked"
            else "Gig quality placeholder summarizes deterministic completeness only."
        ),
        source_availability={
            "gig": isinstance(gig_data, dict),
            "title": title_present,
            "description": description_present,
            "package_count": packages_present,
        },
        warning_count=warning_count,
        missing_fields=missing_fields,
        future_contract_fields=[
            "title_completeness",
            "description_completeness",
            "package_completeness",
            "quality_rubric_ready",
        ],
        required_fields=list(required_fields),
        source_counts=source_counts,
        downstream_scoring_status=(
            "ready_for_competition_scoring" if status == "ready" else "blocked_for_competition_scoring"
        ),
        completeness_ratio=round(completeness, 3),
    )


def _competitor_placeholder_summary(
    *, competitor_rows: Any, warning_count: int, missing_fields: list[str]
) -> dict[str, Any]:
    raw_rows = _as_list(competitor_rows)
    competitors = [entry for entry in raw_rows if isinstance(entry, dict)]
    missing_seller_context_count = 0
    weakness_signal_available = False
    price_signal_count = 0
    rating_signal_count = 0
    for row in competitors:
        if not _non_empty_text_or_none(row.get("seller_level")):
            missing_seller_context_count += 1
        if isinstance(row.get("starting_price"), (int | float)):
            price_signal_count += 1
        if isinstance(row.get("rating"), (int | float)):
            rating_signal_count += 1
        rating = row.get("rating")
        review_count = row.get("review_count")
        if isinstance(rating, (int | float)) and rating <= 4.3 and isinstance(review_count, int) and review_count <= 30:
            weakness_signal_available = True
    minimum_competitors_for_ready = 3
    context_complete_count = len(competitors) - missing_seller_context_count
    if len(competitors) <= 0:
        status = "empty"
    elif len(competitors) < minimum_competitors_for_ready or context_complete_count <= 0:
        status = "sparse"
    else:
        status = "ready"
    warning_hints: list[str] = []
    if missing_seller_context_count > 0:
        warning_hints.append("seller_context_missing")
    if price_signal_count <= 0:
        warning_hints.append("starting_price_missing")
    if rating_signal_count <= 0:
        warning_hints.append("rating_missing")
    return _placeholder_summary(
        stage=AnalysisTaskType.COMPETITOR_PROFILE.value,
        status=status,
        explanation=(
            "Competitor profiling placeholder is sparse; upstream seller context is limited."
            if status != "ready"
            else "Competitor profiling placeholder is ready for deterministic competition signals."
        ),
        source_availability={
            "competitors": bool(competitors),
            "seller_context": missing_seller_context_count < len(competitors) if competitors else False,
            "weakness_signals": weakness_signal_available,
        },
        warning_count=warning_count,
        missing_fields=missing_fields,
        future_contract_fields=[
            "competitor_count",
            "missing_seller_context_count",
            "weakness_signal_available",
        ],
        minimum_competitors_for_ready=minimum_competitors_for_ready,
        source_counts={
            "raw_row_count": len(raw_rows),
            "valid_competitor_count": len(competitors),
            "seller_context_count": context_complete_count,
            "price_signal_count": price_signal_count,
            "rating_signal_count": rating_signal_count,
        },
        confidence_estimate=round(min(1.0, len(competitors) / 5.0), 3) if competitors else 0.0,
        warning_hints=warning_hints,
        competition_scoring_relation=(
            "ready_for_competition_scoring"
            if status == "ready"
            else "blocked_for_competition_scoring"
        ),
        competitor_count=len(competitors),
        missing_seller_context_count=missing_seller_context_count,
        weakness_signal_available=weakness_signal_available,
    )


def _seller_strength_placeholder_summary(*, seller_source: Any, warning_count: int) -> dict[str, Any]:
    seller = _as_dict(seller_source)
    required_fields = ("seller_id", "level", "rating", "review_count", "response_time")
    available_fields = [
        field_name
        for field_name in required_fields
        if (
            _non_empty_text_or_none(seller.get(field_name)) is not None
            if field_name in {"seller_id", "level", "response_time"}
            else seller.get(field_name) is not None
        )
    ]
    missing_fields = [field_name for field_name in required_fields if field_name not in available_fields]
    signal_count = len(available_fields)
    if signal_count == 0:
        status = "empty"
    elif signal_count < 4:
        status = "sparse"
    else:
        status = "ready"
    readiness_state = "usable_fixture" if status == "ready" else "sparse_profile_signals"
    if signal_count == 0:
        readiness_state = "missing_seller_data"
    if not isinstance(seller_source, dict) and seller_source is not None:
        status = "blocked"
        missing_fields.append("seller_fixture_malformed")
        readiness_state = "malformed_seller_data"
    return _placeholder_summary(
        stage=AnalysisTaskType.SELLER_STRENGTH.value,
        status=status,
        explanation=(
            "Seller strength scoring is blocked until required seller profile fields are available."
            if status in {"blocked", "empty"}
            else "Seller strength placeholder reflects deterministic profile-field readiness."
        ),
        source_availability={field_name: field_name in available_fields for field_name in required_fields},
        warning_count=warning_count,
        missing_fields=missing_fields,
        future_contract_fields=["available_fields", "missing_fields", "downstream_status"],
        available_fields=available_fields,
        required_fields=list(required_fields),
        source_counts={
            "seller_records": 1 if isinstance(seller_source, dict) else 0,
            "available_required_fields": signal_count,
            "required_field_count": len(required_fields),
        },
        readiness_state=readiness_state,
        downstream_status="ready_for_scoring" if status == "ready" else "blocked_for_scoring",
    )


def _saturation_placeholder_summary(
    *, keyword_count: int, competitor_count: int, gig_quality_count: int, warning_count: int
) -> dict[str, Any]:
    populated_signal_count = sum(1 for value in (keyword_count, competitor_count, gig_quality_count) if value > 0)
    if competitor_count == 0:
        status = "blocked"
        explanation = "Saturation readiness is blocked because competitor fixtures are unavailable."
    elif competitor_count == 1:
        status = "sparse"
        explanation = "Saturation readiness is sparse with only one competitor fixture."
    else:
        status = _placeholder_status(signal_count=populated_signal_count, minimum_ready_signals=3)
        explanation = (
            "Saturation readiness is ready with keyword, competitor, and quality signals."
            if status == "ready"
            else "Saturation readiness is sparse due to incomplete signal coverage."
        )
    missing_fields: list[str] = []
    if keyword_count <= 0:
        missing_fields.append("keyword_count")
    if competitor_count <= 0:
        missing_fields.append("competitor_count")
    if gig_quality_count <= 0:
        missing_fields.append("gig_quality_scores")
    evidence_fields = {
        "minimum_competitors_for_sparse": 1,
        "minimum_competitors_for_ready": 2,
        "coverage_ratio": round(populated_signal_count / 3.0, 3),
    }
    return _placeholder_summary(
        stage=AnalysisTaskType.SATURATION.value,
        status=status,
        explanation=explanation,
        source_availability={
            "keywords": keyword_count > 0,
            "competitors": competitor_count > 0,
            "gig_quality_scores": gig_quality_count > 0,
        },
        warning_count=warning_count,
        missing_fields=missing_fields,
        future_contract_fields=["keyword_count", "competitor_count", "gig_quality_scores", "signal_counts"],
        signal_counts={
            "keyword_count": keyword_count,
            "competitor_count": competitor_count,
            "gig_quality_count": gig_quality_count,
        },
        evidence_fields=evidence_fields,
        downstream_scoring_status=(
            "ready_for_opportunity_scoring" if status == "ready" else "blocked_for_opportunity_scoring"
        ),
    )


def _review_placeholder_summary(
    *, reviews_source: Any, warning_count: int, missing_fields: list[str]
) -> dict[str, Any]:
    if not isinstance(reviews_source, list):
        status = "blocked"
        explanation = "Review analysis readiness is blocked because review fixtures are unsupported."
        review_count = 0
        source_availability = {
            "reviews": False,
            "review_snippets": False,
            "supported_review_payload": False,
        }
        normalized_missing_fields = list(dict.fromkeys([*missing_fields, "reviews_unsupported"]))
    else:
        review_count = len(reviews_source)
        if review_count <= 0:
            status = "empty"
            explanation = "Review analysis readiness is empty because no review fixtures were provided."
        elif review_count < 3:
            status = "sparse"
            explanation = "Review analysis readiness is sparse with limited review snippets."
        else:
            status = "ready"
            explanation = "Review analysis readiness is usable for deterministic theme extraction."
        source_availability = {
            "reviews": review_count > 0,
            "review_snippets": review_count >= 3,
            "supported_review_payload": True,
        }
        normalized_missing_fields = missing_fields
    return _placeholder_summary(
        stage=AnalysisTaskType.REVIEW_ANALYSIS.value,
        status=status,
        explanation=explanation,
        source_availability=source_availability,
        warning_count=warning_count,
        missing_fields=normalized_missing_fields,
        future_contract_fields=["review_count", "warning_count", "theme_count", "unsupported_state"],
        review_count=review_count,
        downstream_scoring_status=(
            "ready_for_trend_and_conversion_scoring"
            if status == "ready"
            else "blocked_for_trend_and_conversion_scoring"
        ),
    )


def _review_stage_for_unsupported_payload(
    *, source_id: str, reviews_payload: Any
) -> tuple[AnalysisStageSummary, AnalysisWarning]:
    warning = AnalysisWarning(
        code="reviews_fixture_unsupported",
        message="reviews payload must be a list for deterministic review analysis.",
        source_id=source_id,
        missing_data_fields=["reviews"],
        metadata={"payload_type": type(reviews_payload).__name__},
    )
    review_placeholder = _review_placeholder_summary(
        reviews_source=reviews_payload,
        warning_count=1,
        missing_fields=["reviews"],
    )
    stage = AnalysisStageSummary(
        stage=AnalysisTaskType.REVIEW_ANALYSIS,
        status=AnalysisStatus.SUCCESS,
        warnings=[warning],
        result_type="review_analysis",
        metadata=_stage_metadata(
            source_id,
            result_count=0,
            warning_count=1,
            missing_field_count=len(review_placeholder["missing_fields"]),
            theme_count=0,
            complaint_theme_count=0,
            stage_status=review_placeholder["status"],
            source_availability=review_placeholder["source_availability"],
            explanation=review_placeholder["explanation"],
            readiness_contract=review_placeholder,
        ),
    )
    return stage, warning


def _non_empty_text_or_none(value: Any) -> str | None:
    """Return text only when value is present and not blank."""
    if value is None:
        return None
    text = value if isinstance(value, str) else str(value)
    normalized = text.strip().lower()
    if not normalized:
        return None
    if normalized in {"none", "null"}:
        return None
    return text


def _resolve_intent_keyword_selection(
    payload: dict[str, Any], source_id: str
) -> _IntentKeywordSelection:
    """Resolve keyword text with explicit null/blank fallback handling."""
    intent_section = payload.get("intent", {})
    if isinstance(intent_section, dict):
        intent_keyword = _non_empty_text_or_none(intent_section.get("keyword_text"))
        if intent_keyword is not None:
            return _IntentKeywordSelection(
                keyword_text=intent_keyword,
                selection_reason="explicit_intent_keyword",
                selection_confidence=_INTENT_SELECTION_CONFIDENCE["explicit_intent_keyword"],
            )

    payload_keyword = _non_empty_text_or_none(payload.get("keyword_text"))
    if payload_keyword is not None:
        return _IntentKeywordSelection(
            keyword_text=payload_keyword,
            selection_reason="top_level_keyword_text",
            selection_confidence=_INTENT_SELECTION_CONFIDENCE["top_level_keyword_text"],
        )

    keywords_section = payload.get("keywords")
    if isinstance(keywords_section, list):
        for keyword in keywords_section:
            candidate = _non_empty_text_or_none(keyword)
            if candidate is not None:
                return _IntentKeywordSelection(
                    keyword_text=candidate,
                    selection_reason="keywords_first_entry",
                    selection_confidence=_INTENT_SELECTION_CONFIDENCE["keywords_first_entry"],
                )

    # Preserve source_id fallback so intent classification still receives a stable key.
    return _IntentKeywordSelection(
        keyword_text=source_id,
        selection_reason="source_id_fallback",
        selection_confidence=_INTENT_SELECTION_CONFIDENCE["source_id_fallback"],
    )


def _normalize_collection_evidence(
    evidence_input: Any, *, source_id: str
) -> tuple[dict[str, Any] | None, list[AnalysisWarning]]:
    """Normalize optional upstream collection evidence with warning-safe fallback."""
    if evidence_input is None:
        return None, []

    if not isinstance(evidence_input, dict):
        return None, [
            AnalysisWarning(
                code="collection_evidence_invalid",
                message="collection_evidence must be a dictionary when provided.",
                source_id=source_id,
                metadata={"reason": "invalid_type", "type": type(evidence_input).__name__},
            )
        ]

    warnings: list[AnalysisWarning] = []
    normalized: dict[str, Any] = {
        "source_stage_names": [],
        "fixture_mode": None,
        "records_seen": 0,
        "records_written": 0,
        "warnings": [],
        "warning_count": 0,
    }

    source_stages = evidence_input.get("source_stage_names", [])
    if isinstance(source_stages, list):
        normalized["source_stage_names"] = [
            stage_name.strip()
            for stage_name in source_stages
            if isinstance(stage_name, str) and stage_name.strip()
        ]
    else:
        warnings.append(
            AnalysisWarning(
                code="collection_evidence_invalid",
                message="collection_evidence.source_stage_names must be a list.",
                source_id=source_id,
                metadata={"reason": "source_stage_names_not_list"},
            )
        )

    fixture_mode = evidence_input.get("fixture_mode")
    if fixture_mode is None or isinstance(fixture_mode, bool | str):
        normalized["fixture_mode"] = fixture_mode
    else:
        warnings.append(
            AnalysisWarning(
                code="collection_evidence_invalid",
                message="collection_evidence.fixture_mode must be bool or string.",
                source_id=source_id,
                metadata={"reason": "fixture_mode_invalid_type"},
            )
        )

    for field_name in ("records_seen", "records_written"):
        raw_value = evidence_input.get(field_name, 0)
        if isinstance(raw_value, int) and raw_value >= 0:
            normalized[field_name] = raw_value
        else:
            warnings.append(
                AnalysisWarning(
                    code="collection_evidence_invalid",
                    message=f"collection_evidence.{field_name} must be a non-negative integer.",
                    source_id=source_id,
                    metadata={"reason": f"{field_name}_invalid"},
                )
            )

    evidence_warnings = evidence_input.get("warnings", [])
    if isinstance(evidence_warnings, list):
        normalized_warnings = [
            warning_value.strip()
            for warning_value in evidence_warnings
            if isinstance(warning_value, str) and warning_value.strip()
        ]
        normalized["warnings"] = normalized_warnings
        normalized["warning_count"] = len(normalized_warnings)
    elif isinstance(evidence_warnings, int) and evidence_warnings >= 0:
        normalized["warning_count"] = evidence_warnings
    else:
        warnings.append(
            AnalysisWarning(
                code="collection_evidence_invalid",
                message="collection_evidence.warnings must be a list or non-negative integer.",
                source_id=source_id,
                metadata={"reason": "warnings_invalid_type"},
            )
        )

    return normalized, warnings


def run_analysis_dry_run(payload: dict[str, Any]) -> AnalysisRunSummary:
    """
    Execute local deterministic analysis stages.

    This orchestrator intentionally performs no network calls and no persistence.
    """
    started_at = datetime.now(UTC)
    if not isinstance(payload, dict):
        finished_at = datetime.now(UTC)
        return AnalysisRunSummary(
            run_id="analysis-dry-run",
            source_id="analysis-dry-run",
            started_at=started_at,
            finished_at=finished_at,
            status=AnalysisStatus.FAILED,
            stages=[],
            warnings=[],
            metadata={
                "executed_stage_count": 0,
                "success_stage_count": 0,
                "failed_stage_count": 0,
                "invalid_input": True,
                "invalid_input_type": type(payload).__name__,
                "scoring_readiness": summarize_scoring_readiness([]),
            },
        )

    run_id = str(payload.get("run_id", "analysis-dry-run"))
    source_id = _non_empty_text_or_none(payload.get("source_id")) or "analysis-dry-run"

    stages: list[AnalysisStageSummary] = []
    all_warnings: list[AnalysisWarning] = []

    metadata = payload.get("metadata", {})
    metadata_dict = metadata if isinstance(metadata, dict) else {}
    collection_evidence, collection_evidence_warnings = _normalize_collection_evidence(
        payload.get("collection_evidence"),
        source_id=source_id,
    )
    seller_strength_scores: list[float] = []
    gig_quality_scores: list[float] = []

    if "keywords" in payload:
        stage_started_at = datetime.now(UTC)
        try:
            keyword_input = KeywordClusterInput.model_validate(
                {
                    "source_id": source_id,
                    "keywords": payload.get("keywords", []),
                    "min_cluster_size": payload.get("min_cluster_size", 1),
                    "metadata": metadata_dict,
                }
            )
            keyword_result = cluster_keywords(keyword_input)
            keyword_placeholder = _keyword_clustering_placeholder_summary(
                keyword_input_count=len(keyword_input.keywords),
                keyword_result_count=len(keyword_result.clusters),
                warning_count=len(keyword_result.warnings),
                missing_fields=list(keyword_result.missing_data_fields),
            )
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.KEYWORD_CLUSTERING,
                    status=AnalysisStatus.SUCCESS,
                    warnings=keyword_result.warnings,
                    result_type="keyword_clustering",
                    metadata=_with_stage_timing(
                        _stage_metadata(
                            source_id,
                            result_count=len(keyword_result.clusters),
                            warning_count=len(keyword_result.warnings),
                            missing_field_count=len(keyword_result.missing_data_fields),
                            cluster_count=len(keyword_result.clusters),
                            unclustered_count=len(keyword_result.unclustered_keywords),
                            cluster_metrics=keyword_result.cluster_metrics,
                            top_cluster_labels=[cluster.label for cluster in keyword_result.clusters[:3]],
                            stage_status=keyword_placeholder["status"],
                            source_availability=keyword_placeholder["source_availability"],
                            explanation=keyword_placeholder["explanation"],
                            readiness_contract=keyword_placeholder,
                        ),
                        started_at=stage_started_at,
                    ),
                )
            )
            all_warnings.extend(keyword_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                _failed_stage_summary(
                    stage=AnalysisTaskType.KEYWORD_CLUSTERING,
                    source_id=source_id,
                    code="keyword_stage_failed",
                    exc=exc,
                )
            )

    if "gig" in payload:
        stage_started_at = datetime.now(UTC)
        try:
            gig_payload = payload.get("gig")
            if not isinstance(gig_payload, dict):
                gig_placeholder = _gig_quality_placeholder_summary(
                    gig_data=gig_payload,
                    warning_count=1,
                )
                malformed_warning = AnalysisWarning(
                    code="gig_fixture_malformed",
                    message="gig payload must be a dictionary for rubric scoring.",
                    source_id=source_id,
                    missing_data_fields=["gig"],
                )
                stages.append(
                    AnalysisStageSummary(
                        stage=AnalysisTaskType.GIG_QUALITY,
                        status=AnalysisStatus.SUCCESS,
                        warnings=[malformed_warning],
                        result_type="gig_quality",
                        metadata=_with_stage_timing(
                            _stage_metadata(
                                source_id,
                                result_count=0,
                                warning_count=1,
                                missing_field_count=len(gig_placeholder["missing_fields"]),
                                strength_count=0,
                                weakness_count=0,
                                stage_status=gig_placeholder["status"],
                                source_availability=gig_placeholder["source_availability"],
                                explanation=gig_placeholder["explanation"],
                                readiness_contract=gig_placeholder,
                            ),
                            started_at=stage_started_at,
                        ),
                    )
                )
                all_warnings.append(malformed_warning)
            else:
                normalized_gig_payload, gig_input_warnings = _coerce_gig_input_fields(
                    gig_payload,
                    source_id=source_id,
                )
                gig_input = GigQualityInput.model_validate(
                    {
                        "source_id": source_id,
                        "gig_id": normalized_gig_payload.get("gig_id", "dry-run-gig"),
                        "title": normalized_gig_payload.get("title"),
                        "description": normalized_gig_payload.get("description"),
                        "package_count": normalized_gig_payload.get("package_count"),
                        "rating": normalized_gig_payload.get("rating"),
                        "review_count": normalized_gig_payload.get("review_count"),
                        "image_count": normalized_gig_payload.get("image_count"),
                        "has_faq": normalized_gig_payload.get("has_faq"),
                        "metadata": metadata_dict,
                    }
                )
                gig_result = score_gig_quality(gig_input)
                gig_stage_warnings = [*gig_result.warnings, *gig_input_warnings]
                gig_quality_scores.append(gig_result.overall_score)
                gig_placeholder = _gig_quality_placeholder_summary(
                    gig_data=normalized_gig_payload,
                    warning_count=len(gig_stage_warnings),
                )
                stages.append(
                    AnalysisStageSummary(
                        stage=AnalysisTaskType.GIG_QUALITY,
                        status=AnalysisStatus.SUCCESS,
                        warnings=gig_stage_warnings,
                        result_type="gig_quality",
                        metadata=_with_stage_timing(
                            _stage_metadata(
                                source_id,
                                result_count=1,
                                warning_count=len(gig_stage_warnings),
                                missing_field_count=len(gig_result.missing_data_fields),
                                strength_count=len(gig_result.strengths),
                                weakness_count=len(gig_result.weaknesses),
                                stage_status=gig_placeholder["status"],
                                source_availability=gig_placeholder["source_availability"],
                                explanation=gig_placeholder["explanation"],
                                readiness_contract=gig_placeholder,
                            ),
                            started_at=stage_started_at,
                        ),
                    )
                )
                all_warnings.extend(gig_stage_warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                _failed_stage_summary(
                    stage=AnalysisTaskType.GIG_QUALITY,
                    source_id=source_id,
                    code="gig_stage_failed",
                    exc=exc,
                )
            )

    if "competitors" in payload:
        stage_started_at = datetime.now(UTC)
        try:
            competitors_payload = payload.get("competitors")
            if not isinstance(competitors_payload, list):
                raise ValueError("competitors must be a list.")
            competitor_input = CompetitorProfileInput.model_validate(
                {
                    "source_id": source_id,
                    "competitors": competitors_payload,
                    "metadata": metadata_dict,
                }
            )
            competitor_result = profile_competitors(competitor_input)
            competitor_placeholder = _competitor_placeholder_summary(
                competitor_rows=competitors_payload,
                warning_count=len(competitor_result.warnings),
                missing_fields=list(competitor_result.missing_data_fields),
            )
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.COMPETITOR_PROFILE,
                    status=AnalysisStatus.SUCCESS,
                    warnings=competitor_result.warnings,
                    result_type="competitor_profile",
                    metadata=_with_stage_timing(
                        _stage_metadata(
                            source_id,
                            result_count=len(competitor_input.competitors),
                            warning_count=len(competitor_result.warnings),
                            missing_field_count=len(competitor_result.missing_data_fields),
                            competitor_count=len(competitor_input.competitors),
                            high_authority_count=len(competitor_result.high_authority_sellers),
                            stage_status=competitor_placeholder["status"],
                            source_availability=competitor_placeholder["source_availability"],
                            explanation=competitor_placeholder["explanation"],
                            readiness_contract=competitor_placeholder,
                        ),
                        started_at=stage_started_at,
                    ),
                )
            )
            all_warnings.extend(competitor_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                _failed_stage_summary(
                    stage=AnalysisTaskType.COMPETITOR_PROFILE,
                    source_id=source_id,
                    code="competitor_stage_failed",
                    exc=exc,
                )
            )

    if "seller" in payload or "sellers" in payload:
        stage_started_at = datetime.now(UTC)
        try:
            seller_rows = payload.get("sellers")
            if isinstance(seller_rows, list) and seller_rows:
                seller_source = seller_rows[0]
            else:
                seller_source = payload.get("seller", {})
            if not isinstance(seller_source, dict):
                raise ValueError("seller must be a dictionary.")
            seller_input = SellerStrengthInput.model_validate(
                {
                    "source_id": source_id,
                    "seller_id": cast(dict[str, Any], seller_source).get("seller_id", "seller-dry-run"),
                    "level": cast(dict[str, Any], seller_source).get("level"),
                    "rating": cast(dict[str, Any], seller_source).get("rating"),
                    "review_count": cast(dict[str, Any], seller_source).get("review_count"),
                    "response_time": cast(dict[str, Any], seller_source).get("response_time"),
                    "delivery_consistency": cast(dict[str, Any], seller_source).get("delivery_consistency"),
                    "active_gig_count": cast(dict[str, Any], seller_source).get("active_gig_count"),
                    "languages": cast(dict[str, Any], seller_source).get("languages", []),
                    "account_tenure_months": cast(dict[str, Any], seller_source).get("account_tenure_months"),
                    "metadata": metadata_dict,
                }
            )
            seller_result = score_seller_strength(seller_input)
            seller_strength_scores.append(seller_result.score)
            if isinstance(seller_rows, list):
                for entry in seller_rows[1:]:
                    try:
                        additional_input = SellerStrengthInput.model_validate(
                            {
                                "source_id": source_id,
                                "seller_id": entry.get("seller_id", "seller-dry-run"),
                                "level": entry.get("level"),
                                "rating": entry.get("rating"),
                                "review_count": entry.get("review_count"),
                                "response_time": entry.get("response_time"),
                                "delivery_consistency": entry.get("delivery_consistency"),
                                "active_gig_count": entry.get("active_gig_count"),
                                "languages": entry.get("languages", []),
                                "account_tenure_months": entry.get("account_tenure_months"),
                                "metadata": metadata_dict,
                            }
                        )
                        seller_strength_scores.append(score_seller_strength(additional_input).score)
                    except ValidationError:
                        continue
            seller_placeholder = _seller_strength_placeholder_summary(
                seller_source=seller_source,
                warning_count=len(seller_result.warnings),
            )
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.SELLER_STRENGTH,
                    status=AnalysisStatus.SUCCESS,
                    warnings=seller_result.warnings,
                    result_type="seller_strength",
                    metadata=_with_stage_timing(
                        _stage_metadata(
                            source_id,
                            result_count=len(seller_strength_scores),
                            warning_count=len(seller_result.warnings),
                            missing_field_count=len(seller_result.missing_data_fields),
                            evaluated_sellers=len(seller_strength_scores),
                            component_count=len(seller_result.components),
                            stage_status=seller_placeholder["status"],
                            source_availability=seller_placeholder["source_availability"],
                            explanation=seller_placeholder["explanation"],
                            readiness_contract=seller_placeholder,
                        ),
                        started_at=stage_started_at,
                    ),
                )
            )
            all_warnings.extend(seller_result.warnings)
        except (ValidationError, ValueError, AttributeError) as exc:
            stages.append(
                _failed_stage_summary(
                    stage=AnalysisTaskType.SELLER_STRENGTH,
                    source_id=source_id,
                    code="seller_strength_stage_failed",
                    exc=exc,
                )
            )

    saturation_trigger_keys = {
        "keywords",
        "search_result_count",
        "competitors",
        "prices",
        "gig_quality_scores",
        "seller",
        "sellers",
    }
    if any(key in payload for key in saturation_trigger_keys):
        stage_started_at = datetime.now(UTC)
        try:
            prices = [float(price) for price in payload.get("prices", []) if isinstance(price, (int | float))]
            if not prices and isinstance(payload.get("competitors"), list):
                prices = [
                    float(entry["starting_price"])
                    for entry in payload.get("competitors", [])
                    if isinstance(entry, dict) and isinstance(entry.get("starting_price"), (int | float))
                ]
            input_quality_scores = payload.get("gig_quality_scores", [])
            if isinstance(input_quality_scores, list):
                gig_quality_scores.extend(
                    [float(score) for score in input_quality_scores if isinstance(score, (int | float))]
                )
            saturation_input = SaturationInput.model_validate(
                {
                    "source_id": source_id,
                    "keyword_count": len(payload.get("keywords", []))
                    if isinstance(payload.get("keywords"), list)
                    else payload.get("keyword_count"),
                    "search_result_count": payload.get("search_result_count"),
                    "competitor_count": len(payload.get("competitors", []))
                    if isinstance(payload.get("competitors"), list)
                    else payload.get("competitor_count"),
                    "seller_strength_scores": seller_strength_scores,
                    "prices": prices,
                    "gig_quality_scores": gig_quality_scores,
                    "metadata": metadata_dict,
                }
            )
            saturation_result = analyze_saturation(saturation_input)
            saturation_placeholder = _saturation_placeholder_summary(
                keyword_count=(
                    len(payload.get("keywords", []))
                    if isinstance(payload.get("keywords"), list)
                    else 0
                ),
                competitor_count=(
                    len(payload.get("competitors", []))
                    if isinstance(payload.get("competitors"), list)
                    else 0
                ),
                gig_quality_count=len(gig_quality_scores),
                warning_count=len(saturation_result.warnings),
            )
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.SATURATION,
                    status=AnalysisStatus.SUCCESS,
                    warnings=saturation_result.warnings,
                    result_type="saturation",
                    metadata=_with_stage_timing(
                        _stage_metadata(
                            source_id,
                            result_count=len(saturation_result.components),
                            warning_count=len(saturation_result.warnings),
                            missing_field_count=len(saturation_result.missing_data_fields),
                            saturation_level=saturation_result.saturation_level.value,
                            component_count=len(saturation_result.components),
                            stage_status=saturation_placeholder["status"],
                            source_availability=saturation_placeholder["source_availability"],
                            explanation=saturation_placeholder["explanation"],
                            readiness_contract=saturation_placeholder,
                        ),
                        started_at=stage_started_at,
                    ),
                )
            )
            all_warnings.extend(saturation_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                _failed_stage_summary(
                    stage=AnalysisTaskType.SATURATION,
                    source_id=source_id,
                    code="saturation_stage_failed",
                    exc=exc,
                )
            )

    if "reviews" in payload:
        stage_started_at = datetime.now(UTC)
        try:
            reviews_payload = payload.get("reviews")
            if not isinstance(reviews_payload, list):
                unsupported_stage, unsupported_warning = _review_stage_for_unsupported_payload(
                    source_id=source_id,
                    reviews_payload=reviews_payload,
                )
                stages.append(unsupported_stage)
                all_warnings.append(unsupported_warning)
                reviews_payload = None
            if reviews_payload is None:
                pass
            else:
                review_input = ReviewAnalysisInput.model_validate(
                    {
                        "source_id": source_id,
                        "reviews": reviews_payload,
                        "metadata": metadata_dict,
                    }
                )
                review_result = analyze_reviews(review_input)
                review_placeholder = _review_placeholder_summary(
                    reviews_source=reviews_payload,
                    warning_count=len(review_result.warnings),
                    missing_fields=list(review_result.missing_data_fields),
                )
                stages.append(
                    AnalysisStageSummary(
                        stage=AnalysisTaskType.REVIEW_ANALYSIS,
                        status=AnalysisStatus.SUCCESS,
                        warnings=review_result.warnings,
                        result_type="review_analysis",
                        metadata=_with_stage_timing(
                            _stage_metadata(
                                source_id,
                                result_count=len(review_result.themes),
                                warning_count=len(review_result.warnings),
                                missing_field_count=len(review_result.missing_data_fields),
                                theme_count=len(review_result.themes),
                                complaint_theme_count=len(review_result.complaint_frequency),
                                stage_status=review_placeholder["status"],
                                source_availability=review_placeholder["source_availability"],
                                explanation=review_placeholder["explanation"],
                                readiness_contract=review_placeholder,
                            ),
                            started_at=stage_started_at,
                        ),
                    )
                )
                all_warnings.extend(review_result.warnings)
        except (ValidationError, ValueError, TypeError) as exc:
            stages.append(
                _failed_stage_summary(
                    stage=AnalysisTaskType.REVIEW_ANALYSIS,
                    source_id=source_id,
                    code="review_stage_failed",
                    exc=exc,
                )
            )

    if "intent" in payload or "keyword_text" in payload or "keywords" in payload:
        stage_started_at = datetime.now(UTC)
        try:
            intent_section = payload.get("intent", {})
            intent_selection = _resolve_intent_keyword_selection(payload, source_id)
            intent_selection_contract = _compute_intent_selection_contract(
                payload,
                source_id,
                intent_selection,
            )
            intent_metadata = {
                **metadata_dict,
                "intent_keyword_selection_reason": intent_selection.selection_reason,
                "intent_keyword_selection_confidence": intent_selection.selection_confidence,
                "intent_selection_contract": intent_selection_contract,
            }
            if isinstance(intent_section, dict) and "mock_label" in intent_section:
                intent_metadata["mock_label"] = intent_section.get("mock_label")
            if isinstance(intent_section, dict):
                keyword_text = intent_selection.keyword_text
                title_phrases = intent_section.get("title_phrases", [])
            else:
                keyword_text = intent_selection.keyword_text
                title_phrases = payload.get("title_phrases", [])
            intent_input = IntentInput.model_validate(
                {
                    "source_id": source_id,
                    "keyword_text": keyword_text,
                    "title_phrases": title_phrases,
                    "metadata": intent_metadata,
                }
            )
            intent_result = classify_intent(intent_input)
            stages.append(
                AnalysisStageSummary(
                    stage=AnalysisTaskType.INTENT_CLASSIFICATION,
                    status=AnalysisStatus.SUCCESS,
                    warnings=intent_result.warnings,
                    result_type="intent_classification",
                    metadata=_with_stage_timing(
                        _stage_metadata(
                            source_id,
                            result_count=len(intent_result.matched_rules),
                            warning_count=len(intent_result.warnings),
                            missing_field_count=len(intent_selection_contract["missing_input_warnings"]),
                            label=intent_result.label.value,
                            matched_rule_count=len(intent_result.matched_rules),
                            intent_keyword_selection_reason=intent_selection.selection_reason,
                            intent_keyword_selection_confidence=intent_selection.selection_confidence,
                            intent_selection_contract=intent_selection_contract,
                            stage_status=(
                                "ready"
                                if intent_selection_contract["selection_reason"] == "explicit_intent_keyword"
                                else "sparse"
                                if intent_selection_contract["selection_reason"] != "source_id_fallback"
                                else "blocked"
                            ),
                            source_availability={
                                "intent_keyword": "intent.keyword_text_missing"
                                not in intent_selection_contract["missing_input_warnings"],
                                "payload_keyword": "keyword_text_missing"
                                not in intent_selection_contract["missing_input_warnings"],
                                "keywords_array": "keywords_array_missing"
                                not in intent_selection_contract["missing_input_warnings"],
                            },
                            explanation=(
                                "Intent selection used source_id fallback; intent scoring remains blocked."
                                if intent_selection_contract["selection_reason"] == "source_id_fallback"
                                else "Intent selection contract captured deterministic fallback behavior."
                            ),
                        ),
                        started_at=stage_started_at,
                    ),
                )
            )
            all_warnings.extend(intent_result.warnings)
        except (ValidationError, ValueError) as exc:
            stages.append(
                _failed_stage_summary(
                    stage=AnalysisTaskType.INTENT_CLASSIFICATION,
                    source_id=source_id,
                    code="intent_stage_failed",
                    exc=exc,
                )
            )

    for stage in stages:
        stage_contract = stage.metadata.get("readiness_contract")
        if isinstance(stage_contract, dict):
            stage_status = stage_contract.get("status")
            if isinstance(stage_status, str):
                stage.readiness_status = _normalize_readiness_status(stage_status)
                stage.readiness_reasons = _readiness_reasons(stage_contract)
        elif stage.status == AnalysisStatus.FAILED:
            stage.readiness_status = AnalysisReadinessStatus.BLOCKED
        else:
            stage.readiness_status = AnalysisReadinessStatus.READY
        if "duration_ms" not in stage.metadata:
            stage.metadata["duration_ms"] = 0

    statuses = [stage.status for stage in stages]
    if statuses and all(status == AnalysisStatus.SUCCESS for status in statuses):
        run_status = AnalysisStatus.SUCCESS
    elif any(status == AnalysisStatus.SUCCESS for status in statuses):
        run_status = AnalysisStatus.PARTIAL
    else:
        run_status = AnalysisStatus.FAILED

    if collection_evidence_warnings:
        all_warnings.extend(collection_evidence_warnings)

    run_contract = _AnalysisRunContract.from_stages(
        stages=stages,
        warning_count=len(all_warnings),
    )

    run_metadata: dict[str, Any] = {
        "executed_stage_count": len(stages),
        "success_stage_count": sum(1 for stage in stages if stage.status == AnalysisStatus.SUCCESS),
        "failed_stage_count": sum(1 for stage in stages if stage.status == AnalysisStatus.FAILED),
        "stage_order": run_contract.stage_order,
        "successful_stages": run_contract.successful_stages,
        "failed_stages": run_contract.failed_stages,
        "skipped_stages": run_contract.skipped_stages,
        "warning_count": run_contract.warning_count,
        "missing_field_count": run_contract.missing_field_count,
        "scoring_readiness": run_contract.scoring_readiness,
        "stage_contracts": {
            stage.stage.value: stage.metadata.get("readiness_contract", {})
            for stage in stages
        },
        "stage_log_summary": [_stage_log_entry(stage) for stage in stages],
        "dashboard_handoff_contract": _build_dashboard_handoff_contract(stages),
        "stage_run_summary": _build_stage_run_summary(stages),
        "analysis_closure_matrix": _build_analysis_closure_matrix(stages),
        "normalized_warnings": [_normalized_warning_dict(warning) for warning in all_warnings],
        "analysis_output_registry": build_analysis_output_registry(
            AnalysisRunSummary(
                run_id=run_id,
                source_id=source_id,
                started_at=started_at,
                finished_at=datetime.now(UTC),
                status=run_status,
                stages=stages,
                warnings=all_warnings,
                metadata={},
            )
        ),
        **metadata_dict,
    }
    run_metadata["scoring_readiness_handoff"] = _build_scoring_readiness_handoff(
        run_metadata["scoring_readiness"]
    )
    if collection_evidence is not None:
        run_metadata["collection_evidence"] = collection_evidence

    finished_at = datetime.now(UTC)
    return AnalysisRunSummary(
        run_id=run_id,
        source_id=source_id,
        started_at=started_at,
        finished_at=finished_at,
        status=run_status,
        stages=stages,
        warnings=all_warnings,
        metadata=run_metadata,
    )
