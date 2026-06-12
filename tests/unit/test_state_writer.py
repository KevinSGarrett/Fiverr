from __future__ import annotations

import json
from pathlib import Path

import pytest
from automation import state_writer


def test_write_cycle_log_creates_new_file(tmp_path: Path) -> None:
    path = state_writer.write_cycle_log_entry(
        cycle=75,
        run_id="run-1",
        commit_shas=["abc123"],
        agents_complete=["A", "B"],
        scores={"s1": 40, "s2": 35},
        repo_root=tmp_path,
    )
    assert path.exists()
    assert "## Run run-1" in path.read_text(encoding="utf-8")


def test_write_cycle_log_appends_on_second_call(tmp_path: Path) -> None:
    state_writer.write_cycle_log_entry(75, "run-1", [], [], {"s1": 1, "s2": 2}, tmp_path)
    path = state_writer.write_cycle_log_entry(75, "run-2", [], [], {"s1": 1, "s2": 2}, tmp_path)
    text = path.read_text(encoding="utf-8")
    assert "## Run run-1" in text and "## Run run-2" in text


def test_write_cycle_log_is_idempotent(tmp_path: Path) -> None:
    state_writer.write_cycle_log_entry(75, "run-1", [], [], {"s1": 1, "s2": 2}, tmp_path)
    path = state_writer.write_cycle_log_entry(75, "run-1", [], [], {"s1": 1, "s2": 2}, tmp_path)
    text = path.read_text(encoding="utf-8")
    assert text.count("## Run run-1") == 1


def test_write_heartbeat_has_utc_timestamp(tmp_path: Path) -> None:
    state_writer.write_heartbeat("RUNNING", 75, "B", runner_root=tmp_path)
    heartbeat = json.loads((tmp_path / "state/heartbeat.json").read_text(encoding="utf-8"))
    assert heartbeat["last_seen"].endswith("+00:00")
    assert heartbeat["active_cycle"] == 75


def test_update_scorecard_adds_row(tmp_path: Path) -> None:
    scorecard = tmp_path / "PM_Pack/PRODUCTION_READINESS_SCORECARD.md"
    scorecard.parent.mkdir(parents=True, exist_ok=True)
    scorecard.write_text(
        "| Cycle | Score1 | Score2 | Delta1 | Delta2 |\n| --- | --- | --- | --- | --- |\n",
        encoding="utf-8",
    )
    state_writer.update_production_readiness_scorecard(75, 45.0, 40.0, 5.0, 4.0, tmp_path)
    assert "| 75 | 45.0 | 40.0 | +5.0 | +4.0 |" in scorecard.read_text(encoding="utf-8")


def test_write_heartbeat_creates_file(tmp_path: Path) -> None:
    state_writer.write_heartbeat("RUNNING", 75, "A", runner_root=tmp_path)
    assert (tmp_path / "state/heartbeat.json").exists()


def test_write_heartbeat_has_correct_fields(tmp_path: Path) -> None:
    state_writer.write_heartbeat("IDLE", 75, "B", runner_root=tmp_path)
    payload = json.loads((tmp_path / "state/heartbeat.json").read_text(encoding="utf-8"))
    assert {"last_seen", "status", "active_cycle", "pid"}.issubset(payload.keys())
    assert payload["status"] == "IDLE"


def test_write_heartbeat_overwrites_on_second_call(tmp_path: Path) -> None:
    state_writer.write_heartbeat("RUNNING", 75, "A", runner_root=tmp_path)
    first = json.loads((tmp_path / "state/heartbeat.json").read_text(encoding="utf-8"))
    state_writer.write_heartbeat("DONE", 75, "A", runner_root=tmp_path)
    second = json.loads((tmp_path / "state/heartbeat.json").read_text(encoding="utf-8"))
    assert first["status"] == "RUNNING"
    assert second["status"] == "DONE"


def test_write_cycle_log_contains_run_id(tmp_path: Path) -> None:
    path = state_writer.write_cycle_log_entry(75, "run-xyz", [], [], {"s1": 1, "s2": 2}, tmp_path)
    assert "run-xyz" in path.read_text(encoding="utf-8")


def test_update_hydration_header_changes_cycle_number(tmp_path: Path) -> None:
    header = tmp_path / "PM_Pack/07_hydration/HYDRATION_HEADER.md"
    header.parent.mkdir(parents=True, exist_ok=True)
    header.write_text(
        "Active cycle: 74\nScore 1 (Internal Build Progress): ~10%\nScore 2 (Production Readiness): ~20%\nBlockers: none\nBranch cycle/074/integration\n",
        encoding="utf-8",
    )
    state_writer.update_hydration_header(
        cycle=75,
        scores={"s1": 22, "s2": 33},
        branch="cycle/075/integration",
        blockers=["none"],
        repo_root=tmp_path,
    )
    text = header.read_text(encoding="utf-8")
    assert "Active cycle: 75" in text
    assert "cycle/075/integration" in text


def test_all_writers_use_utc_timestamps(tmp_path: Path) -> None:
    state_writer.write_heartbeat("RUNNING", 75, "A", runner_root=tmp_path)
    heartbeat = json.loads((tmp_path / "state/heartbeat.json").read_text(encoding="utf-8"))
    assert heartbeat["last_seen"].endswith("+00:00")
    log_path = state_writer.write_cycle_log_entry(75, "run-utc", [], [], {"s1": 1, "s2": 2}, tmp_path)
    assert "+00:00" in log_path.read_text(encoding="utf-8")


@pytest.mark.parametrize("cycle", [0, 1, 999])
def test_cycle_log_boundary_cycle_numbers(tmp_path: Path, cycle: int) -> None:
    path = state_writer.write_cycle_log_entry(cycle, f"run-{cycle}", [], [], {"s1": 1, "s2": 2}, tmp_path)
    assert path.exists()
    assert f"# Cycle {cycle:03d} Log" in path.read_text(encoding="utf-8")


# Prompt-required name aliases for traceability.
def test_write_heartbeat_timestamp_is_utc_iso(tmp_path: Path) -> None:
    test_write_heartbeat_has_utc_timestamp(tmp_path)


def test_write_cycle_log_appends_second_entry(tmp_path: Path) -> None:
    test_write_cycle_log_appends_on_second_call(tmp_path)


def test_write_cycle_log_idempotent_same_run_id(tmp_path: Path) -> None:
    test_write_cycle_log_is_idempotent(tmp_path)
