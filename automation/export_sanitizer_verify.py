"""Validation helpers that block secret-like files from exports."""
from __future__ import annotations

import re
import sys
from fnmatch import fnmatch
from pathlib import Path
from zipfile import ZipFile


class ExportSecretError(Exception):
    """Raised when an export contains secret-like file paths."""

    def __init__(self, offending_paths: list[str]) -> None:
        self.offending_paths = offending_paths
        message = "Secret-like paths detected: " + ", ".join(offending_paths)
        super().__init__(message)


def _looks_secret(path_value: str) -> bool:
    normalized_path = path_value.replace("\\", "/")
    path_name = Path(normalized_path).name
    full_path_lower = normalized_path.lower()
    path_name_lower = path_name.lower()

    if fnmatch(path_name_lower, "*.env"):
        return True
    if path_name_lower == "runner.env":
        return True
    if fnmatch(path_name_lower, "*.credentials"):
        return True
    if fnmatch(path_name_lower, "*.pem"):
        return True
    if fnmatch(path_name_lower, "*.key"):
        return True
    if "_token" in full_path_lower:
        return True
    if "secret" in full_path_lower:
        return True
    return False


def verify_staged_files(staged_files: list[str]) -> None:
    """Raise when staged files include secret-like names."""
    offending_paths = [path for path in staged_files if _looks_secret(path)]
    if offending_paths:
        raise ExportSecretError(offending_paths)


def verify_zip(zip_path: Path) -> None:
    """Raise when a zip archive includes secret-like names."""
    with ZipFile(zip_path) as archive:
        members = archive.namelist()
    verify_staged_files(members)


_INLINE_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"OPENAI_API_KEY\s*=\s*sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ANTHROPIC_API_KEY\s*=\s*sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?<!no )secret\s*=\s*[\"'][^\"']+[\"']", re.IGNORECASE),
)


def scan_file_for_secrets(path: Path) -> list[str]:
    """Return inline secret-like values found in a text file."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return []
    findings: list[str] = []
    for pattern in _INLINE_SECRET_PATTERNS:
        findings.extend(match.group(0) for match in pattern.finditer(content))
    return findings


def verify_repo_clean(repo_root: Path | None = None) -> tuple[bool, list[str]]:
    """Scan automation files for inline secret patterns."""
    root = repo_root or Path("C:/Fiverr/Fiverr")
    violations: list[str] = []
    for py_file in (root / "automation").rglob("*.py"):
        if not py_file.is_file():
            continue
        matches = scan_file_for_secrets(py_file)
        if matches:
            violations.append(str(py_file))
    return (len(violations) == 0, violations)


if __name__ == "__main__":
    verify_zip(Path(sys.argv[1]))
