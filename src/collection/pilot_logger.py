"""Persistent request logger for TierD-2 live collection pilot."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


@dataclass(slots=True)
class PilotRequestLog:
    """One serialized request-level event captured during pilot collection."""

    timestamp: str
    url: str
    stage: str
    status_code: int
    credits_used: int
    success: bool
    asp_triggered: bool
    error: str | None
    retry_count: int
    blocked: bool


class PilotLogger:
    """Logs every ScrapFly request and builds a persisted evidence bundle."""

    def __init__(self, log_path: str = "data/live_pilot_log.jsonl") -> None:
        self._path = Path(log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[PilotRequestLog] = []

    def log_request(
        self,
        url: str,
        stage: str,
        status_code: int,
        credits_used: int,
        success: bool,
        asp_triggered: bool = False,
        error: str | None = None,
        retry_count: int = 0,
        blocked: bool = False,
    ) -> None:
        """Append one request event to in-memory entries and JSONL disk log."""
        entry = PilotRequestLog(
            timestamp=datetime.now(UTC).isoformat(),
            url=url[:200],
            stage=stage,
            status_code=status_code,
            credits_used=credits_used,
            success=success,
            asp_triggered=asp_triggered,
            error=error,
            retry_count=retry_count,
            blocked=blocked,
        )
        self._entries.append(entry)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(entry), ensure_ascii=True) + "\n")
        log.debug("PilotLogger request stage=%s url=%s credits=%d", stage, entry.url, credits_used)

    def write_evidence_bundle(
        self,
        output_path: str,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist summary evidence JSON and return the assembled bundle payload."""
        total = len(self._entries)
        total_credits = sum(entry.credits_used for entry in self._entries)
        total_errors = sum(1 for entry in self._entries if entry.error)
        total_blocked = sum(1 for entry in self._entries if entry.blocked)
        block_rate = round(total_blocked / max(1, total), 3)
        error_rate = round(total_errors / max(1, total), 3)

        bundle: dict[str, Any] = {
            "generated_at": datetime.now(UTC).isoformat(),
            "total_requests": total,
            "total_credits_used": total_credits,
            "total_errors": total_errors,
            "block_rate": block_rate,
            "error_rate": error_rate,
            "stop_conditions_triggered": block_rate > 0.5 or error_rate > 0.3,
            "requests_by_stage": {},
            "log_path": str(self._path),
        }

        for entry in self._entries:
            stage_data = bundle["requests_by_stage"].setdefault(
                entry.stage,
                {"count": 0, "credits": 0, "errors": 0, "blocked": 0},
            )
            stage_data["count"] += 1
            stage_data["credits"] += entry.credits_used
            if entry.error:
                stage_data["errors"] += 1
            if entry.blocked:
                stage_data["blocked"] += 1

        if extra:
            bundle.update(extra)

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(bundle, indent=2, default=str), encoding="utf-8")
        return bundle
