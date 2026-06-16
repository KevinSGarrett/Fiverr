from __future__ import annotations

import json
from pathlib import Path

import pytest
from automation.provider_router import PolicyViolation, ProviderRouter


@pytest.fixture
def c082_router(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ProviderRouter:
    policy_path = tmp_path / "provider_policy.yml"
    policy_path.write_text(
        json.dumps(
            {
                "version": 1,
                "global_rules": {
                    "no_browser_automation_chatgpt": True,
                    "advisory_only_provider_routing": False,
                },
                "providers": {
                    "cursor_cli": {"enabled": True, "status": "ACTIVE", "billing_mode": "cursor_subscription"},
                    "claude_subscription": {
                        "enabled": True,
                        "status": "ACTIVE",
                        "billing_mode": "claude_subscription_only",
                    },
                    "openai_api": {"enabled": True, "status": "ACTIVE", "billing_mode": "openai_api_key"},
                    "codex_subscription": {
                        "enabled": True,
                        "status": "ACTIVE",
                        "billing_mode": "chatgpt_subscription_only",
                    },
                },
                "routes": {
                    "implementation": "cursor_cli",
                    "official_post_cycle_review": "claude_subscription",
                    "json_classification": "openai_api",
                    "prompt_lint": "openai_api",
                    "docs_agent_work": "codex_subscription",
                    "test_generation": "codex_subscription",
                    "architecture_review": "claude_subscription",
                    "merge_gate": "deterministic_controller",
                    "jira_transition": "deterministic_controller",
                },
            }
        ),
        encoding="utf-8",
    )
    health_path = tmp_path / "provider_health.json"
    health_path.write_text(
        json.dumps(
            {
                "cursorcli": {"status": "READY"},
                "claudesubscription": {"status": "READY"},
                "openaiapi": {"status": "READY"},
                "codexsubscription": {"status": "READY"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    monkeypatch.setattr("automation.provider_router.DECISION_DIR", tmp_path / "provider_decisions")
    return ProviderRouter(policy_path=policy_path)


def test_code_implementation_routes_to_cursor_cli(c082_router: ProviderRouter) -> None:
    decision = c082_router.select_provider("code_implementation")
    assert decision.provider == "cursorcli"
    assert c082_router.route_dry_run("code_implementation")["provider"] == "cursor_cli"


def test_post_cycle_review_routes_to_claude_subscription(c082_router: ProviderRouter) -> None:
    decision = c082_router.select_provider("official_post_cycle_review")
    assert decision.provider == "claudesubscription"


def test_json_classification_routes_to_openai_api(c082_router: ProviderRouter) -> None:
    decision = c082_router.select_provider("json_classification")
    assert decision.provider == "openaiapi"


def test_docs_agent_work_routes_to_codex_subscription(c082_router: ProviderRouter) -> None:
    decision = c082_router.select_provider("docs_agent_work")
    assert decision.provider == "codexsubscription"


def test_no_advisory_confirm_mode_in_any_route(c082_router: ProviderRouter) -> None:
    for task_type in ["code_implementation", "official_post_cycle_review", "json_classification", "docs_agent_work"]:
        decision = c082_router.select_provider(task_type)
        assert decision.reason not in {"ADVISORYONLYBLOCKED", "ADVISORYCONFIRMREQUIRED", "DISPATCHCONFIRM"}


def test_browser_automation_prohibited(c082_router: ProviderRouter) -> None:
    with pytest.raises(PolicyViolation, match="NO_BROWSER_AUTOMATION"):
        c082_router._enforce_no_browser_automation("chatgpt_browser")


def test_all_4_providers_in_route_table(c082_router: ProviderRouter) -> None:
    providers = c082_router.policy.get("providers", {}) if c082_router.policy else {}
    assert {"cursor_cli", "claude_subscription", "openai_api", "codex_subscription"}.issubset(
        set(providers.keys())
    )
