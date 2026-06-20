"""
ci_status_reader.py — Read GitHub Actions CI status for a PR via the gh CLI.

Casing/typename parsing and the required-check set are centralized in
``automation.required_checks`` (item 3.2): ``gh pr view --json statusCheckRollup``
returns CheckRun objects whose ``conclusion`` is UPPERCASE with ``state == null``,
so the previous lowercase ``conclusion == "success"`` test never matched.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from typing import Any

from automation import required_checks


@dataclass
class CIStatus:
    pr_number: int
    all_passed: bool = False
    checks: list[dict[str, Any]] = field(default_factory=list)
    codecov_project: str = "PENDING"
    codecov_patch: str = "PENDING"
    raw: dict[str, Any] = field(default_factory=dict)
    gh_ok: bool = False

    def required_checks_passed(self, required: set[str] | None = None) -> bool:
        """True iff every REQUIRED check has reported SUCCESS (casing-correct)."""
        return required_checks.required_check_disposition(self.checks, required) == "GREEN"

    def disposition(self, required: set[str] | None = None) -> str:
        """Overall required-check disposition: ``GREEN`` | ``PENDING`` | ``FAILED``."""
        return required_checks.required_check_disposition(self.checks, required)

    def summary(self) -> str:
        lines = [f"CI Status for PR #{self.pr_number}:"]
        states = required_checks.latest_by_name(self.checks)
        for name, st in sorted(states.items()):
            lines.append(f"  {name}: {st}")
        return "\n".join(lines)


def read_pr_ci_status(pr_number: int,
                       repo: str = "KevinSGarrett/Fiverr") -> CIStatus:
    """Read all check statuses for a PR. ``gh_ok`` distinguishes a real read from
    a gh failure (so callers can treat an errored read as PENDING, not green)."""
    status = CIStatus(pr_number=pr_number)
    try:
        r = subprocess.run(
            ["gh", "pr", "view", str(pr_number),
             "--repo", repo,
             "--json", "statusCheckRollup,state,mergeable"],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode != 0:
            return status
        data = json.loads(r.stdout)
        status.raw = data
        status.gh_ok = True
        checks = data.get("statusCheckRollup") or []
        status.checks = checks
        # all_passed = every reported check is SUCCESS (casing-correct).
        status.all_passed = bool(checks) and all(
            required_checks.normalize_state(c) == "SUCCESS" for c in checks
        )
    except Exception as e:
        status.checks = [{"name": "error", "state": str(e)}]
        status.gh_ok = False

    return status


def wait_for_ci(pr_number: int, repo: str = "KevinSGarrett/Fiverr",
                max_wait_minutes: int = 30,
                poll_interval_seconds: int = 60) -> CIStatus:
    """Poll CI status until no check is pending or timeout.

    NOTE: this BLOCKS. The autonomous tick loop must NOT use this — it polls a
    single ``read_pr_ci_status`` snapshot per tick (see the AWAITING_CI_GREEN
    branch) so a tick is never held for up to ``max_wait_minutes``. ``wait_for_ci``
    remains for synchronous/CLI use.
    """
    import time
    deadline = time.time() + max_wait_minutes * 60
    while time.time() < deadline:
        status = read_pr_ci_status(pr_number, repo)
        pending = (not status.gh_ok) or any(
            required_checks.normalize_state(c) == "PENDING" for c in status.checks
        )
        if not pending:
            return status
        time.sleep(poll_interval_seconds)
    return read_pr_ci_status(pr_number, repo)
