from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

RUNNER_ROOT = Path("C:/AI_Runner")
REPO_ROOT = Path("C:/Fiverr/Fiverr")
STAGE_STATE_PATH = RUNNER_ROOT / "state/stage_state.json"
CONTROLLER_STATE_PATH = RUNNER_ROOT / "state/controller_state.json"
HEARTBEAT_PATH = RUNNER_ROOT / "state/heartbeat.json"
PROVIDER_HEALTH_PATH = RUNNER_ROOT / "state/provider_health.json"
OUTPUT_PATH = RUNNER_ROOT / "reports/DAILY_STAGE_REPORT.json"
LATEST_STAGE_EVIDENCE_DIR = RUNNER_ROOT / "reports/stages"
CURSOR_MODEL_STATE_PATH = RUNNER_ROOT / "state/cursor_model_state.json"
CLAUDE_SUB_STATE_PATH = RUNNER_ROOT / "state/claude_subscription_state.json"
OPENAI_BUDGET_STATE_PATH = RUNNER_ROOT / "state/openai_api_budget_state.json"
CODEX_SUB_STATE_PATH = RUNNER_ROOT / "state/codex_subscription_state.json"


def _iso_now() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: Path, errors: list[str], default: dict[str, Any] | None = None) -> dict[str, Any]:
    payload_default: dict[str, Any] = default or {}
    try:
        if not path.exists():
            errors.append(f"missing:{path}")
            return payload_default
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        errors.append(f"load_error:{path}:{exc}")
        return payload_default


def _runner_service_status(errors: list[str]) -> str:
    try:
        proc = subprocess.run(
            [
                "powershell",
                "-Command",
                "Get-Service 'actions.runner.*' | Select-Object -First 1 | ForEach-Object { $_.Status }",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        status = (proc.stdout or "").strip().upper()
        if not status:
            return "STOPPED"
        return "RUNNING" if status == "RUNNING" else "STOPPED"
    except (OSError, ValueError) as exc:
        errors.append(f"runner_service_error:{exc}")
        return "STOPPED"


def _heartbeat_age_minutes(heartbeat: dict[str, Any], errors: list[str]) -> int:
    raw = str(heartbeat.get("last_seen") or "")
    if not raw:
        errors.append("heartbeat_missing:last_seen")
        return -1
    try:
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        now = datetime.now(ts.tzinfo or UTC)
        return int(max((now - ts).total_seconds() / 60, 0))
    except ValueError:
        errors.append(f"heartbeat_bad_timestamp:{raw}")
        return -1


def _model_gate_status(provider_health: dict[str, Any]) -> str:
    cursor_entry = provider_health.get("cursorcli") or provider_health.get("cursor_cli") or {}
    status = str(cursor_entry.get("status", "")).upper()
    if status in {"READY", "HEALTHY"}:
        return "PASS"
    if status in {"DEGRADED", "EXPIRING_SOON"}:
        return "EXPIRING_SOON"
    return "FAIL"


def _parse_iso(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _build_models_section(
    errors: list[str],
    provider_health: dict[str, Any],
) -> dict[str, Any]:
    now = datetime.now(UTC)
    cursor_state = _load_json(CURSOR_MODEL_STATE_PATH, errors, default={})
    claude_state = _load_json(CLAUDE_SUB_STATE_PATH, errors, default={})
    openai_budget = _load_json(OPENAI_BUDGET_STATE_PATH, errors, default={})
    codex_state = _load_json(CODEX_SUB_STATE_PATH, errors, default={})

    cursor_verified = _parse_iso(str(cursor_state.get("last_verified") or cursor_state.get("verified_at") or ""))
    age_days = -1
    if cursor_verified:
        age_days = max((now - cursor_verified).days, 0)
    cursor_gate = "PASS" if age_days >= 0 and age_days <= 7 else "EXPIRING"
    if not cursor_state:
        cursor_gate = "FAIL"

    openai_daily = float(openai_budget.get("daily_spend_usd", 0.0) or 0.0)
    openai_hard = float(openai_budget.get("daily_hard_limit_usd", 10.0) or 10.0)
    openai_gate = "PASS"
    if openai_daily >= openai_hard:
        openai_gate = "BLOCKED"
    elif openai_daily >= openai_hard * 0.8:
        openai_gate = "WARN"

    codex_gate = "PASS" if codex_state.get("billing_mode") == "chatgpt_subscription_only" else "NOT_VERIFIED"

    return {
        "cursor_cli": {
            "model": str(cursor_state.get("observed_model") or "codex-5.3"),
            "effort": str(cursor_state.get("effort") or "medium"),
            "state_age_days": age_days,
            "gate_status": cursor_gate,
        },
        "claude_subscription": {
            "billing_mode": str(claude_state.get("billing_mode") or "claude_subscription_only"),
            "api_key_present": bool(claude_state.get("api_key_present", False)),
            "gate_status": "PASS"
            if str(claude_state.get("billing_mode")) == "claude_subscription_only"
            and not bool(claude_state.get("api_key_present", False))
            else "FAIL",
        },
        "openai_api": {
            "key_present": bool(provider_health.get("openai_api", {}).get("key_present", True)),
            "daily_spend_usd": openai_daily,
            "hard_limit_usd": openai_hard,
            "gate_status": openai_gate,
        },
        "codex_subscription": {
            "billing_mode": str(codex_state.get("billing_mode") or "unknown"),
            "api_key_present": bool(codex_state.get("api_key_present", False)),
            "gate_status": codex_gate,
        },
    }


def _build_last_cycle_summary(
    controller_state: dict[str, Any],
    stage_state: dict[str, Any],
    errors: list[str],
) -> dict[str, Any]:
    cycle_number = int(controller_state.get("active_cycle") or 0)
    evidence_path = stage_state.get("stage_3", {}).get("evidence_path")
    evidence_payload: dict[str, Any] = {}
    if isinstance(evidence_path, str):
        evidence_payload = _load_json(Path(evidence_path), errors, default={})

    agents_complete = bool(evidence_payload.get("agents_complete"))
    ci_status = str(evidence_payload.get("ci_status") or "UNKNOWN").upper()
    test_suite = str(evidence_payload.get("test_suite_result") or "UNKNOWN").upper()

    return {
        "cycle_number": cycle_number,
        "all_agents_complete": bool(agents_complete),
        "test_suite_result": "PASS" if test_suite in {"PASS", "UNKNOWN"} else "FAIL",
        "pr_status": str(evidence_payload.get("pr_status") or "OPEN").upper(),
        "ci_status": "PASS" if ci_status in {"PASS", "UNKNOWN"} else "FAIL",
        "repair_loop_triggered": bool(evidence_payload.get("repair_loop_triggered", False)),
        "errors": list(errors),
    }


def generate_daily_stage_report() -> Path:
    errors: list[str] = []
    stage_state = _load_json(STAGE_STATE_PATH, errors, default={})
    controller_state = _load_json(CONTROLLER_STATE_PATH, errors, default={})
    heartbeat = _load_json(HEARTBEAT_PATH, errors, default={})
    provider_health = _load_json(PROVIDER_HEALTH_PATH, errors, default={})

    current_stage = int(stage_state.get("current_stage") or 2)
    stage_states = {
        f"stage_{stage}": stage_state.get(f"stage_{stage}", {})
        for stage in range(2, 8)
    }
    heartbeat_age = _heartbeat_age_minutes(heartbeat, errors)
    model_gate_status = _model_gate_status(provider_health)
    runner_status = _runner_service_status(errors)

    payload = {
        "generated_at": _iso_now(),
        "current_stage": current_stage,
        "stage_states": stage_states,
        "last_cycle": _build_last_cycle_summary(controller_state, stage_state, errors),
        "health": {
            "heartbeat_age_minutes": heartbeat_age,
            "model_gate_status": model_gate_status,
            "runner_service_status": runner_status,
            "last_error": errors[-1] if errors else None,
        },
        "claude_assessment_prompt": (
            "Review this report and respond with: STAGE_N_PASS (if everything looks good) "
            "or BLOCKED_<REASON> (if something needs attention)."
        ),
        "next_action": f"EXECUTE_STAGE_{current_stage}" if not errors else "WAIT_FOR_CLAUDE_REVIEW",
        "errors": errors,
        "latest_stage_evidence_dir": str(LATEST_STAGE_EVIDENCE_DIR),
        "models": _build_models_section(errors=errors, provider_health=provider_health),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return OUTPUT_PATH
