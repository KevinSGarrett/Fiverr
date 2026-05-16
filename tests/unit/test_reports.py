"""Unit tests for reporting and export contract scaffolding."""

from __future__ import annotations

import pytest
from src.exports import (
    ALLOWED_EXPORT_ROOTS,
    CHECKSUM_PLACEHOLDER,
    ExportFormat,
    ExportManifest,
    ExportRequest,
    build_csv_export,
    build_analysis_export_summary,
    build_governance_export_status_map,
    build_governance_manifest_metadata,
    build_json_export,
    build_markdown_export,
    normalize_export_format,
    validate_export_format,
    validate_export_request,
)
from src.reports import (
    DEFAULT_VALIDATION_COMMANDS,
    GOVERNANCE_REPORT_ORDER,
    PENDING_PLACEHOLDER,
    PHASE2_REQUIRED_SECTION_TITLES,
    AnalysisDryRunReport,
    AnalysisMultiStageRunReport,
    CollectionDryRunReport,
    CollectionFixtureRunReport,
    CycleValidationReport,
    FoundationGateReport,
    GigDetailParserCoverageReport,
    Phase2ReadinessReport,
    ReportSection,
    ReportSeverity,
    ReportTemplate,
    RunSummary,
    SellerProfileParserCoverageReport,
    build_default_template,
    build_governance_report_placeholders,
    build_integration_evidence_summary,
    build_jira_mapping_table,
    build_phase2_readiness_report,
    build_phase2_readiness_template,
    build_runtime_diagnostics_markdown_table,
    render_plain_text_summary,
)
from src.reports.placeholders import (
    ACTIVE_STORY_STATUSES,
    JIRA_MAPPING_TYPES,
    JIRA_UPDATED_BY_VALUES,
    build_active_story_groups,
    build_analysis_summary_rows,
)


def test_run_summary_with_minimal_data_validates() -> None:
    summary = RunSummary(run_id="run-002", status="success")
    assert summary.validate() is True


@pytest.mark.parametrize("format_name", ["csv", "xlsx", "json", "html", "pdf", "md"])
def test_validate_export_format_accepts_supported_formats(format_name: str) -> None:
    assert validate_export_format(format_name) is True


def test_validate_export_format_rejects_unsupported_format() -> None:
    with pytest.raises(ValueError, match="Unsupported export format"):
        validate_export_format("docx")


def test_validate_export_request_rejects_parent_directory_traversal() -> None:
    request = ExportRequest(format=ExportFormat.JSON, output_path="../outside.json")
    with pytest.raises(ValueError, match="parent directory traversal"):
        validate_export_request(request)


def test_normalize_export_format_accepts_md() -> None:
    assert normalize_export_format("md") == ExportFormat.MD


def test_export_manifest_is_serializable() -> None:
    manifest = ExportManifest(
        artifact_type="cycle_validation",
        format=ExportFormat.JSON,
        source_cycle="003",
        path="exports/cycle003/validation.json",
        included_sections=("checks", "findings"),
    )
    serialized = manifest.to_dict()
    assert serialized["artifact_type"] == "cycle_validation"
    assert serialized["format"] == "json"
    assert serialized["source_cycle"] == "003"
    assert serialized["path"] == "exports/cycle003/validation.json"
    assert serialized["checksum"] == CHECKSUM_PLACEHOLDER
    assert serialized["allow_pending_checksum"] is True
    assert serialized["included_sections"] == ["checks", "findings"]
    assert serialized["jira_keys"] == []
    assert serialized["github_pr_number"] is None
    assert serialized["codex_threads_resolved"] == 0
    assert serialized["codecov_project_status"] == "pending"
    assert serialized["codecov_patch_status"] == "pending"
    assert serialized["coverage_percent"] is None
    assert serialized["schema_version"] == "1.0"
    assert serialized["record_count"] == 0
    assert serialized["sparse_data_behavior"] == "include_metadata_and_warnings"


def test_export_manifest_rejects_disallowed_root_path() -> None:
    with pytest.raises(ValueError, match="path root must be one of"):
        ExportManifest(
            artifact_type="cycle_validation",
            format=ExportFormat.JSON,
            source_cycle="004",
            path="tmp/cycle004/validation.json",
        )


def test_export_manifest_rejects_traversal_path() -> None:
    with pytest.raises(ValueError, match="parent directory traversal"):
        ExportManifest(
            artifact_type="cycle_validation",
            format=ExportFormat.JSON,
            source_cycle="004",
            path="artifacts/../outside.json",
        )


def test_export_manifest_rejects_unsupported_format() -> None:
    with pytest.raises(ValueError, match="Unsupported export format"):
        ExportManifest(
            artifact_type="cycle_validation",
            format="docx",
            source_cycle="003",
            path="exports/cycle003/validation.docx",
        )


def test_export_manifest_rejects_invalid_checksum_placeholder() -> None:
    with pytest.raises(ValueError, match="checksum must be"):
        ExportManifest(
            artifact_type="cycle_validation",
            format=ExportFormat.MD,
            source_cycle="003",
            path="exports/cycle003/validation.md",
            checksum="pending",
        )


def test_export_manifest_requires_checksum_when_pending_not_allowed() -> None:
    with pytest.raises(ValueError, match="checksum is required"):
        ExportManifest(
            artifact_type="dry_run_summary",
            format=ExportFormat.JSON,
            source_cycle="004",
            path="artifacts/cycle004/dry_run_summary.json",
            allow_pending_checksum=False,
        )


def test_plain_text_summary_includes_run_id_and_status() -> None:
    summary = RunSummary(run_id="run-xyz", status="in_progress", notes=("scaffold only",))
    rendered = render_plain_text_summary(summary)
    assert "Run ID: run-xyz" in rendered
    assert "Status: in_progress" in rendered


def test_missing_required_section_is_detected() -> None:
    template = build_default_template()
    trimmed_template = ReportTemplate(name=template.name, sections=template.sections[:-1])
    assert "Data Freshness" in trimmed_template.missing_required_sections()
    assert trimmed_template.is_valid() is False


def test_report_section_severity_is_constrained() -> None:
    section = ReportSection(title="Executive Summary", severity="info", body="ok")
    assert section.severity == ReportSeverity.INFO


def test_report_section_rejects_invalid_severity_value() -> None:
    with pytest.raises(ValueError, match="severity must be one of"):
        ReportSection(title="Executive Summary", severity="urgent", body="invalid")  # type: ignore[arg-type]


def test_structured_reports_render_markdown_with_data() -> None:
    finding = ReportSection(title="Gate check", severity=ReportSeverity.WARNING, body="Dry run only")
    reports = [
        FoundationGateReport(cycle_id="003", gate_status="conditional", findings=(finding,)),
        CollectionDryRunReport(cycle_id="003", run_id="dry-1", sample_size=10, findings=(finding,)),
        AnalysisDryRunReport(cycle_id="003", analyzed_keywords=12, scored_niches=3, findings=(finding,)),
        CycleValidationReport(cycle_id="003", checks={"pytest": "pass"}, findings=(finding,), summary="green"),
    ]
    for report in reports:
        rendered = report.to_markdown()
        assert "# " in rendered
        assert "003" in rendered
        assert "Gate check" in rendered


def test_structured_reports_render_pending_placeholders_when_optional_missing() -> None:
    reports = [
        FoundationGateReport(cycle_id="003"),
        CollectionDryRunReport(cycle_id="003"),
        AnalysisDryRunReport(cycle_id="003"),
        CycleValidationReport(cycle_id="003"),
    ]
    for report in reports:
        rendered = report.to_markdown()
        assert PENDING_PLACEHOLDER in rendered


def test_phase2_readiness_report_renders_markdown_and_detects_missing_sections() -> None:
    section = ReportSection(
        title="Collection Fixture Run",
        severity=ReportSeverity.INFO,
        body="Fixture run completed for 25 records.",
    )
    report = Phase2ReadinessReport(
        cycle_id="004",
        run_id="phase2-001",
        status="conditional",
        checks={"pytest": "pass", "ruff": "pass"},
        sections=(section,),
        blockers=("Awaiting seller parser fixture delta.",),
    )
    rendered = report.to_markdown()
    assert "Phase 2 PR Readiness Report" in rendered
    assert "conditional" in rendered
    assert "Collection Fixture Run" in rendered
    assert "Gig Detail Parser Coverage" in report.missing_required_sections()


def test_phase2_component_reports_render_and_serialize() -> None:
    reports = [
        CollectionFixtureRunReport(
            cycle_id="004",
            run_id="collect-fixture-1",
            fixture_records_total=30,
            fixture_records_processed=30,
            severity="info",
            notes=("Fixture queue was complete.",),
        ),
        GigDetailParserCoverageReport(
            cycle_id="004",
            coverage_percent=96.5,
            parsed_count=58,
            expected_count=60,
            severity="warning",
            notes=("2 records require parser fallback.",),
        ),
        SellerProfileParserCoverageReport(
            cycle_id="004",
            coverage_percent=98.0,
            parsed_count=49,
            expected_count=50,
            severity="info",
        ),
        AnalysisMultiStageRunReport(
            cycle_id="004",
            run_id="analysis-stage-1",
            stages_completed=("scoring", "ranking"),
            stages_pending=("recommendations",),
            severity=ReportSeverity.WARNING,
            notes=("Recommendation stage still fixture-only.",),
        ),
    ]
    for report in reports:
        rendered = report.to_markdown()
        serialized = report.to_dict()
        assert "004" in rendered
        assert isinstance(serialized, dict)
        assert "report_type" in serialized


def test_phase2_component_reports_reject_invalid_severity() -> None:
    with pytest.raises(ValueError, match="severity must be one of"):
        GigDetailParserCoverageReport(cycle_id="004", severity="urgent")  # type: ignore[arg-type]


def test_phase2_readiness_template_contains_required_sections() -> None:
    template = build_phase2_readiness_template()
    section_titles = [section.title for section in template.sections]
    assert section_titles == list(PHASE2_REQUIRED_SECTION_TITLES)


def test_phase2_readiness_report_dict_is_json_serializable_shape() -> None:
    report = build_phase2_readiness_report(cycle_id="004", run_id="phase2-pr")
    serialized = report.to_dict()
    assert serialized["report_type"] == "phase2_readiness"
    assert serialized["cycle_id"] == "004"
    assert serialized["run_id"] == "phase2-pr"
    assert serialized["missing_sections"] == []
    assert isinstance(serialized["sections"], list)


def test_report_section_invalid_severity_fails_for_phase2_report() -> None:
    with pytest.raises(ValueError, match="severity must be one of"):
        Phase2ReadinessReport(
            cycle_id="004",
            sections=(ReportSection(title="Phase 2 PR Readiness", severity="urgent", body="invalid"),),  # type: ignore[arg-type]
        )


def test_allowed_export_roots_are_artifacts_and_exports() -> None:
    assert ALLOWED_EXPORT_ROOTS == ("artifacts", "exports")


def test_governance_report_placeholders_have_stable_order_and_messages() -> None:
    placeholders = build_governance_report_placeholders()
    assert tuple(item.report_type for item in placeholders) == GOVERNANCE_REPORT_ORDER
    assert placeholders[0].status == "pending"
    assert "Local parity checks" in placeholders[0].message
    assert "GitHub Actions workflow checks" in placeholders[1].message
    assert "Codecov project status check" in placeholders[2].message
    assert "Codecov patch status check" in placeholders[3].message
    assert "Codex review-thread disposition" in placeholders[4].message


def test_governance_export_status_map_uses_expected_keys() -> None:
    status_map = build_governance_export_status_map(
        local_parity="pass",
        github_actions="pass",
        codecov_project="pass",
        codecov_patch="pass",
        codex_disposition="valid_fixed",
    )
    assert status_map == {
        "local_parity": "pass",
        "github_actions": "pass",
        "codecov_project": "pass",
        "codecov_patch": "pass",
        "codex_disposition": "valid_fixed",
    }


def test_build_jira_mapping_table_renders_dict_and_markdown() -> None:
    rows = build_jira_mapping_table(
        [
            {
                "changed_file_group": "src/dashboard/",
                "mapping_type": "product",
                "jira_keys": ("SCRUM-212", "SCRUM-213"),
                "status": "in_progress",
                "dod_status": "partial",
                "agent": "D",
                "cycle": "010",
                "branch": "cycle/010/integration",
                "pull_request": "pending",
                "jira_updated_by": "cursor_agent",
            },
            {
                "changed_file_group": "docs/governance/",
                "mapping_type": "governance",
                "jira_keys": (),
                "status": "done",
                "dod_status": "not_applicable",
                "agent": "D",
                "cycle": "010",
                "branch": "cycle/010/integration",
                "pull_request": "pending",
                "jira_updated_by": "pm",
                "not_applicable_reason": "No product behavior change",
            },
        ]
    )
    assert rows[0]["mapping_type"] == "governance"
    assert rows[0]["not_applicable_reason"] == "No product behavior change"
    assert rows[1]["jira_keys"] == ["SCRUM-212", "SCRUM-213"]

    rendered = build_jira_mapping_table(rows, output_format="markdown")
    assert "| Mapping Type | Changed File Group | Jira Keys | Status | DOD Status | Agent | Cycle | Branch | PR | Jira Updated By | Not Applicable Reason |" in rendered
    assert "src/dashboard/" in rendered
    assert "SCRUM-212, SCRUM-213" in rendered
    assert "No product behavior change" in rendered
    assert "cursor_agent" in rendered


def test_build_jira_mapping_table_rejects_missing_jira_keys_without_not_applicable_reason() -> None:
    with pytest.raises(ValueError, match="jira_keys are required"):
        build_jira_mapping_table(
            [
                {
                    "changed_file_group": "src/reports/",
                    "mapping_type": "governance",
                    "jira_keys": (),
                    "status": "in_progress",
                    "dod_status": "partial",
                    "agent": "D",
                    "cycle": "010",
                    "branch": "cycle/010/integration",
                    "pull_request": "pending",
                    "jira_updated_by": "cursor_agent",
                }
            ]
        )


def test_build_jira_mapping_table_rejects_duplicate_jira_keys_across_rows() -> None:
    with pytest.raises(ValueError, match="duplicate key across rows"):
        build_jira_mapping_table(
            [
                {
                    "changed_file_group": "src/dashboard/",
                    "mapping_type": "product",
                    "jira_keys": ("SCRUM-213",),
                    "status": "in_progress",
                    "dod_status": "partial",
                    "agent": "D",
                    "cycle": "010",
                    "branch": "cycle/010/integration",
                    "pull_request": "pending",
                    "jira_updated_by": "cursor_agent",
                },
                {
                    "changed_file_group": "src/reports/",
                    "mapping_type": "governance",
                    "jira_keys": ("SCRUM-213",),
                    "status": "in_progress",
                    "dod_status": "partial",
                    "agent": "D",
                    "cycle": "010",
                    "branch": "cycle/010/integration",
                    "pull_request": "pending",
                    "jira_updated_by": "cursor_agent",
                },
            ]
        )


def test_build_jira_mapping_table_accepts_mixed_governance_and_product_mappings() -> None:
    rows = build_jira_mapping_table(
        [
            {
                "changed_file_group": "src/reports/",
                "mapping_type": "governance",
                "jira_keys": ("SCRUM-250", "SCRUM-252"),
                "status": "in_progress",
                "dod_status": "partial",
                "agent": "D",
                "cycle": "010",
                "branch": "cycle/010/integration",
                "pull_request": "pending",
                "jira_updated_by": "pm_and_cursor_agent",
            },
            {
                "changed_file_group": "src/dashboard/",
                "mapping_type": "product",
                "jira_keys": ("SCRUM-212",),
                "status": "in_progress",
                "dod_status": "partial",
                "agent": "D",
                "cycle": "010",
                "branch": "cycle/010/integration",
                "pull_request": "pending",
                "jira_updated_by": "cursor_agent",
            },
        ]
    )
    assert rows[0]["mapping_type"] == "governance"
    assert rows[1]["mapping_type"] == "product"


def test_build_governance_manifest_metadata_validates_shape_and_values() -> None:
    metadata = build_governance_manifest_metadata(
        jira_keys=("SCRUM-250", "SCRUM-212"),
        github_pr_number=7,
        codex_threads_resolved=3,
        codecov_project_status="pass",
        codecov_patch_status="warning",
        coverage_percent=92.4,
        cursor_jira_operations_performed=True,
        agent_task_count=11,
        jira_mapping_complete=True,
    )
    assert metadata == {
        "jira_keys": ["SCRUM-212", "SCRUM-250"],
        "github_pr_number": 7,
        "codex_threads_resolved": 3,
        "codecov_project_status": "pass",
        "codecov_patch_status": "warning",
        "coverage_percent": 92.4,
        "cursor_jira_operations_performed": True,
        "agent_task_count": 11,
        "jira_mapping_complete": True,
        "task_count_waiver": "",
    }


def test_build_governance_manifest_metadata_rejects_secret_like_values() -> None:
    with pytest.raises(ValueError, match="secret-like values"):
        build_governance_manifest_metadata(jira_keys=("ghp_abc123",))


def test_export_manifest_includes_governance_metadata_fields() -> None:
    manifest = ExportManifest(
        artifact_type="cycle_validation",
        format=ExportFormat.JSON,
        source_cycle="008",
        path="exports/cycle008/validation.json",
        jira_keys=("SCRUM-250", "SCRUM-212"),
        github_pr_number=8,
        codex_threads_resolved=2,
        codecov_project_status="pass",
        codecov_patch_status="pass",
        coverage_percent=95.5,
        cursor_jira_operations_performed=True,
        agent_task_count=11,
        jira_mapping_complete=True,
    )
    serialized = manifest.to_dict()
    assert serialized["jira_keys"] == ["SCRUM-212", "SCRUM-250"]
    assert serialized["github_pr_number"] == 8
    assert serialized["codex_threads_resolved"] == 2
    assert serialized["codecov_project_status"] == "pass"
    assert serialized["codecov_patch_status"] == "pass"
    assert serialized["coverage_percent"] == 95.5
    assert serialized["cursor_jira_operations_performed"] is True
    assert serialized["agent_task_count"] == 11
    assert serialized["jira_mapping_complete"] is True
    assert serialized["task_count_waiver"] == ""


def test_export_manifest_rejects_out_of_range_coverage_percent() -> None:
    with pytest.raises(ValueError, match="coverage_percent must be between 0 and 100"):
        ExportManifest(
            artifact_type="cycle_validation",
            format=ExportFormat.JSON,
            source_cycle="008",
            path="exports/cycle008/validation.json",
            coverage_percent=120.0,
        )


def test_export_manifest_rejects_negative_record_count() -> None:
    with pytest.raises(ValueError, match="record_count must be zero or greater"):
        ExportManifest(
            artifact_type="cycle_validation",
            format=ExportFormat.JSON,
            source_cycle="008",
            path="exports/cycle008/validation.json",
            record_count=-1,
        )


def test_csv_export_helper_returns_deterministic_metadata_and_content() -> None:
    result = build_csv_export(
        export_name="opportunities",
        records=[
            {"keyword": "logo design", "score": 92.1, "status": "strong_go"},
            {"keyword": "resume writing", "score": 79.0, "status": "conditional_go"},
        ],
    )
    assert result["format"] == "csv"
    assert result["schema_version"] == "1.0"
    assert result["record_count"] == 2
    assert result["path"] == "exports/cycle014/opportunities.csv"
    assert result["checksum"].startswith("sha256:")
    assert "keyword,score,status" in result["content"]
    assert result["warnings"] == []


def test_csv_export_helper_handles_sparse_data_with_headers_only() -> None:
    result = build_csv_export(export_name="empty_export", records=[], columns=("keyword", "score"))
    assert result["record_count"] == 0
    assert result["sparse_data"] is True
    assert "header-only output" in result["warnings"][0]
    assert result["content"].strip() == "keyword,score"


def test_json_export_helper_rejects_non_serializable_payload_values() -> None:
    with pytest.raises(ValueError, match="non-serializable values"):
        build_json_export(export_name="bad_json", payload={"invalid": {1, 2, 3}})


def test_json_export_helper_includes_schema_checksum_and_sparse_state() -> None:
    result = build_json_export(export_name="dashboard_payload", payload=None)
    assert result["format"] == "json"
    assert result["schema_version"] == "1.0"
    assert result["record_count"] == 0
    assert result["sparse_data"] is True
    assert result["checksum"].startswith("sha256:")
    assert result["path"] == "exports/cycle014/dashboard_payload.json"


def test_markdown_export_helper_builds_summary_sections() -> None:
    result = build_markdown_export(
        export_name="opportunity_summary",
        title="Opportunity Summary",
        sections=[
            {
                "heading": "Top Opportunities",
                "body": "Fixture-backed ranked opportunities for cycle 014.",
                "items": ["logo design package", "ats resume writing"],
            }
        ],
    )
    assert result["format"] == "md"
    assert result["record_count"] == 1
    assert result["warnings"] == []
    assert "## Top Opportunities" in result["content"]
    assert "- logo design package" in result["content"]
    assert result["checksum"].startswith("sha256:")


def test_markdown_export_helper_uses_sparse_placeholder_section() -> None:
    result = build_markdown_export(export_name="empty_markdown", title="Empty", sections=[])
    assert result["sparse_data"] is True
    assert "No Data Available" in result["content"]
    assert result["warnings"]


def test_governance_manifest_metadata_rejects_incomplete_cycle_governance_fields() -> None:
    with pytest.raises(ValueError, match="task_count_waiver is required when jira_mapping_complete is False"):
        build_governance_manifest_metadata(
            jira_keys=("SCRUM-252",),
            jira_mapping_complete=False,
            agent_task_count=11,
        )


def test_active_story_groups_placeholder_filters_and_groups_deterministically() -> None:
    rows = build_active_story_groups(
        [
            {
                "story_group": "dashboard",
                "jira_keys": ("SCRUM-212", "SCRUM-213"),
                "status": "in_progress",
                "source": "report",
                "cycle": "010",
                "branch": "cycle/010/integration",
            },
            {
                "story_group": "dashboard",
                "jira_keys": ("SCRUM-213", "SCRUM-228"),
                "status": "in_review",
                "source": "manifest",
                "cycle": "010",
                "branch": "cycle/010/integration",
            },
            {
                "story_group": "exports",
                "jira_keys": ("SCRUM-226",),
                "status": "done",
                "source": "report",
                "cycle": "010",
                "branch": "cycle/010/integration",
            },
        ]
    )
    assert len(rows) == 1
    assert rows[0]["story_group"] == "dashboard"
    assert rows[0]["jira_keys"] == ["SCRUM-212", "SCRUM-213", "SCRUM-228"]
    assert rows[0]["sources"] == ["manifest", "report"]


def test_report_placeholder_exports_include_new_mapping_constants() -> None:
    assert "governance" in JIRA_MAPPING_TYPES
    assert "product" in JIRA_MAPPING_TYPES
    assert "cursor_agent" in JIRA_UPDATED_BY_VALUES
    assert "in_review" in ACTIVE_STORY_STATUSES


def test_integration_evidence_summary_contains_validation_and_jira_progress_rows() -> None:
    summary = build_integration_evidence_summary(
        stage_status={"collection": "pass", "analysis": "warning"},
        codex_status="resolved",
        codecov_project_status="pass",
        codecov_patch_status="warning",
        jira_progress=[
            {
                "jira_key": "SCRUM-226",
                "ac_advanced": "CSV/JSON/Markdown helper contracts added.",
                "dod_remaining": "Full live export orchestration remains open.",
                "status_recommendation": "in_review",
            }
        ],
    )
    assert summary["validation_commands"] == list(DEFAULT_VALIDATION_COMMANDS)
    assert summary["stage_status"]["analysis"] == "warning"
    assert summary["codex_status"] == "resolved"
    assert summary["codecov"] == {"project": "pass", "patch": "warning"}
    assert summary["jira_progress"][0]["jira_key"] == "SCRUM-226"
    assert summary["summary"]["validation_count"] == len(DEFAULT_VALIDATION_COMMANDS)


def test_runtime_diagnostics_markdown_table_renders_categories() -> None:
    rendered = build_runtime_diagnostics_markdown_table(
        diagnostics={
            "categories": {
                "app_readiness": "ok",
                "alerts": "warning",
                "integration_evidence": "error",
            },
            "warning_categories": ["alerts"],
            "blocking_categories": ["integration_evidence"],
        }
    )
    assert "| Diagnostic | Status | Severity | Notes |" in rendered
    assert "| app_readiness | ok | ok | ready |" in rendered
    assert "| alerts | warning | warning | review recommended |" in rendered
    assert "| integration_evidence | error | error | blocking |" in rendered


def test_build_analysis_summary_rows_clamps_invalid_fields_and_skips_duplicates() -> None:
    rows, warnings = build_analysis_summary_rows(
        [
            {
                "id": "gig-1",
                "stage": "gig_quality",
                "status": "completed",
                "score": 130,
                "confidence": -0.2,
                "warning_count": 1,
                "source_id": "run-1",
            },
            {
                "id": "gig-1",
                "stage": "gig_quality",
                "status": "completed",
                "score": 80,
                "confidence": 0.8,
            },
        ]
    )
    assert len(rows) == 1
    assert rows[0]["score"] == 100.0
    assert rows[0]["confidence"] == 0.0
    assert any(item["code"] == "duplicate_identifier" for item in warnings)
    assert any(item["code"] == "score_clamped" for item in warnings)
    assert any(item["code"] == "confidence_clamped" for item in warnings)


def test_build_analysis_export_summary_returns_rows_and_warnings() -> None:
    summary = build_analysis_export_summary(
        [
            {
                "id": "sat-1",
                "stage": "saturation",
                "status": "completed",
                "score": 71.2,
                "confidence": 0.81,
                "warning_count": 0,
                "source_id": "run-2",
            }
        ]
    )
    assert summary["row_count"] == 1
    assert len(summary["rows"]) == 1
    assert summary["warnings"] == []

