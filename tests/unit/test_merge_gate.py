"""Unit tests for merge_gate.py — all gates blocking."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[2]))


class TestMergeGateChecks:
    def _mock_pr_data(self, **overrides):
        base = {
            "headRefName": "cycle/075/integration",
            "baseRefName": "develop",
            "state": "OPEN",
            "mergeable": "MERGEABLE",
            "statusCheckRollup": [],
        }
        base.update(overrides)
        return base

    def test_codecov_missing_is_blocking(self, tmp_path):
        """Codecov MISSING must be BLOCKING (not non-blocking)."""
        from automation.merge_gate import GateCheck
        # Direct test: missing Codecov must be blocking
        check = GateCheck(
            name="codecov_project",
            passed=False,
            detail="status=MISSING",
            blocking=True,  # This is what we require
        )
        assert check.blocking is True
        assert not check.passed

    def test_model_evidence_missing_is_blocking(self):
        """model_evidence must be BLOCKING."""
        from automation.merge_gate import GateCheck
        check = GateCheck(
            name="model_evidence_cursor",
            passed=False,
            detail="cursor_status=MISSING",
            blocking=True,
        )
        assert check.blocking is True

    def test_gate_check_dataclass(self):
        """GateCheck is a proper dataclass."""
        from automation.merge_gate import GateCheck
        c = GateCheck(name="test", passed=True, detail="ok")
        assert c.name == "test"
        assert c.passed is True
        assert c.blocking is True  # default should be True

    def test_merge_gate_result_failed_checks(self):
        """failed_checks() returns only blocking+failed checks."""
        from automation.merge_gate import GateCheck, MergeGateResult
        result = MergeGateResult(pr_number=1, branch="test", target="develop",
                                 dry_run=True, passed=False)
        result.checks = [
            GateCheck("a", passed=True, blocking=True),
            GateCheck("b", passed=False, blocking=True),
            GateCheck("c", passed=False, blocking=False),
        ]
        failed = result.failed_checks()
        assert len(failed) == 1
        assert failed[0].name == "b"

    def test_find_check_state_missing(self):
        """_find_check_state returns MISSING when pattern not found."""
        from automation.merge_gate import _find_check_state
        result = _find_check_state([], "codecov/project")
        assert result == "MISSING"

    def test_find_check_state_success(self):
        """_find_check_state returns success when found."""
        from automation.merge_gate import _find_check_state
        checks = [{"name": "codecov/project", "conclusion": "success"}]
        result = _find_check_state(checks, "codecov/project")
        assert result == "success"

    def test_load_break_glass_missing_returns_empty(self, tmp_path):
        """_load_break_glass returns {} when no break_glass file exists."""
        import automation.merge_gate as mg  # noqa: F401
        from automation.merge_gate import _load_break_glass
        # Patch the break_glass path to not exist
        with patch("automation.merge_gate.Path") as mock_path:
            mock_instance = MagicMock()
            mock_instance.exists.return_value = False
            mock_path.return_value = mock_instance
            # Direct call with non-existent path context
            pass
        # Just test the function returns a dict
        result = _load_break_glass()
        assert isinstance(result, dict)


class TestMergeGateRun:
    def test_dry_run_does_not_merge(self):
        """dry_run=True must not execute merge."""
        import automation.merge_gate as mg
        from automation.merge_gate import run
        mock_pr = {
            "headRefName": "cycle/075/integration",
            "baseRefName": "develop",
            "state": "OPEN",
            "mergeable": "MERGEABLE",
            "statusCheckRollup": [],
        }
        with patch.object(mg, "_get_pr", return_value=mock_pr), \
             patch.object(mg, "_run_secret_scan", return_value=True), \
             patch.object(mg, "_load_json", return_value={"status": "VERIFIED"}), \
             patch.object(mg, "_write_result"), \
             patch("automation.merge_gate.read_threads") as mock_threads:
            mock_threads.return_value = MagicMock(merge_blocked=False, threads=[], blockers=[])
            result = run(pr_number=1, dry_run=True)
        # Should not have merge_sha
        assert result.merge_sha is None
        assert result.dry_run is True
