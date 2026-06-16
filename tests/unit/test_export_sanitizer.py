from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest

from automation.export_sanitizer_verify import ExportSecretError, verify_staged_files, verify_zip


def _write_zip_entry(zip_path: Path, entry_name: str, entry_content: str) -> None:
    with ZipFile(zip_path, "w") as archive:
        archive.writestr(entry_name, entry_content)


def test_verify_staged_files_allows_clean_path() -> None:
    assert verify_staged_files(["automation/prompt_renderer.py"]) is None


@pytest.mark.parametrize(
    "blocked_path",
    [
        "config/.env",
        "artifacts/Build_Token_dump.txt",
        "reports/my_secret_notes.md",
    ],
)
def test_verify_staged_files_blocks_sensitive_path_patterns(blocked_path: str) -> None:
    with pytest.raises(ExportSecretError):
        verify_staged_files([blocked_path])


def test_verify_zip_allows_clean_entries(tmp_path: Path) -> None:
    zip_path = tmp_path / "clean.zip"
    _write_zip_entry(zip_path, "docs/readme.txt", "ok")
    assert verify_zip(zip_path) is None


def test_verify_zip_blocks_sensitive_entries(tmp_path: Path) -> None:
    zip_path = tmp_path / "blocked.zip"
    _write_zip_entry(zip_path, "secrets/runner.env", "bad")
    with pytest.raises(ExportSecretError):
        verify_zip(zip_path)
