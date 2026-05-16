"""Unit tests for dashboard query-layer contracts and sparse-data behavior."""

from __future__ import annotations

from src.dashboard.contracts import FreshnessMetadata, SourceContext
from src.dashboard.query_layer import get_dashboard_query_layer


def test_query_layer_exposes_filter_and_sort_descriptors() -> None:
    layer = get_dashboard_query_layer()
    filter_keys = [descriptor.key for descriptor in layer.filter_descriptors()]
    sort_keys = [descriptor.key for descriptor in layer.sort_descriptors()]
    assert {"status", "niche", "confidence_min", "score_min", "limit", "offset"} <= set(filter_keys)
    assert {"score", "confidence", "generated_at", "run_id"} <= set(sort_keys)


def test_opportunity_query_applies_filters_sort_and_pagination() -> None:
    layer = get_dashboard_query_layer()
    records = [
        {"opportunity": "A", "status": "ready", "niche": "seo", "score": 88, "confidence": 0.9},
        {"opportunity": "B", "status": "ready", "niche": "seo", "score": 81, "confidence": 0.6},
        {"opportunity": "C", "status": "blocked", "niche": "design", "score": 95, "confidence": 0.4},
    ]
    result = layer.opportunities(
        records=records,
        filters={"status": "ready", "niche": "seo", "confidence_min": 0.7},
        sort={"field": "score", "descending": True},
        limit=1,
        offset=0,
        freshness=FreshnessMetadata(freshness_status="fresh", generated_at="2026-05-15T17:45:00Z"),
    )
    assert result.total_count == 1
    assert len(result.records) == 1
    assert result.records[0]["opportunity"] == "A"
    assert result.context.pagination is not None
    assert result.context.pagination.truncated is False
    assert result.context.freshness.freshness_status == "fresh"


def test_query_layer_sparse_data_returns_warning_instead_of_exception() -> None:
    layer = get_dashboard_query_layer()
    result = layer.keywords(records=None, limit=25, offset=0)
    assert result.records == ()
    assert result.context.status == "warning"
    warning_codes = {warning.code for warning in result.context.warnings}
    assert {"missing_records", "empty_result"} <= warning_codes
    assert result.context.empty_state is True


def test_query_layer_coerces_negative_limit_and_offset() -> None:
    layer = get_dashboard_query_layer()
    result = layer.run_history(
        records=[{"run_id": "run-001", "score": 1.0}],
        limit=-5,
        offset=-1,
    )
    assert result.context.pagination is not None
    assert result.context.pagination.limit == 0
    assert result.context.pagination.offset == 0
    warning_codes = {warning.code for warning in result.context.warnings}
    assert {"invalid_limit", "invalid_offset"} <= warning_codes


def test_query_layer_coerces_non_integer_limit_and_offset_inputs() -> None:
    layer = get_dashboard_query_layer()
    result = layer.run_history(
        records=[{"run_id": "run-001", "score": 1.0}],
        limit="5",  # type: ignore[arg-type]
        offset="2",  # type: ignore[arg-type]
    )
    assert result.context.pagination is not None
    assert result.context.pagination.limit == 5
    assert result.context.pagination.offset == 2
    warning_codes = {warning.code for warning in result.context.warnings}
    assert {"invalid_limit_type", "invalid_offset_type"} <= warning_codes


def test_query_layer_preserves_source_and_freshness_traceability() -> None:
    layer = get_dashboard_query_layer()
    summary = layer.source_freshness_summary(
        source_contexts=[
            SourceContext(
                source_name="fiverr_snapshot",
                source_type="fixture",
                generated_at="2026-05-15T16:00:00Z",
                confidence_source="analysis_model_v2",
            )
        ],
        freshness_metadata=[FreshnessMetadata(freshness_status="stale", generated_at="2026-05-14T20:00:00Z")],
    )
    assert summary.total_count == 1
    row = summary.records[0]
    assert row["source_name"] == "fiverr_snapshot"
    assert row["freshness_status"] == "stale"
    assert row["confidence_source"] == "analysis_model_v2"


def test_app_readiness_query_returns_blocked_page_warning() -> None:
    layer = get_dashboard_query_layer()
    result = layer.app_readiness(
        page_registry=[
            {"page_id": "overview", "status": "ready"},
            {"page_id": "keywords", "status": "blocked"},
        ],
        startup_diagnostics={"status": "warning", "warning_count": 1},
        orchestrator_handoff={"stage_status": "warning", "next_actions": ["Run phase2-smoke"]},
    )
    assert result.context.status == "warning"
    assert result.records[0]["blocked_pages"] == ["keywords"]
    assert "Run phase2-smoke" in result.records[0]["next_actions"]


def test_query_sort_handles_mixed_numeric_and_string_values_without_type_errors() -> None:
    layer = get_dashboard_query_layer()
    result = layer.opportunities(
        records=[
            {"opportunity": "A", "score": 88},
            {"opportunity": "B", "score": "87.5"},
            {"opportunity": "C", "score": "unknown"},
            {"opportunity": "D", "score": None},
        ],
        sort={"field": "score", "descending": True},
    )
    assert [row["opportunity"] for row in result.records[:2]] == ["A", "B"]
    assert result.context.status == "warning"


def test_alert_summary_query_returns_counts_and_sparse_warning() -> None:
    layer = get_dashboard_query_layer()
    result = layer.alert_summary(records=None)
    assert result.query_name == "alert_summary"
    assert result.records[0]["record_count"] == 0
    warning_codes = {warning.code for warning in result.context.warnings}
    assert {"missing_alert_records", "empty_alert_records"} <= warning_codes


def test_export_summary_query_sorts_by_generated_at_descending() -> None:
    layer = get_dashboard_query_layer()
    result = layer.export_summary(
        records=[
            {"artifact_type": "run_summary", "generated_at": "2026-05-15T17:00:00Z", "score": 1},
            {"artifact_type": "cycle_validation", "generated_at": "2026-05-15T18:00:00Z", "score": 1},
        ],
    )
    assert [row["artifact_type"] for row in result.records] == ["cycle_validation", "run_summary"]
    assert result.context.status == "ok"


def test_integration_evidence_query_uses_deterministic_default_summary_when_missing() -> None:
    layer = get_dashboard_query_layer()
    result = layer.integration_evidence(evidence=None)
    assert result.query_name == "integration_evidence"
    assert result.records[0]["validation_count"] > 0
    assert result.context.status == "warning"
    warning_codes = {warning.code for warning in result.context.warnings}
    assert "missing_integration_evidence" in warning_codes


def test_integration_evidence_query_handles_malformed_stage_and_jira_shapes() -> None:
    layer = get_dashboard_query_layer()
    result = layer.integration_evidence(
        evidence={
            "stage_status": "pass",
            "jira_progress": {"jira_key": "SCRUM-1"},
            "codex_status": "clean",
        }
    )
    assert result.query_name == "integration_evidence"
    assert result.records[0]["stage_status"] == {}
    assert result.records[0]["jira_progress"] == []
    assert result.context.status == "warning"
    warning_codes = {warning.code for warning in result.context.warnings}
    assert "invalid_integration_stage_status" in warning_codes
    assert "invalid_integration_jira_progress" in warning_codes


def test_analysis_output_contract_reports_missing_expected_fields() -> None:
    layer = get_dashboard_query_layer()
    result = layer.analysis_output_contract(
        records=[
            {"keyword": "logo design", "score": 85, "confidence": 0.8, "niche": "logo"},
            {"keyword": "resume writing", "score": 75, "status": "ready"},
        ]
    )
    assert result.query_name == "analysis_output_contract"
    assert result.records[0]["record_count"] == 2
    assert "status" in result.records[0]["missing_fields"]
    assert "confidence" in result.records[0]["missing_fields"]
    assert result.context.status == "warning"


def test_query_layer_adds_data_integrity_warnings_and_empty_state_contract() -> None:
    layer = get_dashboard_query_layer()
    result = layer.opportunities(
        records=[
            {"id": "dup", "rank": 1, "status": "ready", "score": "bad", "confidence": 0.8},
            {"id": "dup", "rank": 1, "status": "mystery", "score": 80, "confidence": "bad"},
            "not-a-row",  # type: ignore[list-item]
        ]
    )
    warning_codes = {warning.code for warning in result.context.warnings}
    assert "invalid_record_shape" in warning_codes
    assert "duplicate_record_id" in warning_codes
    assert "duplicate_rank" in warning_codes
    assert "invalid_status_category" in warning_codes
    assert "invalid_score" in warning_codes
    assert "invalid_confidence" in warning_codes

    empty_result = layer.keywords(records=None)
    assert empty_result.context.empty_state_contract is not None
    assert empty_result.context.empty_state_contract.source == "dashboard.query_layer"
