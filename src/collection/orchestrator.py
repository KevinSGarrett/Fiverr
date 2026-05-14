"""No-network collection orchestration skeleton."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.collection.checkpoint import CheckpointManager
from src.collection.contracts import (
    CollectionError,
    CollectionStageInput,
    CollectionStageResult,
    CollectionStageStatus,
)
from src.collection.pacing import PacingManager
from src.collection.queue import CollectionJob, QueueProcessor

StageCallable = Callable[[CollectionStageInput], CollectionStageResult]


@dataclass(frozen=True, slots=True)
class CollectionStage:
    name: str
    handler: StageCallable


class CollectionOrchestrator:
    """Composes collection stages with queue, pacing, and checkpoints."""

    def __init__(
        self,
        queue_processor: QueueProcessor,
        pacing_manager: PacingManager,
        checkpoint_manager: CheckpointManager,
        dry_run: bool = True,
    ) -> None:
        self._queue = queue_processor
        self._pacing = pacing_manager
        self._checkpoint = checkpoint_manager
        self._dry_run = dry_run

    def run(
        self,
        run_id: str,
        stages: Sequence[CollectionStage],
        metadata: dict[str, str] | None = None,
    ) -> list[CollectionStageResult]:
        results: list[CollectionStageResult] = []
        base_metadata = metadata or {}

        for index, stage in enumerate(stages):
            _ = self._pacing.next_delay("fiverr")
            job_id = f"{run_id}:{stage.name}:{index}"
            self._queue.enqueue(
                CollectionJob(
                    job_id=job_id,
                    payload={"run_id": run_id, "stage": stage.name, "dry_run": self._dry_run},
                )
            )
            job = self._queue.dequeue()
            if job is None:
                break
            self._queue.mark_running(job.job_id)

            started_at = datetime.now(UTC)
            stage_input = CollectionStageInput(
                stage_name=stage.name,
                checkpoint_path=Path(self._checkpoint.save_checkpoint(run_id, {"stage_name": stage.name})),
                metadata={**base_metadata, "dry_run": str(self._dry_run).lower()},
            )

            try:
                result = stage.handler(stage_input)
                if result.finished_at is None:
                    result.finished_at = datetime.now(UTC)
                self._queue.mark_success(job.job_id)
                self._pacing.record_success("fiverr")
                self._checkpoint.save_checkpoint(
                    run_id,
                    {
                        "stage_name": stage.name,
                        "cursor_offset": index,
                        "record_counts": {
                            "records_seen": result.records_seen,
                            "records_written": result.records_written,
                        },
                        "payload": result.model_dump(mode="json"),
                    },
                )
                results.append(result)
            except Exception as exc:  # pragma: no cover - exercised via tests
                self._queue.retry_or_dead_letter(job.job_id, str(exc))
                self._pacing.record_error("fiverr")
                failure = CollectionStageResult(
                    stage_name=stage.name,
                    status=CollectionStageStatus.FAILED,
                    started_at=started_at,
                    finished_at=datetime.now(UTC),
                    errors=[
                        CollectionError(
                            code="stage_failure",
                            message=str(exc),
                            details={"job_id": job.job_id},
                        )
                    ],
                )
                self._checkpoint.save_checkpoint(
                    run_id,
                    {
                        "stage_name": stage.name,
                        "cursor_offset": index,
                        "record_counts": {"records_seen": 0, "records_written": 0},
                        "payload": failure.model_dump(mode="json"),
                    },
                )
                results.append(failure)
                break

        return results
