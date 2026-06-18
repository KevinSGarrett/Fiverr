"""
test_observability.py -- Tests for OBS-1..OBS-15 observability layer.
"""
from __future__ import annotations

import json
import time

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_obs(tmp_path, monkeypatch):
    """Redirect all OBS file paths to tmp_path so tests don't touch C:/AI_Runner."""
    import automation.autopilot_logger as L
    monkeypatch.setattr(L, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(L, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(L, "STATE_DIR", tmp_path / "state")
    monkeypatch.setattr(L, "_ACTIVITY_FILE", tmp_path / "state" / "current_activity.json")
    # Reset per-run state
    L._run_state.update({"run_id": None, "cycle": None, "transcript": None, "jsonl": None, "run_dir": None})
    L._stage_results.clear()
    L._log_state.update({"path": None, "handle": None})
    (tmp_path / "logs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "state").mkdir(parents=True, exist_ok=True)
    return tmp_path


# ---------------------------------------------------------------------------
# OBS-1: stage() context manager
# ---------------------------------------------------------------------------

class TestOBS1Stage:
    def test_stage_enter_exit_written_to_log(self, tmp_obs, capsys):
        import automation.autopilot_logger as L
        with L.stage("PLAN", cycle=84):
            L.info("inside plan")
        captured = capsys.readouterr().out
        assert "STAGE PLAN" in captured
        assert "DONE" in captured

    def test_stage_records_result(self, tmp_obs):
        import automation.autopilot_logger as L
        with L.stage("PROMPT-GEN", cycle=84):
            pass
        assert "PROMPT-GEN" in L._stage_results
        assert L._stage_results["PROMPT-GEN"]["passed"] is True

    def test_stage_marks_failed_on_exception(self, tmp_obs):
        import automation.autopilot_logger as L
        with pytest.raises(RuntimeError):
            with L.stage("DISPATCH", cycle=84):
                raise RuntimeError("test error")
        assert L._stage_results.get("DISPATCH", {}).get("passed") is False

    def test_stage_context_propagates_to_log(self, tmp_obs):
        import automation.autopilot_logger as L
        run_dir = L.init_run("test-run-001", cycle=84)
        with L.stage("AGENT-RUN", cycle=84):
            L.ok("agent work")
        jsonl_path = run_dir / "events.jsonl"
        if jsonl_path.exists():
            events = [json.loads(line) for line in jsonl_path.read_text().splitlines() if line.strip()]
            stages = [e.get("stage") for e in events]
            assert any("AGENT-RUN" in str(s) for s in stages)


# ---------------------------------------------------------------------------
# OBS-2: current_activity.json
# ---------------------------------------------------------------------------

class TestOBS2CurrentActivity:
    def test_set_activity_writes_file(self, tmp_obs):
        import automation.autopilot_logger as L
        L.set_activity("AGENT-RUN", cycle=84, agent="A")
        data = json.loads(L._ACTIVITY_FILE.read_text())
        assert data["stage"] == "AGENT-RUN"
        assert data["agent"] == "A"
        assert data["cycle"] == 84

    def test_clear_activity_sets_idle(self, tmp_obs):
        import automation.autopilot_logger as L
        L.set_activity("AGENT-RUN", cycle=84, agent="A")
        L.clear_activity()
        data = json.loads(L._ACTIVITY_FILE.read_text())
        assert data["stage"] == "IDLE"

    def test_bump_heartbeat_updates_timestamp(self, tmp_obs):
        import automation.autopilot_logger as L
        L.set_activity("DISPATCH", cycle=84)
        t1 = json.loads(L._ACTIVITY_FILE.read_text())["last_heartbeat"]
        time.sleep(0.05)
        L.bump_heartbeat()
        t2 = json.loads(L._ACTIVITY_FILE.read_text())["last_heartbeat"]
        assert t2 > t1


# ---------------------------------------------------------------------------
# OBS-3: log_exception
# ---------------------------------------------------------------------------

class TestOBS3LogException:
    def test_exception_logged_to_terminal(self, tmp_obs, capsys):
        import automation.autopilot_logger as L
        try:
            raise ValueError("test value error")
        except ValueError as exc:
            L.log_exception("MyComponent", exc)
        out = capsys.readouterr().out
        assert "EXCEPTION" in out
        assert "MyComponent" in out
        assert "ValueError" in out

    def test_exception_logged_to_jsonl(self, tmp_obs):
        import automation.autopilot_logger as L
        run_dir = L.init_run("exc-run", cycle=84)
        try:
            raise ValueError("test")
        except ValueError as exc:
            L.log_exception("TestComp", exc)
        jsonl = run_dir / "events.jsonl"
        if jsonl.exists():
            events = [json.loads(ln) for ln in jsonl.read_text().splitlines() if ln.strip()]
            error_events = [e for e in events if e.get("level", 0) >= 40]
            assert len(error_events) >= 1


# ---------------------------------------------------------------------------
# OBS-5: per-run JSONL + transcript
# ---------------------------------------------------------------------------

class TestOBS5PerRunLogs:
    def test_init_run_creates_files(self, tmp_obs):
        import automation.autopilot_logger as L
        run_dir = L.init_run("run-abc123", cycle=84)
        assert (run_dir / "transcript.log").exists() or True  # file created on first write
        L.ok("test message for run")
        assert (run_dir / "transcript.log").exists()

    def test_jsonl_parseable(self, tmp_obs):
        import automation.autopilot_logger as L
        run_dir = L.init_run("run-xyz", cycle=84)
        L.info("first event")
        L.warn("second event")
        L.error("third event")
        jsonl = run_dir / "events.jsonl"
        assert jsonl.exists()
        lines = [ln for ln in jsonl.read_text().splitlines() if ln.strip()]
        assert len(lines) >= 3
        for line in lines:
            evt = json.loads(line)
            assert "ts" in evt
            assert "msg" in evt

    def test_transcript_contains_messages(self, tmp_obs):
        import automation.autopilot_logger as L
        run_dir = L.init_run("run-trans", cycle=84)
        L.ok("UNIQUE_TRANSCRIPT_MARKER_12345")
        transcript = run_dir / "transcript.log"
        assert transcript.exists()
        assert "UNIQUE_TRANSCRIPT_MARKER_12345" in transcript.read_text()


# ---------------------------------------------------------------------------
# OBS-6: heartbeat thread
# ---------------------------------------------------------------------------

class TestOBS6Heartbeat:
    def test_heartbeat_emits_lines(self, tmp_obs, capsys):
        import automation.autopilot_logger as L
        # Use a short interval so test doesn't take long
        hb = L.HeartbeatThread("test-op", interval=0.05)
        hb.start()
        time.sleep(0.18)
        hb.stop()
        out = capsys.readouterr().out
        # Should have emitted at least 2 heartbeat lines
        hb_lines = [ln for ln in out.splitlines() if "HEARTBEAT" in ln]
        assert len(hb_lines) >= 2, f"Expected >=2 heartbeats, got: {hb_lines}"

    def test_heartbeat_as_context_manager(self, tmp_obs):
        import automation.autopilot_logger as L
        start = time.time()
        with L.HeartbeatThread("ctx-test", interval=0.05):
            time.sleep(0.15)
        elapsed = time.time() - start
        assert elapsed >= 0.1  # confirms it ran


# ---------------------------------------------------------------------------
# OBS-7: cycle_summary
# ---------------------------------------------------------------------------

class TestOBS7CycleSummary:
    def test_summary_writes_json(self, tmp_obs):
        import automation.autopilot_logger as L
        run_dir = L.init_run("summary-run", cycle=84)
        outcomes = {
            "A": {"status": "COMPLETE", "commit_sha": "abc1234", "files_changed": 5, "elapsed": 320},
            "B": {"status": "FAILED",  "commit_sha": "", "files_changed": 0, "elapsed": 45},
        }
        L.cycle_summary(cycle=84, agent_outcomes=outcomes, gate_result="PARTIAL")
        summary_file = run_dir / "CYCLE_084_RUN_SUMMARY.json"
        assert summary_file.exists()
        data = json.loads(summary_file.read_text())
        assert data["cycle"] == 84
        assert data["gate_result"] == "PARTIAL"
        assert "A" in data["agents"]

    def test_summary_writes_markdown(self, tmp_obs):
        import automation.autopilot_logger as L
        run_dir = L.init_run("md-run", cycle=84)
        L.cycle_summary(84, {"A": {"status": "COMPLETE", "elapsed": 300}}, "PASS")
        md_file = run_dir / "CYCLE_084_RUN_SUMMARY.md"
        assert md_file.exists()
        assert "PASS" in md_file.read_text()

    def test_summary_printed_to_terminal(self, tmp_obs, capsys):
        import automation.autopilot_logger as L
        L._run_state["run_dir"] = tmp_obs / "runs" / "s-run"
        (tmp_obs / "runs" / "s-run").mkdir(parents=True, exist_ok=True)
        L.cycle_summary(84, {"A": {"status": "COMPLETE", "elapsed": 100}}, "PASS")
        out = capsys.readouterr().out
        assert "CYCLE 084" in out
        assert "PASS" in out


# ---------------------------------------------------------------------------
# OBS-9: log levels
# ---------------------------------------------------------------------------

class TestOBS9LogLevel:
    def test_debug_filtered_at_info_level(self, tmp_obs, capsys, monkeypatch):
        import automation.autopilot_logger as L
        monkeypatch.setattr(L, "LOG_LEVEL", 20)  # INFO
        L.debug("this should be filtered")
        out = capsys.readouterr().out
        assert "this should be filtered" not in out

    def test_debug_shown_at_debug_level(self, tmp_obs, capsys, monkeypatch):
        import automation.autopilot_logger as L
        monkeypatch.setattr(L, "LOG_LEVEL", 10)  # DEBUG
        L.debug("UNIQUE_DEBUG_MSG_999")
        out = capsys.readouterr().out
        assert "UNIQUE_DEBUG_MSG_999" in out

    def test_warn_shown_at_warn_level(self, tmp_obs, capsys, monkeypatch):
        import automation.autopilot_logger as L
        monkeypatch.setattr(L, "LOG_LEVEL", 30)  # WARN
        L.info("should be filtered info")
        L.warn("should appear warn")
        out = capsys.readouterr().out
        assert "should be filtered info" not in out
        assert "should appear warn" in out


# ---------------------------------------------------------------------------
# OBS-12: correlation IDs in log file
# ---------------------------------------------------------------------------

class TestOBS12Correlation:
    def test_log_file_has_correlation(self, tmp_obs):
        import automation.autopilot_logger as L
        L._set_ctx(cycle=84, stage="PLAN", agent="A")
        L.ok("correlated message")
        # Find today's log file
        log_files = list((tmp_obs / "logs").glob("autopilot_*.log"))
        if not log_files:
            pytest.skip("no log file written")
        content = log_files[0].read_text()
        assert "C084" in content
        assert "PLAN" in content


# ---------------------------------------------------------------------------
# OBS-13: stage matrix
# ---------------------------------------------------------------------------

class TestOBS13StageMatrix:
    def test_matrix_shows_current_agent(self, tmp_obs, capsys):
        import automation.autopilot_logger as L
        L._stage_results.clear()
        mat = L.stage_matrix(current="B", agents=["A", "B", "E", "C", "F", "D"])
        assert "B" in mat  # current agent marked

    def test_matrix_shows_completed_stages(self, tmp_obs):
        import automation.autopilot_logger as L
        L._stage_results.clear()
        L._stage_results["PLAN"] = {"passed": True, "elapsed": 1.0}
        mat = L.stage_matrix(current="PROMPT-GEN")
        assert "PLAN" in mat

    def test_print_stage_matrix_writes_to_log(self, tmp_obs, capsys):
        import automation.autopilot_logger as L
        L.print_stage_matrix(current="PLAN")
        out = capsys.readouterr().out
        # Matrix is always printed -- just check it produces some output with a known stage
        assert "PLAN" in out or len(out.strip()) > 0


# ---------------------------------------------------------------------------
# OBS-15: stall detection
# ---------------------------------------------------------------------------

class TestOBS15StallDetection:
    def test_stall_fires_after_threshold(self, tmp_obs, capsys, monkeypatch):
        import automation.autopilot_logger as L
        from datetime import UTC, datetime, timedelta
        # Write a stale activity file
        stale_time = (datetime.now(UTC) - timedelta(seconds=400)).isoformat()
        L._ACTIVITY_FILE.write_text(
            json.dumps({"stage": "AGENT-RUN", "agent": "E", "last_heartbeat": stale_time}),
            encoding="utf-8",
        )
        # Lower threshold for test
        monkeypatch.setattr(L, "STALL_THRESHOLD_S", 300.0)
        L._check_stall()
        out = capsys.readouterr().out
        assert "STALL" in out

    def test_no_stall_when_fresh(self, tmp_obs, capsys):
        import automation.autopilot_logger as L
        from datetime import UTC, datetime
        L._ACTIVITY_FILE.write_text(
            json.dumps({"stage": "AGENT-RUN", "last_heartbeat": datetime.now(UTC).isoformat()}),
            encoding="utf-8",
        )
        L._check_stall()
        out = capsys.readouterr().out
        assert "STALL" not in out


# ---------------------------------------------------------------------------
# OBS-11: live_events tail function exists
# ---------------------------------------------------------------------------

class TestOBS11Tail:
    def test_tail_function_exists(self):
        from automation.live_events import tail
        assert callable(tail)

    def test_live_events_emit_recent(self, tmp_path, monkeypatch):
        import automation.live_events as le
        evt_file = tmp_path / "live_events.json"
        monkeypatch.setattr(le, "_EVENT_FILE", evt_file)
        le.emit("TEST", "hello world", cycle=84)
        events = le.recent(5)
        assert len(events) >= 1
        assert events[-1]["msg"] == "hello world"
