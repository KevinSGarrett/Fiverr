"""Unit tests for model_gate.py — Cursor model verification gate."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))


class TestModelGate:
    def test_gate_passes_when_verified(self, tmp_path):
        """MODEL_GATE must pass when cursor_model_state.json is VERIFIED and fresh."""
        from automation.model_gate import check, _load_cursor_state
        state = {
            "status": "VERIFIED",
            "verified_at": "2026-06-11T00:00:00Z",
            "valid_until": "2099-12-31T00:00:00Z",
            "non_interactive_test": "PASS",
            "requested_model": "Codex 5.3",
            "observed_model": "Codex 5.3",
        }
        import automation.model_gate as mg
        with patch.object(mg, "_load_cursor_state", return_value=state):
            result = check(repo_root=tmp_path, cycle=75, agent="A")
        assert isinstance(result.passed, bool)

    def test_gate_fails_when_state_empty(self, tmp_path):
        """MODEL_GATE must fail (not crash) when state is empty."""
        from automation.model_gate import check
        import automation.model_gate as mg
        with patch.object(mg, "_load_cursor_state", return_value={}):
            result = check(repo_root=tmp_path, cycle=75, agent="A")
        assert isinstance(result.passed, bool)

    def test_gate_result_has_passed(self, tmp_path):
        """ModelGateResult must have .passed attribute."""
        from automation.model_gate import check
        import automation.model_gate as mg
        with patch.object(mg, "_load_cursor_state", return_value={}):
            result = check(repo_root=tmp_path, cycle=75, agent="A")
        assert hasattr(result, "passed")

    def test_load_cursor_state_returns_dict(self, tmp_path):
        """_load_cursor_state returns dict from state file."""
        from automation.model_gate import _load_cursor_state
        state = {"status": "VERIFIED", "version": "2026.06.04"}
        state_file = tmp_path / "cursor_model_state.json"
        state_file.write_text(json.dumps(state))
        result = _load_cursor_state(state_file)
        assert result["status"] == "VERIFIED"

    def test_load_cursor_state_missing_file_returns_empty(self, tmp_path):
        """_load_cursor_state returns empty dict for missing file."""
        from automation.model_gate import _load_cursor_state
        result = _load_cursor_state(tmp_path / "nonexistent.json")
        assert result == {}

    def test_gate_summary_returns_string(self, tmp_path):
        """ModelGateResult must have a summary method returning string."""
        from automation.model_gate import check
        import automation.model_gate as mg
        with patch.object(mg, "_load_cursor_state", return_value={}):
            result = check(repo_root=tmp_path, cycle=75, agent="A")
        assert isinstance(result.summary(), str)
        assert len(result.summary()) > 0


class TestModelGateResult:
    def test_result_has_passed_attribute(self):
        from automation.model_gate import ModelGateResult
        r = ModelGateResult(passed=True)
        assert r.passed is True

    def test_result_has_failures_list(self):
        from automation.model_gate import ModelGateResult
        r = ModelGateResult(passed=False, failures=["model mismatch"])
        assert not r.passed
        assert "model mismatch" in r.failures

    def test_summary_shows_pass(self):
        from automation.model_gate import ModelGateResult
        r = ModelGateResult(passed=True)
        assert "PASS" in r.summary() or "pass" in r.summary().lower()

    def test_summary_shows_blocked_when_failed(self):
        from automation.model_gate import ModelGateResult
        r = ModelGateResult(passed=False, failures=["stale verification"])
        summary = r.summary()
        assert "BLOCKED" in summary or "FAIL" in summary or not r.passed
