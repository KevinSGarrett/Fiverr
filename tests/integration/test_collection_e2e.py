"""Integration-flavored dry-run checks for collection foundations."""

from __future__ import annotations

from datetime import UTC, datetime

from src.collection.checkpoint import CheckpointManager
from src.collection.contracts import (
    CollectionStageInput,
    CollectionStageResult,
    CollectionStageStatus,
)
from src.collection.orchestrator import CollectionOrchestrator, CollectionStage
from src.collection.pacing import PacingManager
from src.collection.queue import QueueProcessor


def test_collection_orchestrator_dry_run_pipeline(tmp_path) -> None:
    orchestrator = CollectionOrchestrator(
        queue_processor=QueueProcessor(),
        pacing_manager=PacingManager(random_provider=lambda _a, _b: 0.0),
        checkpoint_manager=CheckpointManager(tmp_path),
        dry_run=True,
    )

    def stage_a(_stage_input: CollectionStageInput) -> CollectionStageResult:
        return CollectionStageResult(
            stage_name="stage_a",
            status=CollectionStageStatus.SUCCESS,
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
            records_seen=2,
            records_written=2,
        )

    def stage_b(_stage_input: CollectionStageInput) -> CollectionStageResult:
        return CollectionStageResult(
            stage_name="stage_b",
            status=CollectionStageStatus.SUCCESS,
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
            records_seen=1,
            records_written=1,
        )

    results = orchestrator.run("integration-run", [CollectionStage("stage_a", stage_a), CollectionStage("stage_b", stage_b)])
    assert [result.stage_name for result in results] == ["stage_a", "stage_b"]
