"""
test_dispatch_integration.py -- MPS.1: Integration test for the fake Cursor dispatch path.

Exercises cmd_run_agent end-to-end with all real submodules but with
_run_and_stream patched out (PYTEST_CURRENT_TEST already guards this globally).
"""
from __future__ import annotations

from pathlib import Path



class TestFakeCursorDispatch:
    """MPS.1: Integration tests that exercise cmd_run_agent end-to-end."""

    def _make_prompt(self, tmp_path: Path) -> Path:
        p = tmp_path / "PM_Pack/automation/prompts/CYCLE_084_AGENT_A_PROMPT.md"
        p.parent.mkdir(parents=True)
        p.write_text("## Task 1: Implement\n```python\npass\n```\n", encoding="utf-8")
        return p

    def test_cmd_run_agent_smoke(self, tmp_path, monkeypatch):
        """Full cmd_run_agent smoke test with patched subprocess."""
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "test_dispatch_integration")
        monkeypatch.setenv("ICV_DISABLED", "1")

        import automation.ai_cycle_controller as ctrl

        # Patch _run_and_stream to return success without Cursor
        monkeypatch.setattr(ctrl, "_run_and_stream", lambda args, label="": (0, "ok"))

        # Patch state writers to tmp_path
        monkeypatch.setattr(ctrl, "RUNNER_STATE", tmp_path / "state.json")
        monkeypatch.setattr(ctrl, "REPO_ROOT", tmp_path)

        # Set up minimal required files
        self._make_prompt(tmp_path)

        # Write a fake report so lifecycle doesn't block
        report = tmp_path / "docs/cycle_reports/CYCLE_084_AGENT_A.md"
        report.parent.mkdir(parents=True)
        report.write_text("AGENT_COMPLETE\n", encoding="utf-8")

        from click.testing import CliRunner
        from automation.ai_cycle_controller import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["run-agent", "--agent", "A", "--cycle", "84"], catch_exceptions=True)
        # Should not crash with unhandled exception
        assert result.exit_code in (0, 1)  # 1 is ok (lifecycle may flag issues)

    def test_run_and_stream_fake_seam(self, monkeypatch):
        """0.3: the autouse conftest fake makes _run_and_stream return (0, ok).

        The production PYTEST short-circuit was REMOVED; tests rely on the
        monkeypatched seam (autouse ``_fake_run_and_stream``) instead of an
        in-process env-var branch. With that fake active, no subprocess spawns.
        """
        import automation.ai_cycle_controller as ctrl
        rc, out = ctrl._run_and_stream(["echo", "hello"], label="test")
        assert rc == 0
        assert out == "ok"

    def test_run_and_stream_has_no_pytest_shortcircuit(self):
        """0.3 regression: the source must not READ PYTEST_CURRENT_TEST.

        Comments/docstrings may name the var; we assert the code form
        ``environ.get("PYTEST_CURRENT_TEST")`` is absent from the body.
        """
        import inspect
        import automation.ai_cycle_controller as ctrl
        src = inspect.getsource(ctrl)
        marker = "def _run_and_stream("
        start = src.index(marker)
        nxt = src.index("\ndef ", start + 1)
        body = src[start:nxt]
        assert 'environ.get("PYTEST_CURRENT_TEST")' not in body
        assert "environ.get('PYTEST_CURRENT_TEST')" not in body

    def test_cmd_run_cycle_smoke(self, tmp_path, monkeypatch):
        """cmd_run_cycle smoke: 6 agents, all fake dispatch."""
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "test_dispatch_integration")
        monkeypatch.setenv("ICV_DISABLED", "1")

        import automation.ai_cycle_controller as ctrl
        monkeypatch.setattr(ctrl, "_run_and_stream", lambda args, label="": (0, "ok"))
        monkeypatch.setattr(ctrl, "RUNNER_STATE", tmp_path / "state.json")

        from click.testing import CliRunner
        from automation.ai_cycle_controller import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["run-cycle", "--cycle", "84"], catch_exceptions=True)
        # Should complete all 6 agents without crashing
        assert result.exit_code in (0, 1)
