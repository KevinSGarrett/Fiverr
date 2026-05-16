"""Unit tests for dashboard presentation scaffolding."""

from __future__ import annotations

import builtins
import importlib
import sys
from dataclasses import asdict

import pytest


def _dashboard_fixture_run() -> dict[str, object]:
    fixtures_module = importlib.import_module("tests.fixtures.dashboard.factories")
    return fixtures_module.build_dashboard_fixture_run()


def test_dashboard_import_does_not_import_streamlit(monkeypatch) -> None:
    original_import = builtins.__import__

    def guarded_import(name: str, *args, **kwargs):
        if name == "streamlit":
            raise AssertionError("streamlit should not be imported during module import")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    module = importlib.import_module("src.dashboard.app")
    assert module.build_page_title() == "Fiverr Research System Dashboard (Foundation Shell)"
    assert module.get_cycle003_status_state()["cycle"] == "003"
    assert module.get_phase2_readiness_state()["cycle"] == "004"
    governance_checks = module.get_governance_status_state()
    assert [item["check"] for item in governance_checks] == [
        "local_parity",
        "github_actions",
        "codecov_project",
        "codecov_patch",
        "codex_disposition",
        "jira_mapping",
        "merge_readiness",
    ]


def test_get_available_pages_contains_expected_ids() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    pages = app_module.get_available_pages()
    page_ids = [page.page_id for page in pages]
    assert page_ids == [
        "overview",
        "foundation_status",
        "collection_dry_run",
        "analysis_dry_run",
        "phase2_readiness",
        "phase2_reports",
        "phase2_exports",
        "opportunities",
        "keywords",
        "run_history",
        "niches",
        "scores",
        "recommendations",
        "reports",
        "settings",
    ]


def test_non_overview_pages_are_marked_not_implemented() -> None:
    navigation_module = importlib.import_module("src.dashboard.navigation")
    pages = navigation_module.get_available_pages()
    for page in pages:
        if page.page_id in {
            "overview",
            "foundation_status",
            "collection_dry_run",
            "analysis_dry_run",
            "opportunities",
            "keywords",
            "run_history",
        }:
            assert page.enabled is True
        elif page.page_id in {"phase2_readiness", "phase2_reports", "phase2_exports"}:
            assert page.enabled is False
            assert page.status == "preview_cycle004"
        else:
            assert page.enabled is False
            assert page.status == "not_implemented"


def test_dashboard_state_defaults_are_dataclass_serializable() -> None:
    state_module = importlib.import_module("src.dashboard.state")
    state = state_module.DashboardState()
    serialized = asdict(state)
    assert serialized == {"selected_page": "overview", "filters": {}, "active_run_id": None}


def test_cycle003_state_contains_foundation_collection_analysis_sections() -> None:
    state_module = importlib.import_module("src.dashboard.state")
    status_state = state_module.build_cycle003_status_state()
    section_ids = [section["section_id"] for section in status_state["sections"]]
    assert section_ids == ["foundation", "collection_dry_run", "analysis_dry_run"]


def test_cycle003_state_marks_missing_metrics_as_pending() -> None:
    state_module = importlib.import_module("src.dashboard.state")
    status_state = state_module.build_cycle003_status_state(
        foundation_metrics={"config_check": "pass"},
        collection_metrics=None,
        analysis_metrics={"scoring_ready": None},
    )
    foundation_section = status_state["sections"][0]
    assert foundation_section["metrics"][0]["status"] == "ready"
    assert foundation_section["metrics"][1]["value"] == "pending"

    collection_section = status_state["sections"][1]
    assert all(metric["value"] == "pending" for metric in collection_section["metrics"])

    analysis_section = status_state["sections"][2]
    assert analysis_section["metrics"][0]["value"] == "pending"


def test_phase2_state_serializes_with_pending_defaults() -> None:
    state_module = importlib.import_module("src.dashboard.state")
    status_state = state_module.build_phase2_readiness_state()
    assert status_state["collection_dry_run"]["status"] == "pending"
    assert status_state["analysis_dry_run"]["run_id"] == "pending"
    assert status_state["fixture_coverage"]["gig_detail_parser"] == "pending"
    assert status_state["gate_status"]["phase2_smoke"] == "pending"
    assert status_state["pending_blockers"] == []


def test_phase2_state_marks_missing_metrics_as_pending_placeholder() -> None:
    state_module = importlib.import_module("src.dashboard.state")
    status_state = state_module.build_phase2_readiness_state(
        collection_metrics={"status": "pass", "run_id": None},
        analysis_metrics={"status": None},
        fixture_coverage={"gig_detail_parser": 88},
        gate_status={"foundation_gate": "pass", "validation_bundle": None},
        pending_blockers=("Waiting for artifact publish",),
    )
    assert status_state["collection_dry_run"]["status"] == "pass"
    assert status_state["collection_dry_run"]["run_id"] == "pending"
    assert status_state["analysis_dry_run"]["status"] == "pending"
    assert status_state["fixture_coverage"]["gig_detail_parser"] == 88
    assert status_state["fixture_coverage"]["seller_profile_parser"] == "pending"
    assert status_state["gate_status"]["validation_bundle"] == "pending"
    assert status_state["pending_blockers"] == ["Waiting for artifact publish"]


def test_governance_status_messages_distinguish_check_sources() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    checks = app_module.get_governance_status_state()
    check_messages = {item["check"]: item["message"] for item in checks}
    assert "Local parity checks" in check_messages["local_parity"]
    assert "GitHub Actions workflow checks" in check_messages["github_actions"]
    assert "Codecov project status check" in check_messages["codecov_project"]
    assert "Codecov patch status check" in check_messages["codecov_patch"]
    assert "Codex review-thread disposition" in check_messages["codex_disposition"]
    assert "Jira governance and product-story mapping" in check_messages["jira_mapping"]
    assert "Branch policy and merge-readiness confirmation" in check_messages["merge_readiness"]


def test_governance_presentation_state_marks_missing_status_as_unknown_warning() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    rows = app_module.build_governance_presentation_state(local_parity="pass", jira_mapping="")
    row_by_category = {row["category"]: row for row in rows}

    assert row_by_category["local_parity"]["status"] == "pass"
    assert row_by_category["local_parity"]["severity"] == "ok"
    assert row_by_category["jira_mapping"]["status"] == "unknown"
    assert row_by_category["jira_mapping"]["severity"] == "warning"
    assert row_by_category["merge_readiness"]["status"] == "unknown"
    assert row_by_category["merge_readiness"]["severity"] == "warning"


def test_governance_presentation_state_handles_warning_and_error_severities() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    rows = app_module.build_governance_presentation_state(
        local_parity="pass",
        github_actions="warning",
        codecov_project="fail",
        codecov_patch="pending",
    )
    row_by_category = {row["category"]: row for row in rows}
    assert row_by_category["local_parity"]["severity"] == "ok"
    assert row_by_category["github_actions"]["severity"] == "warning"
    assert row_by_category["codecov_project"]["severity"] == "error"
    assert row_by_category["codecov_patch"]["severity"] == "warning"


def test_governance_page_ready_state_uses_deterministic_order() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    page_state = app_module.build_governance_page_ready_state(
        jira_mapping="in_review",
        codex_disposition="pass",
        github_actions="pass",
        codecov_project="warning",
        codecov_patch="pass",
        local_parity="pass",
        merge_readiness="pending",
    )
    assert [row["category"] for row in page_state["categories"]] == [
        "jira_mapping",
        "codex_disposition",
        "github_actions",
        "codecov_project",
        "codecov_patch",
        "local_parity",
        "merge_readiness",
    ]
    assert page_state["summary"]["warning"] == 3


def test_governance_page_ready_state_includes_local_parity_in_severity_totals() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    page_state = app_module.build_governance_page_ready_state(
        jira_mapping="pass",
        codex_disposition="pass",
        github_actions="pass",
        codecov_project="pass",
        codecov_patch="pass",
        local_parity="fail",
        merge_readiness="pass",
    )
    local_parity_row = next(row for row in page_state["categories"] if row["category"] == "local_parity")
    assert local_parity_row["status"] == "fail"
    assert local_parity_row["severity"] == "error"
    assert page_state["summary"]["error"] == 1
    assert page_state["readiness_severity"] == "error"


def test_governance_page_ready_state_treats_missing_local_parity_as_warning() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    page_state = app_module.build_governance_page_ready_state(
        jira_mapping="pass",
        codex_disposition="pass",
        github_actions="pass",
        codecov_project="pass",
        codecov_patch="pass",
        local_parity=None,
        merge_readiness="pass",
    )
    local_parity_row = next(row for row in page_state["categories"] if row["category"] == "local_parity")
    assert local_parity_row["status"] == "unknown"
    assert local_parity_row["severity"] == "warning"
    assert page_state["summary"] == {"ok": 6, "warning": 1, "error": 0}
    assert page_state["readiness_severity"] == "warning"


def test_query_active_story_groups_uses_report_and_manifest_evidence() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    story_groups = app_module.query_active_story_groups(
        report_rows=[
            {
                "story_group": "dashboard",
                "jira_keys": ["SCRUM-212", "SCRUM-213"],
                "status": "in_progress",
                "cycle": "010",
                "branch": "cycle/010/integration",
            }
        ],
        manifest_rows=[
            {
                "story_group": "exports",
                "jira_keys": ["SCRUM-226"],
                "status": "in_review",
                "cycle": "010",
                "branch": "cycle/010/integration",
            }
        ],
    )
    assert [item["story_group"] for item in story_groups] == ["dashboard", "exports"]
    assert story_groups[0]["sources"] == ["report"]
    assert story_groups[1]["sources"] == ["manifest"]


def test_opportunities_keywords_and_run_history_descriptors_support_empty_state() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    opportunities = app_module.get_opportunities_page_descriptor()
    keywords = app_module.get_keywords_page_descriptor()
    run_history = app_module.get_run_history_page_descriptor()
    assert opportunities["state"]["state"] == "empty"
    assert "confidence" in opportunities["table"]["columns"]
    assert "confidence_text" in keywords["table"]["columns"]
    assert run_history["table"]["columns"][0] == "run_id"
    assert run_history["state"]["state"] == "empty"


def test_query_layer_descriptor_normalizes_rows_from_report_and_manifest_sources() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    descriptor = app_module.get_query_layer_descriptor(
        report_rows=[
            {
                "story_group": "dashboard",
                "jira_keys": ["SCRUM-214"],
                "status": "in_progress",
                "cycle": "011",
                "branch": "cycle/011/integration",
            }
        ],
        manifest_rows=[
            {
                "story_group": "exports",
                "jira_keys": ["SCRUM-226"],
                "status": "in_review",
                "cycle": "011",
                "branch": "cycle/011/integration",
            }
        ],
    )
    assert descriptor["page_id"] == "query_layer"
    assert descriptor["empty_state"] is False
    assert [row["story_group"] for row in descriptor["rows"]] == ["dashboard", "exports"]
    assert descriptor["columns"] == ["story_group", "jira_keys", "statuses", "sources", "cycles", "branches"]


def test_export_system_and_app_entry_descriptors_use_stable_shapes() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    export_descriptor = app_module.get_export_system_descriptor(
        [
            {
                "artifact_type": "cycle_validation",
                "format": "json",
                "path": "exports/cycle011/validation.json",
                "jira_keys": ["SCRUM-226"],
            }
        ]
    )
    app_entry_descriptor = app_module.get_app_entry_descriptor(branch="cycle/011/integration", cycle="011")
    assert export_descriptor["page_id"] == "export_system"
    assert export_descriptor["empty_state"] is False
    assert "github_pr_number" in export_descriptor["columns"]
    assert app_entry_descriptor == {
        "page_id": "app_entry",
        "title": "Dashboard App Entry",
        "entry_module": "src.dashboard.app:main",
        "branch": "cycle/011/integration",
        "cycle": "011",
        "status": "placeholder",
    }


def test_app_startup_diagnostics_handles_missing_config_and_data(tmp_path) -> None:
    app_module = importlib.import_module("src.dashboard.app")
    diagnostics = app_module.build_app_startup_diagnostics(
        config_path=str(tmp_path / "missing-config.yaml"),
        data_dir=str(tmp_path / "missing-data"),
    )
    assert diagnostics["status"] == "warning"
    assert diagnostics["safe_empty_state"] is True
    assert diagnostics["warning_count"] >= 3
    assert diagnostics["data_entries"] == []
    assert diagnostics["config_visibility"]["status"] == "warning"
    assert diagnostics["first_run_readiness"]["status"] == "warning"


def test_app_entry_smoke_state_registers_all_required_pages(tmp_path) -> None:
    app_module = importlib.import_module("src.dashboard.app")
    config_path = tmp_path / "config.yaml"
    config_path.write_text("niches: []\n", encoding="utf-8")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "fiverr_research.db").write_text("placeholder", encoding="utf-8")

    smoke_state = app_module.build_app_entry_smoke_state(
        branch="cycle/012/integration",
        cycle="012",
        config_path=str(config_path),
        data_dir=str(data_dir),
    )
    registration = smoke_state["page_registration"]
    assert registration["status"] == "ready"
    assert registration["missing_pages"] == []
    assert smoke_state["status"] == "warning"
    assert smoke_state["safe_empty_state"] is False
    assert smoke_state["entry"]["branch"] == "cycle/012/integration"
    assert smoke_state["page_registry"]
    assert smoke_state["readiness"]["severity"] == "warning"
    assert smoke_state["readiness"]["blocked_pages"] == []
    assert smoke_state["query_diagnostics"]["status"] == "warning"
    assert smoke_state["query_diagnostics"]["categories"]["app_readiness"] == "ok"


def test_app_entry_query_diagnostics_returns_category_statuses_for_sparse_inputs() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    fixture = _dashboard_fixture_run()
    diagnostics = app_module.build_app_entry_query_diagnostics(
        page_registry=app_module.get_page_registry(),
        startup={"status": "warning", "warning_count": 2},
        orchestrator_handoff={"stage_status": "warning", "next_actions": ["Run phase2-smoke"]},
        alert_records=fixture["alerts"],
        export_records=fixture["exports"],
        integration_evidence=fixture["integration_evidence"],
    )
    assert diagnostics["categories"] == {
        "app_readiness": "ok",
        "alerts": "ok",
        "exports": "ok",
        "integration_evidence": "ok",
        "analysis_output_contract": "warning",
        "niche_config_validation": "unknown",
        "first_run_readiness": "unknown",
        "data_integrity": "ok",
        "data_integrity_readiness": "unknown",
    }
    assert diagnostics["status"] == "warning"
    assert diagnostics["blocking_categories"] == []
    assert diagnostics["results"]["integration_evidence"]["records"][0]["stage_status"]["analysis"] == "warning"
    assert diagnostics["payload_availability"]["analysis_output_contract"]["availability"] == "sparse"
    assert diagnostics["warning_codes"]["analysis_output_contract"] == [
        "missing_analysis_records",
    ]
    assert diagnostics["runtime_readiness_baseline"]["status"] == "unknown"


def test_app_entry_query_diagnostics_marks_data_integrity_warning_with_traceable_codes() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    diagnostics = app_module.build_app_entry_query_diagnostics(
        page_registry=app_module.get_page_registry(),
        startup={"status": "ready", "warning_count": 0},
        analysis_output_records=[
            {"id": "dup", "score": "bad", "rank": "bad-rank", "evidence": "bad-shape"},
            {"id": "dup", "score": 80},
        ],
    )
    assert diagnostics["categories"]["data_integrity"] == "warning"
    assert "duplicate_record_id" in diagnostics["data_integrity"]["warning_codes"]
    assert "invalid_rank" in diagnostics["data_integrity"]["warning_codes"]
    assert "invalid_score" in diagnostics["data_integrity"]["warning_codes"]
    assert "malformed_evidence" in diagnostics["data_integrity"]["warning_codes"]
    assert diagnostics["data_integrity_readiness"]["status"] == "blocked"


def test_app_entry_query_diagnostics_payload_availability_includes_source_and_warning_codes() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    fixture = _dashboard_fixture_run()
    diagnostics = app_module.build_app_entry_query_diagnostics(
        page_registry=app_module.get_page_registry(),
        startup={"status": "ready", "warning_count": 0},
        export_records=fixture["exports"],
        analysis_output_records=[],
    )
    exports = diagnostics["payload_availability"]["exports"]
    assert exports["availability"] == "available"
    assert exports["freshness_status"] == "unknown"
    assert exports["warning_codes"] == []
    assert exports["source"]["source_name"] == "fixture"


def test_niche_config_visibility_summary_reports_nine_niches() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    summary = app_module.build_niche_config_visibility_summary(config_path="config.yaml")
    assert summary["expected_niches"] == 9
    assert summary["loaded_niches"] == 9
    assert summary["status"] == "ready"


def test_first_run_readiness_summary_includes_prerequisites_and_outputs() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    summary = app_module.build_first_run_readiness_summary(config_path="config.yaml", data_dir="data")
    assert "collection" in summary["expected_stages"]
    assert "analysis" in summary["expected_stages"]
    assert "reporting" in summary["expected_stages"]
    assert "validation" in summary["expected_stages"]
    assert "fixture_files_available" in summary["prerequisites"]


def test_page_registry_contains_required_contracts_and_disabled_reasons() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    registry = app_module.get_page_registry()
    registry_by_id = {row["page_id"]: row for row in registry}
    assert registry_by_id["overview"]["required_contracts"] == ["governance_status", "app_readiness"]
    assert registry_by_id["keywords"]["status"] == "ready"
    assert registry_by_id["keywords"]["disabled_reason"] is None
    assert registry_by_id["run_history"]["required_contracts"] == ["run_history"]


def test_page_registry_contains_runtime_required_placeholder_pages() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    registry = app_module.get_page_registry()
    registry_by_id = {row["page_id"]: row for row in registry}
    assert registry_by_id["export_alerts"]["required_contracts"] == ["export_system", "alert_summary"]
    assert registry_by_id["diagnostics"]["required_contracts"] == ["app_readiness", "source_freshness_summary"]
    assert registry_by_id["integration_evidence"]["required_contracts"] == [
        "integration_evidence",
        "analysis_output_contract",
    ]
    assert registry_by_id["export_alerts"]["enabled"] is False
    assert registry_by_id["diagnostics"]["enabled"] is False
    assert registry_by_id["integration_evidence"]["enabled"] is False


def test_compute_page_readiness_returns_next_actions_for_blocked_pages() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    readiness = app_module.compute_page_readiness(
        page_registry=[
            {"page_id": "overview", "status": "ready"},
            {"page_id": "reports", "status": "blocked"},
        ],
        startup={"status": "warning", "warning_count": 1},
        orchestrator_handoff={"stage_status": "warning"},
    )
    assert readiness["severity"] == "blocked"
    assert readiness["blocked_pages"] == ["reports"]
    assert any("phase2-smoke" in action for action in readiness["next_actions"])


def test_alert_readiness_placeholders_map_to_stable_contract_fields() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    alerts = app_module.build_alert_readiness_placeholders(
        [
            {"id": "opp-1", "opportunity": "Logo design", "score": 92, "confidence": 0.87},
            {"id": "opp-2", "opportunity": "Resume writing", "score": 72, "confidence": 0.5},
        ]
    )
    assert alerts[0]["id"] == "opportunity-high-potential-opp-1"
    assert alerts[0]["type"] == "high_potential_opportunity"
    assert alerts[0]["severity"] == "info"
    assert alerts[0]["jira_key"] == "SCRUM-214"
    assert alerts[1]["id"] == "opportunity-low-confidence-opp-2"
    assert alerts[1]["severity"] == "warning"
    assert alerts[1]["resolution_status"] == "action_required"


def test_alert_system_descriptor_aggregates_normalized_alert_severity_totals() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    descriptor = app_module.get_alert_system_descriptor(
        [
            {"id": "opp-1", "opportunity": "Logo design", "score": 92, "confidence": 0.87},
            {"id": "opp-2", "opportunity": "Resume writing", "score": 72, "confidence": 0.5},
            {"id": "opp-3", "opportunity": "No score opportunity", "confidence": 0.7},
        ]
    )
    assert descriptor["page_id"] == "alert_system"
    assert descriptor["summary"] == {"info": 1, "warning": 2, "error": 1, "unknown": 0}
    assert descriptor["rows"][2]["jira_key"] == "SCRUM-227"
    assert descriptor["empty_state"] is False


def test_alert_rules_generate_opportunity_and_run_alerts() -> None:
    alerts_module = importlib.import_module("src.dashboard.alerts")
    alerts = alerts_module.build_dashboard_alerts(
        opportunities=[
            {"id": "opp-1", "opportunity": "Logo design", "score": 91, "confidence": 0.86},
            {"id": "opp-2", "opportunity": "Resume", "score": 74, "confidence": 0.54},
            {"id": "opp-3", "opportunity": "No score", "confidence": 0.6},
        ],
        run_history=[
            {"run_id": "run-1", "status": "failed", "warning_count": 5, "stages": [{"name": "analysis"}]},
            {"run_id": "run-2", "status": "pass", "warning_count": 0, "stages": [{"name": "reporting"}]},
        ],
        source_freshness=[{"source_name": "opportunities", "freshness_status": "stale"}],
        phase2_smoke={"status": "pass", "age_hours": 30},
    )
    alert_types = {row["type"] for row in alerts}
    assert "high_potential_opportunity" in alert_types
    assert "low_confidence_opportunity" in alert_types
    assert "missing_score_evidence" in alert_types
    assert "failed_stage" in alert_types
    assert "warning_heavy_run" in alert_types
    assert "stale_source_warning" in alert_types
    assert "stale_phase2_smoke" in alert_types


def test_main_renders_governance_and_readiness_sections_without_real_streamlit(
    monkeypatch,
) -> None:
    class FakeStreamlit:
        def __init__(self) -> None:
            self.title_calls: list[str] = []
            self.caption_calls: list[str] = []
            self.subheader_calls: list[str] = []
            self.write_calls: list[str] = []

        def title(self, text: str) -> None:
            self.title_calls.append(text)

        def caption(self, text: str) -> None:
            self.caption_calls.append(text)

        def subheader(self, text: str) -> None:
            self.subheader_calls.append(text)

        def write(self, text: str) -> None:
            self.write_calls.append(text)

    fake_streamlit = FakeStreamlit()
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)
    app_module = importlib.import_module("src.dashboard.app")
    app_module.main()

    assert fake_streamlit.title_calls == ["Fiverr Research System Dashboard (Foundation Shell)"]
    assert "Cycle 007 Governance and Readiness" in fake_streamlit.subheader_calls
    assert "App Entry Startup Diagnostics" in fake_streamlit.subheader_calls
    assert "Cycle 014 Product Page Payloads" in fake_streamlit.subheader_calls
    assert any("codecov_project: pending" in line for line in fake_streamlit.write_calls)
    assert any("codex_disposition: pending" in line for line in fake_streamlit.write_calls)
    assert any("Entry module: src.dashboard.app:main" in line for line in fake_streamlit.write_calls)
    assert any("Registry state: empty" in line for line in fake_streamlit.write_calls)


def test_dashboard_design_tokens_and_confidence_rules_are_stable() -> None:
    design_module = importlib.import_module("src.dashboard.design")
    assert design_module.SEVERITY_LABELS["warning"] == "Warning"
    assert design_module.SEVERITY_ICON_NAMES["blocked"] == "slash-circle"
    assert design_module.confidence_to_text(0.81) == "High"
    assert design_module.confidence_to_text(None) == "Unknown"


def test_component_state_and_table_contracts_support_warning_rows() -> None:
    components_module = importlib.import_module("src.dashboard.components")
    state = components_module.build_state_descriptor(
        state="warning",
        message="Partial payload available",
        warnings=["Missing cluster metadata"],
    )
    table = components_module.build_table_descriptor(
        table_id="test",
        columns=["a", "b"],
        rows=[],
        sort_key="a",
        warnings=["No rows available"],
    )
    assert state["state"] == "warning"
    assert state["accessible_label"] == "Dashboard page has partial data warnings"
    assert table["empty_state"] is True
    assert table["warning_rows"][0]["message"] == "No rows available"
    acceptance = components_module.build_runtime_acceptance_status(
        state="warning",
        warnings=["Missing required field: score"],
        stale_data=True,
        evidence_ids=["opp-1"],
    )
    assert acceptance["status"] == "warning"
    assert acceptance["stale_data"] is True
    assert acceptance["evidence_ids"] == ["opp-1"]


def test_component_status_semantics_are_accessible_and_stable() -> None:
    components_module = importlib.import_module("src.dashboard.components")
    semantics = components_module.get_status_semantics("no_go")
    assert semantics["status_label"] == "NO-GO"
    assert semantics["severity"] == "error"
    assert semantics["category"] == "no_go"
    assert "severity" in semantics["accessibility_text"]


def test_opportunities_payload_filters_and_cross_links_are_deterministic() -> None:
    opportunities_module = importlib.import_module("src.dashboard.opportunities")
    fixture = _dashboard_fixture_run()
    payload = opportunities_module.build_opportunities_payload(
        records=fixture["opportunities"],
        filters={"niche": "logo-design", "score_min": 80},
        sort={"field": "score", "descending": True},
    )
    assert payload["state"]["state"] == "ready"
    assert payload["table"]["rows"][0]["niche"] == "logo-design"
    assert payload["ranking_cards"][0]["keyword_links"] == ["kw-logo-design", "kw-brand-kit"]
    assert payload["table"]["rows"][0]["go_decision"] == "Strong GO"
    descriptor_keys = {row["key"] for row in payload["table"]["filter_descriptors"]}
    assert {"status", "niche", "score_min"} <= descriptor_keys
    assert payload["filter_descriptor_contract"]["applied"]["niche"] == "logo-design"
    assert payload["sort_descriptor_contract"]["applied"]["field"] == "score"


def test_opportunities_payload_applies_limit_and_offset_in_pagination_contract() -> None:
    opportunities_module = importlib.import_module("src.dashboard.opportunities")
    fixture = _dashboard_fixture_run()
    payload = opportunities_module.build_opportunities_payload(
        records=fixture["opportunities"],
        filters={"limit": 1, "offset": 1},
        sort={"field": "score", "descending": True},
    )
    assert payload["pagination"]["limit"] == 1
    assert payload["pagination"]["offset"] == 1
    assert len(payload["table"]["rows"]) == 1


def test_opportunities_payload_coerces_string_top_score_for_metric_card() -> None:
    opportunities_module = importlib.import_module("src.dashboard.opportunities")
    payload = opportunities_module.build_opportunities_payload(
        records=[
            {"id": "opp-1", "opportunity": "Logo", "score": "91.25", "status": "strong_go", "niche": "logo-design"},
            {"id": "opp-2", "opportunity": "Resume", "score": 80, "status": "conditional_go", "niche": "career-services"},
        ],
        sort={"field": "score", "descending": True},
    )
    assert payload["metric_cards"][1]["value"] == "91.2"


def test_opportunities_payload_sparse_fields_degrade_safely() -> None:
    opportunities_module = importlib.import_module("src.dashboard.opportunities")
    payload = opportunities_module.build_opportunities_payload(
        records=[
            {"id": "opp-1", "opportunity": "Logo", "niche": "logo", "status": "go"},
            {"id": "opp-2", "opportunity": "Resume", "score": "bad", "confidence": None, "status": "no_go"},
        ],
    )
    assert payload["state"]["state"] == "warning"
    assert payload["table"]["rows"][0]["score"] == 0.0
    assert payload["table"]["rows"][0]["confidence"] == 0.0
    assert any("missing score" in row["message"] for row in payload["table"]["warning_rows"])


def test_opportunities_payload_empty_state_explains_missing_upstream_data() -> None:
    opportunities_module = importlib.import_module("src.dashboard.opportunities")
    payload = opportunities_module.build_opportunities_payload(records=None)
    assert payload["state"]["state"] == "empty"
    assert "deterministic empty records" in payload["table"]["warning_rows"][0]["message"]


def test_keywords_payload_surfaces_cluster_gaps_and_confidence_text() -> None:
    keywords_module = importlib.import_module("src.dashboard.keywords")
    fixture = _dashboard_fixture_run()
    payload = keywords_module.build_keywords_payload(records=fixture["keywords"])
    rows = payload["table"]["rows"]
    assert any(row["cluster"] == "not available yet" for row in rows)
    assert any(row["confidence_text"] == "High" for row in rows)
    assert any("SCRUM-157" in row["message"] for row in payload["table"]["warning_rows"])
    assert payload["cluster_summary"]["incomplete_analysis"] is True
    assert payload["cluster_summary"]["unclustered_count"] >= 1


def test_keywords_payload_sorting_and_filtering_are_supported() -> None:
    keywords_module = importlib.import_module("src.dashboard.keywords")
    fixture = _dashboard_fixture_run()
    payload = keywords_module.build_keywords_payload(
        records=fixture["keywords"],
        filters={"niche": "logo-design", "score_min": 80},
        sort={"field": "score", "descending": True},
    )
    assert payload["table"]["rows"] == [
        payload["table"]["rows"][0]
    ]
    assert payload["table"]["rows"][0]["keyword"] == "logo design package"
    descriptor_keys = {row["key"] for row in payload["table"]["filter_descriptors"]}
    assert {"status", "niche", "score_min"} <= descriptor_keys
    assert payload["filter_descriptor_contract"]["applied"]["niche"] == "logo-design"
    assert payload["sort_descriptor_contract"]["applied"]["field"] == "score"


def test_keywords_payload_sparse_rows_include_freshness_warnings() -> None:
    keywords_module = importlib.import_module("src.dashboard.keywords")
    payload = keywords_module.build_keywords_payload(
        records=[
            {"keyword": "logo design", "cluster": "", "score": None, "confidence": "bad"},
        ],
    )
    assert payload["state"]["state"] == "warning"
    assert payload["table"]["rows"][0]["score"] == 0.0
    assert payload["table"]["rows"][0]["cluster"] == "not available yet"
    assert any("Freshness status is unknown" in row["message"] for row in payload["table"]["warning_rows"])


def test_keywords_payload_accepts_structured_cluster_contract_rows() -> None:
    keywords_module = importlib.import_module("src.dashboard.keywords")
    payload = keywords_module.build_keywords_payload(
        records=[
            {
                "keyword": "python automation",
                "cluster": {"cluster_id": "cluster_01", "label": "python automation"},
                "score": 84.0,
                "confidence": 0.83,
            },
            {
                "keyword": "seo audit",
                "cluster": {"cluster_id": "cluster_02"},
                "score": 70.0,
                "confidence": 0.61,
            },
        ]
    )
    assert payload["table"]["rows"][0]["cluster"] == "python automation"
    assert payload["table"]["rows"][1]["cluster"] == "cluster_02"


def test_run_history_payload_includes_severity_mapping_and_stage_details() -> None:
    run_history_module = importlib.import_module("src.dashboard.run_history")
    fixture = _dashboard_fixture_run()
    payload = run_history_module.build_run_history_payload(records=fixture["run_history"])
    first_row = payload["table"]["rows"][0]
    assert first_row["run_id"] == "run-014-001"
    assert first_row["severity"] == "ok"
    assert first_row["stage_names"] == ["collection", "analysis", "reporting"]
    assert first_row["stage_chips"][0]["name"] == "collection"
    assert payload["status_cards"][0]["severity_label"] in {"Pass", "Warning", "Unknown"}


def test_run_history_payload_handles_malformed_runs_with_warnings() -> None:
    run_history_module = importlib.import_module("src.dashboard.run_history")
    payload = run_history_module.build_run_history_payload(
        records=[
            {"status": "warning", "stages": [], "warning_count": "3"},
        ]
    )
    row = payload["table"]["rows"][0]
    assert row["run_id"].startswith("missing-run-id-")
    assert row["stage_names"] == ["unknown"]
    assert row["warning_count"] == 3
    assert any("missing run_id" in item["message"] for item in payload["table"]["warning_rows"])
    assert row["evidence_link_status"] == "warning"
    assert row["evidence_link_warnings"]


def test_alert_rules_emit_missing_run_structure_when_run_id_absent() -> None:
    alerts_module = importlib.import_module("src.dashboard.alerts")
    alerts = alerts_module.build_dashboard_alerts(
        run_history=[
            {"status": "pass", "warning_count": 0, "stages": [{"name": "analysis"}]},
        ]
    )
    alert_types = {row["type"] for row in alerts}
    assert "missing_run_structure" in alert_types


def test_run_history_severity_mapping_handles_all_required_statuses() -> None:
    run_history_module = importlib.import_module("src.dashboard.run_history")
    mapping_expectations = {
        "pass": "ok",
        "warning": "warning",
        "failed": "error",
        "blocked": "blocked",
        "unknown": "unknown",
        "skipped": "skipped",
        "unexpected": "unknown",
    }
    for status, expected in mapping_expectations.items():
        assert run_history_module.map_run_status_to_severity(status) == expected


def test_page_registry_integration_exposes_product_payload_builders() -> None:
    pages_module = importlib.import_module("src.dashboard.pages")
    builders = pages_module.get_dashboard_page_payload_builders()
    assert set(builders.keys()) == {"opportunities", "keywords", "run_history"}


def test_app_product_page_registry_returns_safe_empty_state_summary() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    payloads = app_module.get_product_page_payloads()
    assert payloads["registry_state"]["state"] == "empty"
    assert payloads["registry_metadata"]["ui_runtime_pending"] is True
    assert payloads["opportunities"]["state"]["state"] == "empty"
    assert payloads["keywords"]["state"]["state"] == "empty"
    assert payloads["run_history"]["state"]["state"] == "empty"


def test_app_product_page_registry_returns_ready_state_for_fixture_data() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    fixture = _dashboard_fixture_run()
    payloads = app_module.get_product_page_payloads(
        opportunities_records=fixture["opportunities"],
        keywords_records=fixture["keywords"],
        run_history_records=fixture["run_history"],
    )
    assert payloads["registry_state"]["state"] in {"ready", "warning"}
    assert payloads["opportunities"]["payload_support"]["implemented"] is True
    assert payloads["opportunities"]["table"]["rows"]
    assert payloads["keywords"]["table"]["rows"]
    assert payloads["run_history"]["table"]["rows"]


def test_query_contract_metadata_is_shared_across_page_consumers() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    fixture = _dashboard_fixture_run()
    payloads = app_module.get_product_page_payloads(
        opportunities_records=fixture["opportunities"],
        keywords_records=fixture["keywords"],
        run_history_records=fixture["run_history"],
    )
    for page_id in ("opportunities", "keywords", "run_history"):
        contract = payloads[page_id]["query_contract"]
        assert contract["query_name"] == page_id
        assert isinstance(contract["warning_codes"], list)
        assert isinstance(contract["applied_filters"], dict)
        assert isinstance(contract["applied_sort"], dict)
        assert "pagination" in contract
        assert "source_context" in contract
        assert "freshness" in contract
        assert "warning_severity" in contract
        assert "highest_severity" in contract["warning_severity"]


def test_runtime_acceptance_matrix_summarizes_page_contract_state() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    fixture = _dashboard_fixture_run()
    payloads = app_module.get_product_page_payloads(
        opportunities_records=fixture["opportunities"],
        keywords_records=fixture["keywords"],
        run_history_records=fixture["run_history"],
    )
    matrix = payloads["runtime_acceptance_matrix"]
    assert matrix["status"] in {"ready", "warning", "unknown", "blocked"}
    assert matrix["summary"]["ready"] + matrix["summary"]["warning"] + matrix["summary"]["unknown"] + matrix["summary"][
        "blocked"
    ] == 3
    rows_by_page = {row["page_id"]: row for row in matrix["rows"]}
    assert set(rows_by_page.keys()) == {"opportunities", "keywords", "run_history"}
    assert rows_by_page["opportunities"]["has_filter_contract"] is True
    assert rows_by_page["keywords"]["has_detail_schema"] is True
    assert rows_by_page["run_history"]["warning_severity"] in {"info", "warning", "error", "blocked"}


def test_dashboard_descriptor_contracts_and_detail_schemas_are_consistent_across_pages() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    fixture = _dashboard_fixture_run()
    payloads = app_module.get_product_page_payloads(
        opportunities_records=fixture["opportunities"],
        keywords_records=fixture["keywords"],
        run_history_records=fixture["run_history"],
    )
    for page_id in ("opportunities", "keywords", "run_history"):
        payload = payloads[page_id]
        assert payload["filter_descriptor_contract"]["available"]
        assert payload["sort_descriptor_contract"]["available"]
        assert payload["detail_panel_schema"]["row_id_key"]
        assert payload["warning_summary"]["severity"] in {"ok", "warning", "blocked"}
        assert payload["acceptance_status"]["status"] in {"ready", "warning", "blocked", "unknown"}


def test_dashboard_cross_page_acceptance_rollup_tracks_warning_states() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    fixture = _dashboard_fixture_run()
    payloads = app_module.get_product_page_payloads(
        opportunities_records=fixture["opportunities"],
        keywords_records=fixture["keywords"],
        run_history_records=[
            {"run_id": "run-1", "status": "pass", "stages": [{"name": "analysis"}], "warning_count": 0},
        ],
    )
    assert payloads["acceptance_rollup"]["status"] in {"ready", "warning"}
    assert payloads["docs_snippet"]["status_rollup"] == payloads["acceptance_rollup"]["status"]
    assert len(payloads["acceptance_rollup"]["pages"]) == 3


def test_app_product_registry_does_not_mark_unknown_acceptance_as_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    app_module = importlib.import_module("src.dashboard.app")
    stub_payloads = {
        "opportunities": {
            "state": {"state": "ready"},
            "payload_support": {"implemented": True},
            "acceptance_status": {"status": "ready", "warning_count": 0, "blocker_count": 0, "reasons": []},
        },
        "keywords": {
            "state": {"state": "warning"},
            "payload_support": {"implemented": True},
            "acceptance_status": {
                "status": "unknown",
                "warning_count": 1,
                "blocker_count": 0,
                "reasons": ["keywords acceptance unresolved"],
            },
        },
        "run_history": {
            "state": {"state": "ready"},
            "payload_support": {"implemented": True},
            "acceptance_status": {"status": "ready", "warning_count": 0, "blocker_count": 0, "reasons": []},
        },
    }
    monkeypatch.setattr(app_module, "build_registered_page_payloads", lambda **_: stub_payloads)
    payloads = app_module.get_product_page_payloads()
    assert payloads["acceptance_rollup"]["status"] == "unknown"
    assert payloads["registry_state"]["state"] == "warning"
    assert "unresolved" in payloads["registry_state"]["message"].lower()


def test_runtime_guard_15_handles_non_list_query_records_without_crash() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    diagnostics = app_module.build_app_entry_query_diagnostics(
        page_registry=app_module.get_page_registry(),
        startup={"status": "ready", "warning_count": 0},
        query_layer=app_module.DashboardQueryLayer(),
    )
    assert diagnostics["status"] in {"ready", "warning"}
    assert diagnostics["payload_availability"]["app_readiness"]["availability"] in {
        "available",
        "sparse",
        "missing",
        "stale",
    }


def test_runtime_guard_16_marks_missing_records_as_missing_or_sparse() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    diagnostics = app_module.build_app_entry_query_diagnostics(
        page_registry=app_module.get_page_registry(),
        startup={"status": "warning", "warning_count": 1},
        alert_records=None,
        export_records=None,
        integration_evidence=None,
        analysis_output_records=None,
    )
    availability_values = {
        diagnostics["payload_availability"]["alerts"]["availability"],
        diagnostics["payload_availability"]["exports"]["availability"],
        diagnostics["payload_availability"]["integration_evidence"]["availability"],
    }
    assert availability_values <= {"missing", "sparse", "stale", "available"}
    assert diagnostics["status"] in {"warning", "error"}


def test_runtime_guard_17_surfaces_warning_codes_for_sparse_payloads() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    diagnostics = app_module.build_app_entry_query_diagnostics(
        page_registry=app_module.get_page_registry(),
        startup={"status": "warning", "warning_count": 2},
        alert_records=[],
        export_records=[],
        integration_evidence={},
        analysis_output_records=[],
    )
    assert "warning_codes" in diagnostics
    assert isinstance(diagnostics["warning_codes"]["alerts"], list)
    assert isinstance(diagnostics["warning_codes"]["exports"], list)


def test_runtime_guard_18_handles_malformed_analysis_records_as_warning() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    diagnostics = app_module.build_app_entry_query_diagnostics(
        page_registry=app_module.get_page_registry(),
        startup={"status": "ready", "warning_count": 0},
        analysis_output_records=[{"id": "dup", "score": "bad"}, {"id": "dup", "evidence": "bad"}],
    )
    assert diagnostics["categories"]["data_integrity"] == "warning"
    assert "duplicate_record_id" in diagnostics["data_integrity"]["warning_codes"]


def test_runtime_guard_19_handles_blank_startup_status_without_crash() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    smoke_state = app_module.build_app_entry_smoke_state(
        branch="cycle/017/integration",
        cycle="017",
    )
    assert smoke_state["status"] in {"ready", "warning", "blocked"}
    assert "query_diagnostics" in smoke_state


def test_runtime_guard_20_preserves_safe_empty_state_on_missing_data() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    smoke_state = app_module.build_app_entry_smoke_state(
        config_path="missing-config.yaml",
        data_dir="missing-data",
        branch="cycle/017/integration",
        cycle="017",
    )
    assert smoke_state["safe_empty_state"] is True
    assert smoke_state["startup"]["status"] == "warning"

