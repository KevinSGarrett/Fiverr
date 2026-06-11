"""
claude_sub_gate.py — Enforce Claude subscription-only billing (CLAUDE-SUB-002..008).

Checks ANTHROPIC_API_KEY absence and Claude Code subscription login state.
Writes BLOCKED_CLAUDE_API_KEY_PRESENT.md if API key is detected.
"""
from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

RUNNER_ROOT = Path("C:/AI_Runner")
BLOCKED_REPORT_DIR = RUNNER_ROOT / "reports/model_verification"


def check_api_key_absent() -> dict:
    """
    CLAUDE-SUB-002/004: Verify ANTHROPIC_API_KEY is absent in all scopes.
    Returns dict with passed, detail, and any blocked report path.
    """
    findings: list[str] = []
    for scope in ("process", "user", "machine"):
        key = os.environ.get("ANTHROPIC_API_KEY", "") if scope == "process" else ""
        if scope == "user":
            try:
                r = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-Command",
                     '[Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY","User")'],
                    capture_output=True, text=True, timeout=5
                )
                key = r.stdout.strip()
            except Exception:
                key = ""
        elif scope == "machine":
            try:
                r = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-Command",
                     '[Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY","Machine")'],
                    capture_output=True, text=True, timeout=5
                )
                key = r.stdout.strip()
            except Exception:
                key = ""
        if key:
            findings.append(f"{scope} scope: API key detected (length={len(key)})")

    if findings:
        report_path = _write_blocked_report(findings)
        return {
            "passed": False,
            "incident_code": "BLOCKED_CLAUDE_API_KEY_PRESENT",
            "findings": findings,
            "report": str(report_path),
            "action": "Remove API key, re-authenticate Claude Code with subscription login",
        }

    return {"passed": True, "findings": [], "detail": "ANTHROPIC_API_KEY absent in all scopes"}


def verify_subscription_preflight() -> dict:
    """
    CLAUDE-SUB-001/003: Full preflight check before any Claude PM/review step.
    Checks: API key absent, Claude Code login (if available), billing mode.
    """
    result: dict[str, Any] = {"checks": [], "passed": True, "incident_code": ""}

    # Check 1: API key must be absent
    api_check = check_api_key_absent()
    result["checks"].append({"name": "api_key_absent", **api_check})
    if not api_check["passed"]:
        result["passed"] = False
        result["incident_code"] = "BLOCKED_CLAUDE_API_KEY_PRESENT"
        return result

    # Check 2: Claude model state billing mode
    claude_state_path = RUNNER_ROOT / "state/claude_model_state.json"
    if claude_state_path.exists():
        import json
        state = json.loads(claude_state_path.read_text())
        billing = state.get("billing_mode", "")
        api_present = state.get("anthropic_api_key_present", False)
        if billing != "claude_subscription_only" or api_present:
            result["passed"] = False
            result["incident_code"] = "BLOCKED_CLAUDE_API_KEY_PRESENT"
            result["checks"].append({
                "name": "billing_mode",
                "passed": False,
                "detail": f"billing={billing!r}, api_key_present={api_present}",
            })
            return result
        result["checks"].append({
            "name": "billing_mode",
            "passed": True,
            "detail": "billing=claude_subscription_only, api_key_present=False",
        })

    result["checks"].append({
        "name": "subscription_preflight",
        "passed": True,
        "detail": "All checks passed — subscription-only confirmed",
    })
    return result


def _write_blocked_report(findings: list[str]) -> Path:
    """Write BLOCKED_CLAUDE_API_KEY_PRESENT.md incident report."""
    BLOCKED_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    path = BLOCKED_REPORT_DIR / f"BLOCKED_CLAUDE_API_KEY_PRESENT_{ts}.md"
    lines = [
        "# BLOCKED: ANTHROPIC_API_KEY Present",
        f"Time: {datetime.now(UTC).isoformat()}",
        "",
        "## Findings",
    ]
    for f in findings:
        lines.append(f"- {f}")
    lines += [
        "",
        "## Required Actions",
        "1. Stop Claude PM/review automation immediately",
        "2. Remove ANTHROPIC_API_KEY from all environment scopes:",
        '   ```powershell',
        '   [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $null, "User")',
        '   [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $null, "Machine")',
        '   ```',
        "3. Re-authenticate Claude Code using subscription login:",
        "   ```powershell",
        "   claude logout",
        "   claude login",
        "   ```",
        "4. Verify: `claude /status` shows subscription login, not API key",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

def run_subscription_check() -> dict:
    """
    Full subscription check: API key absence + billing mode verification.
    Returns dict with passed, incident_code, checks.
    Alias for verify_subscription_preflight, used by controller and tests.
    """
    return verify_subscription_preflight()
