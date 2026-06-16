from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest
from automation.export_sanitizer_verify import ExportSecretError, verify_staged_files, verify_zip


def test_verify_staged_files_clean_returns_none() -> None:
    assert verify_staged_files(["automation/foo.py"]) is None


def test_verify_staged_files_env_file_raises() -> None:
    with pytest.raises(ExportSecretError):
        verify_staged_files([r"C:\AI_Runner\secrets\runner.env"])


def test_verify_staged_files_token_file_raises() -> None:
    with pytest.raises(ExportSecretError):
        verify_staged_files(["MY_GITHUB_TOKEN"])


def test_verify_zip_clean_zip_returns_none(tmp_path: Path) -> None:
    archive_path = tmp_path / "clean.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("automation/test.py", "print('ok')")
    assert verify_zip(archive_path) is None


def test_verify_zip_secret_in_zip_raises(tmp_path: Path) -> None:
    archive_path = tmp_path / "secret.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("runner.env", "TOKEN=1")
    with pytest.raises(ExportSecretError):
        verify_zip(archive_path)
