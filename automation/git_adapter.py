"""
git_adapter.py â€” Clean git operations for the autonomous runner.
All operations constrained to cycle branches; main is never touched directly.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
FORBIDDEN_BRANCHES = {"main", "master"}


@dataclass
class CommitResult:
    sha: str
    branch: str
    files_staged: int
    message: str


def _git(*args: str, cwd: Path = REPO_ROOT, check: bool = True) -> str:
    r = subprocess.run(["git", *args], cwd=str(cwd),
                       capture_output=True, text=True, check=False)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout.strip()


def current_branch(cwd: Path = REPO_ROOT) -> str:
    return _git("branch", "--show-current", cwd=cwd)


def is_clean(cwd: Path = REPO_ROOT) -> bool:
    return _git("status", "--short", cwd=cwd, check=False) == ""


def changed_files(cwd: Path = REPO_ROOT) -> list[str]:
    out = _git("status", "--short", cwd=cwd, check=False)
    files = []
    for line in out.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2:
            files.append(parts[1].strip())
    return files


def diff_stat(cwd: Path = REPO_ROOT) -> str:
    return _git("diff", "--stat", cwd=cwd, check=False)


def create_cycle_branch(branch_name: str, base: str = "develop",
                        cwd: Path = REPO_ROOT) -> None:
    """Create cycle branch from develop. Refuses to create from main."""
    if base in FORBIDDEN_BRANCHES:
        raise ValueError(f"Refusing to create branch from {base}")
    _git("fetch", "--all", "--prune", cwd=cwd)
    _git("checkout", base, cwd=cwd)
    _git("pull", "origin", base, cwd=cwd)
    _git("checkout", "-b", branch_name, cwd=cwd)


def checkout(branch_name: str, cwd: Path = REPO_ROOT) -> None:
    _git("checkout", branch_name, cwd=cwd)


def add_files(files: list[str], cwd: Path = REPO_ROOT) -> int:
    """Stage specific files. Returns count staged."""
    for f in files:
        _git("add", f, cwd=cwd, check=False)
    staged = _git("diff", "--cached", "--name-only", cwd=cwd, check=False)
    return len([line for line in staged.splitlines() if line.strip()])


def add_all(cwd: Path = REPO_ROOT) -> int:
    _git("add", "-A", cwd=cwd)
    staged = _git("diff", "--cached", "--name-only", cwd=cwd, check=False)
    return len([line for line in staged.splitlines() if line.strip()])


def commit(message: str, cwd: Path = REPO_ROOT) -> CommitResult:
    """Commit staged files. Raises if nothing staged or on forbidden branch."""
    branch = current_branch(cwd)
    if branch in FORBIDDEN_BRANCHES:
        raise ValueError(f"Refusing to commit directly to {branch}")

    staged = _git("diff", "--cached", "--name-only", cwd=cwd, check=False)
    count = len([line for line in staged.splitlines() if line.strip()])
    if count == 0:
        raise RuntimeError("Nothing staged to commit")

    _git("commit", "-m", message, cwd=cwd)
    sha = _git("rev-parse", "HEAD", cwd=cwd)
    return CommitResult(sha=sha, branch=branch, files_staged=count, message=message)


def push_branch(branch_name: str, cwd: Path = REPO_ROOT) -> None:
    """Push branch to origin. Never pushes to main."""
    if branch_name in FORBIDDEN_BRANCHES:
        raise ValueError(f"Refusing to push to {branch_name}")
    _git("push", "-u", "origin", branch_name, cwd=cwd)


def secret_scan(cwd: Path = REPO_ROOT) -> list[str]:
    """Scan staged files for obvious secret patterns. Returns list of findings."""
    findings = []
    staged_names = _git("diff", "--cached", "--name-only", cwd=cwd, check=False)
    danger_patterns = [".env", "secret", "token", "credential",
                       "storage_state", "playwright/.auth", "private_key", "api_key"]
    for fname in staged_names.splitlines():
        fname_lower = fname.lower()
        for pat in danger_patterns:
            if pat in fname_lower:
                findings.append(f"Suspicious staged file: {fname} (matches pattern: {pat})")
    return findings


def head_sha(cwd: Path = REPO_ROOT) -> str:
    return _git("rev-parse", "HEAD", cwd=cwd, check=False)


def log_oneline(n: int = 5, cwd: Path = REPO_ROOT) -> list[str]:
    out = _git("log", "--oneline", f"-{n}", cwd=cwd, check=False)
    return out.splitlines()
