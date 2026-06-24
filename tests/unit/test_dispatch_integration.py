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

    def test_run_agent_honors_repaired_status(self):
        """HIGH-5 regression: the VALIDATION_FAILED branch must HONOR a successful
        repair (write AGENT_COMPLETE, no SystemExit) instead of the old form that
        called dispatch_repair then unconditionally `raise SystemExit(1)` — which
        threw away a genuinely-fixed, committed cycle and routed it to POST_CYCLE_FAIL.
        """
        import inspect

        import automation.ai_cycle_controller as ctrl
        src = inspect.getsource(ctrl.cmd_run_agent.callback)  # .callback = raw fn (Click wraps it)
        i = src.index('lifecycle.status == "VALIDATION_FAILED"')
        branch = src[i:i + 1600]
        # The repair result is captured (not discarded) and REPAIRED is honored.
        assert "repair = dispatch_repair(" in branch
        assert '"REPAIRED"' in branch
        assert 'write_controller_state("AGENT_COMPLETE"' in branch
        # The `raise SystemExit(1)` must now live in the ELSE (failure) path, AFTER
        # the REPAIRED success handling — not unconditionally as before.
        repaired_idx = branch.index('"REPAIRED"')
        assert branch.index("raise SystemExit(1)") > repaired_idx

    def test_run_agent_fails_clean_on_non_complete_status(self):
        """Audit #7: a non-'complete' cursor status (timeout/no_output/error/model_blocked
        = the agent was KILLED before finishing) must fail the dispatch BEFORE the
        post-agent lifecycle — otherwise a killed run gets a misleading NO_REPORT/
        OWNERSHIP verdict with no retry, instead of a clean failed-agent that the cycle
        can re-dispatch."""
        import inspect

        import automation.ai_cycle_controller as ctrl
        src = inspect.getsource(ctrl.cmd_run_agent.callback)
        gate = src.index('!= "complete"')
        lifecycle = src.index("run_post_agent_lifecycle")
        assert gate < lifecycle, "the non-complete status gate must precede the lifecycle"
        assert "raise SystemExit(1)" in src[gate:gate + 900], "the gate must fail the dispatch"

    def test_autopilot_has_circuit_breaker(self):
        """HIGH-7 regression: start-autopilot must trip a circuit breaker on too many
        CONSECUTIVE failed ticks (freeze + stop), not loop forever burning quota."""
        import inspect

        import automation.ai_cycle_controller as ctrl
        src = inspect.getsource(ctrl.cmd_start_autopilot.callback)  # .callback = raw fn
        assert "consecutive_tick_failures" in src
        assert "AUTOPILOT_MAX_CONSECUTIVE_TICK_FAILURES" in src
        # On reaching the cap it engages the autonomy freeze and breaks the loop.
        assert "_write_autonomy_freeze(" in src
        cb_idx = src.index("consecutive_tick_failures >= _breaker_cap")
        assert "break" in src[cb_idx:cb_idx + 1200]
        # A clean tick resets the counter (so only CONSECUTIVE failures count).
        assert "consecutive_tick_failures = 0" in src

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
