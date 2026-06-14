from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from automation import report_generator


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_generate_weekly_report_writes_latest_file(tmp_path: Path) -> None:
    report_generator.RUNNER_ROOT = tmp_path / "runner"
    report_generator.REPORTS_DIR = report_generator.RUNNER_ROOT / "reports"
    (report_generator.RUNNER_ROOT / "logs/incidents").mkdir(parents=True, exist_ok=True)
    (report_generator.RUNNER_ROOT / "logs/snapshots").mkdir(parents=True, exist_ok=True)
    out = report_generator.generate_weekly_report()
    latest = report_generator.REPORTS_DIR / "weekly/latest_weekly_report.md"
    assert out.exists()
    assert latest.exists()
    assert "Weekly Autonomy Review" in latest.read_text(encoding="utf-8")


def test_latest_json_returns_empty_when_directory_missing(tmp_path: Path) -> None:
    payload = report_generator._latest_json(tmp_path / "missing", "health_*.json")
    assert payload == {}


def test_latest_json_reads_newest_matching_file(tmp_path: Path) -> None:
    d = tmp_path / "watchdog"
    _write_json(d / "health_1.json", {"Level": "OK"})
    _write_json(d / "health_2.json", {"Level": "WARN"})
    result = report_generator._latest_json(d, "health_*.json")
    assert result["Level"] == "WARN"


def test_count_recent_files_filters_old_files(tmp_path: Path) -> None:
    d = tmp_path / "incidents"
    d.mkdir(parents=True, exist_ok=True)
    recent = d / "recent.txt"
    old = d / "old.txt"
    recent.write_text("x", encoding="utf-8")
    old.write_text("x", encoding="utf-8")
    old_ts = (datetime.now(UTC) - timedelta(days=3)).timestamp()
    recent_ts = datetime.now(UTC).timestamp()
    old.touch()
    recent.touch()
    import os

    os.utime(old, (old_ts, old_ts))
    os.utime(recent, (recent_ts, recent_ts))
    assert report_generator._count_recent_files(d, hours=24) == 1


def test_tail_log_filters_recent_json_lines_and_ignores_invalid(tmp_path: Path) -> None:
    path = tmp_path / "notifications.log"
    recent = datetime.now(UTC).isoformat()
    stale = (datetime.now(UTC) - timedelta(days=5)).isoformat()
    path.write_text(
        "\n".join(
            [
                json.dumps({"ts": stale, "severity": "INFO"}),
                "not json",
                json.dumps({"ts": recent, "severity": "BLOCKED"}),
            ]
        ),
        encoding="utf-8",
    )
    lines = report_generator._tail_log(path, hours=24)
    assert len(lines) == 1
    assert "BLOCKED" in lines[0]


def test_generate_daily_report_handles_invalid_valid_until(tmp_path: Path) -> None:
    runner = tmp_path / "runner"
    report_generator.RUNNER_ROOT = runner
    report_generator.REPORTS_DIR = runner / "reports"
    _write_json(runner / "state/heartbeat.json", {"last_seen": "x"})
    _write_json(runner / "state/controller_state.json", {"status": "RUNNING", "active_cycle": 75})
    _write_json(
        runner / "state/cursor_model_state.json",
        {"observed_model": "Codex 5.3", "status": "VERIFIED", "effort": "medium", "valid_until": "invalid"},
    )
    _write_json(runner / "state/claude_model_state.json", {"billing_mode": "claude_subscription_only"})
    out = report_generator.generate_daily_report(75)
    text = out.read_text(encoding="utf-8")
    assert "Days to expiry: N/A" in text


def test_daily_report_has_health_section(tmp_path: Path) -> None:
    runner = tmp_path / "runner"
    report_generator.RUNNER_ROOT = runner
    report_generator.REPORTS_DIR = runner / "reports"
    _write_json(runner / "state/heartbeat.json", {"last_seen": datetime.now(UTC).isoformat()})
    _write_json(runner / "state/controller_state.json", {"status": "PLANNED", "active_cycle": 78})
    _write_json(runner / "state/cursor_model_state.json", {"valid_until": (datetime.now(UTC) + timedelta(days=5)).isoformat()})
    _write_json(runner / "state/claude_model_state.json", {"billing_mode": "claude_subscription_only"})
    _write_json(runner / "reports/health_20260614.json", {"health_level": "GREEN", "git_dirty_count": 2})
    out = report_generator.generate_daily_report(78)
    text = out.read_text(encoding="utf-8")
    assert "## Health Status" in text
    assert "Level: GREEN" in text


def test_daily_report_has_heartbeat_age(tmp_path: Path) -> None:
    runner = tmp_path / "runner"
    report_generator.RUNNER_ROOT = runner
    report_generator.REPORTS_DIR = runner / "reports"
    _write_json(
        runner / "state/heartbeat.json",
        {"last_seen": (datetime.now(UTC) - timedelta(minutes=5)).isoformat()},
    )
    _write_json(runner / "state/controller_state.json", {"status": "ACTIVE", "active_cycle": 78})
    _write_json(runner / "state/cursor_model_state.json", {})
    _write_json(runner / "state/claude_model_state.json", {})
    out = report_generator.generate_daily_report(78)
    text = out.read_text(encoding="utf-8")
    assert "Heartbeat age:" in text


def test_daily_report_has_model_status_section(tmp_path: Path) -> None:
    runner = tmp_path / "runner"
    report_generator.RUNNER_ROOT = runner
    report_generator.REPORTS_DIR = runner / "reports"
    _write_json(runner / "state/heartbeat.json", {"last_seen": datetime.now(UTC).isoformat()})
    _write_json(runner / "state/controller_state.json", {"status": "PLANNED", "active_cycle": 78})
    _write_json(
        runner / "state/cursor_model_state.json",
        {"valid_until": (datetime.now(UTC) + timedelta(days=5)).isoformat(), "observed_model": "Codex 5.3"},
    )
    _write_json(runner / "state/claude_model_state.json", {"billing_mode": "claude_subscription_only"})
    text = report_generator.generate_daily_report(78).read_text(encoding="utf-8")
    assert "## Model Status" in text


def test_weekly_report_has_cycles_section(tmp_path: Path) -> None:
    runner = tmp_path / "runner"
    repo = tmp_path / "repo"
    report_generator.RUNNER_ROOT = runner
    report_generator.REPORTS_DIR = runner / "reports"
    report_generator.REPO_ROOT = repo
    (repo / "PM_Pack/10_cycle_log").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/10_cycle_log/CYCLE_078_COMPLETE.md").write_text("done", encoding="utf-8")
    text = report_generator.generate_weekly_report().read_text(encoding="utf-8")
    assert "Cycles completed (7d)" in text
