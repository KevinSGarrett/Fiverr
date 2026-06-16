from __future__ import annotations

import json
from pathlib import Path

from automation.cost_guard import CostGuard, update_spend


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


def test_daily_soft_warn_boundary_is_inclusive(monkeypatch) -> None:
    monkeypatch.setattr("automation.cost_guard._get_daily_spend", lambda provider: 4.0)
    monkeypatch.setattr("automation.cost_guard._get_monthly_spend", lambda provider: 20.0)
    guard = CostGuard(policy_path="C:/does/not/exist/provider_policy.yml")
    result = guard.check_budget("openai_api", estimated_cost=1.0)
    assert result.status == "SOFTWARN"


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


<<<<<<< HEAD
def test_get_status_reports_softwarn_when_daily_projection_crosses_soft_limit(monkeypatch) -> None:
    monkeypatch.setattr("automation.cost_guard._get_daily_spend", lambda provider: 6.0)
    monkeypatch.setattr("automation.cost_guard._get_monthly_spend", lambda provider: 20.0)
    status = CostGuard(policy_path="C:/does/not/exist/provider_policy.yml").get_status("openai_api")
    assert status["status"] == "SOFTWARN"


=======
>>>>>>> origin/develop
def test_update_spend_increases_daily(tmp_path: Path, monkeypatch) -> None:
    state_path = tmp_path / "openai_budget_state.json"
    state_path.write_text(json.dumps({"dailyspendusd": 1.5, "monthlyspendusd": 20.0}), encoding="utf-8")
    monkeypatch.setenv("PROVIDER_BUDGET_STATE_PATH", str(state_path))
    monkeypatch.setenv("PROVIDER_POLICY_PATH", str(tmp_path / "missing_policy.yml"))
    update_spend("openai_api", 2.0)
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["dailyspendusd"] == 3.5


def test_update_spend_increases_monthly(tmp_path: Path, monkeypatch) -> None:
    state_path = tmp_path / "openai_budget_state.json"
    state_path.write_text(json.dumps({"dailyspendusd": 0.0, "monthlyspendusd": 7.0}), encoding="utf-8")
    monkeypatch.setenv("PROVIDER_BUDGET_STATE_PATH", str(state_path))
    monkeypatch.setenv("PROVIDER_POLICY_PATH", str(tmp_path / "missing_policy.yml"))
    update_spend("openai_api", 1.25)
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["monthlyspendusd"] == 8.25


def test_update_spend_non_openai_noop(tmp_path: Path, monkeypatch) -> None:
    state_path = tmp_path / "openai_budget_state.json"
    original = {"dailyspendusd": 3.0, "monthlyspendusd": 30.0}
    state_path.write_text(json.dumps(original), encoding="utf-8")
    monkeypatch.setenv("PROVIDER_BUDGET_STATE_PATH", str(state_path))
    monkeypatch.setenv("PROVIDER_POLICY_PATH", str(tmp_path / "missing_policy.yml"))
    update_spend("cursorcli", 9.0)
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["dailyspendusd"] == original["dailyspendusd"]
    assert payload["monthlyspendusd"] == original["monthlyspendusd"]


def test_cost_guard_loads_limits_from_policy(tmp_path: Path, monkeypatch) -> None:
    policy_path = tmp_path / "provider_policy.yml"
    policy_path.write_text(
        json.dumps(
            {
                "providers": {
                    "openaiapi": {
                        "hard_limits": {"daily_usd": 15, "monthly_usd": 225},
                        "soft_warn": {"daily_usd": 7},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("PROVIDER_POLICY_PATH", str(policy_path))
    guard = CostGuard()
    assert guard.daily_limit == 15.0
    assert guard.monthly_limit == 225.0
    assert guard.soft_warn == 7.0
