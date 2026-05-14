"""In-memory queue processor foundation for collection stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from typing import Any


class JobPriority(IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class JobStatus(StrEnum):
    WAITING = "waiting"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3


@dataclass(slots=True)
class CollectionJob:
    job_id: str
    payload: dict[str, Any]
    priority: JobPriority = JobPriority.NORMAL
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    status: JobStatus = JobStatus.WAITING
    attempts: int = 0
    last_error: str | None = None
    error_history: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    finished_at: datetime | None = None


class QueueProcessor:
    """Deterministic in-memory queue with bounded retries."""

    def __init__(self) -> None:
        self._jobs: dict[str, CollectionJob] = {}

    def enqueue(self, job: CollectionJob) -> None:
        if job.job_id in self._jobs:
            raise ValueError(f"Job '{job.job_id}' already exists.")
        job.status = JobStatus.WAITING
        job.updated_at = datetime.now(UTC)
        self._jobs[job.job_id] = job

    def dequeue(self) -> CollectionJob | None:
        waiting_jobs = [job for job in self._jobs.values() if job.status == JobStatus.WAITING]
        if not waiting_jobs:
            return None
        return sorted(waiting_jobs, key=lambda job: (-int(job.priority), job.created_at))[0]

    def mark_running(self, job_id: str) -> None:
        job = self._get_job(job_id)
        job.status = JobStatus.RUNNING
        now = datetime.now(UTC)
        job.started_at = now
        job.updated_at = now

    def mark_success(self, job_id: str) -> None:
        job = self._get_job(job_id)
        now = datetime.now(UTC)
        job.status = JobStatus.SUCCEEDED
        job.finished_at = now
        job.updated_at = now

    def mark_failed(self, job_id: str, error: str) -> None:
        job = self._get_job(job_id)
        now = datetime.now(UTC)
        job.attempts += 1
        job.status = JobStatus.FAILED
        job.last_error = error
        job.error_history.append(error)
        job.finished_at = now
        job.updated_at = now

    def retry_or_dead_letter(self, job_id: str, error: str) -> JobStatus:
        self.mark_failed(job_id, error)
        job = self._get_job(job_id)
        if job.attempts < job.retry_policy.max_attempts:
            job.status = JobStatus.WAITING
            job.updated_at = datetime.now(UTC)
            return JobStatus.WAITING

        job.status = JobStatus.DEAD_LETTER
        job.updated_at = datetime.now(UTC)
        return JobStatus.DEAD_LETTER

    def snapshot(self) -> dict[str, Any]:
        counts = {status.value: 0 for status in JobStatus}
        for job in self._jobs.values():
            counts[job.status.value] += 1
        counts["total"] = len(self._jobs)
        return {
            "counts": counts,
            "jobs": {
                job_id: {
                    "status": job.status.value,
                    "attempts": job.attempts,
                    "last_error": job.last_error,
                    "priority": int(job.priority),
                }
                for job_id, job in self._jobs.items()
            },
        }

    def _get_job(self, job_id: str) -> CollectionJob:
        if job_id not in self._jobs:
            raise KeyError(f"Unknown job id '{job_id}'.")
        return self._jobs[job_id]
