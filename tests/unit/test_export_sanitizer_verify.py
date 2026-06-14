from __future__ import annotations

import zipfile
from pathlib import Path

from automation import export_sanitizer_verify
from automation.export_sanitizer_verify import verify_zip


def _write_zip(path: Path, members: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in members.items():
            zf.writestr(name, content)


def test_clean_zip_passes(tmp_path: Path) -> None:
    zpath = tmp_path / "clean.zip"
    _write_zip(zpath, {"docs/report.md": "ok", "logs/run.txt": "ok"})
    clean, violations = verify_zip(str(zpath))
    assert clean is True
    assert violations == []


def test_zip_with_env_file_fails(tmp_path: Path) -> None:
    zpath = tmp_path / "bad_env.zip"
    _write_zip(zpath, {".env": "SECRET=abc"})
    clean, violations = verify_zip(str(zpath))
    assert clean is False
    assert any(".env" in violation.lower() for violation in violations)


def test_zip_with_runner_env_fails(tmp_path: Path) -> None:
    zpath = tmp_path / "bad_runner.zip"
    _write_zip(zpath, {"secrets/runner.env": "JIRA_API_TOKEN=abc"})
    clean, violations = verify_zip(str(zpath))
    assert clean is False
    assert any("runner.env" in violation.lower() for violation in violations)


def test_zip_with_credentials_file_fails(tmp_path: Path) -> None:
    zpath = tmp_path / "bad_creds.zip"
    _write_zip(zpath, {"actions-runner/.credentials": "token"})
    clean, violations = verify_zip(str(zpath))
    assert clean is False
    assert any(".credentials" in violation.lower() for violation in violations)


def test_main_returns_usage_when_zip_missing() -> None:
    assert export_sanitizer_verify.main([]) == 1


def test_main_accepts_flag_style_zip(tmp_path: Path) -> None:
    zpath = tmp_path / "clean_flag.zip"
    _write_zip(zpath, {"ok.txt": "ok"})
    assert export_sanitizer_verify.main(["--zip", str(zpath)]) == 0


def test_main_returns_nonzero_for_sensitive_archive(tmp_path: Path) -> None:
    zpath = tmp_path / "dirty.zip"
    _write_zip(zpath, {"path/JIRA_API_TOKEN=abc.txt": "leak"})
    assert export_sanitizer_verify.main([str(zpath)]) == 1
