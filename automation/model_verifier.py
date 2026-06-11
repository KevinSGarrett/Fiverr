"""
model_verifier.py — Model verification adapter (MODEL-011).
Validates cursor and claude model state files against policy.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CURSOR_STATE = Path("C:/AI_Runner/state/cursor_model_state.json")
CLAUDE_STATE  = Path("C:/AI_Runner/state/claude_model_state.json")
POLICY_PATH   = Path("C:/Fiverr/Fiverr/PM_Pack/automation/model_policy.yml")

ACCEPTED_CURSOR_LABELS = {
    "Codex 5.3", "GPT-5.3 Codex", "gpt-5.3-codex",
    "codex-5.3", "OpenAI Codex 5.3"
}
MAX_AGE_DAYS = 7


def verify_cursor() -> dict[str, Any]:
    """Verify cursor model state. Returns dict with passed, reason, detail."""
    if not CURSOR_STATE.exists():
        return {"passed": False, "reason": "cursor_model_state.json missing",
                "status": "MISSING"}

    state = json.loads(CURSOR_STATE.read_text())

    if state.get("status") != "VERIFIED":
        return {"passed": False, "reason": f"status={state.get('status')} (need VERIFIED)",
                "status": state.get("status", "UNKNOWN")}

    model = state.get("observed_model", "")
    if model not in ACCEPTED_CURSOR_LABELS:
        return {"passed": False, "reason": f"model={model!r} not in accepted labels",
                "status": "MODEL_MISMATCH"}

    effort = state.get("observed_effort", "")
    if effort.lower() not in ("medium", "medium effort"):
        return {"passed": False, "reason": f"effort={effort!r} (need medium)",
                "status": "EFFORT_MISMATCH"}

    if not state.get("auto_model_disabled"):
        return {"passed": False, "reason": "auto_model_disabled=False",
                "status": "AUTO_ENABLED"}

    # Age check
    try:
        vt = datetime.fromisoformat(state["verified_at"].replace("Z", "+00:00"))
        age = (datetime.now(UTC) - vt).total_seconds() / 86400
        if age > MAX_AGE_DAYS:
            return {"passed": False, "reason": f"verification stale ({age:.1f} days)",
                    "status": "STALE"}
    except Exception:
        pass

    return {"passed": True, "reason": "all checks pass",
            "status": "VERIFIED", "model": model,
            "binary": state.get("binary", "")}


def verify_claude() -> dict[str, Any]:
    """Verify claude model state."""
    if not CLAUDE_STATE.exists():
        return {"passed": False, "reason": "claude_model_state.json missing",
                "status": "MISSING"}

    state = json.loads(CLAUDE_STATE.read_text())

    # Check ANTHROPIC_API_KEY is absent
    if state.get("anthropic_api_key_present"):
        return {"passed": False,
                "reason": "ANTHROPIC_API_KEY detected — billing risk",
                "status": "BLOCKED_API_KEY_PRESENT"}

    billing = state.get("billing_mode", "")
    if billing != "claude_subscription_only":
        return {"passed": False,
                "reason": f"billing_mode={billing!r} (need claude_subscription_only)",
                "status": "WRONG_BILLING"}

    return {"passed": True, "reason": "subscription billing verified",
            "status": state.get("status", "UNVERIFIED"),
            "model": state.get("requested_model", "")}


def verify_all() -> dict[str, Any]:
    """Run both verifications and return combined result."""
    cursor = verify_cursor()
    claude = verify_claude()
    return {
        "cursor": cursor,
        "claude": claude,
        "all_passed": cursor["passed"] and claude["passed"],
    }
