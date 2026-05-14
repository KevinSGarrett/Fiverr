"""Unit tests for analysis interface contracts."""

from __future__ import annotations

from src.analysis.contracts import (
    AnalysisError,
    AnalysisInput,
    AnalysisOutput,
    AnalysisStatus,
    AnalysisTaskType,
)


def test_analysis_contracts_instantiate_and_serialize() -> None:
    payload = AnalysisInput(
        task_type=AnalysisTaskType.KEYWORD_CLUSTERING,
        run_id="run-123",
        records=[{"keyword": "logo design"}],
    )
    output = AnalysisOutput(
        task_type=payload.task_type,
        status=AnalysisStatus.SUCCESS,
        result={"clusters": [{"name": "logo"}]},
    )

    dump = output.model_dump()
    assert payload.task_type == AnalysisTaskType.KEYWORD_CLUSTERING
    assert dump["status"] == AnalysisStatus.SUCCESS
    assert "clusters" in dump["result"]


def test_analysis_task_type_enum_contains_expected_values() -> None:
    values = {task.value for task in AnalysisTaskType}
    assert values == {
        "keyword_clustering",
        "gig_quality",
        "competitor_profile",
        "seller_strength",
        "saturation",
        "review_analysis",
        "intent_classification",
    }


def test_failure_output_contains_sanitized_error_message() -> None:
    err = AnalysisError.from_exception(
        RuntimeError("failed with api_key=sk-test1234567890abcdef"),
        code="analysis_failure",
    )
    output = AnalysisOutput(
        task_type=AnalysisTaskType.GIG_QUALITY,
        status=AnalysisStatus.FAILED,
        errors=[err],
    )

    assert output.errors[0].code == "analysis_failure"
    assert "sk-test1234567890abcdef" not in output.errors[0].message
