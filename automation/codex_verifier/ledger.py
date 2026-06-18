"""
ledger.py -- Persists per-agent attempt history for oscillation/regression detection.

ICV-LEDGER-1..3: Append-only; resumable; stored under run_dir/icv/ledger.json.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path



class VerificationLedger:
    def __init__(self, run_dir: Path, agent: str) -> None:
        self._path = run_dir / "icv" / f"ledger_{agent}.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._records: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []

    def record(
        self,
        agent: str,
        attempt: int,
        verdict_status: str,
        completion_score: float,
        decision_kind: str,
        stop_reason: str | None,
        cost_usd: float,
        tokens_used: int,
        unmet_count: int,
        deterministic_only: bool,
    ) -> None:
        entry = {
            "attempt": attempt,
            "timestamp": datetime.now(UTC).isoformat(),
            "agent": agent,
            "verdict_status": verdict_status,
            "completion_score": completion_score,
            "decision_kind": decision_kind,
            "stop_reason": stop_reason,
            "cost_usd": cost_usd,
            "tokens_used": tokens_used,
            "unmet_count": unmet_count,
            "deterministic_only": deterministic_only,
        }
        self._records.append(entry)
        try:
            self._path.write_text(json.dumps(self._records, indent=2), encoding="utf-8")
        except Exception:
            pass

    def entries(self) -> list[dict]:
        return list(self._records)

    def total_cost(self) -> float:
        return sum(r.get("cost_usd", 0.0) for r in self._records)
