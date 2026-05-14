"""Unit tests for dashboard presentation scaffolding."""

from __future__ import annotations

import builtins
import importlib
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


def test_get_available_pages_contains_expected_ids() -> None:
    app_module = importlib.import_module("src.dashboard.app")
    pages = app_module.get_available_pages()
    page_ids = [page.page_id for page in pages]
    assert page_ids == [
        "overview",
        "foundation_status",
        "collection_dry_run",
        "analysis_dry_run",
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

