from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import jsonschema
import pytest
from automation.adapters import claude_subscription_adapter as csa
from automation.adapters.openai_api_adapter import OpenAIApiAdapter
from automation.provider_router import ProviderRouter


@pytest.fixture(name="full_env")
def _full_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
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
    decision_dir = tmp_path / "provider_decisions"
    ledger_path = tmp_path / "provider_usage_ledger.json"
    daily_dir = tmp_path / "daily_reports"
    monkeypatch.setattr("automation.provider_router.DECISION_DIR", decision_dir)
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    monkeypatch.setenv("PROVIDER_LEDGER_PATH", str(ledger_path))
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(daily_dir))
    return {
        "policy_path": policy_path,
        "decision_dir": decision_dir,
        "ledger_path": ledger_path,
        "daily_dir": daily_dir,
    }


def test_cursor_cli_path_returns_decision_and_schema_valid_artifact(full_env: dict[str, Path]) -> None:
    router = ProviderRouter(policy_path=full_env["policy_path"])
    result = router.dispatch("implementation", cycle="080", agent="F")
    assert result.provider == "cursorcli"
    assert result.status in {"SUCCESS", "ADVISORYONLYBLOCKED"}
    artifact = Path(result.decision_artifact_path or "")
    assert artifact.exists()
    schema = json.loads(Path("automation/schemas/provider_decision.schema.json").read_text(encoding="utf-8"))
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    jsonschema.validate(payload, schema)


def test_openai_hard_cap_blocks_and_does_not_update_ledger(
    full_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    router = ProviderRouter(policy_path=full_env["policy_path"])
    decision = router.select_provider("jsonclassification", cycle="080")
    assert decision.provider == "openaiapi"

    monkeypatch.setattr("automation.adapters.openai_api_adapter.load_secrets", lambda: {"OPENAIAPIKEY": "k"})
    monkeypatch.setattr(
        "automation.adapters.openai_api_adapter.OpenAIApiAdapter._estimate_cost",
        lambda self, prompt: 0.02,
    )
    adapter = OpenAIApiAdapter()
    adapter.cost_guard = SimpleNamespace(
        check_budget=lambda provider, estimated_cost: SimpleNamespace(
            status="HARDBLOCK",
            reason="Projected spend exceeds hard limits",
        )
    )
    result = adapter.send_prompt(prompt="{}", task_type="json_classification", cycle="080")
    assert result.status == "BLOCKED"
    assert result.error_message == "OPENAI_BUDGET_HARDBLOCK"
    assert not full_env["ledger_path"].exists()


def test_advisory_only_mode_returns_without_claude_subprocess(
    full_env: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    called = {"count": 0}

    def _forbidden(*args, **kwargs):
        _ = args, kwargs
        called["count"] += 1
        raise AssertionError("Claude subprocess should not be called for advisory-only router dispatch")

    monkeypatch.setattr(csa.subprocess, "run", _forbidden)
    router = ProviderRouter(policy_path=full_env["policy_path"])
    result = router.dispatch("official_post_cycle_review", cycle="080", agent="F")
    assert result.status == "ADVISORYONLYBLOCKED"
    assert called["count"] == 0
    assert Path(result.decision_artifact_path or "").exists()


def test_integration_advisory_confirm_cursor_dispatches(
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
    decision_dir = tmp_path / "provider_decisions"
    ledger_path = tmp_path / "provider_usage_ledger.json"
    daily_dir = tmp_path / "daily_reports"
    monkeypatch.setattr("automation.provider_router.DECISION_DIR", decision_dir)
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    monkeypatch.setenv("PROVIDER_LEDGER_PATH", str(ledger_path))
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(daily_dir))

    router = ProviderRouter(policy_path=policy_path)
    result = router.dispatch("implementation", cycle="081", agent="F")
    assert result.provider == "cursorcli"
    assert result.status == "SUCCESS"
    artifact = Path(result.decision_artifact_path or "")
    assert artifact.exists()
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    assert payload["reason"] == "DISPATCHCONFIRM"
    assert json.loads(health_path.read_text(encoding="utf-8"))["cursorcli"]["status"] == "READY"
