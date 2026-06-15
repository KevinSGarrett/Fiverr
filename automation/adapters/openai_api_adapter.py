"""OpenAI API adapter guarded by runner.env and budget policy."""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from automation.config_loader import load_secrets
from automation.cost_guard import CostGuard
from automation.provider_router import ProviderRunResult
from automation.provider_usage_ledger import LedgerEntry, record_call


class AdapterBlockedError(RuntimeError):
    """Raised when adapter preflight disallows API usage."""


class OpenAIApiAdapter:
    """OpenAI adapter that only trusts runner.env secrets."""

    RUNNER_ENV = Path(r"C:\AI_Runner\secrets\runner.env")
    APPROVED_TASK_TYPES = {"prompt_lint", "json_classification", "rubric_scoring", "summary_generation"}

    def __init__(self) -> None:
        self.cost_guard = CostGuard()
        self.api_key = ""
        self._api_key_loaded = False

    def _load_api_key(self) -> str:
        secrets = load_secrets()
        secret_key = (secrets.get("OPENAI_API_KEY") or secrets.get("OPENAIAPIKEY") or "").strip()
        env_value = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAIAPIKEY")
        if secret_key:
            return secret_key
        if env_value:
            raise AdapterBlockedError("BLOCKED: OPENAI API key injection mismatch")
        raise AdapterBlockedError("OPENAI_API_KEY not in runner.env")

    def preflight(self, task_type: str = "prompt_lint", estimated_cost: float = 0.0) -> None:
        if task_type not in self.APPROVED_TASK_TYPES:
            raise AdapterBlockedError(f"TASKTYPE_NOT_APPROVED_FOR_OPENAI_API: {task_type}")
        if not self._api_key_loaded:
            self.api_key = self._load_api_key()
            self._api_key_loaded = True
        result = self.cost_guard.check_budget("openai_api", float(estimated_cost))
        if result.status == "HARDBLOCK":
            raise AdapterBlockedError(f"HARD_BLOCK: {getattr(result, 'reason', 'budget exceeded')}")
        if result.status == "SOFTWARN":
            print(f"SOFTWARN: {getattr(result, 'reason', 'budget warning')}")

    def _estimate_cost(self, prompt: str) -> float:
        return (len(prompt) / 4000.0) * 0.002

    def send_prompt(self, prompt: str, task_type: str, cycle: str = "") -> ProviderRunResult:
        estimated_cost = self._estimate_cost(prompt)
        started_at = datetime.now(UTC).isoformat()
        budget_result = self.cost_guard.check_budget("openai_api", float(estimated_cost))
        if budget_result.status == "HARDBLOCK":
            return ProviderRunResult(
                status="BLOCKED",
                provider="openaiapi",
                started_at=started_at,
                completed_at=datetime.now(UTC).isoformat(),
                files_changed=[],
                validation_required=False,
                error_message="OPENAI_BUDGET_HARDBLOCK",
                decision_artifact_path=None,
            )

        self.preflight(task_type=task_type, estimated_cost=estimated_cost)

        response_text = ""
        status = "SUCCESS"
        error_message: str | None = None
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            response = client.responses.create(model="gpt-4o-mini", input=prompt)
            response_text = self._extract_text(response)
        except Exception as exc:
            status = "ERROR"
            error_message = str(exc)

        cycle_folder = f"CYCLE_{(cycle or '000').zfill(3)}"
        advisory_dir = Path(r"C:\AI_Runner\runs") / cycle_folder / "openai_advisory"
        advisory_dir.mkdir(parents=True, exist_ok=True)
        advisory_path = advisory_dir / f"openai_advisory_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
        advisory_payload = {
            "task_type": task_type,
            "cycle": (cycle or "000").zfill(3),
            "estimated_cost_usd": estimated_cost,
            "status": status,
            "response_preview": response_text[:500],
            "error": error_message,
        }
        advisory_path.write_text(json.dumps(advisory_payload, indent=2) + "\n", encoding="utf-8")

        record_call(
            LedgerEntry(
                decision_id=str(uuid.uuid4()),
                provider="openaiapi",
                task_type=task_type,
                estimated_cost_usd=estimated_cost,
                actual_cost_usd=estimated_cost if status == "SUCCESS" else None,
                timestamp=datetime.now(UTC).isoformat(),
                cycle=(cycle or "000").zfill(3),
            )
        )

        return ProviderRunResult(
            status=status,
            provider="openaiapi",
            started_at=started_at,
            completed_at=datetime.now(UTC).isoformat(),
            files_changed=[str(advisory_path)],
            validation_required=False,
            error_message=error_message,
            decision_artifact_path=None,
        )

    def _extract_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str):
            return output_text
        return json.dumps(getattr(response, "model_dump", lambda: {})(), indent=2, default=str)
