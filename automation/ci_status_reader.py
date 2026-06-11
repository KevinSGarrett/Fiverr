"""
ci_status_reader.py — Read GitHub Actions CI status and Codecov check statuses for a PR.
Uses gh CLI (already authenticated) for simplicity.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CIStatus:
    pr_number: int
    all_passed: bool = False
    checks: list[dict[str, Any]] = field(default_factory=list)
    codecov_project: str = "PENDING"
    codecov_patch: str = "PENDING"
    raw: dict[str, Any] = field(default_factory=dict)

    def required_checks_passed(self) -> bool:
        required = {
            "CI / lint", "CI / type-check",
            "CI / tests-coverage", "CI / smoke-gates",
        }
        passed = {
            c["name"] for c in self.checks
            if c.get("state") in ("SUCCESS", "success", "COMPLETED_SUCCESS")
            or c.get("conclusion") == "success"
        }
        return required.issubset(passed)

    def summary(self) -> str:
        lines = [f"CI Status for PR #{self.pr_number}:"]
        for c in self.checks:
            name = c.get("name", "?")
            state = c.get("conclusion") or c.get("state") or "pending"
            lines.append(f"  {name}: {state}")
        lines.append(f"  codecov/project: {self.codecov_project}")
        lines.append(f"  codecov/patch:   {self.codecov_patch}")
        return "\n".join(lines)


def read_pr_ci_status(pr_number: int,
                       repo: str = "KevinSGarrett/Fiverr") -> CIStatus:
    """Read all check statuses for a PR."""
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
        checks = data.get("statusCheckRollup") or []
        status.checks = checks

        # Parse Codecov specifically
        for c in checks:
            name = c.get("name", "") or c.get("context", "")
            conclusion = c.get("conclusion") or c.get("state") or "pending"
            if "codecov/project" in name.lower():
                status.codecov_project = conclusion.upper()
            elif "codecov/patch" in name.lower():
                status.codecov_patch = conclusion.upper()

        passed_states = {"SUCCESS", "success", "COMPLETED_SUCCESS"}
        all_ok = all(
            (c.get("conclusion") or c.get("state", "")) in passed_states
            for c in checks
        )
        status.all_passed = all_ok and bool(checks)

    except Exception as e:
        status.checks = [{"name": "error", "state": str(e)}]

    return status


def wait_for_ci(pr_number: int, repo: str = "KevinSGarrett/Fiverr",
                max_wait_minutes: int = 30,
                poll_interval_seconds: int = 60) -> CIStatus:
    """Poll CI status until complete or timeout."""
    import time
    deadline = time.time() + max_wait_minutes * 60
    while time.time() < deadline:
        status = read_pr_ci_status(pr_number, repo)
        pending = any(
            (c.get("conclusion") or c.get("state", "")) in
            ("PENDING", "pending", "QUEUED", "IN_PROGRESS", "queued", "in_progress")
            for c in status.checks
        )
        if not pending:
            return status
        time.sleep(poll_interval_seconds)
    return read_pr_ci_status(pr_number, repo)
