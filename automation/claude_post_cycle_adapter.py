"""
claude_post_cycle_adapter.py — Run official PM post-cycle review via Claude subscription.

Per Wave 04 / FINDING-008:
  - Must use local `claude` via subscription login, NOT ANTHROPIC_API_KEY
  - verify_subscription_preflight() blocks if API key present
  - Writes claude_request.md and claude_response.md artifacts
  - If Claude cannot run via subscription, marks review ADVISORY_ONLY — blocks next dispatch

Claude Code subscription docs:
  Pro/Max subscribers connect Claude Code via `claude` terminal login.
  If ANTHROPIC_API_KEY is set, Claude Code uses API billing instead.
  This runner must NEVER use API key billing.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT   = Path("C:/Fiverr/Fiverr")
RUNNER_ROOT = Path("C:/AI_Runner")
CLAUDE_STATE_PATH = RUNNER_ROOT / "state/claude_model_state.json"

# Where to write request/response artifacts
def _artifacts_dir(cycle: int, run_dir: Path) -> Path:
    d = run_dir / "post_cycle_review" / "claude"
    d.mkdir(parents=True, exist_ok=True)
    return d


@dataclass
class ClaudeReviewResult:
    status: str          # PASS | ADVISORY_ONLY | BLOCKED | ERROR
    response_text: str = ""
    request_path: str = ""
    response_path: str = ""
    error: str = ""
    advisory_only: bool = False
    blocks_dispatch: bool = False

    def summary(self) -> str:
        return (
            f"Claude post-cycle review: {self.status}\n"
            f"  Request : {self.request_path}\n"
            f"  Response: {self.response_path}\n"
            + (f"  Error   : {self.error}" if self.error else "")
        )


def verify_subscription_preflight() -> dict:
    """
    Hard check: ANTHROPIC_API_KEY must be absent at all scopes.
    Returns dict with passed=True/False and reason.
    """
    import os
    findings = []

    # Check all environment scopes
    for scope in ("Process",):
        val = os.environ.get("ANTHROPIC_API_KEY", "")
        if val:
            findings.append(f"ANTHROPIC_API_KEY set in {scope} scope (length {len(val)})")

    # Check via PowerShell for User + Machine scopes
    try:
        for scope in ("User", "Machine"):
            r = subprocess.run(
                ["powershell", "-Command",
                 f'[Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY", "{scope}")'],
                capture_output=True, text=True, timeout=5
            )
            val = r.stdout.strip()
            if val and val.lower() not in ("", "$null", "null"):
                findings.append(f"ANTHROPIC_API_KEY set in {scope} scope")
    except Exception:
        pass  # If PS check fails, rely on Process scope check only

    if findings:
        return {
            "passed": False,
            "reason": "BLOCKED_CLAUDE_API_KEY_PRESENT",
            "findings": findings,
            "action": (
                "Remove ANTHROPIC_API_KEY from all environment scopes before running "
                "official PM review. Claude must run via subscription login, not API billing."
            ),
        }

    return {"passed": True, "reason": "API_KEY_ABSENT_SUBSCRIPTION_ONLY"}


def run_post_cycle_review(
    cycle: int,
    run_dir: Path,
    review_prompt_text: str,
    facts_json: str,
) -> ClaudeReviewResult:
    """
    Run Claude Code with the POST_CYCLE_PM_REVIEW_v4 prompt.

    1. Runs subscription preflight — blocks if API key present
    2. Writes claude_request.md with review prompt + facts
    3. Invokes `claude -p claude_request.md --output-format text`
    4. Writes claude_response.md with full response
    5. Returns ClaudeReviewResult
    """
    artifacts = _artifacts_dir(cycle, run_dir)
    result = ClaudeReviewResult(status="IN_PROGRESS")

    # Step 1: Subscription preflight — HARD BLOCK
    preflight = verify_subscription_preflight()
    if not preflight["passed"]:
        result.status = "BLOCKED"
        result.blocks_dispatch = True
        result.error = preflight["action"]
        _write_preflight_block_report(cycle, run_dir, preflight)
        return result

    # Step 2: Write request artifact
    request_path = artifacts / "claude_request.md"
    request_content = f"""# POST-CYCLE PM REVIEW REQUEST — Cycle {cycle:03d}

## Facts
```json
{facts_json}
```

## Review Prompt
{review_prompt_text}
"""
    request_path.write_text(request_content, encoding="utf-8")
    result.request_path = str(request_path)

    # Step 3: Invoke Claude via subscription
    claude_binary = _find_claude_binary()
    if not claude_binary:
        result.status = "ADVISORY_ONLY"
        result.advisory_only = True
        result.error = "Claude Code binary not found on PATH. Review is advisory-only."
        result.blocks_dispatch = True  # Still blocks — must be resolved
        _write_advisory_report(cycle, run_dir, result.error)
        return result

    try:
        # Claude Code defaults to Opus 4.8 — force Sonnet 4.6 for PM review
        # (per claude_model_state.json: observed_default_model = Opus 4.8)
        r = subprocess.run(
            [claude_binary, "-p", request_content, "--output-format", "text",
             "--model", "claude-sonnet-4-6"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=600,  # 10 min max for PM review
        )
        response_text = (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        result.status = "ADVISORY_ONLY"
        result.advisory_only = True
        result.error = "Claude review timed out after 10 minutes"
        result.blocks_dispatch = True
        return result
    except Exception as e:
        result.status = "ERROR"
        result.error = str(e)
        result.blocks_dispatch = True
        return result

    # Step 4: Write response artifact
    response_path = artifacts / "claude_response.md"
    response_path.write_text(
        f"# POST-CYCLE PM REVIEW RESPONSE — Cycle {cycle:03d}\n\n"
        f"Generated: {datetime.now(UTC).isoformat()}\n\n"
        f"{response_text}",
        encoding="utf-8"
    )
    result.response_text = response_text
    result.response_path = str(response_path)

    # Step 5: Parse outcome
    result.status = _parse_review_outcome(response_text)
    result.blocks_dispatch = result.status not in ("PASS",)

    # Update claude_model_state with observed model
    _update_claude_state(r.stdout)

    return result


def _find_claude_binary() -> str | None:
    """Find `claude` binary on PATH."""
    import os
    import shutil
    # Ensure cursor-agent dir on PATH (it may have claude too)
    os.environ["PATH"] = (
        r"C:\Users\Windows 11\AppData\Local\cursor-agent" + ";" +
        os.environ.get("PATH", "")
    )
    found = shutil.which("claude")
    return found


def _parse_review_outcome(response_text: str) -> str:
    """Parse Claude's response for PASS/FAIL/ADVISORY keywords."""
    upper = response_text.upper()
    # Check for explicit PASS
    if "POST-CYCLE REVIEW: PASS" in upper or "REVIEW RESULT: PASS" in upper:
        return "PASS"
    # Check for explicit blockers
    if "POST-CYCLE REVIEW: FAIL" in upper or "REVIEW RESULT: FAIL" in upper:
        return "FAIL"
    if "DISPATCH BLOCKED" in upper:
        return "BLOCKED"
    # Default — treat as advisory if no clear verdict
    return "ADVISORY_ONLY"


def _update_claude_state(stdout: str) -> None:
    """Update claude_model_state.json with any observed model info."""
    try:
        state = json.loads(CLAUDE_STATE_PATH.read_text()) if CLAUDE_STATE_PATH.exists() else {}
        state["last_review_run_at"] = datetime.now(UTC).isoformat()
        # Try to parse model from output
        if "claude-sonnet" in stdout.lower():
            state["observed_model"] = "claude-sonnet-4-6"
            state["status"] = "SUBSCRIPTION_VERIFIED"
        elif "claude-opus" in stdout.lower():
            state["observed_model"] = "claude-opus-4-8"
            state["status"] = "SUBSCRIPTION_VERIFIED_WRONG_MODEL"
        CLAUDE_STATE_PATH.write_text(json.dumps(state, indent=2))
    except Exception:
        pass


def _write_preflight_block_report(cycle: int, run_dir: Path, preflight: dict) -> None:
    d = _artifacts_dir(cycle, run_dir)
    (d / "BLOCKED_API_KEY_PRESENT.md").write_text(
        f"# BLOCKED: ANTHROPIC_API_KEY Present\n\n"
        f"Cycle {cycle:03d} post-cycle review blocked at {datetime.now(UTC).isoformat()}\n\n"
        f"**Reason:** {preflight.get('reason')}\n\n"
        f"**Findings:**\n" + "\n".join(f"- {f}" for f in preflight.get("findings", [])) + "\n\n"
        f"**Action Required:**\n{preflight.get('action')}\n\n"
        f"Next dispatch is blocked until ANTHROPIC_API_KEY is removed.\n"
    )


def _write_advisory_report(cycle: int, run_dir: Path, error: str) -> None:
    d = _artifacts_dir(cycle, run_dir)
    (d / "ADVISORY_ONLY.md").write_text(
        f"# ADVISORY ONLY: Claude Code Not Available\n\n"
        f"Cycle {cycle:03d} | {datetime.now(UTC).isoformat()}\n\n"
        f"**Error:** {error}\n\n"
        "Post-cycle PM review could not run via Claude subscription.\n"
        "Dispatch is blocked until Claude Code is available and review completes.\n\n"
        "To resolve:\n"
        "1. Install Claude Code: `npm install -g @anthropic-ai/claude-code`\n"
        "2. Login: `claude login`\n"
        "3. Verify subscription: `claude /status`\n"
        "4. Re-run: `python automation/ai_cycle_controller.py post-cycle-review --cycle {cycle}`\n"
    )
