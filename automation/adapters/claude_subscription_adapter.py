"""Claude subscription adapter for official PM review routing."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from automation.provider_health import refresh_after_dispatch
from automation.provider_router import ProviderRunResult

CLAUDE_ADAPTER_CONFIG = Path(r"C:\AI_Runner\config\claude_adapter.yaml")
CLAUDE_MODEL_STATE_PATH = Path(r"C:\AI_Runner\state\claude_model_state.json")
CLAUDE_SUB_STATE_PATH = Path(r"C:\AI_Runner\state\claude_subscription_state.json")
INCIDENTS_DIR = Path(r"C:\AI_Runner\reports\incidents")


class AdapterBlockedError(RuntimeError):
    """Raised when adapter preflight blocks execution."""


class ClaudeSubscriptionAdapter:
    """Subscription-only Claude adapter (never API billing fallback)."""

    def __init__(
        self,
        adapter_config_path: Path | None = None,
        state_file_path: Path | None = None,
    ) -> None:
        self.adapter_config_path = adapter_config_path or CLAUDE_ADAPTER_CONFIG
        self.model_state_file_path = CLAUDE_MODEL_STATE_PATH
        self.state_file_path = state_file_path or CLAUDE_SUB_STATE_PATH
        self.limit_hit = False
        self.config = self._load_yaml(self.adapter_config_path)
        self.model_state = self._load_json(self.model_state_file_path)
        self.state = self._load_json(self.state_file_path)
        self.timeout_seconds = int(self.config.get("timeout_seconds", 900))
        self.binary = shutil.which("claude") or shutil.which("claude.exe") or ""

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}

    def _load_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}

    def preflight(self) -> None:
        if "ANTHROPICAPIKEY" in os.environ or "ANTHROPIC_API_KEY" in os.environ:
            raise AdapterBlockedError(
                "BLOCKED: ANTHROPIC_API_KEY detected in environment — "
                "subscription-only mode required [SUBSCRIPTION_ONLY_REQUIRED]"
            )
        billing_source = self.state.get("billing_mode", self.model_state.get("billing_mode", ""))
        billing_mode = str(billing_source).strip().lower().replace("_", "")
        if billing_mode != "claudesubscriptiononly":
            raise AdapterBlockedError("BLOCKED: billing_mode is not claude_subscription_only")
        if not self.binary:
            raise AdapterBlockedError("BLOCKED: claude binary not on PATH")
        login_probe = subprocess.run(
            [self.binary, "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if login_probe.returncode != 0:
            raise AdapterBlockedError("BLOCKED: claude subscription login not verified")

    def _handle_limit_reached(self) -> None:
        state = self._load_json(self.state_file_path)
        limit_events = int(state.get("limit_events_today", 0) or 0) + 1
        state["limit_events_today"] = limit_events
        state["limiteventstoday"] = limit_events
        state["last_limit_reached_at"] = datetime.now(UTC).isoformat()
        self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_file_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

        INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        incident_path = INCIDENTS_DIR / f"CLAUDE_LIMIT_{timestamp}.json"
        incident = {
            "incident": "CLAUDE_LIMIT_REACHED",
            "occurred_at": datetime.now(UTC).isoformat(),
            "limit_events_today": limit_events,
            "fallback_to_api_allowed": False,
        }
        incident_path.write_text(json.dumps(incident, indent=2) + "\n", encoding="utf-8")
        self.limit_hit = True

    def _status_from_text(self, text: str) -> str:
        upper = text.upper()
        if "ADVISORY_ONLY" in upper or "ADVISORYONLY" in upper:
            return "ADVISORY_ONLY"
        if "BLOCKED" in upper:
            return "BLOCKED"
        if "PASS" in upper:
            return "SUCCESS"
        return "SUCCESS"

    def _is_limit_output(self, text: str) -> bool:
        upper = text.upper()
        return "LIMIT" in upper or "USAGE CAP" in upper or "RATE_LIMIT" in upper

    def run_review(self, prompt_path: Path, cycle: str, run_dir: Path) -> ProviderRunResult:
        self.preflight()
        run_dir.mkdir(parents=True, exist_ok=True)
        prompt_text = prompt_path.read_text(encoding="utf-8", errors="replace")
        request_path = run_dir / "claude_request.md"
        response_path = run_dir / "claude_response.md"
        request_path.write_text(prompt_text, encoding="utf-8")

        started_at = datetime.now(UTC).isoformat()
        proc = subprocess.run(
            [self.binary, "--stdin"],
            input=prompt_text,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        response_text = (proc.stdout or "") + (proc.stderr or "")
        response_path.write_text(response_text, encoding="utf-8")

        error_message: str | None = None
        status = self._status_from_text(response_text)
        if proc.returncode != 0:
            error_message = f"claude exited with {proc.returncode}"
            status = "ERROR"
        if proc.returncode != 0 or self._is_limit_output(response_text):
            self._handle_limit_reached()
            status = "BLOCKED"
            error_message = "SUBSCRIPTIONLIMITREACHED"
            refresh_after_dispatch("claude_subscription", "LIMIT_HIT", run_dir=run_dir)
        if status == "ADVISORY_ONLY":
            status = "ADVISORYONLYBLOCKED"
        if error_message != "SUBSCRIPTIONLIMITREACHED":
            refresh_after_dispatch(
                "claude_subscription",
                "SUCCESS" if status == "SUCCESS" else "ERROR",
                run_dir=run_dir,
            )

        return ProviderRunResult(
            status=status,
            provider="claudesubscription",
            started_at=started_at,
            completed_at=datetime.now(UTC).isoformat(),
            files_changed=[str(request_path), str(response_path)],
            validation_required=True,
            error_message=error_message,
            decision_artifact_path=None,
        )
