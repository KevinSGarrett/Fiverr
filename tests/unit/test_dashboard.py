"""Unit tests for dashboard presentation scaffolding."""

from __future__ import annotations

import builtins
import importlib
import sys
from dataclasses import asdict


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
        "niches",
        "keywords",
        "collection_runs",
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
    assert any(row["category"] == "local_parity" for row in page_state["categories"])
    assert page_state["summary"]["error"] == 1


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
    assert opportunities["empty_state"] is True
    assert "confidence" in opportunities["table_columns"]
    assert keywords["columns"] == [
        "keyword",
        "niche",
        "cluster",
        "score",
        "confidence",
        "freshness_status",
    ]
    assert run_history["columns"][0] == "run_id"
    assert run_history["empty_state"] is True


def test_alert_readiness_placeholders_normalize_unknown_severity_and_missing_jira_keys() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    alerts = app_module.build_alert_readiness_placeholders(
        [
            {"severity": "warning", "source": "governance", "jira_key": "SCRUM-228", "message": "Needs review"},
            {"severity": "critical", "source": "ci", "jira_key": "", "message": "Unknown severity"},
        ]
    )
    assert alerts[0]["severity"] == "warning"
    assert alerts[0]["jira_key"] == "SCRUM-228"
    assert alerts[1]["severity"] == "unknown"
    assert alerts[1]["jira_key"] == "UNMAPPED"


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
    assert any("codecov_project: pending" in line for line in fake_streamlit.write_calls)
    assert any("codex_disposition: pending" in line for line in fake_streamlit.write_calls)

