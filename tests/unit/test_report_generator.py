from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from automation import report_generator as module


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_model_status_section_formats_expected_lines(tmp_path: Path, monkeypatch) -> None:
    cursor_state = tmp_path / "state" / "cursor_model_state.json"
    claude_state = tmp_path / "state" / "claude_model_state.json"
    verified_at = "2026-06-10T00:00:00+00:00"
    _write_json(
        cursor_state,
        {"observed_model": "codex-5.3", "effort": "medium", "verified_at": verified_at},
    )
    _write_json(
        claude_state,
        {"model": "claude-opus-4-8", "effort": "high", "billing_mode": "subscription"},
    )

    original_load_json = module._load_json

    def _fake_load_json(path: Path) -> dict[str, object]:
        if str(path).endswith("cursor_model_state.json"):
            return original_load_json(cursor_state)
        if str(path).endswith("claude_model_state.json"):
            return original_load_json(claude_state)
        return original_load_json(path)

    monkeypatch.setattr(module, "_load_json", _fake_load_json)
    section = module.ReportGenerator()._get_model_status_section()
    assert section.startswith("## Model Verification Status")
    assert "Cursor: codex-5.3 | effort: medium | age:" in section
    assert "Claude: claude-opus-4-8 | effort: high | billing: subscription" in section


def test_ci_timing_section_handles_gh_unavailable(monkeypatch) -> None:
    def _raise(*_: object, **__: object) -> None:
        raise FileNotFoundError("gh missing")

    monkeypatch.setattr(module.subprocess, "run", _raise)
    section = module.ReportGenerator()._get_ci_timing_section()
    assert "## CI Timing" in section
    assert "unavailable" in section


def test_ci_timing_section_computes_average(monkeypatch) -> None:
    runs = [
        {
            "conclusion": "success",
            "createdAt": "2026-06-16T00:00:00Z",
            "updatedAt": "2026-06-16T00:01:00Z",
        },
        {
            "conclusion": "failure",
            "createdAt": "2026-06-15T00:00:00Z",
            "updatedAt": "2026-06-15T00:02:00Z",
        },
    ]

    class _Result:
        stdout = json.dumps(runs)

    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: _Result())
    section = module.ReportGenerator()._get_ci_timing_section()
    assert section == "## CI Timing\nLast 5 runs avg: 90s | last run: success (60s)"


def test_generate_daily_report_includes_model_and_ci_sections(tmp_path: Path, monkeypatch) -> None:
    now = datetime.now(UTC).isoformat()
    _write_json(tmp_path / "state" / "heartbeat.json", {"last_seen": now})
    _write_json(tmp_path / "state" / "controller_state.json", {"status": "ACTIVE", "active_cycle": 82})
    _write_json(
        tmp_path / "state" / "cursor_model_state.json",
        {"observed_model": "codex-5.3", "status": "VERIFIED", "effort": "medium", "verified_at": now},
    )
    _write_json(
        tmp_path / "state" / "claude_model_state.json",
        {"status": "VERIFIED", "billing_mode": "subscription", "model": "claude-opus-4-8", "effort": "high"},
    )

    monkeypatch.setattr(module, "RUNNER_ROOT", tmp_path)
    monkeypatch.setattr(module, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(
        module.ReportGenerator,
        "_get_ci_timing_section",
        lambda self: "## CI Timing\nLast 5 runs avg: 10s | last run: success (10s)",
    )
    report_path = module.generate_daily_report(cycle=82)
    text = report_path.read_text(encoding="utf-8")
    assert "## Model Verification Status" in text
    assert "## CI Timing" in text
