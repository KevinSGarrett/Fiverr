from __future__ import annotations

from pathlib import Path

from automation.export_sanitizer_verify import scan_file_for_secrets, verify_repo_clean


def test_export_sanitizer_import() -> None:
    assert scan_file_for_secrets is not None
    assert verify_repo_clean is not None


def test_scan_finds_no_secrets_in_automation_dir() -> None:
    automation_dir = Path("C:/Fiverr/Fiverr/automation")
    violations: list[str] = []
    for path in automation_dir.rglob("*.py"):
        violations.extend(scan_file_for_secrets(path))
    assert violations == []


def test_scan_clean_test_file_returns_empty(tmp_path: Path) -> None:
    clean = tmp_path / "clean.txt"
    clean.write_text("hello\nno secret here\n", encoding="utf-8")
    assert scan_file_for_secrets(clean) == []


def test_scan_file_with_fake_key_returns_violation(tmp_path: Path) -> None:
    bad = tmp_path / "bad.txt"
    bad.write_text("OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz1234567890\n", encoding="utf-8")
    assert scan_file_for_secrets(bad)


def test_repo_clean_check_completes() -> None:
    clean, violations = verify_repo_clean()
    assert isinstance(clean, bool)
    assert isinstance(violations, list)
