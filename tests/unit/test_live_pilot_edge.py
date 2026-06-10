"""Edge case tests for TierD-2 live collection pilot infrastructure.

Agent F - C074 corrected cycle.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

import run as run_module
from run import cli
from src.collection.live_pilot import _seed_pilot_niche, run_live_collection_pilot
from src.collection.pilot_logger import PilotLogger
from src.collection.scrapfly_client import ScrapFlyRateLimitError
from src.models.database import create_session_factory, get_session, initialize_database, normalize_database_url
from src.models.niche import Niche
from src.playbook.generator import (
    build_gig_creation_section,
    build_ongoing_optimization_section,
    build_review_strategy_section,
    export_playbook_markdown,
    generate_playbook,
    get_niche_name,
)


class TestPilotLoggerEdgeCases:
    def test_error_rate_triggers_stop(self, tmp_path: Path) -> None:
        logger = PilotLogger(log_path=str(tmp_path / "pilot.jsonl"))
        logger.log_request("http://a.com", "stage03_search", 200, 10, True)
        logger.log_request(
            "http://b.com",
            "stage03_search",
            500,
            5,
            False,
            error="server error",
        )
        logger.log_request("http://c.com", "stage04_gig_detail", 200, 10, True)
        logger.log_request(
            "http://d.com",
            "stage04_gig_detail",
            500,
            5,
            False,
            error="timeout",
        )
        bundle = logger.write_evidence_bundle(str(tmp_path / "ev.json"))
        assert bundle["error_rate"] == 0.5
        assert bundle["stop_conditions_triggered"] is True

    def test_sequential_requests_correct(self, tmp_path: Path) -> None:
        log_path = tmp_path / "concurrent.jsonl"
        logger = PilotLogger(log_path=str(log_path))
        for i in range(20):
            logger.log_request(f"http://url{i}.com", "stage03_search", 200, 3, True)
        lines = log_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 20
        for line in lines:
            entry = json.loads(line)
            assert "timestamp" in entry and "credits_used" in entry
        bundle = logger.write_evidence_bundle(str(tmp_path / "ev.json"))
        assert bundle["total_credits_used"] == 60

    def test_zero_requests_valid_bundle(self, tmp_path: Path) -> None:
        logger = PilotLogger(log_path=str(tmp_path / "pilot.jsonl"))
        bundle = logger.write_evidence_bundle(str(tmp_path / "ev.json"))
        assert bundle["total_requests"] == 0
        assert bundle["block_rate"] == 0.0
        assert bundle["error_rate"] == 0.0
        assert bundle["stop_conditions_triggered"] is False
        assert bundle["requests_by_stage"] == {}

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        nested = tmp_path / "deep" / "nested" / "dir" / "pilot.jsonl"
        logger = PilotLogger(log_path=str(nested))
        logger.log_request("http://test.com", "stage03_search", 200, 5, True)
        assert nested.exists()

    def test_requests_by_stage_breakdown(self, tmp_path: Path) -> None:
        logger = PilotLogger(log_path=str(tmp_path / "pilot.jsonl"))
        for i in range(3):
            logger.log_request(f"http://s3/{i}", "stage03_search", 200, 10, True)
        for i in range(2):
            logger.log_request(f"http://s4/{i}", "stage04_gig_detail", 200, 15, True)
        bundle = logger.write_evidence_bundle(str(tmp_path / "ev.json"))
        rbs = bundle["requests_by_stage"]
        assert rbs["stage03_search"]["count"] == 3
        assert rbs["stage03_search"]["credits"] == 30
        assert rbs["stage04_gig_detail"]["count"] == 2
        assert rbs["stage04_gig_detail"]["credits"] == 30
        assert bundle["total_credits_used"] == 60

    def test_survives_multiple_instantiations(self, tmp_path: Path) -> None:
        log_path = tmp_path / "shared.jsonl"
        logger1 = PilotLogger(log_path=str(log_path))
        logger1.log_request("http://a.com", "stage03_search", 200, 5, True)
        logger1.log_request("http://b.com", "stage04_gig_detail", 200, 10, True)
        logger2 = PilotLogger(log_path=str(log_path))
        logger2.log_request("http://c.com", "stage05_seller_profile", 200, 8, True)
        lines = log_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 3

    def test_no_credentials_in_jsonl(self, tmp_path: Path) -> None:
        logger = PilotLogger(log_path=str(tmp_path / "pilot.jsonl"))
        long_prefix = "x" * 210
        test_urls = [
            "https://www.fiverr.com/search/gigs?query=python+automation",
            "https://www.fiverr.com/seller_profile/username123",
            f"https://api.scrapfly.io/scrape?padding={long_prefix}&key=scp-live-REDACTED",
        ]
        for url in test_urls:
            logger.log_request(url, "stage03_search", 200, 10, True)
        for line in (tmp_path / "pilot.jsonl").read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            assert len(entry["url"]) <= 200
            assert "scp-live" not in entry["url"]

    def test_stage_breakdown_all_3_stages(self, tmp_path: Path) -> None:
        logger = PilotLogger(log_path=str(tmp_path / "pilot.jsonl"))
        stage_requests = {
            "stage03_search": (5, 10),
            "stage04_gig_detail": (3, 15),
            "stage05_seller_profile": (2, 8),
        }
        for stage, (count, credits) in stage_requests.items():
            for i in range(count):
                logger.log_request(f"http://test{i}.com/{stage}", stage, 200, credits, True)
        bundle = logger.write_evidence_bundle(str(tmp_path / "ev.json"))
        rbs = bundle["requests_by_stage"]
        assert rbs["stage03_search"]["count"] == 5
        assert rbs["stage03_search"]["credits"] == 50
        assert rbs["stage04_gig_detail"]["count"] == 3
        assert rbs["stage04_gig_detail"]["credits"] == 45
        assert rbs["stage05_seller_profile"]["count"] == 2
        assert rbs["stage05_seller_profile"]["credits"] == 16
        assert bundle["total_requests"] == 10
        assert bundle["total_credits_used"] == 111

    def test_evidence_includes_extra_keys(self, tmp_path: Path) -> None:
        logger = PilotLogger(log_path=str(tmp_path / "pilot.jsonl"))
        logger.log_request("http://t.com", "stage03_search", 200, 5, True)
        extra = {
            "niche_id": "python_automation",
            "run_id": "test-123",
            "db_url": "sqlite:///test.db",
        }
        bundle = logger.write_evidence_bundle(str(tmp_path / "ev.json"), extra=extra)
        for key in extra:
            assert key in bundle


class TestRunLivePilotEdgeCases:
    def test_db_url_never_references_baseline(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_invalid(_self: Any) -> bool:
            return False

        monkeypatch.setattr("src.collection.session_manager.SessionManager.is_session_valid", fake_invalid)
        for niche in ["python_automation", "ai_agent_development", "mcp_ai_agent"]:
            result = asyncio.run(run_live_collection_pilot(niche, database_url=None))
            assert "cycle037_live" not in result["db_url"]
            assert niche in result["db_url"]

    def test_session_expired_success_false(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        async def fake_invalid(_self: Any) -> bool:
            return False

        monkeypatch.setattr("src.collection.session_manager.SessionManager.is_session_valid", fake_invalid)
        result = asyncio.run(
            run_live_collection_pilot(
                "python_automation",
                database_url=f"sqlite:///{(tmp_path / 'pilot.db').as_posix()}",
                evidence_path=str(tmp_path / "ev.json"),
            )
        )
        assert result["success"] is False
        assert result["stop_reason"] == "session_expired"

    def test_budget_exceeded_correct_stop_reason(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        async def fake_valid(_self: Any) -> bool:
            return True

        async def fake_pipeline(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            raise ScrapFlyRateLimitError("budget exceeded")

        monkeypatch.setattr("src.collection.session_manager.SessionManager.is_session_valid", fake_valid)
        monkeypatch.setattr("src.collection.orchestrator.run_collection_pipeline", fake_pipeline)
        result = asyncio.run(
            run_live_collection_pilot(
                "python_automation",
                database_url=f"sqlite:///{(tmp_path / 'pilot.db').as_posix()}",
                evidence_path=str(tmp_path / "ev.json"),
            )
        )
        assert result["success"] is False
        assert result["stop_reason"] == "budget_exceeded"

    def test_evidence_written_on_pipeline_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        async def fake_valid(_self: Any) -> bool:
            return True

        async def fake_pipeline(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("pipeline error")

        evidence_path = tmp_path / "ev.json"
        monkeypatch.setattr("src.collection.session_manager.SessionManager.is_session_valid", fake_valid)
        monkeypatch.setattr("src.collection.orchestrator.run_collection_pipeline", fake_pipeline)
        result = asyncio.run(
            run_live_collection_pilot(
                "python_automation",
                database_url=f"sqlite:///{(tmp_path / 'pilot.db').as_posix()}",
                evidence_path=str(evidence_path),
            )
        )
        assert result["success"] is False
        assert evidence_path.exists()

    def test_seed_niche_idempotent(self, tmp_path: Path) -> None:
        db_path = tmp_path / "seed.db"
        engine = initialize_database(database_url=normalize_database_url(f"sqlite:///{db_path.as_posix()}"))
        _seed_pilot_niche("python_automation", engine)
        _seed_pilot_niche("python_automation", engine)
        session_factory = create_session_factory(engine)
        with get_session(session_factory) as db:
            count = db.query(Niche).filter(Niche.slug == "python_automation").count()
            assert count == 1

    def test_pilot_result_contains_run_id(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        async def fake_invalid(_self: Any) -> bool:
            return False

        monkeypatch.setattr("src.collection.session_manager.SessionManager.is_session_valid", fake_invalid)
        result = asyncio.run(
            run_live_collection_pilot(
                "python_automation",
                database_url=f"sqlite:///{(tmp_path / 'pilot.db').as_posix()}",
                evidence_path=str(tmp_path / "ev.json"),
            )
        )
        assert "run_id" in result
        assert "python_automation" in str(result["run_id"])

    def test_pilot_db_url_contains_niche_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_invalid(_self: Any) -> bool:
            return False

        monkeypatch.setattr("src.collection.session_manager.SessionManager.is_session_valid", fake_invalid)
        for niche in ["python_automation", "ai_agent_development", "mcp_ai_agent"]:
            result = asyncio.run(run_live_collection_pilot(niche, database_url=None))
            assert niche in result["db_url"]
            assert "live_pilot_" in result["db_url"]

    def test_scopes_config_to_single_niche(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        captured_configs: list[dict[str, Any]] = []

        async def fake_valid(_self: Any) -> bool:
            return True

        async def fake_pipeline(*_args: Any, **kwargs: Any) -> dict[str, Any]:
            captured_configs.append(kwargs["config"])
            return {"errors": [], "gig_detail_jobs_run": 0, "search_jobs_run": 0}

        monkeypatch.setattr("src.collection.session_manager.SessionManager.is_session_valid", fake_valid)
        monkeypatch.setattr("src.collection.orchestrator.run_collection_pipeline", fake_pipeline)
        result = asyncio.run(
            run_live_collection_pilot(
                "python_automation",
                database_url=f"sqlite:///{(tmp_path / 'pilot.db').as_posix()}",
                evidence_path=str(tmp_path / "ev.json"),
            )
        )
        assert result["success"] is True
        assert captured_configs
        niches = captured_configs[0].get("niches", [])
        assert isinstance(niches, list)
        for niche in niches:
            assert niche.get("niche_id") == "python_automation"

    def test_evidence_bundle_always_has_8_required_keys(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        required_keys = [
            "generated_at",
            "total_requests",
            "total_credits_used",
            "block_rate",
            "error_rate",
            "stop_conditions_triggered",
            "requests_by_stage",
            "log_path",
        ]

        async def _run_case(case_name: str, valid: bool) -> None:
            async def fake_valid(_self: Any) -> bool:
                return valid

            monkeypatch.setattr("src.collection.session_manager.SessionManager.is_session_valid", fake_valid)
            evidence_path = tmp_path / f"{case_name}.json"
            result = await run_live_collection_pilot(
                "python_automation",
                database_url=f"sqlite:///{(tmp_path / f'{case_name}.db').as_posix()}",
                evidence_path=str(evidence_path),
            )
            assert "evidence_path" in result
            ev = json.loads(evidence_path.read_text(encoding="utf-8"))
            for key in required_keys:
                assert key in ev

        asyncio.run(_run_case("session_expired_case", valid=False))
        asyncio.run(_run_case("successful_case", valid=True))


class TestCollectLiveEdgeCases:
    def test_exits_1_on_budget_exceeded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_pilot(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            return {
                "success": False,
                "stop_reason": "budget_exceeded",
                "credits_used": 100,
                "gigs_collected": 0,
                "search_results": 0,
                "errors": ["ScrapFlyRateLimitError: budget exceeded"],
                "evidence_path": "data/test.json",
            }

        monkeypatch.setattr("src.collection.live_pilot.run_live_collection_pilot", fake_pilot)
        runner = CliRunner()
        result = runner.invoke(cli, ["collect-live", "--niche", "python_automation"])
        assert result.exit_code == 1
        assert "budget_exceeded" in result.output or "Pilot stopped" in result.output

    def test_exits_1_on_session_expired(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_pilot(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            return {
                "success": False,
                "stop_reason": "session_expired",
                "credits_used": 0,
                "gigs_collected": 0,
                "search_results": 0,
                "errors": ["Session expired"],
                "evidence_path": "data/test.json",
            }

        monkeypatch.setattr("src.collection.live_pilot.run_live_collection_pilot", fake_pilot)
        runner = CliRunner()
        result = runner.invoke(cli, ["collect-live", "--niche", "python_automation"])
        assert result.exit_code == 1

    def test_exits_0_on_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_pilot(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            return {
                "success": True,
                "stop_reason": None,
                "credits_used": 45,
                "gigs_collected": 10,
                "search_results": 3,
                "errors": [],
                "evidence_path": "data/test.json",
            }

        monkeypatch.setattr("src.collection.live_pilot.run_live_collection_pilot", fake_pilot)
        runner = CliRunner()
        result = runner.invoke(cli, ["collect-live", "--niche", "python_automation", "--budget", "100"])
        assert result.exit_code == 0
        assert "gigs=10" in result.output or "10" in result.output

    def test_fails_without_niche_option(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["collect-live"])
        assert result.exit_code != 0
        assert "niche" in result.output.lower() or "missing" in result.output.lower() or result.exit_code == 2

    def test_displays_errors_on_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_pilot(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            return {
                "success": False,
                "stop_reason": "pipeline_error",
                "credits_used": 50,
                "gigs_collected": 0,
                "search_results": 0,
                "errors": ["Connection refused", "Timeout after 30s"],
                "evidence_path": "data/test_err.json",
            }

        monkeypatch.setattr("src.collection.live_pilot.run_live_collection_pilot", fake_pilot)
        runner = CliRunner()
        result = runner.invoke(cli, ["collect-live", "--niche", "python_automation"])
        assert result.exit_code == 1
        assert "Connection refused" in result.output or "error" in result.output.lower()

    def test_output_contains_key_metrics(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_pilot(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            return {
                "success": True,
                "stop_reason": None,
                "credits_used": 45,
                "gigs_collected": 8,
                "search_results": 3,
                "errors": [],
                "evidence_path": "data/live_pilot_log.json",
            }

        monkeypatch.setattr("src.collection.live_pilot.run_live_collection_pilot", fake_pilot)
        runner = CliRunner()
        result = runner.invoke(cli, ["collect-live", "--niche", "python_automation", "--budget", "100"])
        assert result.exit_code == 0
        assert "gigs=8" in result.output or "8" in result.output
        assert "45" in result.output


class TestLiveValidateEdgeCases:
    def test_skip_collection_does_not_call_pilot(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        mock_pilot_called = {"called": False}

        async def fake_pilot(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            mock_pilot_called["called"] = True
            return {}

        monkeypatch.setattr("src.collection.live_pilot.run_live_collection_pilot", fake_pilot)
        monkeypatch.setattr(
            run_module,
            "_validate_pilot_db_state",
            lambda _db: {"gigs": 5, "keywords": 10, "search_results": 15},
        )
        monkeypatch.setattr(run_module, "run_pipeline", lambda **_kwargs: 0)
        monkeypatch.setattr(
            run_module,
            "_run_live_recommendations",
            lambda *_args: {"count": 2, "dry_run": True},
        )
        monkeypatch.setattr(
            run_module,
            "_generate_playbook_from_live_data",
            lambda *_args: {"success": True, "has_full_data": False, "sections_count": 5},
        )
        ev_path = tmp_path / "skip_collection_ev.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "live-validate",
                "--niche",
                "python_automation",
                "--skip-collection",
                "--evidence-path",
                str(ev_path),
            ],
        )
        assert result.exit_code == 0
        assert mock_pilot_called["called"] is False
        assert "Skipped" in result.output

    def test_evidence_written_on_scoring_failure(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        ev_path = tmp_path / "scoring_fail_ev.json"
        monkeypatch.setattr(
            run_module,
            "_validate_pilot_db_state",
            lambda _db: {"gigs": 5, "keywords": 10, "search_results": 15},
        )

        def fail_pipeline(**_kwargs: Any) -> int:
            raise Exception("scoring failed")

        monkeypatch.setattr(run_module, "run_pipeline", fail_pipeline)
        monkeypatch.setattr(
            run_module,
            "_run_live_recommendations",
            lambda *_args: {"count": 0, "dry_run": True},
        )
        monkeypatch.setattr(
            run_module,
            "_generate_playbook_from_live_data",
            lambda *_args: {"success": False, "error": "no data"},
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "live-validate",
                "--niche",
                "python_automation",
                "--skip-collection",
                "--evidence-path",
                str(ev_path),
            ],
        )
        assert result.exit_code == 0
        assert ev_path.exists()
        ev = json.loads(ev_path.read_text(encoding="utf-8"))
        assert "stages" in ev

    def test_evidence_has_required_stage_keys(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        ev_path = tmp_path / "stage_keys_ev.json"
        monkeypatch.setattr(
            run_module,
            "_validate_pilot_db_state",
            lambda _db: {"gigs": 0, "keywords": 0, "search_results": 0},
        )
        monkeypatch.setattr(run_module, "run_pipeline", lambda **_kwargs: 0)
        monkeypatch.setattr(
            run_module,
            "_run_live_recommendations",
            lambda *_args: {"count": 0, "dry_run": True},
        )
        monkeypatch.setattr(
            run_module,
            "_generate_playbook_from_live_data",
            lambda *_args: {"success": False, "has_full_data": False, "sections_count": 5},
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "live-validate",
                "--niche",
                "python_automation",
                "--skip-collection",
                "--evidence-path",
                str(ev_path),
            ],
            catch_exceptions=True,
        )
        assert result.exit_code == 0
        ev = json.loads(ev_path.read_text(encoding="utf-8"))
        expected_stages = ["db_validation", "scoring", "recommendations", "playbook"]
        for stage in expected_stages:
            assert stage in ev.get("stages", {})

    def test_evidence_has_minimum_stage_keys(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        ev_path = tmp_path / "stage_keys_full.json"
        monkeypatch.setattr(
            run_module,
            "_validate_pilot_db_state",
            lambda _db: {"gigs": 5, "keywords": 10, "search_results": 15},
        )
        monkeypatch.setattr(run_module, "run_pipeline", lambda **_kwargs: 0)
        monkeypatch.setattr(
            run_module,
            "_run_live_recommendations",
            lambda *_args: {"count": 2, "dry_run": True},
        )
        monkeypatch.setattr(
            run_module,
            "_generate_playbook_from_live_data",
            lambda *_args: {"success": True, "has_full_data": False, "sections_count": 5},
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "live-validate",
                "--niche",
                "python_automation",
                "--skip-collection",
                "--evidence-path",
                str(ev_path),
            ],
            catch_exceptions=True,
        )
        assert result.exit_code == 0
        ev = json.loads(ev_path.read_text(encoding="utf-8"))
        stages = ev.get("stages", {})
        assert len(stages) >= 4

    def test_evidence_success_false_when_no_gigs(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        ev_path = tmp_path / "empty_gigs_ev.json"
        monkeypatch.setattr(
            run_module,
            "_validate_pilot_db_state",
            lambda _db: {"gigs": 0, "keywords": 0, "search_results": 0},
        )
        monkeypatch.setattr(run_module, "run_pipeline", lambda **_kwargs: 0)
        monkeypatch.setattr(
            run_module,
            "_run_live_recommendations",
            lambda *_args: {"count": 0, "dry_run": True},
        )
        monkeypatch.setattr(
            run_module,
            "_generate_playbook_from_live_data",
            lambda *_args: {"success": False, "has_full_data": False, "sections_count": 5},
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "live-validate",
                "--niche",
                "python_automation",
                "--skip-collection",
                "--evidence-path",
                str(ev_path),
            ],
        )
        assert result.exit_code == 0
        ev = json.loads(ev_path.read_text(encoding="utf-8"))
        assert ev.get("success") is False


class TestRecommendationsEdgeCases:
    def test_live_flag_passes_dry_run_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured_calls: list[dict[str, Any]] = []

        async def fake_pipeline(**kwargs: Any) -> dict[str, Any]:
            captured_calls.append(kwargs)
            return {"status": "ok"}

        class _DummyCtx:
            def __enter__(self) -> Any:
                return object()

            def __exit__(self, *args: Any) -> bool:
                return False

        monkeypatch.setattr("src.recommendations.pipeline.run_recommendations_pipeline", fake_pipeline)
        monkeypatch.setattr(run_module, "_recommendation_db_session", lambda *_args, **_kwargs: _DummyCtx())
        monkeypatch.setattr(run_module, "_load_recommendation_config", lambda *_args, **_kwargs: {})
        monkeypatch.setattr("src.llm.client.build_llm_client", lambda _cfg: object())
        runner = CliRunner()
        result = runner.invoke(cli, ["recommendations-only", "--live"], catch_exceptions=False)
        assert result.exit_code == 0
        assert captured_calls
        assert captured_calls[0].get("dry_run", True) is False

    def test_default_still_dry_run_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured_calls: list[dict[str, Any]] = []

        async def fake_pipeline(**kwargs: Any) -> dict[str, Any]:
            captured_calls.append(kwargs)
            return {}

        class _DummyCtx:
            def __enter__(self) -> Any:
                return object()

            def __exit__(self, *args: Any) -> bool:
                return False

        monkeypatch.setattr("src.recommendations.pipeline.run_recommendations_pipeline", fake_pipeline)
        monkeypatch.setattr(run_module, "_recommendation_db_session", lambda *_args, **_kwargs: _DummyCtx())
        monkeypatch.setattr(run_module, "_load_recommendation_config", lambda *_args, **_kwargs: {})
        runner = CliRunner()
        result = runner.invoke(cli, ["recommendations-only"], catch_exceptions=True)
        assert result.exit_code == 0
        assert captured_calls
        assert captured_calls[0].get("dry_run", True) is True

    def test_live_falls_back_when_no_openai_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured_calls: list[dict[str, Any]] = []

        async def fake_pipeline(**kwargs: Any) -> dict[str, Any]:
            captured_calls.append(kwargs)
            return {}

        class _DummyCtx:
            def __enter__(self) -> Any:
                return object()

            def __exit__(self, *args: Any) -> bool:
                return False

        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setattr("src.recommendations.pipeline.run_recommendations_pipeline", fake_pipeline)
        monkeypatch.setattr(run_module, "_recommendation_db_session", lambda *_args, **_kwargs: _DummyCtx())
        monkeypatch.setattr(run_module, "_load_recommendation_config", lambda *_args, **_kwargs: {})
        monkeypatch.setattr("src.llm.client.build_llm_client", lambda _cfg: None)
        runner = CliRunner()
        result = runner.invoke(cli, ["recommendations-only", "--live"], catch_exceptions=True)
        assert result.exit_code == 0
        assert captured_calls
        assert captured_calls[0].get("dry_run", True) is True


class TestPlaybookEdgeCases:
    def test_does_not_mutate_input_config(self) -> None:
        config = {"scoring": {"profiles": {}}}
        snapshot = json.loads(json.dumps(config))

        class _FailDB:
            def query(self, _model: Any) -> Any:
                raise RuntimeError("db error")

        _ = generate_playbook("python_automation", _FailDB(), config)
        assert config == snapshot

    def test_markdown_handles_all_section_types(self) -> None:
        playbook = {
            "niche_id": "test",
            "niche_name": "Test Niche",
            "generated_at": "2026-06-09T00:00:00+00:00",
            "keyword_used": "test keyword",
            "has_full_data": False,
            "sections": [
                {
                    "section": "Steps Section",
                    "estimated_time": "1 week",
                    "steps": [{"title": "Step 1", "action": "Do this", "detail": "Details"}],
                },
                {
                    "section": "Strategies Section",
                    "estimated_time": "2 weeks",
                    "strategies": [{"strategy": "Strategy 1", "detail": "How to", "type": "PRIMARY"}],
                },
                {
                    "section": "Milestones Section",
                    "estimated_time": "1 month",
                    "milestones": [{"milestone": "10 Reviews", "actions": ["Action 1", "Action 2"]}],
                },
                {"section": "Empty Section", "estimated_time": "?", "steps": []},
            ],
        }
        md = export_playbook_markdown(playbook)
        assert "Step 1" in md
        assert "Strategy 1" in md
        assert "10 Reviews" in md
        assert "Empty Section" in md

    def test_has_full_data_true_with_recommendation(self) -> None:
        rec = SimpleNamespace(
            keyword_id=None,
            raw_json={
                "pricing_strategy": {"acquisition_prices": {"basic": 25, "standard": 60}},
                "visual_recommendations": {},
                "profile_optimization": {},
                "buyer_persona": {},
            },
            gig_titles=["I will automate your workflows"],
        )

        class _RecQuery:
            def filter(self, *_args: Any, **_kwargs: Any) -> "_RecQuery":
                return self

            def order_by(self, *_args: Any, **_kwargs: Any) -> "_RecQuery":
                return self

            def first(self) -> Any:
                return rec

        class _RecDB:
            def query(self, _model: Any) -> _RecQuery:
                return _RecQuery()

        playbook = generate_playbook("python_automation", _RecDB(), {})
        assert playbook["has_full_data"] is True
        assert isinstance(playbook["keyword_used"], str)
        assert len(playbook["keyword_used"]) > 0

    def test_build_gig_creation_section_handles_none_recommendation(self) -> None:
        section = build_gig_creation_section(None, {}, {})
        steps = section.get("steps", [])
        assert len(steps) == 8
        assert isinstance(steps[7].get("checklist", []), list)

    def test_generate_playbook_uses_display_name_not_slug(self) -> None:
        class _EmptyQuery:
            def filter(self, *_args: Any, **_kwargs: Any) -> "_EmptyQuery":
                return self

            def order_by(self, *_args: Any, **_kwargs: Any) -> "_EmptyQuery":
                return self

            def first(self) -> None:
                return None

        class _EmptyDB:
            def query(self, _model: Any) -> _EmptyQuery:
                return _EmptyQuery()

        playbook = generate_playbook("python_automation", _EmptyDB(), {})
        expected_name = get_niche_name("python_automation")
        assert playbook["niche_name"] == expected_name
        assert playbook["niche_name"] != "python_automation"

    def test_sections_in_exact_order(self) -> None:
        class _EmptyQuery:
            def filter(self, *_args: Any, **_kwargs: Any) -> "_EmptyQuery":
                return self

            def order_by(self, *_args: Any, **_kwargs: Any) -> "_EmptyQuery":
                return self

            def first(self) -> None:
                return None

        class _EmptyDB:
            def query(self, _model: Any) -> _EmptyQuery:
                return _EmptyQuery()

        playbook = generate_playbook("python_automation", _EmptyDB(), {})
        expected_order = [
            "Account Setup",
            "Gig Creation",
            "First 5 Orders",
            "Review Acquisition",
            "Ongoing Optimization",
        ]
        actual_names = [section["section"] for section in playbook["sections"]]
        assert actual_names == expected_order

    def test_all_sections_have_estimated_time(self) -> None:
        class _EmptyQuery:
            def filter(self, *_args: Any, **_kwargs: Any) -> "_EmptyQuery":
                return self

            def order_by(self, *_args: Any, **_kwargs: Any) -> "_EmptyQuery":
                return self

            def first(self) -> None:
                return None

        class _EmptyDB:
            def query(self, _model: Any) -> _EmptyQuery:
                return _EmptyQuery()

        playbook = generate_playbook("python_automation", _EmptyDB(), {})
        for section in playbook["sections"]:
            estimated_time = section.get("estimated_time", "")
            assert isinstance(estimated_time, str)
            assert estimated_time

    def test_build_review_strategy_section_all_niche_inputs(self) -> None:
        for niche_id in ["unknown_niche_xyz", "", "python_automation", "ai_agent_development"]:
            section = build_review_strategy_section(niche_id)
            strategies = section.get("strategies", [])
            assert len(strategies) == 3
            assert "template" in strategies[0]
            assert len(strategies[0].get("template", "")) > 20

    def test_playbook_cli_graceful_for_invalid_niche(self, tmp_path: Path) -> None:
        db_url = f"sqlite:///{(tmp_path / 'playbook_invalid.db').as_posix()}"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "playbook",
                "completely_invalid_niche_xyz_not_real",
                "--database-url",
                db_url,
            ],
        )
        assert result.exit_code in (0, 1)
        if result.exit_code == 0:
            assert "Playbook" in result.output or "Setup" in result.output or "unknown" in result.output.lower()

    def test_ongoing_optimization_uses_price_ladder_when_available(self) -> None:
        pricing_with_ladder = {
            "entry_prices": {"basic": 25, "standard": 60, "premium": 150},
            "price_ladder": [
                {"reviews": 5, "target": 35, "price": 35},
                {"reviews": 10, "target": 50, "price": 50},
                {"reviews": 25, "target": 75, "price": 75},
            ],
        }
        section = build_ongoing_optimization_section(pricing_with_ladder)
        milestones = section.get("milestones", [])
        assert len(milestones) == 4
        milestone_text = str(milestones)
        has_price_ref = any(str(price) in milestone_text for price in [35, 50, 75, 25, 60])
        assert isinstance(milestones[0].get("actions", []), list)
        assert has_price_ref is True


class TestConfigEdgeCases:
    def test_scrapfly_enabled_false_in_config(self) -> None:
        config = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
        enabled = config.get("collection", {}).get("scrapfly", {}).get("enabled")
        assert not enabled

    def test_scrapfly_enabled_runtime_override_exists_in_live_pilot(self) -> None:
        content = Path("src/collection/live_pilot.py").read_text(encoding="utf-8")
        assert "enabled" in content and "True" in content

    def test_export_playbook_markdown_starts_with_heading(self) -> None:
        class _EmptyQuery:
            def filter(self, *_args: Any, **_kwargs: Any) -> "_EmptyQuery":
                return self

            def order_by(self, *_args: Any, **_kwargs: Any) -> "_EmptyQuery":
                return self

            def first(self) -> None:
                return None

        class _EmptyDB:
            def query(self, _model: Any) -> _EmptyQuery:
                return _EmptyQuery()

        playbook = generate_playbook("python_automation", _EmptyDB(), {})
        markdown = export_playbook_markdown(playbook)
        lines = [line for line in markdown.splitlines() if line.strip()]
        assert lines
        assert lines[0].startswith("#")
        assert "Playbook" in lines[0]

