"""
drift_detector.py — lightweight model drift checks for runner state artifacts.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DriftDetector:
    """Detect simple model drift against the verified cursor model state."""

    def __init__(self, expected_state_path: str | Path | None = None) -> None:
        self.expected_state_path = Path(expected_state_path or "C:/AI_Runner/state/cursor_model_state.json")

    def check_drift(self, candidate_state_path: str | Path) -> dict[str, Any]:
        expected = self._load_json(self.expected_state_path)
        candidate = self._load_json(Path(candidate_state_path))

        expected_model = (
            expected.get("observed_model")
            or expected.get("requested_model")
            or expected.get("model")
            or "UNKNOWN"
        )
        candidate_model = candidate.get("model") or candidate.get("observed_model") or "UNKNOWN"

        drift_detected = candidate_model != expected_model
        return {
            "drift_detected": drift_detected,
            "expected_model": expected_model,
            "candidate_model": candidate_model,
            "candidate_status": candidate.get("status", "UNKNOWN"),
            "reason": "model_mismatch" if drift_detected else "none",
        }

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
