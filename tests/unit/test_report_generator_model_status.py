from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import automation.report_generator as report_generator


def test_daily_report_includes_model_status_fields(tmp_path: Path) -> None:
    runner = tmp_path / "runner"
    report_generator.RUNNER_ROOT = runner
    report_generator.REPORTS_DIR = runner / "reports"
    (runner / "state").mkdir(parents=True, exist_ok=True)
    (runner / "state/cursor_model_state.json").write_text(
        json.dumps(
            {
                "observed_model": "Codex 5.3",
                "status": "VERIFIED",
                "effort": "medium",
                "verified_at": datetime.now(UTC).isoformat(),
                "valid_until": (datetime.now(UTC) + timedelta(days=10)).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    path = report_generator.generate_daily_report(75)
    text = path.read_text(encoding="utf-8")
    assert "## Model Status" in text
    assert "Days to expiry" in text


def test_daily_report_warns_when_model_expires_soon(tmp_path: Path) -> None:
    runner = tmp_path / "runner"
    report_generator.RUNNER_ROOT = runner
    report_generator.REPORTS_DIR = runner / "reports"
    (runner / "state").mkdir(parents=True, exist_ok=True)
    (runner / "state/cursor_model_state.json").write_text(
        json.dumps(
            {
                "observed_model": "Codex 5.3",
                "status": "VERIFIED",
                "effort": "medium",
                "verified_at": datetime.now(UTC).isoformat(),
                "valid_until": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    path = report_generator.generate_daily_report(75)
    text = path.read_text(encoding="utf-8")
    assert "## Model Status WARNING" in text


def test_model_status_warning_header_not_garbled(tmp_path: Path) -> None:
    runner = tmp_path / "runner"
    report_generator.RUNNER_ROOT = runner
    report_generator.REPORTS_DIR = runner / "reports"
    (runner / "state").mkdir(parents=True, exist_ok=True)
    (runner / "state/heartbeat.json").write_text(
        json.dumps({"last_seen": datetime.now(UTC).isoformat()}),
        encoding="utf-8",
    )
    (runner / "state/controller_state.json").write_text(
        json.dumps({"status": "PLANNED", "active_cycle": 78}),
        encoding="utf-8",
    )
    (runner / "state/cursor_model_state.json").write_text(
        json.dumps(
            {
                "observed_model": "Codex 5.3",
                "status": "VERIFIED",
                "effort": "medium",
                "verified_at": datetime.now(UTC).isoformat(),
                "valid_until": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    (runner / "state/claude_model_state.json").write_text(
        json.dumps({"billing_mode": "claude_subscription_only"}),
        encoding="utf-8",
    )
    text = report_generator.generate_daily_report(78).read_text(encoding="utf-8")
    assert "## Model Status WARNING" in text
    assert "â" not in text
