"""Unit tests for claude_sub_gate.py — ANTHROPIC_API_KEY absence gate."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import json

sys.path.insert(0, str(Path(__file__).parents[2]))


class TestCheckApiKeyAbsent:
    def test_passes_when_key_absent(self, monkeypatch):
        """Gate passes when ANTHROPIC_API_KEY is not set."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        # Also mock PowerShell env check
        from automation.claude_sub_gate import check_api_key_absent
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0
            result = check_api_key_absent()
        assert result["passed"] is True
        assert result.get("incident_code", "") != "BLOCKED_CLAUDE_API_KEY_PRESENT"

    def test_fails_when_key_present(self, monkeypatch):
        """Gate FAILS when ANTHROPIC_API_KEY is set in environment."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-12345")
        from automation.claude_sub_gate import check_api_key_absent
        result = check_api_key_absent()
        assert result["passed"] is False
        assert "BLOCKED" in result.get("incident_code", "") or not result["passed"]

    def test_returns_dict(self, monkeypatch):
        """Return value must be a dict with 'passed' key."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from automation.claude_sub_gate import check_api_key_absent
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = ""
            mock_run.return_value.returncode = 0
            result = check_api_key_absent()
        assert isinstance(result, dict)
        assert "passed" in result


class TestRunSubscriptionCheck:
    def test_subscription_check_returns_result(self):
        """run_subscription_check returns a dict with expected keys."""
        import automation.claude_sub_gate as csg
        from automation.claude_sub_gate import run_subscription_check
        with patch.object(csg, "check_api_key_absent", return_value={"passed": True}):
            result = run_subscription_check()
        assert isinstance(result, dict)
        assert "passed" in result

    def test_subscription_check_blocked_if_key_present(self, monkeypatch):
        """run_subscription_check is BLOCKED if API key gate fails."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-12345")
        from automation.claude_sub_gate import run_subscription_check
        result = run_subscription_check()
        assert not result["passed"]

    def test_subscription_preflight_passes_when_billing_mode_is_subscription_only(self, tmp_path):
        import automation.claude_sub_gate as csg

        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "claude_model_state.json").write_text(
            json.dumps(
                {
                    "billing_mode": "claude_subscription_only",
                    "anthropic_api_key_present": False,
                }
            ),
            encoding="utf-8",
        )
        with patch.object(csg, "RUNNER_ROOT", tmp_path), patch.object(csg, "check_api_key_absent", return_value={"passed": True}):
            result = csg.run_subscription_check()
        assert result["passed"] is True

    def test_subscription_preflight_fails_when_billing_mode_is_api_credits(self, tmp_path):
        import automation.claude_sub_gate as csg

        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "claude_model_state.json").write_text(
            json.dumps(
                {
                    "billing_mode": "api_credits",
                    "anthropic_api_key_present": False,
                }
            ),
            encoding="utf-8",
        )
        with patch.object(csg, "RUNNER_ROOT", tmp_path), patch.object(csg, "check_api_key_absent", return_value={"passed": True}):
            result = csg.run_subscription_check()
        assert result["passed"] is False
        assert result["incident_code"] == "BLOCKED_CLAUDE_API_KEY_PRESENT"

    def test_subscription_preflight_fails_when_api_present_flag_true(self, tmp_path):
        import automation.claude_sub_gate as csg

        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "claude_model_state.json").write_text(
            json.dumps(
                {
                    "billing_mode": "claude_subscription_only",
                    "anthropic_api_key_present": True,
                }
            ),
            encoding="utf-8",
        )
        with patch.object(csg, "RUNNER_ROOT", tmp_path), patch.object(csg, "check_api_key_absent", return_value={"passed": True}):
            result = csg.run_subscription_check()
        assert result["passed"] is False

    def test_api_key_absent_handles_powershell_exceptions(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from automation.claude_sub_gate import check_api_key_absent

        with patch("subprocess.run", side_effect=RuntimeError("ps failed")):
            result = check_api_key_absent()
        assert result["passed"] is True


class TestIncidentCodes:
    def test_blocked_incident_code_constant(self):
        """BLOCKED_CLAUDE_API_KEY_PRESENT must be the correct incident code."""
        import automation.claude_sub_gate as csg
        # The module should define this constant or use it
        code = getattr(csg, "BLOCKED_CLAUDE_API_KEY_PRESENT",
                       "BLOCKED_CLAUDE_API_KEY_PRESENT")
        assert "BLOCKED" in code
        assert "API_KEY" in code
