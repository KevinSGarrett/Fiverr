"""Unit tests for secret_guard.py — secret scanning gate."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[2]))


class TestSecretGuard:
    def test_scan_clean_file(self, tmp_path):
        """Clean file with no secrets passes."""
        from automation.secret_guard import scan_file
        clean_file = tmp_path / "clean.py"
        clean_file.write_text('print("hello world")\nx = 1 + 1\n')
        result = scan_file(clean_file)
        assert result.passed, f"Clean file should pass. Findings: {result.findings}"

    def test_scan_file_with_github_token(self, tmp_path):
        """File with GitHub token literal fails."""
        from automation.secret_guard import scan_file
        bad_file = tmp_path / "bad.py"
        token = "gh" + "p_" + "abcdefghijklmnopqrstuvwxyz123456789"
        bad_file.write_text(f'token = "{token}"\n')
        result = scan_file(bad_file)
        assert not result.passed, "File with GitHub token should fail"

    def test_scan_file_with_api_key(self, tmp_path):
        """File with ANTHROPIC_API_KEY= fails."""
        from automation.secret_guard import scan_file
        bad_file = tmp_path / "bad.py"
        key_name = "ANTHROPIC_" + "API_KEY"
        key_value = "sk-" + "ant-test123"
        bad_file.write_text(f'{key_name} = "{key_value}"\n')
        result = scan_file(bad_file)
        assert not result.passed, "File with API key should fail"

    def test_scan_file_with_env_file(self, tmp_path):
        """Actual .env file with token values fails."""
        from automation.secret_guard import scan_file
        env_file = tmp_path / ".env"
        env_file.write_text("GH_AUTOMATION_TOKEN=" + "gh" + "p_realtoken12345\n")
        result = scan_file(env_file)
        assert not result.passed

    def test_scan_result_has_findings(self, tmp_path):
        """ScanResult.findings must be a list."""
        from automation.secret_guard import scan_file
        clean = tmp_path / "test.py"
        clean.write_text("x = 1\n")
        result = scan_file(clean)
        assert hasattr(result, "findings")
        assert isinstance(result.findings, list)

    def test_scan_result_has_passed(self, tmp_path):
        """ScanResult must have .passed attribute."""
        from automation.secret_guard import scan_file
        clean = tmp_path / "test.py"
        clean.write_text("x = 1\n")
        result = scan_file(clean)
        assert hasattr(result, "passed")

    def test_scan_staged_returns_result(self, tmp_path):
        """scan_staged returns a ScanResult even if no staged files."""
        from automation.secret_guard import scan_staged
        result = scan_staged(tmp_path)
        assert hasattr(result, "passed")
        assert hasattr(result, "findings")


class TestSecretPatterns:
    """Verify that the secret guard catches the required patterns."""

    def _check_pattern(self, content: str, should_fail: bool, tmp_path: Path) -> None:
        from automation.secret_guard import scan_file
        f = tmp_path / "test_file.py"
        f.write_text(content)
        result = scan_file(f)
        if should_fail:
            assert not result.passed, f"Should have caught secret in: {content[:50]}"
        else:
            assert result.passed, f"False positive for: {content[:50]}"

    def test_catches_github_token(self, tmp_path):
        token = "gh" + "p_" + "aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456"
        self._check_pattern(f'x = "{token}"', True, tmp_path)

    def test_catches_atlassian_token(self, tmp_path):
        # Real Atlassian tokens: ATATT3x prefix + 20+ alphanumeric chars
        token = "ATAT" + "T3x" + "FfGFHhIiJjKk"
        self._check_pattern(f'x = "{token}"', True, tmp_path)

    def test_catches_anthropic_key(self, tmp_path):
        key_name = "ANTHROPIC_" + "API_KEY"
        key_value = "sk-" + "ant-api03-xxx"
        self._check_pattern(f'{key_name} = "{key_value}"', True, tmp_path)

    def test_ignores_comment_about_key(self, tmp_path):
        # A comment explaining where to PUT the key should not trip the guard
        self._check_pattern('# Set ANTHROPIC_API_KEY in runner.env\n', False, tmp_path)

    def test_ignores_empty_env_assignment(self, tmp_path):
        self._check_pattern('ANTHROPIC_API_KEY=\n', False, tmp_path)


def test_scan_staged_detects_dangerous_file_and_secret_content(tmp_path: Path) -> None:
    from automation.secret_guard import scan_staged

    (tmp_path / ".env").write_text("KEY=value", encoding="utf-8")
    token = "gh" + "p_" + "abcdefghijklmnopqrstuvwxyz123456789"
    (tmp_path / "safe.py").write_text(f'token = "{token}"', encoding="utf-8")
    with patch("automation.secret_guard.subprocess.run") as run:
        run.return_value = MagicMock(stdout=".env\nsafe.py\n")
        result = scan_staged(tmp_path)
    assert result.passed is False
    assert ".env" in result.dangerous_files
    assert any("GitHub token" in item for item in result.findings)


def test_scan_working_tree_flags_dangerous_paths(tmp_path: Path) -> None:
    from automation.secret_guard import scan_working_tree

    with patch("automation.secret_guard.subprocess.run") as run:
        run.return_value = MagicMock(stdout=" M .env\n M src/app.py\n")
        result = scan_working_tree(tmp_path)
    assert result.passed is False
    assert ".env" in result.dangerous_files


def test_scan_file_missing_path_returns_default_pass(tmp_path: Path) -> None:
    from automation.secret_guard import scan_file

    result = scan_file(tmp_path / "missing.py")
    assert result.passed is True
    assert result.findings == []


def test_secret_guard_result_summary_for_failures() -> None:
    from automation.secret_guard import SecretGuardResult

    result = SecretGuardResult(
        passed=False,
        findings=["a.py: GitHub token"],
        dangerous_files=[".env"],
    )
    text = result.summary()
    assert "SECRET GUARD FAIL" in text
    assert "DANGEROUS FILE: .env" in text
