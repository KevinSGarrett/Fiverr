"""Unit tests for secret_guard.py — secret scanning gate."""
from __future__ import annotations

import sys
from pathlib import Path

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
        bad_file.write_text('token = "ghp_abcdefghijklmnopqrstuvwxyz123456789"\n')
        result = scan_file(bad_file)
        assert not result.passed, "File with GitHub token should fail"

    def test_scan_file_with_api_key(self, tmp_path):
        """File with ANTHROPIC_API_KEY= fails."""
        from automation.secret_guard import scan_file
        bad_file = tmp_path / "bad.py"
        bad_file.write_text('ANTHROPIC_API_KEY = "sk-ant-test123"\n')
        result = scan_file(bad_file)
        assert not result.passed, "File with API key should fail"

    def test_scan_file_with_env_file(self, tmp_path):
        """Actual .env file with token values fails."""
        from automation.secret_guard import scan_file
        env_file = tmp_path / ".env"
        env_file.write_text("GH_AUTOMATION_TOKEN=ghp_realtoken12345\n")
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
        self._check_pattern('x = "ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456"', True, tmp_path)

    def test_catches_atlassian_token(self, tmp_path):
        # Real Atlassian tokens: ATATT3x prefix + 20+ alphanumeric chars
        self._check_pattern('x = "ATATT3xFfGFHhIiJjKk"', True, tmp_path)

    def test_catches_anthropic_key(self, tmp_path):
        self._check_pattern('ANTHROPIC_API_KEY = "sk-ant-api03-xxx"', True, tmp_path)

    def test_ignores_comment_about_key(self, tmp_path):
        # A comment explaining where to PUT the key should not trip the guard
        self._check_pattern('# Set ANTHROPIC_API_KEY in runner.env\n', False, tmp_path)

    def test_ignores_empty_env_assignment(self, tmp_path):
        self._check_pattern('ANTHROPIC_API_KEY=\n', False, tmp_path)
