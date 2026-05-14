"""Repository hygiene checks for local runtime artifacts."""

from __future__ import annotations

import fnmatch
import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.utils.paths import project_root

FORBIDDEN_TRACKED_PATTERNS = (
    "__pycache__/*",
    ".pytest_cache/*",
    ".mypy_cache/*",
    ".ruff_cache/*",
    "playwright/.auth/*",
    "storage_state.json",
    "*.session",
)
UNTRACKED_RUNTIME_DB_PATTERNS = ("*.db", "*.sqlite", "*.sqlite3")


@dataclass(frozen=True)
class HygieneIssue:
    issue_type: str
    path: str
    details: str


def _run_git_list(repo_root: Path, args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def _matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    normalized = path.replace("\\", "/")
    for pattern in patterns:
        if fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(Path(normalized).name, pattern):
            return True
    return False


def find_hygiene_issues(repo_root: Path | None = None) -> list[HygieneIssue]:
    """Return deterministic list of repository hygiene issues."""
    root = repo_root or project_root()

    tracked_files = _run_git_list(root, ["ls-files"])
    untracked_files = _run_git_list(root, ["ls-files", "--others", "--exclude-standard"])

    issues: list[HygieneIssue] = []
    for path in tracked_files:
        if _matches_any(path, UNTRACKED_RUNTIME_DB_PATTERNS):
            issues.append(
                HygieneIssue(
                    issue_type="tracked_runtime_database",
                    path=path,
                    details="Runtime database artifacts must not be tracked in git.",
                )
            )
        if _matches_any(path, FORBIDDEN_TRACKED_PATTERNS):
            issues.append(
                HygieneIssue(
                    issue_type="forbidden_tracked_artifact",
                    path=path,
                    details="Path should be ignored and removed from tracked files.",
                )
            )

    for path in untracked_files:
        if _matches_any(path, UNTRACKED_RUNTIME_DB_PATTERNS):
            issues.append(
                HygieneIssue(
                    issue_type="untracked_runtime_database",
                    path=path,
                    details="Runtime database artifacts must not accumulate in repo root.",
                )
            )

    return sorted(issues, key=lambda issue: (issue.issue_type, issue.path))
