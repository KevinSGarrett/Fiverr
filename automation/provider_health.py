"""Provider health loading and readiness checks."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from json import JSONDecodeError
from pathlib import Path
from typing import Any

__version__ = "1.1.0"

DEFAULT_PROVIDER_HEALTH_PATH = Path("C:/AI_Runner/state/provider_health.json")
KNOWN_PROVIDERS = ("cursorcli", "claudesubscription", "openaiapi", "codexsubscription")
EDITING_PROVIDERS = {"cursorcli", "codexsubscription"}
VALID_STATUSES = {"READY", "NOTVERIFIED", "DEGRADED", "BLOCKED"}
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
        if health_path is not None and not selected_path.exists():
            raise FileNotFoundError(f"Provider health file not found: {selected_path}")
        self._health_path = selected_path
        self._health_data = self._load_health_data()

    def _load_health_data(self) -> dict[str, Any]:
        payload = _read_health_payload(self._health_path)
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
        if status not in {"READY", "DEGRADED"}:
            return "BLOCKED"
        is_ready, _ = self.is_editing_provider_ready(provider)
        if not is_ready:
            return "BLOCKED"
        return "READY" if status == "READY" else "DEGRADED"

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


def _default_health_payload() -> dict[str, Any]:
    generated_at = datetime.now(tz=UTC).isoformat()
    return {
        "generated_at": generated_at,
        **{provider: {"status": "NOT_VERIFIED"} for provider in KNOWN_PROVIDERS},
    }


def _read_health_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _default_health_payload()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError:
        return _default_health_payload()
    if not isinstance(payload, dict):
        return _default_health_payload()

    # M-PROV-1 FIX: migrate alias keys to canonical keys and drop duplicates.
    # The live file accumulated both "cursorcli" and "cursor_cli" (and similar) because
    # some writers used snake_case and others used the canonical form.
    # Resolution: canonical key wins; alias key value merged only if canonical absent.
    migrated: dict[str, Any] = {}
    for raw_key, value in payload.items():
        canonical = _normalize_provider_name(raw_key)
        if canonical in KNOWN_PROVIDERS or raw_key == "generated_at":
            # For provider entries: canonical wins; alias fills only if canonical absent
            if canonical not in migrated:
                migrated[canonical] = value
            elif raw_key != canonical:
                pass  # alias already superseded by canonical -- discard
        else:
            migrated[raw_key] = value  # preserve non-provider fields (generated_at etc.)

    merged = _default_health_payload()
    merged.update(migrated)
    for provider in KNOWN_PROVIDERS:
        entry = merged.get(provider)
        if not isinstance(entry, dict):
            merged[provider] = {"status": "NOT_VERIFIED"}
        elif "status" not in entry:
            merged[provider]["status"] = "NOT_VERIFIED"
    return merged


def _write_health_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload["generated_at"] = datetime.now(tz=UTC).isoformat()
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def update_provider_status(provider: str, status: str, extras: dict[str, Any] | None = None) -> None:
    normalized_provider = _normalize_provider_name(provider)
    normalized_status = _normalize_status(status)
    if normalized_status not in VALID_STATUSES:
        raise ValueError(f"Invalid provider status: {status}")
    if normalized_provider not in KNOWN_PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}")

    health_path = Path(os.getenv("PROVIDER_HEALTH_PATH", str(DEFAULT_PROVIDER_HEALTH_PATH)))
    payload = _read_health_payload(health_path)
    entry = payload.get(normalized_provider)
    if not isinstance(entry, dict):
        entry = {}
    entry["status"] = "NOT_VERIFIED" if normalized_status == "NOTVERIFIED" else normalized_status
    if extras:
        entry.update(extras)
    payload[normalized_provider] = entry
    _write_health_payload(health_path, payload)


def refresh_after_dispatch(provider: str, result_status: str, run_dir: Path | None = None) -> None:
    normalized_provider = _normalize_provider_name(provider)
    health_path = Path(os.getenv("PROVIDER_HEALTH_PATH", str(DEFAULT_PROVIDER_HEALTH_PATH)))
    payload = _read_health_payload(health_path)
    entry = payload.get(normalized_provider)
    if not isinstance(entry, dict):
        entry = {"status": "NOT_VERIFIED", "error_count": 0}

    normalized_result = str(result_status).strip().upper()
    extras: dict[str, Any] = {"last_checked_at": datetime.now(tz=UTC).isoformat()}
    if run_dir is not None:
        extras["last_run_dir"] = str(run_dir)

    if normalized_result in {"SUCCESS", "PASS", "OK"}:
        extras["error_count"] = 0
        extras["last_ok"] = datetime.now(tz=UTC).isoformat()
        update_provider_status(normalized_provider, "READY", extras)
        return

    previous_errors = int(entry.get("error_count", 0) or 0)
    next_error_count = previous_errors + 1
    extras["error_count"] = next_error_count
    extras["last_error"] = datetime.now(tz=UTC).isoformat()
    next_status = "BLOCKED" if next_error_count >= 2 else "DEGRADED"
    update_provider_status(normalized_provider, next_status, extras)


SCHEMA_PATH = Path(__file__).parent / "schemas" / "provider_health.schema.json"


def get_schema_path() -> Path:
    return SCHEMA_PATH
