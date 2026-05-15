# ruff: noqa: I001
"""Unit tests for orchestration helper functions."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import src.orchestrator as orchestrator


def test_run_export_stub_validates_inputs(capsys: pytest.CaptureFixture[str]) -> None:
    assert orchestrator.run_export_stub("xml", "input.json") == 2
    assert "Unsupported export format" in capsys.readouterr().out

    assert orchestrator.run_export_stub("csv", "   ") == 2
    assert "Missing required --input-path" in capsys.readouterr().out


def test_run_export_stub_accepts_supported_format(capsys: pytest.CaptureFixture[str]) -> None:
    assert orchestrator.run_export_stub("markdown", "data/input.json") == 0
    assert "Export CLI surface is available" in capsys.readouterr().out


def test_run_dashboard_stub_normalizes_mode(capsys: pytest.CaptureFixture[str]) -> None:
    assert orchestrator.run_dashboard_stub("  LOCAL  ") == 0
    output = capsys.readouterr().out
    assert "local" in output
    assert "Dashboard app-entry module" in output
    assert "Dashboard startup status" in output
    assert "Dashboard readiness stage status" in output


def test_run_dashboard_stub_returns_error_when_pages_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeDashboardModule:
        @staticmethod
        def build_app_entry_smoke_state() -> dict[str, Any]:
            return {
                "entry": {"entry_module": "src.dashboard.app:main"},
                "page_registration": {
                    "status": "blocked",
                    "missing_pages": ["overview"],
                },
                "startup": {"status": "ready", "safe_empty_state": False},
                "readiness": {"severity": "blocked", "blocked_pages": ["overview"]},
            }

    monkeypatch.setattr(orchestrator.importlib, "import_module", lambda _name: _FakeDashboardModule())
    assert orchestrator.run_dashboard_stub("preview") == 1


def test_build_dashboard_readiness_handoff_uses_smoke_state_payload() -> None:
    handoff = orchestrator.build_dashboard_readiness_handoff(
        {
            "status": "warning",
            "startup": {"status": "warning", "warning_count": 2},
            "page_registration": {"status": "ready", "missing_pages": []},
            "readiness": {
                "severity": "warning",
                "blocked_pages": [],
                "next_actions": ["Run phase2-smoke"],
            },
        }
    )
    assert handoff["phase"] == "dashboard-readiness"
    assert handoff["stage_status"] == "warning"
    assert handoff["warning_count"] == 2
    assert handoff["next_actions"] == ["Run phase2-smoke"]


def test_load_fixture_payload_handles_missing_invalid_and_nondict(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing = tmp_path / "missing.json"
    assert orchestrator._load_fixture_payload(str(missing)) is None
    assert "Fixture file not found" in capsys.readouterr().out

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{not-json", encoding="utf-8")
    assert orchestrator._load_fixture_payload(str(invalid)) is None
    assert "Unable to read fixture file" in capsys.readouterr().out

    list_payload = tmp_path / "list.json"
    list_payload.write_text('["not", "an", "object"]', encoding="utf-8")
    assert orchestrator._load_fixture_payload(str(list_payload)) is None
    assert "must be a JSON object" in capsys.readouterr().out


def test_run_collection_dry_run_uses_positive_max_candidates_when_sample_non_positive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps({"seed_keywords": ["logo design", "seo audit"], "max_pages": 1}),
        encoding="utf-8",
    )
    output_path = tmp_path / "checkpoint.json"
    captured: dict[str, Any] = {}

    def _fake_run_collection_dry_run(seeds: list[str], **kwargs: Any) -> Any:
        captured["seeds"] = seeds
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            status="success",
            records_seen=2,
            records_written=2,
            checkpoint_path=kwargs["checkpoint_path"],
            errors=[],
        )

    monkeypatch.setattr(
        orchestrator.importlib,
        "import_module",
        lambda _name: SimpleNamespace(run_collection_dry_run=_fake_run_collection_dry_run),
    )

    assert orchestrator.run_collection_dry_run(str(fixture), str(output_path), sample_size=0) == 0
    assert captured["seeds"] == ["logo design", "seo audit"]
    assert captured["kwargs"]["max_candidates"] == 2


def test_run_collection_dry_run_returns_failure_with_error_lines(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({"seed_keywords": ["logo design"]}), encoding="utf-8")

    error = SimpleNamespace(code="expansion_failed", message="Unable to expand keywords")

    monkeypatch.setattr(
        orchestrator.importlib,
        "import_module",
        lambda _name: SimpleNamespace(
            run_collection_dry_run=lambda *_args, **_kwargs: SimpleNamespace(
                status="failed",
                records_seen=0,
                records_written=0,
                checkpoint_path=Path("unused"),
                errors=[error],
            )
        ),
    )

    assert orchestrator.run_collection_dry_run(str(fixture), str(tmp_path / "checkpoint.json"), 5) == 1
    output = capsys.readouterr().out
    assert "Collection dry-run failed." in output
    assert "expansion_failed" in output


def test_run_analysis_dry_run_truncates_fixture_lists_and_writes_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = tmp_path / "analysis_fixture.json"
    fixture.write_text(
        json.dumps(
            {
                "keywords": ["a", "b", "c"],
                "competitors": ["x", "y", "z"],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "analysis_output.json"
    captured_payload: dict[str, Any] = {}

    class _FakeResult:
        status = "success"
        stages = ["stage_1"]

        @staticmethod
        def model_dump_json(indent: int = 2) -> str:
            del indent
            return '{"status":"success"}'

    def _fake_analysis(payload: dict[str, Any]) -> _FakeResult:
        captured_payload.update(payload)
        return _FakeResult()

    monkeypatch.setattr(
        orchestrator.importlib,
        "import_module",
        lambda _name: SimpleNamespace(run_analysis_dry_run=_fake_analysis),
    )

    assert orchestrator.run_analysis_dry_run(str(fixture), str(output), sample_size=2) == 0
    assert captured_payload["keywords"] == ["a", "b"]
    assert captured_payload["competitors"] == ["x", "y"]
    assert output.exists()


def test_run_analysis_dry_run_persists_when_database_url_is_provided(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = tmp_path / "analysis_fixture_persist.json"
    fixture.write_text(json.dumps({"keywords": ["a", "b"], "competitors": []}), encoding="utf-8")
    output = tmp_path / "analysis_output_persist.json"

    class _FakeResult:
        status = "success"
        stages = ["stage_1"]

        @staticmethod
        def model_dump_json(indent: int = 2) -> str:
            del indent
            return '{"status":"success"}'

    def _fake_import_module(module_name: str) -> Any:
        if module_name == "src.analysis.orchestrator":
            return SimpleNamespace(run_analysis_dry_run=lambda _payload: _FakeResult())
        if module_name == "src.analysis.persistence":
            return SimpleNamespace(
                persist_analysis_run_summary=lambda *_args, **_kwargs: {
                    "run_table_id": 7,
                    "persisted_stage_count": 1,
                    "persisted_log_count": 2,
                }
            )
        raise AssertionError(f"Unexpected module import: {module_name}")

    monkeypatch.setattr(orchestrator.importlib, "import_module", _fake_import_module)

    assert (
        orchestrator.run_analysis_dry_run(
            str(fixture),
            str(output),
            sample_size=2,
            database_url="sqlite:///tmp/test.sqlite3",
        )
        == 0
    )
    assert output.exists()


def test_run_phase2_smoke_returns_failure_when_module_import_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def _fake_import_module(module_name: str) -> Any:
        if module_name == "src.analysis":
            raise RuntimeError("boom")
        return object()

    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            return object()

    monkeypatch.setattr(orchestrator.importlib, "import_module", _fake_import_module)
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)

    assert orchestrator.run_phase2_smoke(config_path="config.yaml") == 1
    assert "Phase2 smoke failed" in capsys.readouterr().out


def test_phase2_smoke_metadata_includes_dashboard_handoff_requirements() -> None:
    metadata = orchestrator.build_phase2_smoke_metadata()
    assert metadata["dashboard_handoff_required"] is True
    assert "stage_status" in metadata["dashboard_handoff_fields"]


def test_run_pipeline_initializes_database_and_prints_mode(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: dict[str, Any] = {}

    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            calls["loaded"] = True
            return object()

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: calls.setdefault("logged", True))
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///normalized.db")
    monkeypatch.setattr(
        orchestrator,
        "initialize_database",
        lambda database_url: calls.setdefault("db_url", database_url),
    )

    assert orchestrator.run_pipeline("full", config_path="config.yaml", database_url=None) == 0
    assert calls["loaded"] is True
    assert calls["logged"] is True
    assert calls["db_url"] == "sqlite:///normalized.db"
    assert "Mode: full" in capsys.readouterr().out


def test_run_pipeline_rejects_unsupported_mode() -> None:
    with pytest.raises(ValueError, match="Unsupported mode"):
        orchestrator.run_pipeline("unknown-mode")
