from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from automation import daily_report_generator as module

ORIGINAL_RUNNER_SERVICE_STATUS = module._runner_service_status


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_paths(tmp_path: Path, monkeypatch) -> Path:
    stage_state = tmp_path / "state" / "stage_state.json"
    controller_state = tmp_path / "state" / "controller_state.json"
    heartbeat = tmp_path / "state" / "heartbeat.json"
    provider_health = tmp_path / "state" / "provider_health.json"
    output = tmp_path / "reports" / "DAILY_STAGE_REPORT.json"
    cursor_state = tmp_path / "state" / "cursor_model_state.json"
    claude_state = tmp_path / "state" / "claude_subscription_state.json"
    openai_state = tmp_path / "state" / "openai_api_budget_state.json"
    codex_state = tmp_path / "state" / "codex_subscription_state.json"

    _write_json(stage_state, {"current_stage": 3, "stage_3": {"status": "PASS"}})
    _write_json(controller_state, {"active_cycle": 82})
    _write_json(heartbeat, {"last_seen": datetime.now(UTC).isoformat()})
    _write_json(
        provider_health,
        {
            "cursor_cli": {"status": "READY"},
            "openai_api": {"key_present": True},
        },
    )
    _write_json(
        cursor_state,
        {"observed_model": "codex-5.3", "effort": "medium", "last_verified": datetime.now(UTC).isoformat()},
    )
    _write_json(claude_state, {"billing_mode": "claude_subscription_only", "api_key_present": False})
    _write_json(openai_state, {"daily_spend_usd": 1.0, "daily_hard_limit_usd": 10})
    _write_json(codex_state, {"billing_mode": "chatgpt_subscription_only", "api_key_present": False})

    monkeypatch.setattr(module, "STAGE_STATE_PATH", stage_state)
    monkeypatch.setattr(module, "CONTROLLER_STATE_PATH", controller_state)
    monkeypatch.setattr(module, "HEARTBEAT_PATH", heartbeat)
    monkeypatch.setattr(module, "PROVIDER_HEALTH_PATH", provider_health)
    monkeypatch.setattr(module, "OUTPUT_PATH", output)
    monkeypatch.setattr(module, "CURSOR_MODEL_STATE_PATH", cursor_state)
    monkeypatch.setattr(module, "CLAUDE_SUB_STATE_PATH", claude_state)
    monkeypatch.setattr(module, "OPENAI_BUDGET_STATE_PATH", openai_state)
    monkeypatch.setattr(module, "CODEX_SUB_STATE_PATH", codex_state)
    monkeypatch.setattr(module, "_runner_service_status", lambda errors: "RUNNING")
    return output


def _generate(tmp_path: Path, monkeypatch) -> dict:
    out = _seed_paths(tmp_path, monkeypatch)
    module.generate_daily_stage_report()
    return json.loads(out.read_text(encoding="utf-8"))


def test_report_has_all_required_keys(tmp_path: Path, monkeypatch) -> None:
    report = _generate(tmp_path, monkeypatch)
    assert {
        "generated_at",
        "current_stage",
        "stage_states",
        "last_cycle",
        "health",
        "claude_assessment_prompt",
        "next_action",
        "models",
    }.issubset(report.keys())


def test_claude_assessment_prompt_non_empty(tmp_path: Path, monkeypatch) -> None:
    report = _generate(tmp_path, monkeypatch)
    assert isinstance(report["claude_assessment_prompt"], str)
    assert report["claude_assessment_prompt"].strip()


def test_models_section_has_all_4_providers(tmp_path: Path, monkeypatch) -> None:
    report = _generate(tmp_path, monkeypatch)
    assert {"cursor_cli", "claude_subscription", "openai_api", "codex_subscription"}.issubset(
        report["models"].keys()
    )


def test_stage_states_has_stages_2_through_7(tmp_path: Path, monkeypatch) -> None:
    report = _generate(tmp_path, monkeypatch)
    assert {f"stage_{i}" for i in range(2, 8)} == set(report["stage_states"].keys())


def test_next_action_is_actionable(tmp_path: Path, monkeypatch) -> None:
    report = _generate(tmp_path, monkeypatch)
    assert isinstance(report["next_action"], str)
    assert report["next_action"].strip()


def test_health_section_present(tmp_path: Path, monkeypatch) -> None:
    report = _generate(tmp_path, monkeypatch)
    assert "health" in report
    assert "heartbeat_age_minutes" in report["health"]
    errors: list[str] = []
    assert module._heartbeat_age_minutes({}, errors) == -1
    assert module._heartbeat_age_minutes({"last_seen": "bad-time"}, errors) == -1
    assert module._model_gate_status({"cursor_cli": {"status": "DEGRADED"}}) == "EXPIRING_SOON"
    assert module._model_gate_status({"cursor_cli": {"status": "BLOCKED"}}) == "FAIL"
    assert module._parse_iso("") is None
    assert module._parse_iso("not-an-iso") is None
    naive = module._parse_iso("2026-06-16T01:00:00")
    assert naive is not None
    assert naive.tzinfo is not None


def test_report_is_valid_json(tmp_path: Path, monkeypatch) -> None:
    output = _seed_paths(tmp_path, monkeypatch)
    module.generate_daily_stage_report()
    parsed = json.loads(output.read_text(encoding="utf-8"))
    assert parsed["current_stage"] == 3
    errors: list[str] = []
    assert module._load_json(tmp_path / "missing.json", errors, default={"a": 1}) == {"a": 1}
    broken = tmp_path / "broken.json"
    broken.write_text("{oops", encoding="utf-8")
    assert module._load_json(broken, errors, default={"b": 2}) == {"b": 2}
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: type("Proc", (), {"stdout": "Running\n", "returncode": 0})(),
    )
    assert ORIGINAL_RUNNER_SERVICE_STATUS(errors) == "RUNNING"
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: type("Proc", (), {"stdout": "", "returncode": 0})(),
    )
    assert ORIGINAL_RUNNER_SERVICE_STATUS(errors) == "STOPPED"

    def _raise_oserror(*args, **kwargs):  # type: ignore[no-untyped-def]
        _ = args, kwargs
        raise OSError("boom")

    monkeypatch.setattr(module.subprocess, "run", _raise_oserror)
    assert ORIGINAL_RUNNER_SERVICE_STATUS(errors) == "STOPPED"
    monkeypatch.setattr(module, "CURSOR_MODEL_STATE_PATH", tmp_path / "missing_cursor_model_state.json")
    models_fail = module._build_models_section(errors, provider_health={})
    assert models_fail["cursor_cli"]["gate_status"] == "FAIL"
    models_block = module._build_models_section(
        errors,
        provider_health={"openai_api": {"key_present": True}},
    )
    assert models_block["openai_api"]["gate_status"] in {"PASS", "WARN", "BLOCKED"}
    _write_json(module.OPENAI_BUDGET_STATE_PATH, {"daily_spend_usd": 10.0, "daily_hard_limit_usd": 10})
    models_block = module._build_models_section(errors, provider_health={"openai_api": {"key_present": True}})
    assert models_block["openai_api"]["gate_status"] == "BLOCKED"
    _write_json(module.OPENAI_BUDGET_STATE_PATH, {"daily_spend_usd": 8.5, "daily_hard_limit_usd": 10})
    models_warn = module._build_models_section(errors, provider_health={"openai_api": {"key_present": True}})
    assert models_warn["openai_api"]["gate_status"] == "WARN"
    evidence_path = tmp_path / "stage3_evidence.json"
    _write_json(evidence_path, {"ci_status": "PASS", "test_suite_result": "PASS"})
    summary = module._build_last_cycle_summary(
        {"active_cycle": 82},
        {"stage_3": {"evidence_path": str(evidence_path)}},
        errors,
    )
    assert summary["cycle_number"] == 82


def test_report_written_to_correct_path() -> None:
    # Under test isolation OUTPUT_PATH is redirected away from the live runner
    # root (C:/AI_Runner) into a per-session tmp root. What must remain stable is
    # the relative location within that root: reports/DAILY_STAGE_REPORT.json.
    output_path = module.OUTPUT_PATH
    assert output_path.name == "DAILY_STAGE_REPORT.json"
    assert output_path.parent.name == "reports"
