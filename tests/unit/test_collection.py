"""Unit tests for collection package foundation scaffolding."""

import importlib
import json
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType

import pytest
from src.collection import CollectionStageResult
from src.collection.checkpoint import CheckpointCorruptionError, CheckpointManager
from src.collection.contracts import CollectionStageInput, CollectionStageStatus
from src.collection.orchestrator import CollectionOrchestrator, CollectionStage
from src.collection.pacing import PacingConfig, PacingManager
from src.collection.playwright_check import (
    INSTALL_COMMAND,
    check_playwright_chromium_available,
)
from src.collection.proxy import ProxyConfig, ProxyConfigurationError, ProxyProvider
from src.collection.queue import CollectionJob, JobPriority, JobStatus, QueueProcessor, RetryPolicy
from src.collection.safety import validate_collection_action
from src.collection.selectors import (
    SelectorEntry,
    explain_missing_required_selectors,
    get_selector_group,
    list_selector_groups,
    validate_selector_registry,
)
from src.collection.session import BrowserMode, PlaywrightSessionManager, SessionManagerConfig


def test_collection_package_and_exports_are_importable() -> None:
    module = importlib.import_module("src.collection")
    assert module is not None
    assert CollectionStageResult.__name__ == "CollectionStageResult"


def test_collection_stage_result_model_dump() -> None:
    result = CollectionStageResult(
        stage_name="seed_stage",
        status=CollectionStageStatus.SUCCESS,
        records_seen=12,
        records_written=10,
        warnings=["sample warning"],
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        metadata={"batch_id": "batch-001"},
    )

    payload = result.model_dump()
    assert payload["stage_name"] == "seed_stage"
    assert payload["records_seen"] == 12
    assert payload["metadata"]["batch_id"] == "batch-001"


def test_playwright_checker_import_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_import_error(name: str) -> ModuleType:
        raise ImportError(f"module not found: {name}")

    monkeypatch.setattr("src.collection.playwright_check.importlib.import_module", _raise_import_error)

    result = check_playwright_chromium_available()
    assert result["available"] is False
    assert result["needs_install"] is True
    assert result["command"] == INSTALL_COMMAND
    assert "not importable" in str(result["message"]).lower()


def test_playwright_checker_import_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def _import_ok(name: str) -> ModuleType:
        return ModuleType(name)

    monkeypatch.setattr("src.collection.playwright_check.importlib.import_module", _import_ok)

    result = check_playwright_chromium_available()
    assert result["available"] is True
    assert result["needs_install"] is False
    assert result["command"] == INSTALL_COMMAND
    assert "importable" in str(result["message"]).lower()


def test_validate_collection_action_allows_read_only_action() -> None:
    assert validate_collection_action("view_search_results") is True


def test_validate_collection_action_blocks_forbidden_mutation() -> None:
    with pytest.raises(ValueError, match="Forbidden collection action"):
        validate_collection_action("purchase")


def test_selector_registry_has_required_groups() -> None:
    groups = set(list_selector_groups())
    assert {"search_results", "gig_detail", "seller_profile", "autocomplete", "navigation"} <= groups


def test_selector_registry_validates_current_definitions() -> None:
    assert validate_selector_registry() == []


def test_missing_required_selector_detection_works_for_custom_registry() -> None:
    broken = {
        "search_results": (SelectorEntry(name="cards", css_candidates=(), required=True),),
    }
    messages = explain_missing_required_selectors(broken)
    assert any("has no candidates" in message for message in messages)


def test_no_selector_group_is_empty() -> None:
    for group_name in list_selector_groups():
        assert get_selector_group(group_name), f"{group_name} should not be empty"


class FakeClock:
    def __init__(self) -> None:
        self.current = 100.0

    def now(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


def test_pacing_next_delay_deterministic_with_injected_random() -> None:
    clock = FakeClock()
    manager = PacingManager(
        config=PacingConfig(base_delay_seconds=1.0, jitter_min_seconds=0.0, jitter_max_seconds=1.0),
        random_provider=lambda min_s, max_s: (min_s + max_s) / 2,
        clock=clock.now,
    )
    assert manager.next_delay() == pytest.approx(1.5)


def test_pacing_repeated_error_increases_cooldown() -> None:
    clock = FakeClock()
    manager = PacingManager(clock=clock.now)
    manager.record_error("fiverr", status_code=500)
    first = manager.get_state("fiverr").cooldown_until
    manager.record_error("fiverr", status_code=500)
    second = manager.get_state("fiverr").cooldown_until
    assert first is not None and second is not None
    assert second >= first


def test_pacing_429_applies_stronger_cooldown() -> None:
    clock = FakeClock()
    manager = PacingManager(clock=clock.now)
    manager.record_error("fiverr", status_code=500)
    regular_backoff = manager.get_state("fiverr").backoff_seconds
    manager.record_error("fiverr", status_code=429)
    throttled_backoff = manager.get_state("fiverr").backoff_seconds
    assert throttled_backoff >= regular_backoff


def test_pacing_success_reduces_backoff_safely() -> None:
    clock = FakeClock()
    manager = PacingManager(clock=clock.now)
    manager.record_error("fiverr", status_code=500)
    before = manager.get_state("fiverr").backoff_seconds
    manager.record_success("fiverr")
    after = manager.get_state("fiverr").backoff_seconds
    assert 0.0 <= after <= before


def test_pacing_delay_never_negative() -> None:
    manager = PacingManager(
        config=PacingConfig(base_delay_seconds=0.0, jitter_min_seconds=0.0, jitter_max_seconds=0.0)
    )
    assert manager.next_delay("fiverr") >= 0.0


def test_queue_dequeues_highest_priority_first() -> None:
    queue = QueueProcessor()
    queue.enqueue(CollectionJob(job_id="low", payload={}, priority=JobPriority.LOW))
    queue.enqueue(CollectionJob(job_id="high", payload={}, priority=JobPriority.HIGH))
    assert queue.dequeue() is not None
    assert queue.dequeue().job_id == "high"


def test_queue_retries_then_dead_letters() -> None:
    queue = QueueProcessor()
    queue.enqueue(
        CollectionJob(
            job_id="job-1",
            payload={},
            retry_policy=RetryPolicy(max_attempts=2),
        )
    )
    queue.mark_running("job-1")
    assert queue.retry_or_dead_letter("job-1", "boom") == JobStatus.WAITING
    queue.mark_running("job-1")
    assert queue.retry_or_dead_letter("job-1", "boom-again") == JobStatus.DEAD_LETTER


def test_queue_success_records_status_and_timestamps() -> None:
    queue = QueueProcessor()
    queue.enqueue(CollectionJob(job_id="job-2", payload={}))
    queue.mark_running("job-2")
    queue.mark_success("job-2")
    snapshot = queue.snapshot()
    assert snapshot["jobs"]["job-2"]["status"] == JobStatus.SUCCEEDED.value


def test_queue_snapshot_counts_statuses() -> None:
    queue = QueueProcessor()
    queue.enqueue(CollectionJob(job_id="waiting", payload={}))
    queue.enqueue(CollectionJob(job_id="running", payload={}))
    queue.mark_running("running")
    queue.enqueue(CollectionJob(job_id="done", payload={}))
    queue.mark_running("done")
    queue.mark_success("done")
    queue.enqueue(CollectionJob(job_id="dead", payload={}, retry_policy=RetryPolicy(max_attempts=1)))
    queue.mark_running("dead")
    queue.retry_or_dead_letter("dead", "fail")
    counts = queue.snapshot()["counts"]
    assert counts["waiting"] == 1
    assert counts["running"] == 1
    assert counts["succeeded"] == 1
    assert counts["dead_letter"] == 1


def test_checkpoint_round_trip_and_list() -> None:
    with TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(temp_dir)
        manager.save_checkpoint("run-1", {"stage_name": "seed", "cursor_offset": 0, "record_counts": {}})
        loaded = manager.load_checkpoint("run-1")
        assert loaded["run_id"] == "run-1"
        assert "run-1" in manager.list_checkpoints()


def test_checkpoint_atomic_write_creates_final_file() -> None:
    with TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(temp_dir)
        final_path = manager.save_checkpoint("run-atomic", {"stage_name": "seed", "record_counts": {}})
        assert final_path.exists()
        assert final_path.suffix == ".json"


def test_checkpoint_corruption_raises_custom_error() -> None:
    with TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(temp_dir)
        path = Path(temp_dir) / "run-bad.json"
        path.write_text("{not-json", encoding="utf-8")
        with pytest.raises(CheckpointCorruptionError):
            manager.load_checkpoint("run-bad")
        assert path.exists()


def test_checkpoint_delete_requires_allow_delete() -> None:
    with TemporaryDirectory() as temp_dir:
        manager = CheckpointManager(temp_dir)
        manager.save_checkpoint("run-delete", {"stage_name": "seed", "record_counts": {}})
        with pytest.raises(PermissionError):
            manager.delete_checkpoint("run-delete")
        manager.delete_checkpoint("run-delete", allow_delete=True)
        assert manager.checkpoint_exists("run-delete") is False


def test_session_missing_file_returns_invalid_message(tmp_path: Path) -> None:
    manager = PlaywrightSessionManager(
        SessionManagerConfig(
            mode=BrowserMode.AUTHENTICATED_READ_ONLY,
            session_file_path=tmp_path / "missing.json",
        )
    )
    validation = manager.validate_session_state_file()
    assert validation.valid is False
    assert "does not exist" in validation.message


def test_session_launch_options_do_not_include_credentials(tmp_path: Path) -> None:
    session_file = tmp_path / "state.json"
    session_file.write_text("{}", encoding="utf-8")
    manager = PlaywrightSessionManager(
        SessionManagerConfig(
            mode=BrowserMode.AUTHENTICATED_READ_ONLY,
            session_file_path=session_file,
        )
    )
    options = manager.build_launch_options()
    assert "password" not in json.dumps(options)
    assert options["storage_state"] == str(session_file)


def test_authenticated_mode_requires_external_session_path() -> None:
    manager = PlaywrightSessionManager(
        SessionManagerConfig(mode=BrowserMode.AUTHENTICATED_READ_ONLY, session_file_path=None)
    )
    assert manager.validate_session_state_file().valid is False


def test_unauthenticated_mode_proceeds_without_session_file() -> None:
    manager = PlaywrightSessionManager(
        SessionManagerConfig(mode=BrowserMode.UNAUTHENTICATED_READ_ONLY, session_file_path=None)
    )
    assert manager.validate_session_state_file().valid is True


def test_session_paths_under_repo_are_rejected_when_not_safe(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    session_file = repo_root / "state.json"
    session_file.write_text("{}", encoding="utf-8")
    manager = PlaywrightSessionManager(
        SessionManagerConfig(
            mode=BrowserMode.AUTHENTICATED_READ_ONLY,
            session_file_path=session_file,
            repo_root=repo_root,
        )
    )
    assert manager.validate_session_state_file().valid is False


def test_proxy_disabled_returns_none() -> None:
    provider = ProxyProvider()
    assert provider.build_proxy_settings(ProxyConfig(enabled=False)) is None


def test_proxy_enabled_with_env_credentials_returns_dict() -> None:
    env = {"P_USER": "user-a", "P_PASS": "pass-a"}
    provider = ProxyProvider(env_provider=env.get)
    config = ProxyConfig(
        enabled=True,
        server="http://proxy.test",
        username_env_var="P_USER",
        password_env_var="P_PASS",
    )
    proxy = provider.build_proxy_settings(config)
    assert proxy == {
        "server": "http://proxy.test",
        "username": "user-a",
        "password": "pass-a",
    }


def test_proxy_repr_and_redact_hide_password_name() -> None:
    config = ProxyConfig(
        enabled=True,
        server="http://proxy.test",
        username_env_var="P_USER",
        password_env_var="P_PASS",
    )
    assert config.redact()["password_env_var"] == "***"
    assert "***" in repr(config)


def test_proxy_missing_env_var_raises_safe_error() -> None:
    provider = ProxyProvider(env_provider=lambda key: None)
    config = ProxyConfig(
        enabled=True,
        server="http://proxy.test",
        username_env_var="P_USER",
        password_env_var="P_PASS",
    )
    with pytest.raises(ProxyConfigurationError) as exc:
        provider.build_proxy_settings(config)
    assert "pass-a" not in str(exc.value)


def _success_stage(stage_name: str) -> CollectionStage:
    def _handler(stage_input: CollectionStageInput) -> CollectionStageResult:
        return CollectionStageResult(
            stage_name=stage_name,
            status=CollectionStageStatus.SUCCESS,
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
            records_seen=1,
            records_written=1,
            metadata={"received_stage": stage_input.stage_name},
        )

    return CollectionStage(name=stage_name, handler=_handler)


def test_orchestrator_runs_fake_stages_in_order_and_saves_checkpoint(tmp_path: Path) -> None:
    queue = QueueProcessor()
    pacing = PacingManager(random_provider=lambda _a, _b: 0.0)
    checkpoint = CheckpointManager(tmp_path)
    orchestrator = CollectionOrchestrator(queue, pacing, checkpoint, dry_run=True)

    results = orchestrator.run("run-order", [_success_stage("one"), _success_stage("two")])
    assert [result.stage_name for result in results] == ["one", "two"]
    assert checkpoint.checkpoint_exists("run-order")


def test_orchestrator_stage_failure_records_failure_preserving_prior_results(tmp_path: Path) -> None:
    queue = QueueProcessor()
    pacing = PacingManager(random_provider=lambda _a, _b: 0.0)
    checkpoint = CheckpointManager(tmp_path)
    orchestrator = CollectionOrchestrator(queue, pacing, checkpoint, dry_run=True)

    stage_calls: deque[str] = deque()

    def first(stage_input: CollectionStageInput) -> CollectionStageResult:
        stage_calls.append(stage_input.stage_name)
        return CollectionStageResult(
            stage_name="one",
            status=CollectionStageStatus.SUCCESS,
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
        )

    def second(_stage_input: CollectionStageInput) -> CollectionStageResult:
        raise RuntimeError("synthetic failure")

    results = orchestrator.run(
        "run-fail",
        [CollectionStage("one", first), CollectionStage("two", second), _success_stage("three")],
    )
    assert len(results) == 2
    assert results[0].status == CollectionStageStatus.SUCCESS
    assert results[1].status == CollectionStageStatus.FAILED
    assert list(stage_calls) == ["one"]


def test_orchestrator_consults_pacing_without_sleep(tmp_path: Path) -> None:
    queue = QueueProcessor()
    pacing = PacingManager(random_provider=lambda _a, _b: 0.0)
    checkpoint = CheckpointManager(tmp_path)
    orchestrator = CollectionOrchestrator(queue, pacing, checkpoint, dry_run=True)

    calls = {"count": 0}

    def fake_next_delay(source: str = "fiverr") -> float:
        calls["count"] += 1
        return 0.0

    pacing.next_delay = fake_next_delay  # type: ignore[assignment]
    orchestrator.run("run-pacing", [_success_stage("one"), _success_stage("two")])
    assert calls["count"] == 2
