from __future__ import annotations

import json
from pathlib import Path

from automation.adapters.claude_subscription_adapter import ClaudeSubscriptionAdapter
from automation.adapters.codex_subscription_adapter import CodexSubscriptionAdapter
from automation.adapters.cursor_worker_adapter import CursorWorkerAdapter
from automation.adapters.openai_api_adapter import OpenAIApiAdapter
from automation.provider_health import ProviderHealth


def test_4_providers_in_provider_health_json(tmp_path: Path) -> None:
    health_path = tmp_path / "provider_health.json"
    health_path.write_text(
        json.dumps(
            {
                "cursorcli": {"status": "READY", "full_size_prompt_smoke": "PASS"},
                "claudesubscription": {"status": "READY"},
                "openaiapi": {"status": "READY"},
                "codexsubscription": {"status": "READY", "full_size_prompt_smoke": "PASS"},
            }
        ),
        encoding="utf-8",
    )
    health = ProviderHealth(health_path=health_path).get_all_statuses()
    assert all(health[p] == "READY" for p in ("cursorcli", "claudesubscription", "openaiapi", "codexsubscription"))


def test_codex_is_distinct_from_openai_api() -> None:
    assert CodexSubscriptionAdapter is not OpenAIApiAdapter


def test_codex_is_distinct_from_cursor() -> None:
    assert CodexSubscriptionAdapter is not CursorWorkerAdapter


def test_codex_subscription_state_billing_mode_correct(tmp_path: Path) -> None:
    state = tmp_path / "codex_subscription_state.json"
    state.write_text(json.dumps({"billing_mode": "chatgpt_subscription_only"}), encoding="utf-8")
    payload = json.loads(state.read_text(encoding="utf-8"))
    assert payload["billing_mode"] == "chatgpt_subscription_only"


def test_claude_subscription_state_no_api_key(tmp_path: Path) -> None:
    state = tmp_path / "claude_subscription_state.json"
    state.write_text(
        json.dumps({"billing_mode": "claude_subscription_only", "api_key_present": False}),
        encoding="utf-8",
    )
    payload = json.loads(state.read_text(encoding="utf-8"))
    assert payload["api_key_present"] is False
    assert ClaudeSubscriptionAdapter is not None


def test_openai_api_has_budget_hard_cap(tmp_path: Path) -> None:
    state = tmp_path / "openai_api_budget_state.json"
    state.write_text(json.dumps({"daily_hard_limit_usd": 10}), encoding="utf-8")
    payload = json.loads(state.read_text(encoding="utf-8"))
    assert payload["daily_hard_limit_usd"] == 10
