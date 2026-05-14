"""Checkpoint persistence with atomic JSON writes."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


class CheckpointCorruptionError(RuntimeError):
    """Raised when a checkpoint file cannot be parsed safely."""


class CheckpointManager:
    """JSON checkpoint manager with atomic write guarantees."""

    schema_version = "1.0"

    def __init__(self, checkpoint_dir: Path | str) -> None:
        self._checkpoint_dir = Path(checkpoint_dir)
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, run_id: str, payload: dict[str, Any]) -> Path:
        checkpoint = {
            "schema_version": self.schema_version,
            "run_id": run_id,
            "stage_name": payload.get("stage_name", "unknown"),
            "cursor_offset": payload.get("cursor_offset"),
            "record_counts": payload.get("record_counts", {}),
            "updated_at": datetime.now(UTC).isoformat(),
            "payload": payload,
        }
        path = self._checkpoint_path(run_id)
        temp_path = path.with_suffix(f".tmp.{uuid4().hex}")
        temp_path.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
        os.replace(temp_path, path)
        return path

    def load_checkpoint(self, run_id: str) -> dict[str, Any]:
        path = self._checkpoint_path(run_id)
        try:
            raw = path.read_text(encoding="utf-8")
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CheckpointCorruptionError(
                f"Checkpoint for '{run_id}' is corrupted: {exc.msg}."
            ) from exc

    def checkpoint_exists(self, run_id: str) -> bool:
        return self._checkpoint_path(run_id).exists()

    def list_checkpoints(self) -> list[str]:
        run_ids: list[str] = []
        for path in sorted(self._checkpoint_dir.glob("*.json")):
            run_ids.append(path.stem)
        return run_ids

    def mark_complete(self, run_id: str) -> Path:
        checkpoint = self.load_checkpoint(run_id)
        checkpoint["completed"] = True
        checkpoint["completed_at"] = datetime.now(UTC).isoformat()
        path = self._checkpoint_path(run_id)
        temp_path = path.with_suffix(f".tmp.{uuid4().hex}")
        temp_path.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
        os.replace(temp_path, path)
        return path

    def delete_checkpoint(self, run_id: str, allow_delete: bool = False) -> None:
        if not allow_delete:
            raise PermissionError("Checkpoint deletion requires allow_delete=True.")
        path = self._checkpoint_path(run_id)
        if path.exists():
            path.unlink()

    def _checkpoint_path(self, run_id: str) -> Path:
        safe_run_id = run_id.replace("/", "_").replace("\\", "_")
        return self._checkpoint_dir / f"{safe_run_id}.json"
