<<<<<<< HEAD
"""Export path sanitizer checks for staged files and ZIP artifacts."""
=======
"""Verify staged paths and zip members do not expose secrets."""
>>>>>>> origin/develop

from __future__ import annotations

import fnmatch
<<<<<<< HEAD
import re
=======
>>>>>>> origin/develop
import sys
from pathlib import Path
from zipfile import ZipFile


class ExportSecretError(Exception):
    """Raised when sensitive paths are found in staged files or archive entries."""

    def __init__(self, offending_paths: list[str]) -> None:
        self.offending_paths = offending_paths
        super().__init__(f"Sensitive paths detected: {', '.join(offending_paths)}")


<<<<<<< HEAD
_PATH_PATTERNS = ("*.env", "runner.env", "*.credentials", "*.pem", "*.key")
_INLINE_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"OPENAI_API_KEY\s*=\s*sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ANTHROPIC_API_KEY\s*=\s*sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?<!no )secret\s*=\s*[\"'][^\"']+[\"']", re.IGNORECASE),
)
=======
_PATTERNS = ("*.env", "runner.env", "*.credentials", "*.pem", "*.key")
>>>>>>> origin/develop


def _is_sensitive(path_value: str) -> bool:
    normalized = path_value.replace("\\", "/")
    lower = normalized.lower()
<<<<<<< HEAD
    basename = Path(lower).name
    if any(fnmatch.fnmatch(basename, pattern) for pattern in _PATH_PATTERNS):
        return True
    return "_token" in lower or "secret" in lower
=======
    if any(fnmatch.fnmatch(lower, pattern) for pattern in _PATTERNS):
        return True
    name = Path(normalized).name.lower()
    return "_token" in lower or "secret" in lower or "_token" in name or "secret" in name
>>>>>>> origin/develop


def verify_staged_files(staged_files: list[str]) -> None:
    offending = [path for path in staged_files if _is_sensitive(path)]
    if offending:
        raise ExportSecretError(offending)


def verify_zip(zip_path: Path) -> None:
<<<<<<< HEAD
    offending_paths: list[str] = []
    with ZipFile(zip_path, "r") as archive:
        for member in archive.namelist():
            if member.endswith("/"):
                continue
            if _is_sensitive(member):
                offending_paths.append(member)
    if offending_paths:
        raise ExportSecretError(offending_paths)


def scan_file_for_secrets(path: Path) -> list[str]:
    """Return any inline secret-like matches found in a text file."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return []
    findings: list[str] = []
    for pattern in _INLINE_SECRET_PATTERNS:
        findings.extend(match.group(0) for match in pattern.finditer(content))
    return findings


def verify_repo_clean(repo_root: Path | None = None) -> tuple[bool, list[str]]:
    """Scan automation Python files and report any secret-like findings."""
    root = repo_root or Path("C:/Fiverr/Fiverr")
    violations: list[str] = []
    for py_file in (root / "automation").rglob("*.py"):
        if not py_file.is_file():
            continue
        matches = scan_file_for_secrets(py_file)
        if matches:
            violations.append(str(py_file))
    return len(violations) == 0, violations
=======
    offending: list[str] = []
    with ZipFile(zip_path, "r") as archive:
        for member in archive.namelist():
            if _is_sensitive(member):
                offending.append(member)
    if offending:
        raise ExportSecretError(offending)
>>>>>>> origin/develop


if __name__ == "__main__":
    verify_zip(Path(sys.argv[1]))
