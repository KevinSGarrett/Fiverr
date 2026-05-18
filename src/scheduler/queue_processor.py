"""Queue processor for sequential collection job execution."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models.job import Job

NEXT_JOB_QUERY = text(
    """
    SELECT j.id
    FROM jobs j
    WHERE j.run_id = :run_id
      AND j.status = 'QUEUED'
    ORDER BY
      CASE j.priority
        WHEN 'CRITICAL' THEN 0
        WHEN 'HIGH' THEN 1
        WHEN 'STANDARD' THEN 2
        WHEN 'LOW' THEN 3
        WHEN 'BACKGROUND' THEN 4
        ELSE 5
      END ASC,
      j.stage ASC,
      j.created_at ASC
    LIMIT 1
    """
)


async def execute_with_retry(
    job_func: Callable[..., Any],
    job: Job,
    pacing_manager: Any,
    session_manager: Any,
    db: Session,
) -> bool:
    """Runs job_func with retry logic. Marks job COMPLETE, FAILED, or DEAD_LETTER."""
    job.mark_running()
    db.commit()
    try:
        await job_func(job, session_manager=session_manager, pacing_manager=pacing_manager, db=db)
        job.mark_complete()
        db.commit()
        return True
    except Exception as exc:
        job.mark_failed(str(exc))
        db.commit()
        return False


class QueueProcessor:
    """
    v1: Sequential single-job processor.
    v2: Will be replaced by Celery workers.
    """

    def __init__(self, db: Session, config: Any, session_manager: Any, pacing_manager: Any):
        self.db = db
        self.config = config
        self.session_manager = session_manager
        self.pacing_manager = pacing_manager
        self._job_handlers: dict[str, Callable[..., Any]] = {}
        self._running = False
        self._processed = 0
        self._failed = 0

    def register_handler(self, job_type: str, handler: Callable[..., Any]) -> None:
        """Register a handler function for a specific job type."""
        self._job_handlers[job_type] = handler

    async def run_until_empty(self, run_id: str) -> tuple[int, int]:
        """Sequential v1: processes jobs one at a time until none remain."""
        self._running = True
        self._processed = 0
        self._failed = 0

        while self._running:
            job = self._pull_next_job(run_id)
            if job is None:
                break

            await self._execute_job(job)
            self._processed += 1

        self._running = False
        return self._processed, self._failed

    def stop(self) -> None:
        """Gracefully stop queue processing after current job finishes."""
        self._running = False

    def _pull_next_job(self, run_id: str) -> Job | None:
        """Implements QUEUE_DESIGN.md priority query."""
        result = self.db.execute(NEXT_JOB_QUERY, {"run_id": run_id}).mappings().first()
        if result is None:
            return None
        return self.db.query(Job).filter(Job.id == result["id"]).first()

    async def _execute_job(self, job: Job) -> None:
        """Execute one queued job using its registered handler."""
        handler = self._job_handlers.get(job.job_type)
        if handler is None:
            job.status = "DEAD_LETTER"
            job.error_log = [f"No handler registered for job_type: {job.job_type}"]
            self.db.commit()
            self._failed += 1
            return

        success = await execute_with_retry(
            job_func=handler,
            job=job,
            pacing_manager=self.pacing_manager,
            session_manager=self.session_manager,
            db=self.db,
        )
        if not success:
            self._failed += 1

    def _count_queued(self, run_id: str) -> int:
        return self.db.query(Job).filter(Job.run_id == run_id, Job.status == "QUEUED").count()

    def get_stats(self) -> dict[str, float]:
        return {
            "processed": self._processed,
            "failed": self._failed,
            "success_rate": (self._processed - self._failed) / max(1, self._processed),
        }
