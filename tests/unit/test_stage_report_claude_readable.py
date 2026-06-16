from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from automation import daily_report_generator as module


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_report(tmp_path: Path, monkeypatch) -> dict:
    state_dir = tmp_path / "state"
    report_dir = tmp_path / "reports"
    _write_json(state_dir / "stage_state.json", {"current_stage": 4})
    _write_json(state_dir / "controller_state.json", {"active_cycle": 82})
    _write_json(state_dir / "heartbeat.json", {"last_seen": datetime.now(UTC).isoformat()})
    _write_json(state_dir / "provider_health.json", {"cursor_cli": {"status": "READY"}, "openai_api": {}})
    _write_json(
        state_dir / "cursor_model_state.json",
        {"last_verified": datetime.now(UTC).isoformat(), "observed_model": "codex-5.3", "effort": "medium"},
    )
    _write_json(state_dir / "claude_subscription_state.json", {"billing_mode": "claude_subscription_only", "api_key_present": False})
    _write_json(state_dir / "openai_api_budget_state.json", {"daily_spend_usd": 0.2, "daily_hard_limit_usd": 10})
    _write_json(state_dir / "codex_subscription_state.json", {"billing_mode": "chatgpt_subscription_only", "api_key_present": False})

    monkeypatch.setattr(module, "STAGE_STATE_PATH", state_dir / "stage_state.json")
    monkeypatch.setattr(module, "CONTROLLER_STATE_PATH", state_dir / "controller_state.json")
    monkeypatch.setattr(module, "HEARTBEAT_PATH", state_dir / "heartbeat.json")
    monkeypatch.setattr(module, "PROVIDER_HEALTH_PATH", state_dir / "provider_health.json")
    monkeypatch.setattr(module, "CURSOR_MODEL_STATE_PATH", state_dir / "cursor_model_state.json")
    monkeypatch.setattr(module, "CLAUDE_SUB_STATE_PATH", state_dir / "claude_subscription_state.json")
    monkeypatch.setattr(module, "OPENAI_BUDGET_STATE_PATH", state_dir / "openai_api_budget_state.json")
    monkeypatch.setattr(module, "CODEX_SUB_STATE_PATH", state_dir / "codex_subscription_state.json")
    monkeypatch.setattr(module, "OUTPUT_PATH", report_dir / "DAILY_STAGE_REPORT.json")
    monkeypatch.setattr(module, "_runner_service_status", lambda errors: "RUNNING")
    module.generate_daily_stage_report()
    return json.loads((report_dir / "DAILY_STAGE_REPORT.json").read_text(encoding="utf-8"))


def test_claude_assessment_prompt_has_pass_format(tmp_path: Path, monkeypatch) -> None:
    report = _build_report(tmp_path, monkeypatch)
    assert "STAGE_N_PASS" in report["claude_assessment_prompt"]


def test_claude_assessment_prompt_has_blocked_format(tmp_path: Path, monkeypatch) -> None:
    report = _build_report(tmp_path, monkeypatch)
    assert "BLOCKED" in report["claude_assessment_prompt"]


def test_report_next_action_describes_stage(tmp_path: Path, monkeypatch) -> None:
    report = _build_report(tmp_path, monkeypatch)
    assert "4" in report["next_action"]


def test_report_has_no_human_intervention_required(tmp_path: Path, monkeypatch) -> None:
    report = _build_report(tmp_path, monkeypatch)
    rendered = json.dumps(report).lower()
    assert "kevin must" not in rendered
    assert "human must" not in rendered


def test_report_has_all_4_provider_statuses(tmp_path: Path, monkeypatch) -> None:
    report = _build_report(tmp_path, monkeypatch)
    assert {"cursor_cli", "claude_subscription", "openai_api", "codex_subscription"}.issubset(
        report["models"].keys()
    )
