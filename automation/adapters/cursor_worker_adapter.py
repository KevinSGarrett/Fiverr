"""Cursor worker adapter wrapping existing cursor_adapter dispatch logic."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from automation import model_gate
from automation.cursor_adapter import _resolve_binary
from automation.cursor_adapter import run_agent as cursor_run_agent
from automation.provider_health import refresh_after_dispatch
from automation.provider_router import ProviderRouter, ProviderRunResult

CURSOR_ADAPTER_CONFIG_PATH = Path(r"C:\AI_Runner\config\cursor_adapter.yaml")
CURSOR_MODEL_STATE_PATH = Path(r"C:\AI_Runner\state\cursor_model_state.json")


class AdapterBlockedError(RuntimeError):
    """Raised when Cursor worker preflight rejects dispatch."""


class CursorWorkerAdapter:
    """Thin wrapper around cursor_adapter dispatch."""

    def __init__(self) -> None:
        self.config = self._load_config()
        self.model_state = self._load_model_state()
        try:
            self.binary = _resolve_binary()
        except Exception:
            self.binary = str(self.config.get("binary", ""))

    def _load_config(self) -> dict[str, Any]:
        if not CURSOR_ADAPTER_CONFIG_PATH.exists():
            return {}
        payload = yaml.safe_load(CURSOR_ADAPTER_CONFIG_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}

    def _load_model_state(self) -> dict[str, Any]:
        if not CURSOR_MODEL_STATE_PATH.exists():
            return {}
        payload = json.loads(CURSOR_MODEL_STATE_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}

    def _is_desktop_binary(self, binary_path: str) -> bool:
        lowered = binary_path.lower()
        return "programs\\cursor\\resources\\app\\bin\\cursor" in lowered or lowered.endswith("cursor.cmd")

    def _validate_prompt_path(self, prompt_path: Path) -> bool:
        normalized = prompt_path.as_posix().lower()
        if "/prompts/drafts/" in normalized:
            raise AdapterBlockedError("BLOCKED_DRAFT_PROMPT: only validated prompts may be dispatched")
        if "/prompts/validated/" not in normalized:
            raise AdapterBlockedError("BLOCKED_DRAFT_PROMPT: only validated prompts may be dispatched")
        return True

    def preflight(self, prompt_path: Path | None = None, cycle: str = "", agent: str = "") -> None:
        _ = cycle, agent
        gate = model_gate.check()
        observed_model = getattr(gate, "observed_model", "")
        if (not gate.passed) or observed_model == "UNVERIFIED":
            raise AdapterBlockedError("BLOCKED_MODEL_VERIFICATION")
        router = ProviderRouter()
        if router.advisory_only_mode:
            raise AdapterBlockedError("BLOCKED_ADVISORY_ONLY_MODE")
        if self._is_desktop_binary(self.binary):
            raise AdapterBlockedError("BLOCKED_CURSOR_DESKTOP_BINARY_PATH")
        if prompt_path is not None:
            self._validate_prompt_path(prompt_path)

    def run_agent(self, prompt_path: Path, cycle: str, agent: str) -> ProviderRunResult:
        self.preflight(prompt_path=prompt_path, cycle=cycle, agent=agent)

        started_at = datetime.now(UTC).isoformat()
        run_dir = Path(r"C:\AI_Runner\runs") / f"CYCLE_{(cycle or '000').zfill(3)}" / "agent_runs" / agent
        result = cursor_run_agent(
            agent_id=agent,
            prompt_path=str(prompt_path),
            working_dir=str(Path(__file__).resolve().parents[2]),
            output_dir=str(run_dir),
        )
        completed_at = datetime.now(UTC).isoformat()

        report_path = Path("docs/cycle_reports") / f"CYCLE_{(cycle or '000').zfill(3)}_AGENT_{agent}.md"
        report_complete = False
        if report_path.exists():
            first_line = report_path.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
            report_complete = first_line == ["AGENT_COMPLETE"]

        status = "SUCCESS" if result.status == "complete" and report_complete else "ERROR"
        refresh_after_dispatch(
            "cursor_cli",
            "SUCCESS" if status == "SUCCESS" else "ERROR",
            run_dir=run_dir,
        )
        return ProviderRunResult(
            status=status,
            provider="cursorcli",
            started_at=started_at,
            completed_at=completed_at,
            files_changed=[str(report_path)] if report_path.exists() else [],
            validation_required=(status != "SUCCESS"),
            error_message=None if status == "SUCCESS" else (result.error_message or "AGENT_INCOMPLETE"),
            decision_artifact_path=None,
        )
