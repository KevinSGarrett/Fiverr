"""Deterministic queue model for collection search plan jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from src.collection.search_plan import SearchPlan


class QueueJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    DEAD_LETTER = "dead_letter"


@dataclass(frozen=True, slots=True)
class QueueJob:
    """Planned queue job derived from a search plan item."""

    job_id: str
    keyword_id: str
    query: str
    url: str
    page_number: int
    max_pages: int
    source: str
    estimated_priority: int
    source_seed: str
    status: QueueJobStatus = QueueJobStatus.PENDING


@dataclass(frozen=True, slots=True)
class CollectionQueue:
    """Immutable queue snapshot used for deterministic checkpointing."""

    jobs: list[QueueJob] = field(default_factory=list)


def enqueue_search_plan(plan: SearchPlan) -> CollectionQueue:
    """Convert a search plan into deterministic pending queue jobs."""

    ordered_items = sorted(
        plan.items,
        key=lambda item: (-item.estimated_priority, item.keyword_id, item.page_number, item.url),
    )
    jobs = [
        QueueJob(
            job_id=f"job-{index + 1:05d}",
            keyword_id=item.keyword_id,
            query=item.query,
            url=item.url,
            page_number=item.page_number,
            max_pages=item.max_pages,
            source=item.source,
            estimated_priority=item.estimated_priority,
            source_seed=item.source_seed,
        )
        for index, item in enumerate(ordered_items)
    ]
    return CollectionQueue(jobs=jobs)
