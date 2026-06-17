"""
test_phase1_fixes.py -- Regression tests for Phase 1 critical fixes (H1/H3/C1/C2).
"""
from __future__ import annotations
import subprocess
import pytest


# H1 ---------------------------------------------------------

class TestH1NullPriorityFix:
    def _norm(self, fields):
        from automation.jira_client import _normalise_issue
        return _normalise_issue({"key": "TEST-1", "fields": fields})

    def test_null_priority_no_raise(self):
        assert self._norm({"priority": None, "status": {"name": "To Do"}})["priority"] == "Medium"

    def test_missing_priority_defaults_medium(self):
        assert self._norm({"status": {"name": "To Do"}})["priority"] == "Medium"

    def test_normal_priority_preserved(self):
        assert self._norm({"priority": {"name": "High"}})["priority"] == "High"

    def test_nested_fields_populated(self):
        r = self._norm({"priority": None, "status": {"name": "Done"}, "summary": "S"})
        assert r["status"] == "Done" and r["summary"] == "S"


# H3 ---------------------------------------------------------

class TestH3CursorFlags:
    def _src(self):
        import inspect, automation.cursor_adapter as ca
        return inspect.getsource(ca)

    def test_short_path_has_print(self):
        assert "--print" in self._src(), "cursor_adapter missing --print"

    def test_short_path_has_force(self):
        assert "--force" in self._src(), "cursor_adapter missing --force"

    def test_short_path_has_trust(self):
        assert "--trust" in self._src(), "cursor_adapter missing --trust"

    def test_h3_comment_present(self):
        """Verify the H3 fix comment is present (proves intentional fix, not accidental)."""
        assert "H3 FIX" in self._src()


# C1 ---------------------------------------------------------

class TestC1OwnershipScoping:
    def test_accepts_no_sha(self):
        from automation.run_agent_lifecycle import _get_changed_files
        assert isinstance(_get_changed_files(pre_dispatch_sha=None), list)

    def test_invalid_sha_no_crash(self):
        from automation.run_agent_lifecycle import _get_changed_files
        result = _get_changed_files(pre_dispatch_sha="0" * 40)
        assert isinstance(result, list)

    def test_lifecycle_signature_has_pre_dispatch_sha(self):
        import inspect
        from automation.run_agent_lifecycle import run_post_agent_lifecycle
        assert "pre_dispatch_sha" in inspect.signature(run_post_agent_lifecycle).parameters

    def test_agent_lifecycle_run_signature_has_pre_dispatch_sha(self):
        import inspect
        from automation.run_agent_lifecycle import AgentLifecycle
        assert "pre_dispatch_sha" in inspect.signature(AgentLifecycle.run).parameters


# C2 ---------------------------------------------------------

def _fake_cursor_result():
    from automation.cursor_adapter import AgentRunResult
    from datetime import UTC, datetime
    return AgentRunResult(
        agent="A", status="ok",
        started_at=datetime.now(UTC).isoformat(),
        ended_at=datetime.now(UTC).isoformat(),
        exit_code=0,
    )


def _mock_all(monkeypatch, lifecycle_status, lifecycle_errors=None):
    """Mock out all external calls in cmd_run_agent."""
    from automation.run_agent_lifecycle import AgentLifecycleResult
    from automation.model_gate import ModelGateResult

    # Block real git rev-parse
    orig_run = subprocess.run
    def _safe_run(args, **kwargs):
        if isinstance(args, list) and "rev-parse" in " ".join(str(a) for a in args):
            class _R:
                stdout = "abc1234def\n"
                returncode = 0
            return _R()
        return orig_run(args, **kwargs)
    monkeypatch.setattr("subprocess.run", _safe_run)

    monkeypatch.setattr("automation.ai_cycle_controller._run_and_stream", lambda *a, **k: (0, "ok"))
    monkeypatch.setattr("automation.ai_cycle_controller._run_shell_command", lambda *a, **k: (0, "ok"))
    monkeypatch.setattr("automation.cursor_adapter.run_agent", lambda *a, **k: _fake_cursor_result())
    # Explicitly mock model_gate.check so CI never needs real state files or git remote
    monkeypatch.setattr(
        "automation.model_gate.check",
        lambda **kwargs: ModelGateResult(passed=True),
    )
    monkeypatch.setattr(
        "automation.run_agent_lifecycle.run_post_agent_lifecycle",
        lambda *a, **k: AgentLifecycleResult(
            agent="A", cycle=84, run_id="t", status=lifecycle_status,
            errors=lifecycle_errors or [], commit_sha="abc1234" if lifecycle_status == "COMPLETE" else "",
        )
    )


class TestC2ExitCodeMasking:
    def test_ownership_violation_exits_nonzero(self, monkeypatch):
        """Regression: OWNERSHIP_VIOLATION used to return (exit 0) = counted as DONE."""
        from click.testing import CliRunner
        from automation.ai_cycle_controller import cli
        _mock_all(monkeypatch, "OWNERSHIP_VIOLATION", ["outside scope: ['src/foo.py']"])
        r = CliRunner().invoke(cli, ["run-agent", "--agent", "A", "--cycle", "84"])
        assert r.exit_code != 0, f"Got {r.exit_code}: {r.output[-400:]}"

    def test_validation_failed_exits_nonzero(self, monkeypatch):
        """Regression: VALIDATION_FAILED used to return (exit 0)."""
        from click.testing import CliRunner
        from automation.ai_cycle_controller import cli
        _mock_all(monkeypatch, "VALIDATION_FAILED", ["mypy: 3 errors"])
        monkeypatch.setattr("automation.repair_loop.dispatch_repair", lambda *a, **k: None)
        r = CliRunner().invoke(cli, ["run-agent", "--agent", "B", "--cycle", "84"])
        assert r.exit_code != 0, f"Got {r.exit_code}: {r.output[-400:]}"

    def test_complete_exits_zero(self, monkeypatch):
        """COMPLETE lifecycle must still exit 0."""
        from click.testing import CliRunner
        from automation.ai_cycle_controller import cli
        _mock_all(monkeypatch, "COMPLETE")
        r = CliRunner().invoke(cli, ["run-agent", "--agent", "A", "--cycle", "84"])
        assert r.exit_code == 0, f"Expected 0, got {r.exit_code}: {r.output[-400:]}"

    def test_no_report_exits_nonzero(self, monkeypatch):
        """NO_REPORT must also exit non-zero."""
        from click.testing import CliRunner
        from automation.ai_cycle_controller import cli
        _mock_all(monkeypatch, "NO_REPORT")
        r = CliRunner().invoke(cli, ["run-agent", "--agent", "A", "--cycle", "84"])
        assert r.exit_code != 0
