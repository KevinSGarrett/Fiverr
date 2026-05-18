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


class CheckpointManager:
    """File-backed checkpoint manager for resumable collection runs."""

    def __init__(self, run_id: str, data_dir: str = "data") -> None:
        self.run_id = run_id
        self.checkpoint_dir = Path(data_dir) / "checkpoints" / run_id
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def write(self, stage: str, niche_id: str, data: dict[str, Any]) -> None:
        """Atomically write a checkpoint using tmp + fsync + os.replace."""
        filename = f"{stage}_{niche_id}.json"
        tmp_path = self.checkpoint_dir / f"{filename}.tmp"
        final_path = self.checkpoint_dir / filename

        checkpoint_data: dict[str, Any] = {
            "schema_version": "1.0",
            "run_id": self.run_id,
            "stage": stage,
            "niche_id": niche_id,
            "checkpoint_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
        # Preserve mandatory common fields even if caller provides colliding keys.
        checkpoint_data.update(data)
        checkpoint_data["schema_version"] = "1.0"
        checkpoint_data["run_id"] = self.run_id
        checkpoint_data["stage"] = stage
        checkpoint_data["niche_id"] = niche_id
        checkpoint_data["checkpoint_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(checkpoint_data, handle, indent=2, default=str)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(tmp_path, final_path)

    def read(self, stage: str, niche_id: str) -> dict[str, Any] | None:
        """Read a checkpoint file, returning None when missing or invalid."""
        path = self.checkpoint_dir / f"{stage}_{niche_id}.json"
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
        except (json.JSONDecodeError, OSError):
            return None
        if not isinstance(loaded, dict):
            return None
        return loaded

    def cleanup(self) -> None:
        """Delete this run's checkpoint directory if it exists."""
        import shutil

        if self.checkpoint_dir.exists():
            shutil.rmtree(self.checkpoint_dir)

    def list_checkpoints(self) -> list[dict[str, Any]]:
        """Return all valid checkpoint payloads sorted by stage name."""
        checkpoints: list[dict[str, Any]] = []
        for checkpoint_path in sorted(self.checkpoint_dir.glob("*.json")):
            stage, _, niche_id = checkpoint_path.stem.partition("_")
            if not stage or not niche_id:
                continue
            checkpoint = self.read(stage, niche_id)
            if checkpoint is not None:
                checkpoints.append(checkpoint)
        return checkpoints

    @staticmethod
    def find_latest_run(data_dir: str = "data") -> str | None:
        """Return the most recent run_id directory that has checkpoint JSON files."""
        checkpoint_root = Path(data_dir) / "checkpoints"
        if not checkpoint_root.exists():
            return None

        run_dirs = sorted(
            (path for path in checkpoint_root.iterdir() if path.is_dir()),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for run_dir in run_dirs:
            if list(run_dir.glob("*.json")):
                return run_dir.name
        return None


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
