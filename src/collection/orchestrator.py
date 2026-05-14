"""Dry-run collection orchestration with no browser or network usage."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.collection.checkpoint import checkpoint_queue_state
from src.collection.contracts import CollectionError, CollectionStageResult, CollectionStageStatus
from src.collection.keyword_expansion import expand_keywords
from src.collection.queue import enqueue_search_plan
from src.collection.search_plan import build_search_plan


def run_collection_dry_run(
    seed_keywords: Sequence[str],
    *,
    niche_metadata: Mapping[str, Any] | None = None,
    max_candidates: int = 50,
    max_pages: int = 1,
    checkpoint_path: Path | str = "artifacts/collection/queue_checkpoint.json",
    region: str | None = None,
    language: str | None = None,
    sort: str | None = None,
) -> CollectionStageResult:
    """Run collection planning stages without external side effects."""

    started_at = datetime.now(UTC)
    try:
        if not isinstance(seed_keywords, Sequence) or isinstance(seed_keywords, (str, bytes)):
            raise ValueError("seed_keywords must be a sequence of strings.")

        expanded = expand_keywords(
            seed_keywords,
            niche_metadata=niche_metadata,
            max_candidates=max_candidates,
        )
        plan = build_search_plan(
            expanded.expanded_keywords,
            region=region,
            language=language,
            sort=sort,
            max_pages=max_pages,
        )
        queue = enqueue_search_plan(plan)
        saved_checkpoint = checkpoint_queue_state(queue, checkpoint_path)

        warnings = list(expanded.warnings) + list(plan.warnings)
        return CollectionStageResult(
            stage_name="collection_dry_run",
            status=CollectionStageStatus.SUCCESS,
            records_seen=len(expanded.expanded_keywords),
            records_written=len(queue.jobs),
            warnings=warnings,
            checkpoint_path=saved_checkpoint,
            started_at=started_at,
            finished_at=datetime.now(UTC),
            metadata={
                "expanded_keywords_count": len(expanded.expanded_keywords),
                "search_plan_items_count": len(plan.items),
                "queue_jobs_count": len(queue.jobs),
                "max_pages": max_pages,
            },
        )
    except Exception as exc:
        return CollectionStageResult(
            stage_name="collection_dry_run",
            status=CollectionStageStatus.FAILED,
            started_at=started_at,
            finished_at=datetime.now(UTC),
            errors=[
                CollectionError(
                    code="dry_run_failed",
                    message=str(exc),
                )
            ],
        )
