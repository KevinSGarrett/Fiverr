# ruff: noqa: I001
"""Unit tests for orchestration helper functions."""

from __future__ import annotations
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.exc import SQLAlchemyError

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
    assert "First-run readiness stage status" in output


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


def test_build_first_run_readiness_handoff_uses_app_entry_first_run_summary() -> None:
    handoff = orchestrator.build_first_run_readiness_handoff(
        {
            "startup": {
                "first_run_readiness": {
                    "status": "warning",
                    "expected_stages": ["collection", "analysis"],
                    "fixture_paths": ["tests/fixtures/dashboard/factories.py"],
                    "required_outputs": ["artifacts"],
                    "missing_outputs": ["artifacts"],
                    "known_blockers": ["Missing output directories."],
                    "prerequisites": {"config_exists": True, "fixture_files_available": True},
                }
            }
        }
    )
    assert handoff["phase"] == "first-run-readiness"
    assert handoff["stage_status"] == "warning"
    assert handoff["expected_stages"] == ["collection", "analysis"]
    assert handoff["known_blockers"] == ["Missing output directories."]


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
            return SimpleNamespace(
                scoring=SimpleNamespace(active_profile="default"),
                model_dump=lambda: {"niches": [{"niche_id": "12"}]},
            )

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: calls.setdefault("logged", True))
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///normalized.db")
    monkeypatch.setattr(
        orchestrator,
        "initialize_database",
        lambda database_url: calls.setdefault("db_url", object()),
    )
    monkeypatch.setattr(orchestrator, "create_session_factory", lambda _engine: object())

    class _FakeQuery:
        def filter(self, *args: Any, **kwargs: Any) -> _FakeQuery:
            return self

        def all(self) -> list[tuple[int]]:
            return [(101,)]

    class _FakeSession:
        def query(self, _model: Any) -> _FakeQuery:
            return _FakeQuery()

    class _FakeSessionContext:
        def __enter__(self) -> _FakeSession:
            return _FakeSession()

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            del exc_type, exc, tb
            return None

    async def _fake_score_keyword_batch(**kwargs: Any) -> list[dict[str, Any]]:
        calls["keyword_ids"] = kwargs["keyword_ids"]
        return [{"keyword_id": 101}]

    monkeypatch.setattr(orchestrator, "get_session", lambda _factory: _FakeSessionContext())
    monkeypatch.setattr("src.scoring.pipeline.score_keyword_batch", _fake_score_keyword_batch)

    assert orchestrator.run_pipeline("full", config_path="config.yaml", database_url=None) == 0
    assert calls["loaded"] is True
    assert calls["logged"] is True
    assert calls["keyword_ids"] == [101]
    assert "Scoring complete: 1 keywords scored" in capsys.readouterr().out


def test_run_pipeline_rejects_unsupported_mode() -> None:
    with pytest.raises(ValueError, match="Unsupported mode"):
        orchestrator.run_pipeline("unknown-mode")


def test_run_pipeline_recommendations_only_uses_stage_runner(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FakeSessionContext:
        def __enter__(self) -> object:
            return object()

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            del exc_type, exc, tb
            return None

    class _FakeConfig:
        @staticmethod
        def model_dump() -> dict[str, Any]:
            return {"recommendations": {"min_tag": "CONDITIONAL_GO"}}

    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> _FakeConfig:
            return _FakeConfig()

    async def _fake_stage(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["run_id"]
        assert kwargs["dry_run"] is True
        return {"generated": 1, "failed": 0}

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: None)
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///tmp.db")
    monkeypatch.setattr(orchestrator, "initialize_database", lambda database_url: object())
    monkeypatch.setattr(orchestrator, "create_session_factory", lambda _engine: object())
    monkeypatch.setattr(orchestrator, "get_session", lambda _factory: _FakeSessionContext())
    monkeypatch.setattr("src.recommendations.run.run_recommendations_stage", _fake_stage)

    assert orchestrator.run_pipeline("recommendations-only", config_path="config.yaml", database_url=None) == 0
    assert "Recommendations stage complete" in capsys.readouterr().out


def test_run_pipeline_recommendations_only_returns_error_on_stage_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            return object()

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: None)
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///tmp.db")
    monkeypatch.setattr(orchestrator, "initialize_database", lambda database_url: object())
    monkeypatch.setattr(orchestrator, "create_session_factory", lambda _engine: (_ for _ in ()).throw(RuntimeError("no session")))
    assert orchestrator.run_pipeline("recommendations-only", config_path="config.yaml", database_url=None) == 1
    assert "Recommendations stage failed" in capsys.readouterr().out


def test_run_pipeline_collect_only_runs_collection_orchestrator(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            return SimpleNamespace(model_dump=lambda: {"niches": []})

    async def _fake_collection_pipeline(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["dry_run"] is True
        return {"run_id": kwargs["run_id"], "stages_run": ["stage01_niche_init"], "errors": []}

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: None)
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///tmp.db")
    monkeypatch.setattr(orchestrator, "initialize_database", lambda database_url: object())
    monkeypatch.setattr("src.collection.orchestrator.run_collection_pipeline", _fake_collection_pipeline)

    assert orchestrator.run_pipeline("collect-only", config_path="config.yaml", database_url=None) == 0
    assert "Collection dry run complete" in capsys.readouterr().out


def test_run_pipeline_collect_only_returns_error_on_orchestrator_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            return SimpleNamespace(model_dump=lambda: {"niches": []})

    async def _broken_collection_pipeline(**_kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("dry-run boom")

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: None)
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///tmp.db")
    monkeypatch.setattr(orchestrator, "initialize_database", lambda database_url: object())
    monkeypatch.setattr("src.collection.orchestrator.run_collection_pipeline", _broken_collection_pipeline)

    assert orchestrator.run_pipeline("collect-only", config_path="config.yaml", database_url=None) == 1
    assert "Collection dry run failed: dry-run boom" in capsys.readouterr().out


def test_run_pipeline_cluster_only_runs_clustering_stage(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            return SimpleNamespace(model_dump=lambda: {"niches": [{"niche_id": "ai_saas"}]})

    class _FakeSessionContext:
        def __enter__(self) -> object:
            return object()

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            del exc_type, exc, tb
            return None

    async def _fake_cluster_all(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["run_id"]
        return {"niches_processed": 1, "niches_clustered": 1, "results": []}

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: None)
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///tmp.db")
    monkeypatch.setattr(orchestrator, "initialize_database", lambda database_url: object())
    monkeypatch.setattr(orchestrator, "create_session_factory", lambda _engine: object())
    monkeypatch.setattr(orchestrator, "get_session", lambda _factory: _FakeSessionContext())
    monkeypatch.setattr("src.analysis.keyword_clusterer.run_clustering_for_all_niches", _fake_cluster_all)

    assert orchestrator.run_pipeline("cluster-only", config_path="config.yaml", database_url=None) == 0
    assert "Cluster-only run complete" in capsys.readouterr().out


def test_run_pipeline_cluster_only_returns_error_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            return SimpleNamespace(model_dump=lambda: {"niches": []})

    async def _broken_cluster_all(**_kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("cluster boom")

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: None)
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///tmp.db")
    monkeypatch.setattr(orchestrator, "initialize_database", lambda database_url: object())
    monkeypatch.setattr(orchestrator, "create_session_factory", lambda _engine: object())

    class _FakeSessionContext:
        def __enter__(self) -> object:
            return object()

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            del exc_type, exc, tb
            return None

    monkeypatch.setattr(orchestrator, "get_session", lambda _factory: _FakeSessionContext())
    monkeypatch.setattr("src.analysis.keyword_clusterer.run_clustering_for_all_niches", _broken_cluster_all)

    assert orchestrator.run_pipeline("cluster-only", config_path="config.yaml", database_url=None) == 1
    assert "Cluster-only run failed: cluster boom" in capsys.readouterr().out


def test_resolve_existing_run_id_prefers_search_result_run() -> None:
    class _FakeQuery:
        def __init__(self, value: Any) -> None:
            self._value = value

        def order_by(self, *_args: Any) -> _FakeQuery:
            return self

        def limit(self, _count: int) -> _FakeQuery:
            return self

        def scalar(self) -> Any:
            return self._value

        def filter(self, *_args: Any) -> _FakeQuery:
            return self

    class _FakeSession:
        def __init__(self) -> None:
            self.calls = 0

        def query(self, _column: Any) -> _FakeQuery:
            self.calls += 1
            if self.calls == 1:
                return _FakeQuery("run-search-001")
            return _FakeQuery("run-gig-001")

    assert orchestrator._resolve_existing_run_id(_FakeSession()) == "run-search-001"


def test_resolve_existing_run_id_falls_back_to_gig_run() -> None:
    class _FakeQuery:
        def __init__(self, value: Any) -> None:
            self._value = value

        def order_by(self, *_args: Any) -> _FakeQuery:
            return self

        def limit(self, _count: int) -> _FakeQuery:
            return self

        def scalar(self) -> Any:
            return self._value

        def filter(self, *_args: Any) -> _FakeQuery:
            return self

    class _FakeSession:
        def __init__(self) -> None:
            self.calls = 0

        def query(self, _column: Any) -> _FakeQuery:
            self.calls += 1
            if self.calls == 1:
                return _FakeQuery(None)
            return _FakeQuery("run-gig-002")

    assert orchestrator._resolve_existing_run_id(_FakeSession()) == "run-gig-002"


def test_resolve_existing_run_id_returns_none_without_query() -> None:
    assert orchestrator._resolve_existing_run_id(object()) is None


def test_resolve_existing_run_id_handles_legacy_search_results_schema() -> None:
    class _SearchQuery:
        def order_by(self, *_args: Any) -> _SearchQuery:
            return self

        def limit(self, _count: int) -> _SearchQuery:
            return self

        def scalar(self) -> Any:
            raise SQLAlchemyError("no such column: search_results.run_id")

    class _GigQuery:
        def order_by(self, *_args: Any) -> _GigQuery:
            return self

        def limit(self, _count: int) -> _GigQuery:
            return self

        def scalar(self) -> Any:
            return "run-gig-legacy-001"

        def filter(self, *_args: Any) -> _GigQuery:
            return self

    class _FakeSession:
        def __init__(self) -> None:
            self.calls = 0

        def query(self, _column: Any) -> _SearchQuery | _GigQuery:
            self.calls += 1
            if self.calls == 1:
                return _SearchQuery()
            return _GigQuery()

    assert orchestrator._resolve_existing_run_id(_FakeSession()) == "run-gig-legacy-001"


def test_run_pipeline_profile_only_uses_existing_run_id(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            return SimpleNamespace(model_dump=lambda: {"niches": [{"niche_id": "ai_saas"}]})

    class _FakeSessionContext:
        def __enter__(self) -> object:
            return object()

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            del exc_type, exc, tb
            return None

    async def _fake_profile_all(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["run_id"] == "run-existing-123"
        return {"niches_processed": 1, "niches_profiled": 1, "results": []}

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: None)
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///tmp.db")
    monkeypatch.setattr(orchestrator, "initialize_database", lambda database_url: object())
    monkeypatch.setattr(orchestrator, "create_session_factory", lambda _engine: object())
    monkeypatch.setattr(orchestrator, "get_session", lambda _factory: _FakeSessionContext())
    monkeypatch.setattr(orchestrator, "_resolve_existing_run_id", lambda _db: "run-existing-123")
    monkeypatch.setattr("src.analysis.competitor_profiler.run_competitor_profiling_for_all_niches", _fake_profile_all)

    assert orchestrator.run_pipeline("profile-only", config_path="config.yaml", database_url=None) == 0
    assert "Profile-only run complete" in capsys.readouterr().out


def test_profile_only_resolves_existing_run_id(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            return SimpleNamespace(model_dump=lambda: {"niches": [{"niche_id": "ai_saas"}]})

    class _FakeSessionContext:
        def __enter__(self) -> object:
            return object()

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            del exc_type, exc, tb
            return None

    async def _fake_profile_all(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["run_id"] == "run-existing-321"
        return {"niches_processed": 1, "niches_profiled": 1, "results": []}

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: None)
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///tmp.db")
    monkeypatch.setattr(orchestrator, "initialize_database", lambda database_url: object())
    monkeypatch.setattr(orchestrator, "create_session_factory", lambda _engine: object())
    monkeypatch.setattr(orchestrator, "get_session", lambda _factory: _FakeSessionContext())
    monkeypatch.setattr(orchestrator, "_resolve_existing_run_id", lambda _db: "run-existing-321")
    monkeypatch.setattr("src.analysis.competitor_profiler.run_competitor_profiling_for_all_niches", _fake_profile_all)

    assert orchestrator.run_pipeline("profile-only", config_path="config.yaml", database_url=None) == 0
    assert "Profile-only run complete" in capsys.readouterr().out


def test_profile_only_does_not_create_fresh_uuid(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            return SimpleNamespace(model_dump=lambda: {"niches": [{"niche_id": "ai_saas"}]})

    class _FakeSessionContext:
        def __enter__(self) -> object:
            return object()

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            del exc_type, exc, tb
            return None

    async def _fake_profile_all(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["run_id"] == "run-existing-654"
        return {"niches_processed": 1, "niches_profiled": 1, "results": []}

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: None)
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///tmp.db")
    monkeypatch.setattr(orchestrator, "initialize_database", lambda database_url: object())
    monkeypatch.setattr(orchestrator, "create_session_factory", lambda _engine: object())
    monkeypatch.setattr(orchestrator, "get_session", lambda _factory: _FakeSessionContext())
    monkeypatch.setattr(orchestrator, "_resolve_existing_run_id", lambda _db: "run-existing-654")
    monkeypatch.setattr("src.analysis.competitor_profiler.run_competitor_profiling_for_all_niches", _fake_profile_all)
    def _fail_uuid4() -> object:
        raise AssertionError("uuid4 should not be called")

    monkeypatch.setattr("uuid.uuid4", _fail_uuid4)

    assert orchestrator.run_pipeline("profile-only", config_path="config.yaml", database_url=None) == 0
    assert "Profile-only run complete" in capsys.readouterr().out


def test_run_pipeline_quality_analysis_uses_existing_run_id(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            return SimpleNamespace(model_dump=lambda: {"niches": [{"niche_id": "ai_saas"}]})

    class _FakeSessionContext:
        def __enter__(self) -> object:
            return object()

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            del exc_type, exc, tb
            return None

    async def _fake_quality_all(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["run_id"] == "run-existing-456"
        return {"niches_processed": 1, "niches_analyzed": 1, "results": []}

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: None)
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///tmp.db")
    monkeypatch.setattr(orchestrator, "initialize_database", lambda database_url: object())
    monkeypatch.setattr(orchestrator, "create_session_factory", lambda _engine: object())
    monkeypatch.setattr(orchestrator, "get_session", lambda _factory: _FakeSessionContext())
    monkeypatch.setattr(orchestrator, "_resolve_existing_run_id", lambda _db: "run-existing-456")
    monkeypatch.setattr("src.analysis.gig_quality_rubric.run_gig_quality_analysis_for_all_niches", _fake_quality_all)

    assert orchestrator.run_pipeline("quality-analysis", config_path="config.yaml", database_url=None) == 0
    assert "Quality-analysis run complete" in capsys.readouterr().out


def test_run_pipeline_review_analysis_uses_existing_run_id(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            return SimpleNamespace(model_dump=lambda: {"niches": [{"niche_id": "ai_saas"}]})

    class _FakeSessionContext:
        def __enter__(self) -> object:
            return object()

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            del exc_type, exc, tb
            return None

    async def _fake_review_all(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["run_id"] == "run-existing-789"
        return {"niches_processed": 1, "niches_analyzed": 1, "results": []}

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: None)
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///tmp.db")
    monkeypatch.setattr(orchestrator, "initialize_database", lambda database_url: object())
    monkeypatch.setattr(orchestrator, "create_session_factory", lambda _engine: object())
    monkeypatch.setattr(orchestrator, "get_session", lambda _factory: _FakeSessionContext())
    monkeypatch.setattr(orchestrator, "_resolve_existing_run_id", lambda _db: "run-existing-789")
    monkeypatch.setattr("src.analysis.review_analyzer.run_review_analysis_for_all_niches", _fake_review_all)

    assert orchestrator.run_pipeline("review-analysis", config_path="config.yaml", database_url=None) == 0
    assert "Review-analysis run complete" in capsys.readouterr().out


def test_run_pipeline_saturation_analysis_uses_existing_run_id(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            return SimpleNamespace(model_dump=lambda: {"niches": [{"niche_id": "ai_saas"}]})

    class _FakeSessionContext:
        def __enter__(self) -> object:
            return object()

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            del exc_type, exc, tb
            return None

    async def _fake_saturation_all(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["run_id"] == "run-existing-999"
        return {"niches_processed": 1, "niches_analyzed": 1, "results": []}

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: None)
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///tmp.db")
    monkeypatch.setattr(orchestrator, "initialize_database", lambda database_url: object())
    monkeypatch.setattr(orchestrator, "create_session_factory", lambda _engine: object())
    monkeypatch.setattr(orchestrator, "get_session", lambda _factory: _FakeSessionContext())
    monkeypatch.setattr(orchestrator, "_resolve_existing_run_id", lambda _db: "run-existing-999")
    monkeypatch.setattr("src.analysis.saturation_model.run_saturation_analysis_for_all_niches", _fake_saturation_all)

    assert orchestrator.run_pipeline("saturation-analysis", config_path="config.yaml", database_url=None) == 0
    assert "Saturation-analysis run complete" in capsys.readouterr().out
