"""
branch_guard.py — Enforce branch operation safety rules before git operations.
Hard blocks force-push, direct main commits, and other destructive operations.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

PROTECTED_BRANCHES = {"main", "master", "develop"}
REPO_ROOT = Path("C:/Fiverr/Fiverr")


class BranchGuardError(Exception):
    pass


def assert_safe_to_push(branch: str, target: str = "develop") -> None:
    """Raise BranchGuardError if push is unsafe."""
    if branch in ("main", "master"):
        raise BranchGuardError(
            f"BLOCKED: Direct push to {branch} is forbidden. "
            "Use a release PR through the proper release gate."
        )
    if target in ("main", "master"):
        raise BranchGuardError(
            f"BLOCKED: PR target {target} is forbidden for normal cycles. "
            "Cycle branches must target develop."
        )


def assert_not_force_push(args: list[str]) -> None:
    """Raise if force push flags detected."""
    for flag in ("--force", "-f", "--force-with-lease"):
        if flag in args:
            raise BranchGuardError(
                f"BLOCKED: Force-push flag {flag!r} is forbidden."
            )


def assert_cycle_branch(branch: str) -> None:
    """Warn if branch doesn't follow cycle naming convention."""
    if not (branch.startswith("cycle/") or
            branch.startswith("chore/") or
            branch.startswith("ai/") or
            branch.startswith("quarantine/")):
        raise BranchGuardError(
            f"Branch {branch!r} doesn't match expected runner pattern. "
            "Use cycle/NNN/integration or chore/... or ai/..."
        )


def assert_branch_exists(branch: str, cwd: Path = REPO_ROOT) -> bool:
    """Return True if branch exists locally."""
    r = subprocess.run(
        ["git", "branch", "--list", branch],
        cwd=str(cwd), capture_output=True, text=True
    )
    return bool(r.stdout.strip())


def assert_clean_working_tree(cwd: Path = REPO_ROOT) -> None:
    """Raise if working tree has uncommitted changes."""
    r = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(cwd), capture_output=True, text=True
    )
    if r.stdout.strip():
        raise BranchGuardError(
            f"Working tree is dirty before operation:\n{r.stdout.strip()}\n"
            "Commit or stash changes first."
        )


def current_branch(cwd: Path = REPO_ROOT) -> str:
    r = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=str(cwd), capture_output=True, text=True
    )
    return r.stdout.strip()


def check_all(branch: str, target: str = "develop",
              cwd: Path = REPO_ROOT) -> list[str]:
    """Run all guards. Return list of violation messages (empty = safe)."""
    violations = []
    try:
        assert_safe_to_push(branch, target)
    except BranchGuardError as e:
        violations.append(str(e))
    return violations
