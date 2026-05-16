"""Unit tests for dashboard query-layer contracts and sparse-data behavior."""

from __future__ import annotations

from src.dashboard.contracts import FreshnessMetadata, SourceContext
from src.dashboard.queries import map_warning_codes_to_operator_severity
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


def test_query_layer_coerces_invalid_limit_to_default_page_size() -> None:
    layer = get_dashboard_query_layer()
    records = [{"run_id": f"run-{index}", "score": index} for index in range(30)]
    result = layer.run_history(
        records=records,
        limit="bad-limit",  # type: ignore[arg-type]
        offset=0,
    )
    assert result.context.pagination is not None
    assert result.context.pagination.limit == 25
    assert result.context.pagination.returned_count == 25
    assert result.context.pagination.truncated is True
    warning_codes = {warning.code for warning in result.context.warnings}
    assert "invalid_limit_type" in warning_codes


def test_query_layer_caps_over_limit_page_size_and_marks_warning() -> None:
    layer = get_dashboard_query_layer()
    records = [{"run_id": f"run-{index}", "score": index} for index in range(400)]
    result = layer.run_history(
        records=records,
        limit=999,
        offset=0,
    )
    assert result.context.pagination is not None
    assert result.context.pagination.limit == 250
    assert result.context.pagination.returned_count == 250
    warning_codes = {warning.code for warning in result.context.warnings}
    assert "limit_capped" in warning_codes


def test_query_layer_handles_missing_offset_with_default_zero() -> None:
    layer = get_dashboard_query_layer()
    result = layer.opportunities(
        records=[{"opportunity": "A", "score": 90}],
        limit=1,
        offset=None,  # type: ignore[arg-type]
    )
    assert result.context.pagination is not None
    assert result.context.pagination.offset == 0
    warning_codes = {warning.code for warning in result.context.warnings}
    assert "invalid_offset_type" not in warning_codes


def test_query_layer_exact_limit_boundary_has_no_truncation() -> None:
    layer = get_dashboard_query_layer()
    records = [{"run_id": f"run-{index}", "score": index} for index in range(25)]
    result = layer.run_history(
        records=records,
        limit=25,
        offset=0,
    )
    assert result.context.pagination is not None
    assert result.context.pagination.returned_count == 25
    assert result.context.pagination.truncated is False


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


def test_invalid_rank_values_do_not_trigger_duplicate_rank_warning() -> None:
    layer = get_dashboard_query_layer()
    result = layer.opportunities(
        records=[
            {"id": "a", "rank": "bad-rank", "score": 10},
            {"id": "b", "rank": "still-bad", "score": 9},
        ]
    )
    warning_codes = {warning.code for warning in result.context.warnings}
    assert "invalid_rank" in warning_codes
    assert "duplicate_rank" not in warning_codes


def test_summarize_data_integrity_records_returns_traceable_warning_codes() -> None:
    from src.dashboard.queries import summarize_data_integrity_records

    summary = summarize_data_integrity_records(
        records=[
            {"id": "dup", "score": "bad", "generated_at": " ", "evidence": "bad-shape"},
            {"id": "dup", "rank": "bad"},
        ]
    )
    assert summary["status"] == "warning"
    assert summary["record_count"] == 2
    assert {"duplicate_record_id", "invalid_score", "invalid_rank", "malformed_evidence", "invalid_generated_at"} <= set(
        summary["warning_codes"]
    )


def test_data_integrity_readiness_signal_supports_unknown_warning_and_blocked() -> None:
    from src.dashboard.queries import build_data_integrity_readiness_signal

    unknown_signal = build_data_integrity_readiness_signal(records=None)
    assert unknown_signal["status"] == "unknown"

    warning_signal = build_data_integrity_readiness_signal(records=[{"id": "row-1", "score": "bad"}])
    assert warning_signal["status"] == "warning"

    blocked_signal = build_data_integrity_readiness_signal(
        records=[
            {"id": "dup", "score": "bad", "rank": "bad-rank"},
            {"id": "dup", "score": "still-bad", "rank": "still-bad-rank"},
        ]
    )
    assert blocked_signal["status"] == "blocked"


def test_warning_code_severity_mapping_produces_operator_contract() -> None:
    summary = map_warning_codes_to_operator_severity(
        [
            "missing_records",
            "invalid_score",
            "blocked_pages",
            "invalid_score",
        ]
    )
    assert summary["highest_severity"] == "blocked"
    assert summary["counts"]["blocked"] == 1
    assert summary["counts"]["error"] == 1
    assert summary["counts"]["warning"] == 1
    assert {row["code"] for row in summary["rows"]} == {"missing_records", "invalid_score", "blocked_pages"}


def test_analysis_outputs_feed_dashboard_contract_for_complete_payload() -> None:
    layer = get_dashboard_query_layer()
    result = layer.analysis_output_contract(
        records=[
            {
                "keyword": "python automation",
                "score": 82.5,
                "confidence": 0.84,
                "niche": "automation",
                "status": "ready",
            }
        ]
    )
    assert result.context.status == "ok"
    assert result.records[0]["missing_fields"] == []


def test_analysis_outputs_feed_dashboard_contract_for_partial_payload() -> None:
    layer = get_dashboard_query_layer()
    result = layer.analysis_output_contract(
        records=[
            {
                "keyword": "seo audit",
                "score": 72.0,
                "confidence": None,
                "niche": "seo",
                "status": "",
            }
        ]
    )
    assert result.context.status == "warning"
    assert {"confidence", "status"} <= set(result.records[0]["missing_fields"])
