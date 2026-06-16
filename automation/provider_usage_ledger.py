"""Provider usage ledger persistence and spend calculations."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from json import JSONDecodeError
from pathlib import Path
from typing import Any

__version__ = "1.1.0"

DEFAULT_LEDGER_PATH = Path("PM_Pack/automation/provider_usage_ledger.json")
DEFAULT_DAILY_REPORT_DIR = Path("C:/AI_Runner/reports/provider_usage")
SUMMARY_PROVIDERS = ("cursorcli", "claudesubscription", "openaiapi", "codexsubscription")


@dataclass(frozen=True)
class LedgerEntry:
    decision_id: str
    provider: str
    task_type: str
    estimated_cost_usd: float
    actual_cost_usd: float | None
    timestamp: str
    cycle: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "provider": self.provider,
            "task_type": self.task_type,
            "estimated_cost_usd": float(self.estimated_cost_usd),
            "actual_cost_usd": self.actual_cost_usd,
            "timestamp": self.timestamp,
            "cycle": self.cycle,
        }


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)


def _ledger_path() -> Path:
    return Path(os.getenv("PROVIDER_LEDGER_PATH", str(DEFAULT_LEDGER_PATH)))


def _daily_report_dir() -> Path:
    return Path(os.getenv("PROVIDER_DAILY_REPORT_DIR", str(DEFAULT_DAILY_REPORT_DIR)))


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except JSONDecodeError:
        decoder = json.JSONDecoder()
        idx = 0
        last_payload: Any = None
        while idx < len(text):
            while idx < len(text) and text[idx].isspace():
                idx += 1
            if idx >= len(text):
                break
            try:
                payload, end = decoder.raw_decode(text, idx)
            except JSONDecodeError:
                break
            last_payload = payload
            idx = end
        return last_payload


def _read_entries(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("entries"), list):
        return [item for item in payload["entries"] if isinstance(item, dict)]
    return []


def _normalize_provider(provider: str) -> str:
    return provider.strip().lower().replace("_", "")


def _daily_path_for(date_key: str) -> Path:
    return _daily_report_dir() / f"daily_{date_key}.json"


def _sum_estimated(entries: list[dict[str, Any]], provider: str) -> float:
    normalized = _normalize_provider(provider)
    total = 0.0
    for entry in entries:
        entry_provider = _normalize_provider(str(entry.get("provider", "")))
        if entry_provider != normalized:
            continue
        total += float(entry.get("estimated_cost_usd", entry.get("estimatedcostusd", 0.0)))
    return total


def record_call(entry: LedgerEntry) -> None:
    serialized = entry.to_dict()

    ledger_path = _ledger_path()
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    existing_ledger = _read_json(ledger_path)
    ledger_entries = _read_entries(existing_ledger)
    ledger_entries.append(serialized)
    ledger_path.write_text(json.dumps(ledger_entries, indent=2) + "\n", encoding="utf-8")

    date_key = _utc_now().strftime("%Y%m%d")
    daily_path = _daily_path_for(date_key)
    daily_path.parent.mkdir(parents=True, exist_ok=True)
    existing_daily = _read_json(daily_path)
    daily_entries = _read_entries(existing_daily)
    daily_entries.append(serialized)
    provider_totals: dict[str, float] = {}
    for row in daily_entries:
        provider_name = str(row.get("provider", "unknown"))
        provider_totals[provider_name] = provider_totals.get(provider_name, 0.0) + float(
            row.get("estimated_cost_usd", row.get("estimatedcostusd", 0.0))
        )
    daily_payload = {
        "date": date_key,
        "provider_totals": provider_totals,
        "entries": daily_entries,
    }
    daily_path.write_text(json.dumps(daily_payload, indent=2) + "\n", encoding="utf-8")


def get_daily_spend(provider: str, date: str | None = None) -> float:
    date_key = date or _utc_now().strftime("%Y%m%d")
    payload = _read_json(_daily_path_for(date_key))
    if payload is None:
        return 0.0
    return float(_sum_estimated(_read_entries(payload), provider))


def get_monthly_spend(provider: str) -> float:
    report_dir = _daily_report_dir()
    if not report_dir.exists():
        return 0.0
    month_prefix = _utc_now().strftime("daily_%Y%m")
    total = 0.0
    for daily_file in report_dir.glob(f"{month_prefix}*.json"):
        payload = _read_json(daily_file)
        total += _sum_estimated(_read_entries(payload), provider)
    return float(total)


def get_weekly_spend(provider: str) -> float:
    report_dir = _daily_report_dir()
    if not report_dir.exists():
        return 0.0
    today = _utc_now().date()
    total = 0.0
    for delta in range(7):
        target_key = (today - timedelta(days=delta)).strftime("%Y%m%d")
        payload = _read_json(_daily_path_for(target_key))
        total += _sum_estimated(_read_entries(payload), provider)
    return float(total)


def get_ledger_summary() -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for provider in SUMMARY_PROVIDERS:
        summary[provider] = {
            "daily": float(get_daily_spend(provider)),
            "weekly": float(get_weekly_spend(provider)),
            "monthly": float(get_monthly_spend(provider)),
        }
    return summary


SCHEMA_PATH = Path(__file__).parent / "schemas" / "provider_usage_ledger.schema.json"


def get_schema_path() -> Path:
    return SCHEMA_PATH
