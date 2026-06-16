from __future__ import annotations

import json
from pathlib import Path

import pytest
from automation.provider_router import (
    PolicyLoadError,
    PolicyViolation,
    ProviderDecision,
    ProviderRouter,
    ProviderRunResult,
    ValidationResult,
    _cli,
)


@pytest.fixture
def policy_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    policy_path = tmp_path / "provider_policy.yml"
    policy_payload = {
        "version": 1,
        "global_rules": {
            "no_browser_automation_chatgpt": True,
            "advisory_only_provider_routing": True,
        },
        "providers": {
            "cursorcli": {"billing_mode": "cursor_subscription"},
            "claude_subscription": {"billing_mode": "claude_subscription_only"},
            "openai_api": {"billing_mode": "openai_api_key"},
            "codex_subscription": {"billing_mode": "codex_subscription"},
        },
        "routes": {
            "implementation": "cursorcli",
            "repair": "cursorcli",
            "test_generation": "cursorcli",
            "docs_agent_work": "cursorcli",
            "prompt_lint": "deterministic_validator",
            "json_classification": "openai_api",
            "official_post_cycle_review": "claude_subscription",
            "merge_gate": "deterministic_controller",
            "jira_transition": "deterministic_controller",
        },
    }
    policy_path.write_text(json.dumps(policy_payload), encoding="utf-8")
    monkeypatch.setattr("automation.provider_router.POLICY_PATH", policy_path)
    return policy_path


@pytest.fixture
def health_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    health_path = tmp_path / "provider_health.json"
    health_payload = {
        "cursorcli": {"status": "READY", "full_size_prompt_smoke": "PASS"},
        "claudesubscription": {"status": "READY"},
        "openaiapi": {"status": "READY"},
        "codexsubscription": {"status": "READY", "full_size_prompt_smoke": "PASS"},
    }
    health_path.write_text(json.dumps(health_payload), encoding="utf-8")
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    return health_path


@pytest.fixture
def decision_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    decision_dir = tmp_path / "provider_decisions"
    monkeypatch.setattr("automation.provider_router.DECISION_DIR", decision_dir)
    return decision_dir


@pytest.fixture
def router(policy_env: Path, health_env: Path, decision_env: Path) -> ProviderRouter:
    _ = health_env, decision_env
    return ProviderRouter(policy_path=policy_env)


def test_select_provider_implementation_routes_cursorcli(router: ProviderRouter) -> None:
    decision = router.select_provider("implementation")
    assert decision.provider == "cursorcli"


def test_select_provider_official_post_cycle_review_routes_claude(router: ProviderRouter) -> None:
    decision = router.select_provider("official_post_cycle_review")
    assert decision.provider == "claudesubscription"


def test_select_provider_merge_gate_routes_deterministic_controller(router: ProviderRouter) -> None:
    decision = router.select_provider("merge_gate")
    assert decision.provider == "deterministiccontroller"


def test_select_provider_jira_transition_routes_deterministic_controller(router: ProviderRouter) -> None:
    decision = router.select_provider("jira_transition")
    assert decision.provider == "deterministiccontroller"


def test_select_provider_prompt_lint_routes_deterministic_validator(router: ProviderRouter) -> None:
    decision = router.select_provider("prompt_lint")
    assert decision.provider == "deterministicvalidator"


def test_selectprovider_alias_routes_same_as_select_provider(router: ProviderRouter) -> None:
    assert router.selectprovider("implementation").provider == "cursorcli"


def test_route_dry_run_writes_decision_artifact_with_decision_id(
    router: ProviderRouter, decision_env: Path
) -> None:
    _ = router.route_dryrun("implementation", cycle="080")
    files = sorted(decision_env.glob("PROVIDER_DECISION_*.json"))
    assert files, "expected a decision artifact file"
    payload = json.loads(files[-1].read_text(encoding="utf-8"))
    assert payload["decisionid"]


def test_route_dry_run_artifact_is_valid_json(router: ProviderRouter, decision_env: Path) -> None:
    _ = router.route_dryrun("implementation", cycle="080")
    files = sorted(decision_env.glob("PROVIDER_DECISION_*.json"))
    _ = json.loads(files[-1].read_text(encoding="utf-8"))


def test_policy_violation_for_chatgpt_browser_automation(router: ProviderRouter) -> None:
    with pytest.raises(PolicyViolation):
        router.select_provider("chatgptbrowserautomation")


def test_validate_policy_passes_for_valid_policy(router: ProviderRouter) -> None:
    result = router.validatepolicy()
    assert isinstance(result, ValidationResult)
    assert result.passed is True


def test_validate_policy_fails_when_routes_dict_empty(tmp_path: Path) -> None:
    policy_path = tmp_path / "provider_policy.yml"
    policy_path.write_text(
        json.dumps({"providers": {}, "global_rules": {}, "routes": {}}),
        encoding="utf-8",
    )
    test_router = ProviderRouter.__new__(ProviderRouter)
    test_router.policy_path = policy_path
    test_router.policy = None
    result = ProviderRouter.validate_policy(test_router)
    assert result.passed is False


def test_advisory_only_mode_still_returns_provider_decision(router: ProviderRouter) -> None:
    decision = router.select_provider("officialpostcyclereview")
    assert isinstance(decision, ProviderDecision)
    assert decision.reason == "ADVISORYONLYBLOCKED"


def test_missing_policy_file_raises_policy_load_error_on_select(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    health_path = tmp_path / "provider_health.json"
    health_path.write_text(json.dumps({"cursorcli": {"status": "READY"}}), encoding="utf-8")
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    test_router = ProviderRouter(policy_path=tmp_path / "missing_policy.yml")
    with pytest.raises(PolicyLoadError):
        test_router.select_provider("implementation")


def test_malformed_yaml_raises_policy_load_error_on_init(tmp_path: Path) -> None:
    policy_path = tmp_path / "bad_provider_policy.yml"
    policy_path.write_text("routes: [", encoding="utf-8")
    with pytest.raises(PolicyLoadError):
        ProviderRouter(policy_path=policy_path)


def test_dispatch_returns_advisory_only_blocked_for_claude(router: ProviderRouter) -> None:
    result = router.dispatch("official_post_cycle_review", cycle="080", agent="F")
    assert isinstance(result, ProviderRunResult)
    assert result.status == "ADVISORYONLYBLOCKED"
    assert result.error_message == "ADVISORYONLYBLOCKED"


def test_dispatch_returns_advisory_block_for_implementation_in_advisory_only(
    router: ProviderRouter,
) -> None:
    result = router.dispatch("implementation", cycle="080", agent="F")
    assert result.status == "ADVISORYONLYBLOCKED"
    assert result.provider == "cursorcli"


def test_select_provider_uses_classifier_fallback_when_route_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
                    "cursorcli": {"billing_mode": "cursor_subscription"},
                    "claude_subscription": {"billing_mode": "claude_subscription_only"},
                    "openai_api": {"billing_mode": "openai_api_key"},
                    "codex_subscription": {"billing_mode": "codex_subscription"},
                },
                "routes": {
                    "implementation": "cursorcli",
                    "repair": "cursorcli",
                    "test_generation": "cursorcli",
                    "docs_agent_work": "cursorcli",
                    "prompt_lint": "deterministic_validator",
                    "official_post_cycle_review": "claude_subscription",
                    "merge_gate": "deterministic_controller",
                    "jira_transition": "deterministic_controller",
                },
            }
        ),
        encoding="utf-8",
    )
    health_path = tmp_path / "provider_health.json"
    health_path.write_text(json.dumps({"openaiapi": {"status": "READY"}}), encoding="utf-8")
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    decision = ProviderRouter(policy_path=policy_path).select_provider("json_classification")
    assert decision.provider == "openaiapi"


def test_select_provider_blocks_claude_for_code_implementation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
                    "cursorcli": {"billing_mode": "cursor_subscription"},
                    "claude_subscription": {"billing_mode": "claude_subscription_only"},
                    "openai_api": {"billing_mode": "openai_api_key"},
                    "codex_subscription": {"billing_mode": "codex_subscription"},
                },
                "routes": {
                    "implementation": "claude_subscription",
                    "repair": "cursorcli",
                    "test_generation": "cursorcli",
                    "docs_agent_work": "cursorcli",
                    "prompt_lint": "deterministic_validator",
                    "json_classification": "openai_api",
                    "official_post_cycle_review": "claude_subscription",
                    "merge_gate": "deterministic_controller",
                    "jira_transition": "deterministic_controller",
                },
            }
        ),
        encoding="utf-8",
    )
    health_path = tmp_path / "provider_health.json"
    health_path.write_text(json.dumps({"claudesubscription": {"status": "READY"}}), encoding="utf-8")
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    with pytest.raises(PolicyViolation, match="CLAUDE_SUBSCRIPTION_CODE_IMPLEMENTATION_BLOCKED"):
        ProviderRouter(policy_path=policy_path).select_provider("implementation")


def test_dispatch_success_records_usage_and_refreshes_health(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
                    "cursorcli": {"billing_mode": "cursor_subscription"},
                    "claude_subscription": {"billing_mode": "claude_subscription_only"},
                    "openai_api": {"billing_mode": "openai_api_key"},
                    "codex_subscription": {"billing_mode": "codex_subscription"},
                },
                "routes": {
                    "implementation": "cursorcli",
                    "repair": "cursorcli",
                    "test_generation": "cursorcli",
                    "docs_agent_work": "cursorcli",
                    "prompt_lint": "deterministic_validator",
                    "json_classification": "openai_api",
                    "official_post_cycle_review": "claude_subscription",
                    "merge_gate": "deterministic_controller",
                    "jira_transition": "deterministic_controller",
                },
            }
        ),
        encoding="utf-8",
    )
    health_path = tmp_path / "provider_health.json"
    health_path.write_text(
        json.dumps({"cursorcli": {"status": "READY", "full_size_prompt_smoke": "PASS"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    monkeypatch.setattr("automation.provider_router.record_call", lambda entry: None)
    refreshed: dict[str, str] = {}

    def _refresh(provider: str, status: str) -> None:
        refreshed["provider"] = provider
        refreshed["status"] = status

    monkeypatch.setattr("automation.provider_router.refresh_after_dispatch", _refresh)
    monkeypatch.setattr("automation.provider_router.DECISION_DIR", tmp_path / "provider_decisions")

    result = ProviderRouter(policy_path=policy_path).dispatch("implementation", cycle="082", agent="F")

    assert result.status == "SUCCESS"
    assert refreshed == {"provider": "cursorcli", "status": "SUCCESS"}


def test_dispatch_returns_blocked_when_advisory_confirm_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy_path = tmp_path / "provider_policy.yml"
    policy_path.write_text(
        json.dumps(
            {
                "version": 1,
                "global_rules": {
                    "no_browser_automation_chatgpt": True,
                    "advisory_only_provider_routing": False,
                    "advisory_confirm_mode": True,
                },
                "providers": {
                    "cursorcli": {"billing_mode": "cursor_subscription"},
                    "claude_subscription": {"billing_mode": "claude_subscription_only"},
                    "openai_api": {"billing_mode": "openai_api_key"},
                    "codex_subscription": {"billing_mode": "codex_subscription"},
                },
                "routes": {
                    "implementation": "cursorcli",
                    "repair": "cursorcli",
                    "test_generation": "cursorcli",
                    "docs_agent_work": "cursorcli",
                    "prompt_lint": "deterministic_validator",
                    "json_classification": "openai_api",
                    "official_post_cycle_review": "claude_subscription",
                    "merge_gate": "deterministic_controller",
                    "jira_transition": "deterministic_controller",
                },
            }
        ),
        encoding="utf-8",
    )
    health_path = tmp_path / "provider_health.json"
    health_path.write_text(
        json.dumps({"openaiapi": {"status": "READY"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    monkeypatch.setattr("automation.provider_router.DECISION_DIR", tmp_path / "provider_decisions")

    result = ProviderRouter(policy_path=policy_path).dispatch("json_classification", cycle="082", agent="F")

    assert result.status == "ADVISORYONLYBLOCKED"
    assert result.error_message == "ADVISORYCONFIRMREQUIRED"


def test_validate_routes_alias_returns_true_for_valid_policy(router: ProviderRouter) -> None:
    assert router.validate_routes() is True


def test_route_dry_run_alias_methods_return_payload(router: ProviderRouter) -> None:
    assert router.routedry_run("implementation", cycle="080")["provider"] == "cursor_cli"
    assert router.route_dryrun("implementation", cycle="080")["provider"] == "cursor_cli"


def test_cli_validate_mode_returns_zero(monkeypatch: pytest.MonkeyPatch, router: ProviderRouter) -> None:
    monkeypatch.setattr("automation.provider_router.ProviderRouter", lambda: router)

    class _Args:
        dry_run = False
        task_type = "implementation"
        cycle = "080"

    monkeypatch.setattr(
        "automation.provider_router.argparse.ArgumentParser.parse_args",
        lambda self: _Args(),
    )
    assert _cli() == 0


def test_cli_dry_run_returns_error_on_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    class _BoomRouter:
        def route_dry_run(self, task_type: str, cycle: str) -> dict[str, str]:
            _ = task_type, cycle
            raise RuntimeError("boom")

        def validate_policy(self) -> ValidationResult:
            return ValidationResult(passed=True, issues=[])

    monkeypatch.setattr("automation.provider_router.ProviderRouter", lambda: _BoomRouter())

    class _Args:
        dry_run = True
        task_type = "implementation"
        cycle = "080"

    monkeypatch.setattr(
        "automation.provider_router.argparse.ArgumentParser.parse_args",
        lambda self: _Args(),
    )
    assert _cli() == 1


def test_cursor_cli_routes_no_advisory_confirm(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
                    "cursorcli": {"billing_mode": "cursor_subscription"},
                    "claude_subscription": {"billing_mode": "claude_subscription_only"},
                    "openai_api": {"billing_mode": "openai_api_key"},
                    "codex_subscription": {"billing_mode": "codex_subscription"},
                },
                "routes": {
                    "implementation": "cursorcli",
                    "official_post_cycle_review": "claude_subscription",
                    "merge_gate": "deterministic_controller",
                    "jira_transition": "deterministic_controller",
                    "prompt_lint": "deterministic_validator",
                    "json_classification": "openai_api",
                    "repair": "cursorcli",
                    "test_generation": "cursorcli",
                    "docs_agent_work": "cursorcli",
                },
            }
        ),
        encoding="utf-8",
    )
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
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    decision = ProviderRouter(policy_path=policy_path).select_provider("code_implementation")
    assert decision.provider == "cursorcli"
    assert decision.reason != "ADVISORYCONFIRMREQUIRED"
    assert decision.reason != "DISPATCHCONFIRM"
    assert decision.reason != "ADVISORYONLYBLOCKED"


def test_browser_automation_prohibited(router: ProviderRouter) -> None:
    with pytest.raises(PolicyViolation, match="NO_BROWSER_AUTOMATION"):
        router._enforce_no_browser_automation("chatgpt_browser")


def test_dispatch_with_dispatchconfirm_still_executes_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    policy_path = tmp_path / "provider_policy.yml"
    policy_path.write_text(
        json.dumps(
            {
                "version": 1,
                "global_rules": {
                    "no_browser_automation_chatgpt": True,
                    "advisory_only_provider_routing": False,
                    "advisory_confirm_mode": True,
                },
                "providers": {
                    "cursorcli": {"billing_mode": "cursor_subscription"},
                    "claude_subscription": {"billing_mode": "claude_subscription_only"},
                    "openai_api": {"billing_mode": "openai_api_key"},
                    "codex_subscription": {"billing_mode": "codex_subscription"},
                },
                "routes": {
                    "implementation": "cursorcli",
                    "repair": "cursorcli",
                    "test_generation": "cursorcli",
                    "docs_agent_work": "cursorcli",
                    "prompt_lint": "deterministic_validator",
                    "json_classification": "openai_api",
                    "official_post_cycle_review": "claude_subscription",
                    "merge_gate": "deterministic_controller",
                    "jira_transition": "deterministic_controller",
                },
            }
        ),
        encoding="utf-8",
    )
    health_path = tmp_path / "provider_health.json"
    health_path.write_text(
        json.dumps({"cursorcli": {"status": "READY", "full_size_prompt_smoke": "PASS"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    monkeypatch.setattr("automation.provider_router.record_call", lambda entry: None)
    monkeypatch.setattr("automation.provider_router.refresh_after_dispatch", lambda *_: None)
    monkeypatch.setattr("automation.provider_router.DECISION_DIR", tmp_path / "provider_decisions")

    result = ProviderRouter(policy_path=policy_path).dispatch("implementation", cycle="082", agent="F")

    assert result.status == "SUCCESS"
    assert result.error_message is None
    assert result.provider == "cursorcli"
