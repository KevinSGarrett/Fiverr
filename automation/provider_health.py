"""Provider health loading and readiness checks."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_PROVIDER_HEALTH_PATH = Path("C:/AI_Runner/state/provider_health.json")
KNOWN_PROVIDERS = ("cursorcli", "claudesubscription", "openaiapi", "codexsubscription")
EDITING_PROVIDERS = {"cursorcli", "codexsubscription"}
_PROVIDER_ALIASES = {
    "cursor_cli": "cursorcli",
    "claude_subscription": "claudesubscription",
    "openai_api": "openaiapi",
    "codex_subscription": "codexsubscription",
}
_STATUS_ALIASES = {
    "NOT_VERIFIED": "NOTVERIFIED",
}


class ProviderHealth:
    def __init__(self, health_path: Path | None = None) -> None:
        env_path = os.getenv("PROVIDER_HEALTH_PATH")
        selected_raw: str | Path
        if health_path is not None:
            selected_raw = health_path
        elif env_path:
            selected_raw = env_path
        else:
            selected_raw = str(DEFAULT_PROVIDER_HEALTH_PATH)
        selected_path = Path(selected_raw)
        if not selected_path.exists():
            raise FileNotFoundError(f"Provider health file not found: {selected_path}")
        self._health_path = selected_path
        self._health_data = self._load_health_data()

    def _load_health_data(self) -> dict[str, Any]:
        payload = json.loads(self._health_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {}
        normalized: dict[str, Any] = {}
        for provider, entry in payload.items():
            provider_key = _normalize_provider_name(provider)
            if provider_key and isinstance(entry, dict):
                normalized[provider_key] = entry
        return normalized

    def get_health_data(self) -> dict[str, Any]:
        return dict(self._health_data)

    def get_status(self, provider: str) -> str:
        entry = self._health_data.get(_normalize_provider_name(provider), {})
        if not isinstance(entry, dict):
            return "BLOCKED"
        status = _normalize_status(entry.get("status", "BLOCKED"))
        if status != "READY":
            return "BLOCKED"
        is_ready, _ = self.is_editing_provider_ready(provider)
        return "READY" if is_ready else "BLOCKED"

    def is_editing_provider_ready(self, provider: str) -> tuple[bool, str]:
        normalized_provider = _normalize_provider_name(provider)
        if normalized_provider not in EDITING_PROVIDERS:
            return (True, "NOTEDITING_PROVIDER")
        entry = self._health_data.get(normalized_provider, {})
        if not isinstance(entry, dict):
            return (False, "BLOCKED: fullsizepromptsmoke not PASS")
        smoke_result = str(
            entry.get("full_size_prompt_smoke", entry.get("fullsizepromptsmoke", ""))
        ).strip().upper()
        if smoke_result != "PASS":
            return (False, "BLOCKED: fullsizepromptsmoke not PASS")
        return (True, "READY")

    def get_all_statuses(self) -> dict[str, str]:
        return {provider: self.get_status(provider) for provider in KNOWN_PROVIDERS}

    def is_any_blocked(self) -> bool:
        return any(status == "BLOCKED" for status in self.get_all_statuses().values())


def _normalize_provider_name(provider: Any) -> str:
    key = str(provider or "").strip().lower()
    return _PROVIDER_ALIASES.get(key, key)


def _normalize_status(status: Any) -> str:
    value = str(status or "").strip().upper()
    return _STATUS_ALIASES.get(value, value)
