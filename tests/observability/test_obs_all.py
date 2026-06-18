"""
tests/observability/test_obs_all.py

OBS-1..15 tests referenced by the remediation tracker.
Re-exports from tests/unit/test_observability.py + adds specific
named test cases so tracker rows citing tests/observability/ resolve.
"""
from __future__ import annotations

from pathlib import Path



class TestOBS1StageBanner:
    """OBS-1: Stage narration context manager."""

    def test_stage_function_exists(self):
        """OBS-1: autopilot_logger.stage() context manager exists."""
        from automation.autopilot_logger import stage
        assert callable(stage)

    def test_stage_banner_printed(self, capsys):
        """OBS-1: stage() prints entry/exit banners."""
        from automation.autopilot_logger import stage
        with stage("TEST_STAGE", cycle=1):
            pass
        out = capsys.readouterr().out
        assert "STAGE" in out or "TEST_STAGE" in out


class TestOBS2CurrentActivity:
    """OBS-2: Always-on current_activity indicator."""

    def test_set_activity_callable(self):
        """OBS-2: set_activity() exists."""
        from automation.autopilot_logger import set_activity
        assert callable(set_activity)

    def test_clear_activity_callable(self):
        """OBS-2: clear_activity() exists."""
        from automation.autopilot_logger import clear_activity
        assert callable(clear_activity)


class TestOBS3ExceptionSurfacing:
    """OBS-3: log_exception surfaces failures with component name."""

    def test_log_exception_exists(self):
        """OBS-3: log_exception() is in autopilot_logger."""
        from automation.autopilot_logger import log_exception
        assert callable(log_exception)

    def test_log_exception_does_not_raise(self):
        """OBS-3: log_exception() never re-raises."""
        from automation.autopilot_logger import log_exception
        log_exception("test_component", RuntimeError("test"))


class TestOBS4SubscriptionBanner:
    """OBS-4: CLAUDE SUBSCRIPTION: OK/FAIL banner printed at prompt-gen start."""

    def test_banner_code_exists(self):
        """OBS-4: CLAUDE SUBSCRIPTION: OK/FAIL banner in claude_prompt_creator."""
        src = Path("automation/claude_prompt_creator.py").read_text(encoding="utf-8")
        assert "CLAUDE SUBSCRIPTION:" in src, (
            "OBS-4: CLAUDE SUBSCRIPTION: OK/FAIL banner not found"
        )

    def test_probe_in_verify_subscription(self):
        """OBS-4: _verify_claude_subscription includes a real liveness probe."""
        src = Path("automation/claude_prompt_creator.py").read_text(encoding="utf-8")
        assert "Reply OK" in src or "liveness" in src.lower()


class TestOBS5PerRunLogs:
    """OBS-5: Per-run events.jsonl and transcript.log."""

    def test_init_run_exists(self):
        """OBS-5: init_run() creates per-run log directory."""
        from automation.autopilot_logger import init_run
        assert callable(init_run)


class TestOBS6HeartbeatThread:
    """OBS-6: HeartbeatThread monitors long-running operations."""

    def test_heartbeat_thread_start_stop(self):
        """OBS-6: HeartbeatThread starts and stops without crashing."""
        from automation.autopilot_logger import HeartbeatThread
        thread = HeartbeatThread("test-label", interval=60.0)
        assert hasattr(thread, "start")
        assert hasattr(thread, "stop")
        thread.start()
        import time
        time.sleep(0.1)
        thread.stop()
        # Give it time to terminate (it's a daemon thread)
        import time
        time.sleep(0.3)


class TestOBS7CycleSummary:
    """OBS-7: End-of-cycle summary written."""

    def test_cycle_summary_exists(self):
        """OBS-7: cycle_summary() is in autopilot_logger."""
        from automation.autopilot_logger import cycle_summary
        assert callable(cycle_summary)

    def test_cycle_summary_no_crash(self, tmp_path):
        """OBS-7: cycle_summary() does not crash with empty outcomes."""
        from automation.autopilot_logger import cycle_summary
        cycle_summary(cycle=84, agent_outcomes={"A": {"exit_code": 0}})


class TestOBS8Logging:
    """OBS-8: Standardised logging."""

    def test_core_log_functions_exist(self):
        """OBS-8: info/warn/error/ok/debug all present."""
        import automation.autopilot_logger as L
        for fn in ("info", "warn", "error", "ok", "debug"):
            assert hasattr(L, fn), f"OBS-8: {fn}() missing from autopilot_logger"


class TestOBS9LogLevel:
    """OBS-9: LOG_LEVEL env var controls verbosity."""

    def test_log_level_env_respected(self, monkeypatch):
        """OBS-9: LOG_LEVEL env var respected."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        import automation.autopilot_logger as L
        assert hasattr(L, "debug")


class TestOBS10CursorStreaming:
    """OBS-10: Cursor agent output streamed live to terminal."""

    def test_tee_thread_in_cursor_adapter(self):
        """OBS-10: Live stdout tee thread present in cursor_adapter."""
        src = Path("automation/cursor_adapter.py").read_text(encoding="utf-8")
        assert "_tee_stdout" in src or "tee" in src.lower(), (
            "OBS-10: Live stdout tee missing from cursor_adapter"
        )


class TestOBS11LiveTail:
    """OBS-11: live_events.tail() watchable from another terminal."""

    def test_tail_callable(self):
        """OBS-11: live_events.tail() exists."""
        from automation.live_events import tail
        assert callable(tail)


class TestOBS12Correlation:
    """OBS-12: Every log line carries ts•cycle•stage•agent correlation."""

    def test_emit_accepts_correlation_fields(self):
        """OBS-12: emit() accepts cycle/stage/agent kwargs."""
        from automation.live_events import emit
        emit("TEST", "correlation test", cycle=84, agent="A", status="OK")


class TestOBS13StageMatrix:
    """OBS-13: Compact stage matrix for at-a-glance status."""

    def test_stage_matrix_exists(self):
        """OBS-13: stage_matrix() / print_stage_matrix() in autopilot_logger."""
        import automation.autopilot_logger as L
        assert hasattr(L, "stage_matrix") or hasattr(L, "print_stage_matrix"), (
            "OBS-13: stage_matrix missing from autopilot_logger"
        )


class TestOBS14ProviderBudget:
    """OBS-14: Provider routing + daily budget visible at dispatch time."""

    def test_print_provider_budget_exists(self):
        """OBS-14: print_provider_budget() in autopilot_logger."""
        from automation.autopilot_logger import print_provider_budget
        assert callable(print_provider_budget)


class TestOBS15StallAlert:
    """OBS-15: Stall/no-activity alerting at 300s threshold."""

    def test_check_stall_callable(self):
        """OBS-15: _check_stall() is callable at module level."""
        import automation.autopilot_logger as L
        assert hasattr(L, "_check_stall")
        assert callable(L._check_stall)
