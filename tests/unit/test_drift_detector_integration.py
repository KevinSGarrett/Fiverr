from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from automation.drift_detector import DriftDetector


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_drift_detector_integration_detect_and_write_report(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    runner = tmp_path / "runner"
    repo.mkdir(parents=True, exist_ok=True)

    _write_json(repo / "PM_Pack/automation/policy_snapshots/current_policy_snapshot.json", {"current_cycle": 75})
    _write_json(
        runner / "state/controller_state.json",
        {"active_cycle": 75, "status": "PLANNED", "active_branch": "cycle/075/integration"},
    )
    _write_json(
        runner / "state/cursor_model_state.json",
        {"valid_until": (datetime.now(UTC) + timedelta(days=1)).isoformat()},
    )
    (repo / "PM_Pack/07_hydration").mkdir(parents=True, exist_ok=True)
    (repo / "PM_Pack/07_hydration/HYDRATION_HEADER.md").write_text("Active cycle: 75\n", encoding="utf-8")
    (repo / "PM_Pack/CURRENT_STATE_CANONICAL.md").write_text("Cycle: 75\n", encoding="utf-8")
    prompts_dir = repo / "PM_Pack/automation/prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (prompts_dir / "CYCLE_075_AGENT_A.md").write_text("ok", encoding="utf-8")
    freeze_path = repo / "PM_Pack/automation/policies/autonomy_freeze.yml"
    freeze_path.parent.mkdir(parents=True, exist_ok=True)
    freeze_path.write_text("frozen: false\n", encoding="utf-8")

    detector = DriftDetector()
    with patch("automation.drift_detector.subprocess.run", return_value=MagicMock(returncode=1, stdout="")):
        report = detector.detect(repo, runner)
    assert report.passed is True
    out = detector.write_report(report, tmp_path / "out")
    assert out.exists()
