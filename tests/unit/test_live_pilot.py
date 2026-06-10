"""Tests for TierD-2 live pilot infrastructure."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

import run as run_module
from run import cli
from src.collection.live_pilot import run_live_collection_pilot
from src.collection.pilot_logger import PilotLogger


class TestPilotLogger:
    def test_log_request_creates_jsonl_file(self, tmp_path: Path) -> None:
        log_path = tmp_path / "pilot_log.jsonl"
        logger = PilotLogger(str(log_path))
        logger.log_request("http://test.com/path", "stage03_search", 200, 10, True)
        assert log_path.exists()

    def test_log_request_appends_each_entry(self, tmp_path: Path) -> None:
        log_path = tmp_path / "pilot_log.jsonl"
        logger = PilotLogger(str(log_path))
        for index in range(3):
            logger.log_request(f"http://example.com/{index}", "stage03_search", 200, 3, True)
        lines = log_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 3
        assert all(isinstance(json.loads(line), dict) for line in lines)

    def test_write_evidence_bundle_produces_json_with_required_keys(self, tmp_path: Path) -> None:
        log_path = tmp_path / "pilot_log.jsonl"
        evidence_path = tmp_path / "evidence.json"
        logger = PilotLogger(str(log_path))
        logger.log_request("http://ok.com", "stage03_search", 200, 10, True)
        logger.log_request("http://blocked.com", "stage04_gig_detail", 403, 12, False, blocked=True)
        bundle = logger.write_evidence_bundle(str(evidence_path))
        stored = json.loads(evidence_path.read_text(encoding="utf-8"))
        for key in [
            "total_requests",
            "total_credits_used",
            "total_errors",
            "block_rate",
            "error_rate",
            "stop_conditions_triggered",
            "requests_by_stage",
            "generated_at",
        ]:
            assert key in bundle
            assert key in stored

    def test_block_rate_calculation(self, tmp_path: Path) -> None:
        logger = PilotLogger(str(tmp_path / "pilot_log.jsonl"))
        for blocked in [True, False, True, False]:
            logger.log_request("http://x.com", "stage03_search", 200, 5, not blocked, blocked=blocked)
        bundle = logger.write_evidence_bundle(str(tmp_path / "evidence.json"))
        assert bundle["block_rate"] == 0.5

    def test_stop_conditions_triggered_when_block_rate_exceeds_threshold(self, tmp_path: Path) -> None:
        logger = PilotLogger(str(tmp_path / "pilot_log.jsonl"))
        for blocked in [True, True, True, False]:
            logger.log_request("http://x.com", "stage03_search", 200, 5, not blocked, blocked=blocked)
        bundle = logger.write_evidence_bundle(str(tmp_path / "evidence.json"))
        assert bundle["stop_conditions_triggered"] is True

    def test_total_credits_summed_correctly(self, tmp_path: Path) -> None:
        logger = PilotLogger(str(tmp_path / "pilot_log.jsonl"))
        logger.log_request("http://a.com", "stage03_search", 200, 10, True)
        logger.log_request("http://b.com", "stage04_gig_detail", 200, 20, True)
        logger.log_request("http://c.com", "stage05_seller_profile", 200, 30, True)
        bundle = logger.write_evidence_bundle(str(tmp_path / "evidence.json"))
        assert bundle["total_credits_used"] == 60


class TestRunLiveCollectionPilot:
    def test_returns_success_false_on_session_expired(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        async def fake_invalid(_self: Any) -> bool:
            return False

        monkeypatch.setattr("src.collection.session_manager.SessionManager.is_session_valid", fake_invalid)
        result = asyncio.run(
            run_live_collection_pilot(
                "python_automation",
                database_url=f"sqlite:///{(tmp_path / 'pilot.db').as_posix()}",
                evidence_path=str(tmp_path / "evidence.json"),
            )
        )
        assert result["success"] is False
        assert result["stop_reason"] == "session_expired"

    def test_returns_stop_reason_budget_exceeded(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        from src.collection.scrapfly_client import ScrapFlyRateLimitError

        async def fake_valid(_self: Any) -> bool:
            return True

        async def fake_pipeline(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            raise ScrapFlyRateLimitError("budget hit")

        monkeypatch.setattr("src.collection.session_manager.SessionManager.is_session_valid", fake_valid)
        monkeypatch.setattr("src.collection.orchestrator.run_collection_pipeline", fake_pipeline)
        result = asyncio.run(
            run_live_collection_pilot(
                "python_automation",
                database_url=f"sqlite:///{(tmp_path / 'pilot.db').as_posix()}",
                evidence_path=str(tmp_path / "evidence.json"),
            )
        )
        assert result["stop_reason"] == "budget_exceeded"

    def test_returns_success_false_on_pipeline_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        async def fake_valid(_self: Any) -> bool:
            return True

        async def fake_pipeline(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("pipeline exploded")

        monkeypatch.setattr("src.collection.session_manager.SessionManager.is_session_valid", fake_valid)
        monkeypatch.setattr("src.collection.orchestrator.run_collection_pipeline", fake_pipeline)
        result = asyncio.run(
            run_live_collection_pilot(
                "python_automation",
                database_url=f"sqlite:///{(tmp_path / 'pilot.db').as_posix()}",
                evidence_path=str(tmp_path / "evidence.json"),
            )
        )
        assert result["success"] is False
        assert result["stop_reason"] == "pipeline_error"

    def test_evidence_bundle_written_even_on_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        async def fake_valid(_self: Any) -> bool:
            return True

        async def fake_pipeline(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("boom")

        evidence_path = tmp_path / "evidence.json"
        monkeypatch.setattr("src.collection.session_manager.SessionManager.is_session_valid", fake_valid)
        monkeypatch.setattr("src.collection.orchestrator.run_collection_pipeline", fake_pipeline)
        asyncio.run(
            run_live_collection_pilot(
                "python_automation",
                database_url=f"sqlite:///{(tmp_path / 'pilot.db').as_posix()}",
                evidence_path=str(evidence_path),
            )
        )
        assert evidence_path.exists()

    def test_pilot_db_url_never_equals_baseline(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        async def fake_invalid(_self: Any) -> bool:
            return False

        monkeypatch.setattr("src.collection.session_manager.SessionManager.is_session_valid", fake_invalid)
        result = asyncio.run(
            run_live_collection_pilot(
                "python_automation",
                database_url=f"sqlite:///{(tmp_path / 'pilot.db').as_posix()}",
                evidence_path=str(tmp_path / "evidence.json"),
            )
        )
        assert "cycle037_live" not in str(result["db_url"])

    def test_seeds_niche_into_pilot_db(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        calls: list[str] = []
        original = __import__("src.collection.live_pilot", fromlist=["_seed_pilot_niche"])._seed_pilot_niche

        def spy_seed(niche_id: str, engine: Any) -> None:
            calls.append(niche_id)
            original(niche_id, engine)

        async def fake_invalid(_self: Any) -> bool:
            return False

        monkeypatch.setattr("src.collection.live_pilot._seed_pilot_niche", spy_seed)
        monkeypatch.setattr("src.collection.session_manager.SessionManager.is_session_valid", fake_invalid)
        asyncio.run(
            run_live_collection_pilot(
                "python_automation",
                database_url=f"sqlite:///{(tmp_path / 'pilot.db').as_posix()}",
                evidence_path=str(tmp_path / "evidence.json"),
            )
        )
        assert calls == ["python_automation"]


class TestCollectLiveCommand:
    def test_collect_live_registered_in_cli(self) -> None:
        content = Path("run.py").read_text(encoding="utf-8")
        assert "collect-live" in content

    def test_collect_live_requires_niche(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["collect-live"])
        assert result.exit_code != 0

    def test_collect_live_exits_1_on_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_pilot(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            return {
                "success": False,
                "credits_used": 0,
                "gigs_collected": 0,
                "search_results": 0,
                "errors": ["failed"],
                "stop_reason": "pipeline_error",
            }

        monkeypatch.setattr("src.collection.live_pilot.run_live_collection_pilot", fake_pilot)
        runner = CliRunner()
        result = runner.invoke(cli, ["collect-live", "--niche", "python_automation"])
        assert result.exit_code == 1


class TestLiveValidateCommand:
    def test_live_validate_registered_in_cli(self) -> None:
        content = Path("run.py").read_text(encoding="utf-8")
        assert "live-validate" in content

    def test_live_validate_skip_collection_accepted(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(run_module, "_validate_pilot_db_state", lambda _db: {"gigs": 0, "keywords": 5, "search_results": 3})
        monkeypatch.setattr(run_module, "_run_live_recommendations", lambda *_args: {"success": True, "count": 0, "dry_run": True})
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
                "--skip-collection",
                "--database-url",
                f"sqlite:///{(tmp_path / 'pilot.db').as_posix()}",
            ],
        )
        assert result.exit_code == 0
        assert "Stage 2: Skipped" in result.output

    def test_live_validate_writes_evidence_bundle(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        evidence_path = tmp_path / "evidence.json"
        monkeypatch.setattr(run_module, "_validate_pilot_db_state", lambda _db: {"gigs": 0, "keywords": 0, "search_results": 0})
        monkeypatch.setattr(run_module, "_run_live_recommendations", lambda *_args: {"success": False, "dry_run": True})
        monkeypatch.setattr(
            run_module,
            "_generate_playbook_from_live_data",
            lambda *_args: {"success": True, "has_full_data": False, "sections_count": 5},
        )
        monkeypatch.setattr(run_module, "run_pipeline", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("score fail")))
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "live-validate",
                "--skip-collection",
                "--database-url",
                f"sqlite:///{(tmp_path / 'pilot.db').as_posix()}",
                "--evidence-path",
                str(evidence_path),
            ],
        )
        assert result.exit_code == 0
        assert evidence_path.exists()


class TestPilotLoggerIntegration:
    def test_evidence_bundle_from_live_pilot_result(self, tmp_path: Path) -> None:
        logger = PilotLogger(str(tmp_path / "pilot.jsonl"))
        logger.log_request("http://x.com", "stage03_search", 200, 15, True)
        bundle = logger.write_evidence_bundle(
            str(tmp_path / "evidence.json"),
            extra={"success": False, "stop_reason": "budget_exceeded"},
        )
        assert "stop_reason" in bundle
        assert bundle["stop_reason"] == "budget_exceeded"

    def test_jsonl_and_evidence_consistent(self, tmp_path: Path) -> None:
        logger = PilotLogger(str(tmp_path / "pilot.jsonl"))
        for blocked in [True, False, True, False, False]:
            logger.log_request("http://x.com", "stage03_search", 200, 4, not blocked, blocked=blocked)
        evidence = logger.write_evidence_bundle(str(tmp_path / "evidence.json"))
        jsonl_lines = (tmp_path / "pilot.jsonl").read_text(encoding="utf-8").strip().splitlines()
        assert len(jsonl_lines) == evidence["total_requests"] == 5

    def test_credits_in_evidence_match_logs(self, tmp_path: Path) -> None:
        logger = PilotLogger(str(tmp_path / "pilot.jsonl"))
        logger.log_request("http://a.com", "stage03_search", 200, 10, True)
        logger.log_request("http://b.com", "stage03_search", 200, 15, True)
        logger.log_request("http://c.com", "stage03_search", 200, 20, True)
        evidence = logger.write_evidence_bundle(str(tmp_path / "evidence.json"))
        assert evidence["total_credits_used"] == 45


class TestCollectLiveEvidenceIntegration:
    def test_exit_0_when_pilot_success_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_pilot(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            return {
                "success": True,
                "credits_used": 50,
                "gigs_collected": 3,
                "search_results": 4,
                "errors": [],
            }

        monkeypatch.setattr("src.collection.live_pilot.run_live_collection_pilot", fake_pilot)
        runner = CliRunner()
        result = runner.invoke(cli, ["collect-live", "--niche", "python_automation"])
        assert result.exit_code == 0

    def test_exit_1_when_pilot_success_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_pilot(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            return {
                "success": False,
                "credits_used": 1,
                "gigs_collected": 0,
                "search_results": 0,
                "errors": ["failed"],
                "stop_reason": "pipeline_error",
            }

        monkeypatch.setattr("src.collection.live_pilot.run_live_collection_pilot", fake_pilot)
        runner = CliRunner()
        result = runner.invoke(cli, ["collect-live", "--niche", "python_automation"])
        assert result.exit_code == 1


class TestScrapFlyIntegration:
    def test_scrapfly_config_cost_budget_respected(self) -> None:
        from src.collection.scrapfly_client import ScrapFlyConfig

        cfg = ScrapFlyConfig(cost_budget_credits=100)
        assert cfg.cost_budget_credits == 100

    def test_scrapfly_stats_initializes_to_zero(self) -> None:
        from src.collection.scrapfly_client import ScrapFlyStats

        stats = ScrapFlyStats()
        assert stats.total_requests == 0
        assert stats.total_credits_used == 0
        assert stats.errors == 0
        assert stats.asp_bypasses == 0
        assert stats.blocked == 0

    def test_scrapfly_client_requires_api_key_env(self) -> None:
        from src.collection.scrapfly_client import ScrapFlyError, ScrapFlyMissingKeyError

        assert issubclass(ScrapFlyMissingKeyError, ScrapFlyError)
