"""Type-safe, side-effect-free contracts for collection stages."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

REQUIRED_COLLECTION_SUMMARY_STAGES: tuple[str, ...] = (
    "stage_1_keyword_expansion",
    "stage_2b_autocomplete",
    "stage_2_search_plan",
    "stage_3_queue",
    "stage_4_gig_detail",
    "stage_5_seller_profile",
    "stage_6a_external_signals",
    "stage_6b_community_signals",
    "stage_7_checkpoint_metadata",
    "stage_8_pacing_decisions",
    "stage_9_auto_promotion_decision",
)

STABLE_COLLECTION_STAGE_NAMES: tuple[str, ...] = (
    "stage_1_keyword_expansion",
    "stage_2b_autocomplete",
    "stage_2_search_plan",
    "stage_3_queue",
    "stage_4_gig_detail",
    "stage_5_seller_profile",
    "stage_6a_external_signals",
    "stage_6b_community_signals",
    "stage_7_checkpoint_metadata",
    "stage_8_pacing_decisions",
    "stage_9_auto_promotion_decision",
)

RECORDS_SEEN_STAGE_NAMES: tuple[str, ...] = ("stage_1_keyword_expansion",)
RECORDS_WRITTEN_STAGE_NAMES: tuple[str, ...] = (
    "stage_2b_autocomplete",
    "stage_3_queue",
    "stage_4_gig_detail",
    "stage_5_seller_profile",
    "stage_6a_external_signals",
    "stage_6b_community_signals",
    "stage_7_checkpoint_metadata",
    "stage_8_pacing_decisions",
    "stage_9_auto_promotion_decision",
)


class CollectionStageStatus(StrEnum):
    """High-level status for a collection stage execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class CollectionError(BaseModel):
    """Structured error payload emitted by collection stages."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class CollectionStageInput(BaseModel):
    """Input envelope for future stage implementations."""

    stage_name: str
    checkpoint_path: Path | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CollectionStageResult(BaseModel):
    """Output contract for future collection orchestration."""

    stage_name: str
    status: CollectionStageStatus
    records_seen: int = 0
    records_written: int = 0
    errors: list[CollectionError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checkpoint_path: Path | None = None
    started_at: datetime
    finished_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CollectionCheckpointEvidence(BaseModel):
    """Serializable checkpoint and pacing evidence for downstream reporting."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    checkpoint_path: str
    pacing_decisions: dict[str, Any] = Field(default_factory=dict)
    cooldown_applied: bool = False
    retry_count: int = Field(default=0, ge=0)
    fixture_mode: bool = True


def validate_collection_stage_summary(summary: dict[str, Any]) -> None:
    """Validate required dry-run stage representation in one summary payload."""

    stage_counts = summary.get("stage_counts")
    if not isinstance(stage_counts, dict):
        raise ValueError("Collection stage summary requires a 'stage_counts' mapping.")

    missing_stages = [stage for stage in REQUIRED_COLLECTION_SUMMARY_STAGES if stage not in stage_counts]
    if missing_stages:
        raise ValueError(
            "Collection stage summary is missing required stages: "
            + ", ".join(sorted(missing_stages))
            + "."
        )

    invalid_stage_counts = [
        stage_name
        for stage_name, value in stage_counts.items()
        if not isinstance(value, int) or value < 0
    ]
    if invalid_stage_counts:
        raise ValueError(
            "Collection stage summary has invalid stage_counts values for: "
            + ", ".join(sorted(invalid_stage_counts))
            + "."
        )

    unknown_stages = [
        stage_name for stage_name in stage_counts if stage_name not in STABLE_COLLECTION_STAGE_NAMES
    ]
    if unknown_stages:
        raise ValueError(
            "Collection stage summary has unstable stage names: "
            + ", ".join(sorted(unknown_stages))
            + "."
        )

    stage_names = summary.get("stage_names")
    if stage_names is not None:
        if not isinstance(stage_names, list) or any(not isinstance(name, str) for name in stage_names):
            raise ValueError("Collection stage summary 'stage_names' must be a list of strings.")
        duplicate_stage_names = sorted({name for name in stage_names if stage_names.count(name) > 1})
        if duplicate_stage_names:
            raise ValueError(
                "Collection stage summary 'stage_names' contains duplicate stages: "
                + ", ".join(duplicate_stage_names)
                + "."
            )
        unknown_stage_names = sorted(
            stage_name for stage_name in stage_names if stage_name not in STABLE_COLLECTION_STAGE_NAMES
        )
        if unknown_stage_names:
            raise ValueError(
                "Collection stage summary 'stage_names' has unstable stage names: "
                + ", ".join(unknown_stage_names)
                + "."
            )
        stage_name_set = set(stage_names)
        stage_count_key_set = set(stage_counts.keys())
        if stage_name_set != stage_count_key_set:
            missing_stage_names = sorted(stage_count_key_set - stage_name_set)
            extra_stage_names = sorted(stage_name_set - stage_count_key_set)
            mismatch_messages: list[str] = []
            if missing_stage_names:
                mismatch_messages.append("missing: " + ", ".join(missing_stage_names))
            if extra_stage_names:
                mismatch_messages.append("extra: " + ", ".join(extra_stage_names))
            raise ValueError(
                "Collection stage summary 'stage_names' must match stage_counts stage keys (unordered); "
                + "; ".join(mismatch_messages)
                + "."
            )

    stage_execution = summary.get("stage_execution")
    if stage_execution is not None:
        if not isinstance(stage_execution, list):
            raise ValueError("Collection stage summary 'stage_execution' must be a list when provided.")
        if not stage_execution:
            raise ValueError("Collection stage summary 'stage_execution' must not be empty when provided.")
        execution_stage_names: list[str] = []
        execution_indices: list[int] = []
        failed_stage_names_from_execution: list[str] = []
        skipped_stage_names_from_execution: list[str] = []
        for entry in stage_execution:
            if not isinstance(entry, dict):
                raise ValueError("Collection stage summary 'stage_execution' entries must be mappings.")
            stage_name = entry.get("stage_name")
            if not isinstance(stage_name, str) or stage_name not in STABLE_COLLECTION_STAGE_NAMES:
                raise ValueError(
                    "Collection stage summary 'stage_execution' has unstable stage_name values."
                )
            execution_stage_names.append(stage_name)

            execution_index = entry.get("execution_index")
            if not isinstance(execution_index, int) or execution_index < 1:
                raise ValueError(
                    "Collection stage summary 'stage_execution' requires positive integer execution_index."
                )
            execution_indices.append(execution_index)

            status = entry.get("status")
            if not isinstance(status, str) or status not in {member.value for member in CollectionStageStatus}:
                raise ValueError("Collection stage summary 'stage_execution' has invalid status values.")
            if status == CollectionStageStatus.FAILED.value:
                failed_stage_names_from_execution.append(stage_name)
                failure_code = entry.get("failure_code")
                if not isinstance(failure_code, str) or not failure_code.strip():
                    raise ValueError(
                        "Failed stage_execution entries must include a non-empty failure_code."
                    )
            if status == CollectionStageStatus.SKIPPED.value:
                skipped_stage_names_from_execution.append(stage_name)
                skip_reason = entry.get("skip_reason")
                if not isinstance(skip_reason, str) or not skip_reason.strip():
                    raise ValueError(
                        "Skipped stage_execution entries must include a non-empty skip_reason."
                    )

            started_at = entry.get("started_at")
            finished_at = entry.get("finished_at")
            if not isinstance(started_at, str) or not started_at.strip():
                raise ValueError("Each stage_execution entry must include a non-empty started_at string.")
            if not isinstance(finished_at, str) or not finished_at.strip():
                raise ValueError("Each stage_execution entry must include a non-empty finished_at string.")

            resumable_stage_id = entry.get("resumable_stage_id")
            if not isinstance(resumable_stage_id, str) or not resumable_stage_id.strip():
                raise ValueError(
                    "Each stage_execution entry must include a non-empty resumable_stage_id string."
                )

        if sorted(execution_indices) != list(range(1, len(stage_execution) + 1)):
            raise ValueError("Collection stage summary 'stage_execution' indices must be contiguous from 1.")
        if len(set(execution_stage_names)) != len(execution_stage_names):
            raise ValueError("Collection stage summary 'stage_execution' stage names must not repeat.")
        if stage_names is not None and execution_stage_names != stage_names:
            raise ValueError(
                "Collection stage summary 'stage_execution' order must match stage_names execution order."
            )

        skipped_stage_names = summary.get("skipped_stage_names")
        if skipped_stage_names is not None:
            if not isinstance(skipped_stage_names, list) or any(
                not isinstance(stage_name, str) for stage_name in skipped_stage_names
            ):
                raise ValueError(
                    "Collection stage summary 'skipped_stage_names' must be a list of strings."
                )
            if sorted(skipped_stage_names) != sorted(skipped_stage_names_from_execution):
                raise ValueError(
                    "Collection stage summary 'skipped_stage_names' must match skipped stage_execution entries."
                )

        failed_stage_names = summary.get("failed_stage_names")
        if failed_stage_names is not None:
            if not isinstance(failed_stage_names, list) or any(
                not isinstance(stage_name, str) for stage_name in failed_stage_names
            ):
                raise ValueError(
                    "Collection stage summary 'failed_stage_names' must be a list of strings."
                )
            if sorted(failed_stage_names) != sorted(failed_stage_names_from_execution):
                raise ValueError(
                    "Collection stage summary 'failed_stage_names' must match failed stage_execution entries."
                )

        resumable_stage_identity = summary.get("resumable_stage_identity")
        if resumable_stage_identity is not None:
            if not isinstance(resumable_stage_identity, dict):
                raise ValueError(
                    "Collection stage summary 'resumable_stage_identity' must be an object when provided."
                )
            run_id = resumable_stage_identity.get("run_id")
            if not isinstance(run_id, str) or not run_id.strip():
                raise ValueError("resumable_stage_identity.run_id must be a non-empty string.")
            last_completed_stage_id = resumable_stage_identity.get("last_completed_stage_id")
            if not isinstance(last_completed_stage_id, str) or not last_completed_stage_id.strip():
                raise ValueError(
                    "resumable_stage_identity.last_completed_stage_id must be a non-empty string."
                )

    records_seen = summary.get("records_seen")
    if records_seen is not None:
        if not isinstance(records_seen, int) or records_seen < 0:
            raise ValueError("Collection stage summary 'records_seen' must be a non-negative integer.")
        expected_records_seen = sum(stage_counts.get(stage_name, 0) for stage_name in RECORDS_SEEN_STAGE_NAMES)
        if records_seen != expected_records_seen:
            raise ValueError(
                "Collection stage summary records_seen mismatch: "
                f"expected {expected_records_seen}, found {records_seen}."
            )

    records_written = summary.get("records_written")
    if records_written is not None:
        if not isinstance(records_written, int) or records_written < 0:
            raise ValueError("Collection stage summary 'records_written' must be a non-negative integer.")
        expected_records_written = sum(
            stage_counts.get(stage_name, 0) for stage_name in RECORDS_WRITTEN_STAGE_NAMES
        )
        if records_written != expected_records_written:
            raise ValueError(
                "Collection stage summary records_written mismatch: "
                f"expected {expected_records_written}, found {records_written}."
            )

    warning_count = summary.get("warning_count")
    warnings = summary.get("warnings")
    if warning_count is not None or warnings is not None:
        if not isinstance(warnings, list) or any(not isinstance(warning, str) for warning in warnings):
            raise ValueError("Collection stage summary 'warnings' must be a list of strings.")
        if not isinstance(warning_count, int) or warning_count < 0:
            raise ValueError("Collection stage summary 'warning_count' must be a non-negative integer.")
        if warning_count != len(warnings):
            raise ValueError(
                "Collection stage summary warning_count mismatch: "
                f"expected {len(warnings)}, found {warning_count}."
            )

    failed = summary.get("failed")
    error_code = summary.get("error_code")
    if failed is not None and not isinstance(failed, bool):
        raise ValueError("Collection stage summary 'failed' must be a boolean when provided.")
    if failed:
        if not isinstance(error_code, str) or not error_code.strip():
            raise ValueError("Failed collection stage summaries must include a non-empty 'error_code'.")
    elif error_code is not None:
        raise ValueError("Collection stage summary must not include 'error_code' unless failed is true.")
