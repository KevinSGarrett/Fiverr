"""Deterministic atomic queue checkpoint helpers."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.collection.contracts import validate_collection_stage_summary
from src.collection.queue import CollectionQueue


class QueueCheckpointError(RuntimeError):
    """Raised when queue checkpoint read/write operations fail safely."""


def checkpoint_queue_state(
    queue: CollectionQueue,
    path: Path | str,
    *,
    stage_summary: dict[str, object] | None = None,
) -> Path:
    """Persist queue state atomically as deterministic JSON."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, object] = {
        "schema_version": "1.0",
        "saved_at": datetime.now(UTC).isoformat(),
        "jobs": [
            {
                "job_id": job.job_id,
                "keyword_id": job.keyword_id,
                "query": job.query,
                "url": job.url,
                "page_number": job.page_number,
                "max_pages": job.max_pages,
                "source": job.source,
                "source_seed": job.source_seed,
                "estimated_priority": job.estimated_priority,
                "status": job.status.value,
            }
            for job in queue.jobs
        ],
    }
    if stage_summary is not None:
        payload["stage_summary"] = stage_summary

    temp_path = output_path.with_suffix(f"{output_path.suffix}.tmp.{uuid4().hex}")
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temp_path, output_path)
    return output_path


def load_queue_checkpoint(path: Path | str) -> dict[str, object]:
    """Load queue checkpoint and raise controlled error on corruption."""

    checkpoint_path = Path(path)
    try:
        payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise QueueCheckpointError(
            f"Checkpoint at '{checkpoint_path}' is corrupted: {exc.msg}."
        ) from exc
    if not isinstance(payload, dict):
        raise QueueCheckpointError(
            f"Checkpoint at '{checkpoint_path}' must be a JSON object payload."
        )
    return payload


def load_checkpoint_stage_summary(path: Path | str) -> dict[str, Any]:
    """Load and validate stage summary from checkpoint payload."""

    payload = load_queue_checkpoint(path)
    raw_summary = payload.get("stage_summary")
    if not isinstance(raw_summary, dict):
        raise QueueCheckpointError(f"Checkpoint at '{Path(path)}' does not include a stage_summary mapping.")
    validate_collection_stage_summary(raw_summary)
    return raw_summary


def load_checkpoint_stage_summary_or_fallback(path: Path | str) -> dict[str, Any] | None:
    """Return validated stage summary, or None when checkpoint is unavailable/corrupted."""

    try:
        return load_checkpoint_stage_summary(path)
    except (FileNotFoundError, QueueCheckpointError, ValueError):
        return None
