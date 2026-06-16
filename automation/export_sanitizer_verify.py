"""Verify staged paths and zip members do not expose secrets."""

from __future__ import annotations

import fnmatch
import sys
from pathlib import Path
from zipfile import ZipFile


class ExportSecretError(Exception):
    """Raised when sensitive paths are found in staged files or archive entries."""

    def __init__(self, offending_paths: list[str]) -> None:
        self.offending_paths = offending_paths
        super().__init__(f"Sensitive paths detected: {', '.join(offending_paths)}")


_PATTERNS = ("*.env", "runner.env", "*.credentials", "*.pem", "*.key")


def _is_sensitive(path_value: str) -> bool:
    normalized = path_value.replace("\\", "/")
    lower = normalized.lower()
    if any(fnmatch.fnmatch(lower, pattern) for pattern in _PATTERNS):
        return True
    name = Path(normalized).name.lower()
    return "_token" in lower or "secret" in lower or "_token" in name or "secret" in name


def verify_staged_files(staged_files: list[str]) -> None:
    offending = [path for path in staged_files if _is_sensitive(path)]
    if offending:
        raise ExportSecretError(offending)


def verify_zip(zip_path: Path) -> None:
    offending: list[str] = []
    with ZipFile(zip_path, "r") as archive:
        for member in archive.namelist():
            if _is_sensitive(member):
                offending.append(member)
    if offending:
        raise ExportSecretError(offending)


if __name__ == "__main__":
    verify_zip(Path(sys.argv[1]))
