from __future__ import annotations

import json
from pathlib import Path

from automation.cost_guard import CostGuard


def test_under_limits_returns_pass(monkeypatch) -> None:
    monkeypatch.setattr("automation.cost_guard._get_daily_spend", lambda provider: 1.0)
    monkeypatch.setattr("automation.cost_guard._get_monthly_spend", lambda provider: 20.0)
    guard = CostGuard(policy_path="C:/does/not/exist/provider_policy.yml")
    result = guard.check_budget("openai_api", estimated_cost=1.0)
    assert result.status == "PASS"


def test_soft_warn_threshold_returns_softwarn(monkeypatch) -> None:
    monkeypatch.setattr("automation.cost_guard._get_daily_spend", lambda provider: 4.99)
    monkeypatch.setattr("automation.cost_guard._get_monthly_spend", lambda provider: 20.0)
    guard = CostGuard(policy_path="C:/does/not/exist/provider_policy.yml")
    result = guard.check_budget("openai_api", estimated_cost=0.02)
    assert result.status == "SOFTWARN"


def test_daily_hard_limit_returns_hardblock(monkeypatch) -> None:
    monkeypatch.setattr("automation.cost_guard._get_daily_spend", lambda provider: 9.99)
    monkeypatch.setattr("automation.cost_guard._get_monthly_spend", lambda provider: 20.0)
    guard = CostGuard(policy_path="C:/does/not/exist/provider_policy.yml")
    result = guard.check_budget("openai_api", estimated_cost=0.02)
    assert result.status == "HARDBLOCK"


def test_monthly_hard_limit_returns_hardblock(monkeypatch) -> None:
    monkeypatch.setattr("automation.cost_guard._get_daily_spend", lambda provider: 1.0)
    monkeypatch.setattr("automation.cost_guard._get_monthly_spend", lambda provider: 149.99)
    guard = CostGuard(policy_path="C:/does/not/exist/provider_policy.yml")
    result = guard.check_budget("openai_api", estimated_cost=0.02)
    assert result.status == "HARDBLOCK"


def test_non_openai_provider_always_passes(monkeypatch) -> None:
    monkeypatch.setattr("automation.cost_guard._get_daily_spend", lambda provider: 999.0)
    monkeypatch.setattr("automation.cost_guard._get_monthly_spend", lambda provider: 999.0)
    guard = CostGuard(policy_path="C:/does/not/exist/provider_policy.yml")
    result = guard.check_budget("cursorcli", estimated_cost=999.0)
    assert result.status == "PASS"


def test_estimated_cost_pushing_over_hard_limit_blocks(monkeypatch) -> None:
    monkeypatch.setattr("automation.cost_guard._get_daily_spend", lambda provider: 9.0)
    monkeypatch.setattr("automation.cost_guard._get_monthly_spend", lambda provider: 120.0)
    guard = CostGuard(policy_path="C:/does/not/exist/provider_policy.yml")
    result = guard.check_budget("openai_api", estimated_cost=1.0)
    assert result.status == "HARDBLOCK"


def test_policy_path_resolution_prefers_env_override(tmp_path: Path, monkeypatch) -> None:
    policy_path = tmp_path / "provider_policy.yml"
    policy_path.write_text(
        json.dumps({"providers": {"openai_api": {"hard_limits": {"daily_usd": 11}}}}), encoding="utf-8"
    )
    monkeypatch.setenv("PROVIDER_POLICY_PATH", str(policy_path))
    guard = CostGuard()
    assert guard.policy_path == policy_path


def test_get_status_returns_budget_snapshot(monkeypatch) -> None:
    monkeypatch.setattr("automation.cost_guard._get_daily_spend", lambda provider: 1.0)
    monkeypatch.setattr("automation.cost_guard._get_monthly_spend", lambda provider: 2.0)
    guard = CostGuard(policy_path="C:/does/not/exist/provider_policy.yml")
    status = guard.get_status("openai_api")
    assert status["provider"] == "openai_api"
    assert status["status"] == "PASS"


def test_check_budget_non_openai_always_passes_even_with_large_estimate(monkeypatch) -> None:
    monkeypatch.setattr("automation.cost_guard._get_daily_spend", lambda provider: 900.0)
    monkeypatch.setattr("automation.cost_guard._get_monthly_spend", lambda provider: 900.0)
    guard = CostGuard(policy_path="C:/does/not/exist/provider_policy.yml")
    result = guard.check_budget("deterministic_controller", estimated_cost=999.0)
    assert result.status == "PASS"


def test_budget_check_result_status_is_always_expected_enum(monkeypatch) -> None:
    monkeypatch.setattr("automation.cost_guard._get_daily_spend", lambda provider: 0.0)
    monkeypatch.setattr("automation.cost_guard._get_monthly_spend", lambda provider: 0.0)
    result = CostGuard(policy_path="C:/does/not/exist/provider_policy.yml").check_budget(
        "openai_api",
        estimated_cost=0.01,
    )
    assert result.status in {"PASS", "SOFTWARN", "HARDBLOCK"}
