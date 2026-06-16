"""Cost governance checks for provider routing."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import yaml

from automation.provider_usage_ledger import get_daily_spend, get_monthly_spend

__version__ = "1.1.0"

DEFAULT_POLICY_PATH = Path("PM_Pack/automation/provider_policy.yml")
DEFAULT_BUDGET_STATE_PATH = Path("C:/AI_Runner/state/openai_api_budget_state.json")


@dataclass(frozen=True)
class BudgetCheckResult:
    status: str
    reason: str
    current_daily: float
    current_monthly: float
    daily_limit: float
    monthly_limit: float


class CostGuard:
    def __init__(
        self,
        policy_path: Path | None = None,
        budget_state_path: Path | None = None,
    ) -> None:
        self.policy_path = Path(os.getenv("PROVIDER_POLICY_PATH", str(policy_path or DEFAULT_POLICY_PATH)))
        self.budget_state_path = Path(
            os.getenv("PROVIDER_BUDGET_STATE_PATH", str(budget_state_path or DEFAULT_BUDGET_STATE_PATH))
        )
        self.daily_limit = 10.0
        self.monthly_limit = 150.0
        self.soft_warn = 5.0
        self._load_policy_limits()

    @classmethod
    def load_from_policy(cls, policy_path: Path) -> CostGuard:
        return cls(policy_path=policy_path)

    def _load_policy_limits(self) -> None:
        if not self.policy_path.exists():
            return
        payload = yaml.safe_load(self.policy_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return
        providers = payload.get("providers")
        if not isinstance(providers, dict):
            return
        openai_config = providers.get("openaiapi") or providers.get("openai_api")
        if not isinstance(openai_config, dict):
            return
        hard_limits = openai_config.get("hardlimits") or openai_config.get("hard_limits")
        if isinstance(hard_limits, dict):
            self.daily_limit = _as_float(hard_limits.get("dailyusd", hard_limits.get("daily_usd")), 10.0)
            self.monthly_limit = _as_float(
                hard_limits.get("monthlyusd", hard_limits.get("monthly_usd")),
                150.0,
            )
        soft_warn = openai_config.get("softwarn") or openai_config.get("soft_warn")
        if isinstance(soft_warn, dict):
            self.soft_warn = _as_float(
                soft_warn.get("dailyusd", soft_warn.get("daily_usd")),
                5.0,
            )

    def check_budget(self, provider: str, estimated_cost: float) -> BudgetCheckResult:
        normalized = provider.strip().lower().replace("_", "")
        if normalized != "openaiapi":
            return BudgetCheckResult(
                status="PASS",
                reason="Provider not hard-capped",
                current_daily=0.0,
                current_monthly=0.0,
                daily_limit=self.daily_limit,
                monthly_limit=self.monthly_limit,
            )

        state = self._load_budget_state()
        current_daily = max(0.0, float(state.get("dailyspendusd", 0.0)))
        current_monthly = max(0.0, float(state.get("monthlyspendusd", 0.0)))
        if current_daily == 0.0 and current_monthly == 0.0:
            # Backward compatibility if state has not been initialized yet.
            current_daily = max(0.0, _get_daily_spend("openai_api"))
            current_monthly = max(0.0, _get_monthly_spend("openai_api"))
        projected_daily = current_daily + estimated_cost
        projected_monthly = current_monthly + estimated_cost

        if projected_daily >= self.daily_limit or projected_monthly >= self.monthly_limit:
            return BudgetCheckResult(
                status="HARDBLOCK",
                reason="Projected spend exceeds hard limits",
                current_daily=current_daily,
                current_monthly=current_monthly,
                daily_limit=self.daily_limit,
                monthly_limit=self.monthly_limit,
            )
        if projected_daily >= self.soft_warn:
            return BudgetCheckResult(
                status="SOFTWARN",
                reason="Projected daily spend exceeds soft warning limit",
                current_daily=current_daily,
                current_monthly=current_monthly,
                daily_limit=self.daily_limit,
                monthly_limit=self.monthly_limit,
            )
        return BudgetCheckResult(
            status="PASS",
            reason="Projected spend within limits",
            current_daily=current_daily,
            current_monthly=current_monthly,
            daily_limit=self.daily_limit,
            monthly_limit=self.monthly_limit,
        )

    def get_status(self, provider: str = "openai_api") -> dict[str, Any]:
        result = self.check_budget(provider, estimated_cost=0.0)
        return {
            "provider": provider,
            "status": result.status,
            "reason": result.reason,
            "current_daily": result.current_daily,
            "current_monthly": result.current_monthly,
            "daily_limit": result.daily_limit,
            "monthly_limit": result.monthly_limit,
            "soft_warn": self.soft_warn,
        }

    def _load_budget_state(self) -> dict[str, Any]:
        if not self.budget_state_path.exists():
            return _default_budget_state()
        try:
            payload = json.loads(self.budget_state_path.read_text(encoding="utf-8"))
        except JSONDecodeError:
            return _default_budget_state()
        if not isinstance(payload, dict):
            return _default_budget_state()
        merged = _default_budget_state()
        merged.update(payload)
        if float(merged.get("dailyspendusd", 0.0)) < 0:
            merged["dailyspendusd"] = 0.0
        if float(merged.get("monthlyspendusd", 0.0)) < 0:
            merged["monthlyspendusd"] = 0.0
        return merged

    def _write_budget_state(self, payload: dict[str, Any]) -> None:
        self.budget_state_path.parent.mkdir(parents=True, exist_ok=True)
        self.budget_state_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    guard = CostGuard()
    target_provider = sys.argv[1] if len(sys.argv) > 1 else "openai_api"
    print(guard.get_status(target_provider))


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _get_daily_spend(provider: str) -> float:
    return get_daily_spend(provider)


def _get_monthly_spend(provider: str) -> float:
    return get_monthly_spend(provider)


def _default_budget_state() -> dict[str, Any]:
    return {
        "provider": "openai_api",
        "dailyspendusd": 0.0,
        "monthlyspendusd": 0.0,
        "updatedat": datetime.now(tz=UTC).isoformat(),
    }


def update_spend(provider: str, actual_cost: float) -> None:
    normalized = provider.strip().lower().replace("_", "")
    if normalized != "openaiapi":
        return
    guard = CostGuard()
    payload = guard._load_budget_state()
    spend_value = max(0.0, float(actual_cost))

    # Reset daily spend when the calendar date has rolled over.
    # Only resets if last_reset_date is recorded AND differs from today
    # (missing field means fresh/new state — treat as same day).
    today_str = datetime.now(tz=UTC).date().isoformat()
    last_reset = payload.get("last_reset_date")
    if last_reset is not None and last_reset != today_str:
        payload["dailyspendusd"] = 0.0
    payload.setdefault("last_reset_date", today_str)
    if payload.get("last_reset_date") != today_str:
        payload["last_reset_date"] = today_str

    # Reset monthly spend when the calendar month has rolled over.
    this_month = datetime.now(tz=UTC).strftime("%Y-%m")
    last_month = payload.get("last_reset_month")
    if last_month is not None and last_month != this_month:
        payload["monthlyspendusd"] = 0.0
    payload.setdefault("last_reset_month", this_month)

    payload["dailyspendusd"] = max(0.0, float(payload.get("dailyspendusd", 0.0))) + spend_value
    payload["monthlyspendusd"] = max(0.0, float(payload.get("monthlyspendusd", 0.0))) + spend_value
    payload["updatedat"] = datetime.now(tz=UTC).isoformat()
    guard._write_budget_state(payload)


SCHEMA_PATH = Path(__file__).parent / "schemas" / "cost_guard.schema.json"


def get_schema_path() -> Path:
    return SCHEMA_PATH
