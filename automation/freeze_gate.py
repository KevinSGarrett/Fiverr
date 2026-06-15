"""
freeze_gate.py — Autonomy freeze enforcement.
Every dangerous command (run-agent, merge-gate execute, post-cycle official) must call
_check_freeze() before proceeding.
"""
from __future__ import annotations

from pathlib import Path

import yaml

FREEZE_POLICY_PATH = Path("PM_Pack/automation/policies/autonomy_freeze.yml")
REPO_ROOT = Path("C:/Fiverr/Fiverr")

BLOCKED_COMMANDS = {
    "run-agent",
    "merge-gate-execute",
    "dev-auto",
    "post-cycle-review-official",
}


class FreezeBlockedError(RuntimeError):
    """Raised when a command is blocked by the autonomy freeze policy."""
    pass


def load_freeze_policy(repo_root: Path | None = None) -> dict:
    """Load autonomy_freeze.yml. Returns {'frozen': False} if file absent."""
    root = repo_root or REPO_ROOT
    path = root / FREEZE_POLICY_PATH
    if not path.exists():
        return {"frozen": False}
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {"frozen": False}
    except Exception:
        # Fail closed: if policy unreadable, treat as frozen
        return {"frozen": True, "reason": "POLICY_FILE_UNREADABLE"}


def check_freeze(command: str, repo_root: Path | None = None) -> None:
    """
    Raise FreezeBlockedError if the autonomy freeze is active and
    the given command is in the blocked list.

    Safe commands (dry-run, status, brain-check) pass through.
    """
    policy = load_freeze_policy(repo_root)
    if not policy.get("frozen", False):
        return  # Not frozen — allow

    permitted = policy.get("permitted_while_frozen", [])
    # If command is a permitted status-only command, allow it
    for allow_pattern in permitted:
        if command.startswith(allow_pattern.split()[0]):
            return

    reason = policy.get("reason", "FROZEN")
    incident = policy.get("incident_ref", "")
    raise FreezeBlockedError(
        f"AUTONOMY FROZEN: command '{command}' is blocked.\n"
        f"Reason: {reason}\n"
        f"Incident: {incident}\n"
        f"To unfreeze, resolve all P0 audit findings and set frozen: false in "
        f"PM_Pack/automation/policies/autonomy_freeze.yml\n"
        f"See: C:/AI_Runner/reports/incidents/{incident}.md"
    )


def is_frozen(repo_root: Path | None = None) -> bool:
    """Return True if automation is frozen."""
    return load_freeze_policy(repo_root).get("frozen", False)
