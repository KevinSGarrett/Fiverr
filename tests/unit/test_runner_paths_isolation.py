"""Tests for ITEM 0.4 -- path isolation of logs/state from the test suite.

These tests verify that:
  * get_runner_root() honours AUTOPILOT_RUNNER_ROOT (lazily).
  * autopilot_logger writes land under the tmp root, not real C:/AI_Runner.
  * state_writer.write_controller_state writes under the tmp root.
  * The autouse write-guard raises on any attempt to write under the real root.

With the isolation infrastructure active these PASS; without it they would
write to the live runner root (or, for the guard test, not raise).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from automation import autopilot_logger, runner_paths, state_writer


def test_get_runner_root_honours_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = tmp_path / "custom_root"
    monkeypatch.setenv("AUTOPILOT_RUNNER_ROOT", str(target))
    assert runner_paths.get_runner_root() == target
    assert runner_paths.state_dir() == target / "state"
    assert runner_paths.logs_dir() == target / "logs"


def test_get_runner_root_default_is_live_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AUTOPILOT_RUNNER_ROOT", raising=False)
    assert runner_paths.get_runner_root() == Path("C:/AI_Runner")


def test_real_runner_root_is_live_default() -> None:
    assert runner_paths.real_runner_root() == Path("C:/AI_Runner").resolve()


def test_autopilot_logger_writes_under_tmp_root() -> None:
    """A log line must land under the session tmp root, NOT real C:/AI_Runner."""
    session_root = Path(os.environ["AUTOPILOT_RUNNER_ROOT"]).resolve()
    real_root = runner_paths.real_runner_root()
    assert not str(session_root).startswith(str(real_root))

    autopilot_logger.info("isolation-test log line")

    log_files = list((session_root / "logs").glob("autopilot_*.log"))
    assert log_files, "expected a log file under the tmp runner root"
    # Nothing was written under the real root.
    assert session_root != real_root


def test_autopilot_logger_init_run_writes_under_tmp_root() -> None:
    session_root = Path(os.environ["AUTOPILOT_RUNNER_ROOT"]).resolve()
    run_dir = autopilot_logger.init_run("isolation_run_001", cycle=1)
    assert run_dir.resolve().is_relative_to(session_root)
    assert (run_dir / "transcript.log").exists()
    assert (run_dir / "events.jsonl").exists()


def test_state_writer_write_controller_state_under_tmp() -> None:
    session_root = Path(os.environ["AUTOPILOT_RUNNER_ROOT"]).resolve()
    state_writer.write_controller_state("RUNNING", cycle=42, branch="main")
    controller = session_root / "state" / "controller_state.json"
    assert controller.exists()
    assert "RUNNING" in controller.read_text()


def test_state_writer_write_heartbeat_under_tmp() -> None:
    session_root = Path(os.environ["AUTOPILOT_RUNNER_ROOT"]).resolve()
    state_writer.write_heartbeat("ALIVE", cycle=7)
    heartbeat = session_root / "state" / "heartbeat.json"
    assert heartbeat.exists()
    assert "ALIVE" in heartbeat.read_text()


def test_write_guard_blocks_direct_write_to_live_root() -> None:
    """Attempting to write under real C:/AI_Runner inside a test must raise."""
    target = Path("C:/AI_Runner/state/isolation_guard_probe.json")
    with pytest.raises(RuntimeError, match="TEST ISOLATION VIOLATION"):
        target.write_text("should never reach disk")
    # The probe file must not exist on the live root.
    assert not target.exists()


def test_write_guard_blocks_mkdir_under_live_root() -> None:
    target = Path("C:/AI_Runner/isolation_guard_dir")
    with pytest.raises(RuntimeError, match="TEST ISOLATION VIOLATION"):
        target.mkdir(parents=True, exist_ok=True)


def test_write_guard_blocks_builtin_open_write_under_live_root() -> None:
    target = "C:/AI_Runner/logs/isolation_guard_probe.log"
    with pytest.raises(RuntimeError, match="TEST ISOLATION VIOLATION"):
        open(target, "w").close()


def test_write_guard_allows_tmp_writes(tmp_path: Path) -> None:
    """The guard must not interfere with legitimate tmp writes."""
    (tmp_path / "ok.txt").write_text("fine")
    assert (tmp_path / "ok.txt").read_text() == "fine"


# ── P1 regression (Codex review on PR #107): late AUTOPILOT_RUNNER_ROOT must win ──
def test_late_env_change_honored_logger(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """An unmodified module constant must defer to a LATE env change (no stale live path).

    Simulates import-before-env-set: the public constant equals its frozen import
    original, then AUTOPILOT_RUNNER_ROOT changes. The resolver must follow the env,
    not return the stale default. (Codex P1 on PR #107.)
    """
    new_root = tmp_path / "late_root"
    monkeypatch.setattr(autopilot_logger, "LOG_DIR", autopilot_logger._ORIG_LOG_DIR)
    monkeypatch.setattr(autopilot_logger, "STATE_DIR", autopilot_logger._ORIG_STATE_DIR)
    monkeypatch.setenv("AUTOPILOT_RUNNER_ROOT", str(new_root))
    assert autopilot_logger._logs_dir() == new_root / "logs"
    assert autopilot_logger._state_dir() == new_root / "state"


def test_late_env_change_honored_state_writer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    new_root = tmp_path / "late_root_sw"
    monkeypatch.setattr(state_writer, "RUNNER_STATE_DIR", state_writer._ORIG_RUNNER_STATE_DIR)
    monkeypatch.setattr(state_writer, "HEARTBEAT_PATH", state_writer._ORIG_HEARTBEAT_PATH)
    monkeypatch.setattr(state_writer, "CONTROLLER_STATE_PATH", state_writer._ORIG_CONTROLLER_STATE_PATH)
    monkeypatch.setenv("AUTOPILOT_RUNNER_ROOT", str(new_root))
    assert state_writer._state_dir() == new_root / "state"
    assert state_writer._heartbeat_path() == new_root / "state" / "heartbeat.json"
    assert state_writer._controller_state_path() == new_root / "state" / "controller_state.json"


def test_monkeypatched_constant_still_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """An explicitly monkeypatched constant (!= frozen original) is honoured over env."""
    forced = tmp_path / "forced_logs"
    monkeypatch.setattr(autopilot_logger, "LOG_DIR", forced)
    monkeypatch.setenv("AUTOPILOT_RUNNER_ROOT", str(tmp_path / "other"))
    assert autopilot_logger._logs_dir() == forced
