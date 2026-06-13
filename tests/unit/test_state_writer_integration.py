from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from automation import state_writer


def test_state_writer_integration_idempotent_sequence(tmp_path: Path) -> None:
    state_writer.write_heartbeat("RUNNING", 75, "F", runner_root=tmp_path)
    log_path = state_writer.write_cycle_log_entry(
        cycle=75,
        run_id="run-1",
        commit_shas=["abc"],
        agents_complete=["F"],
        scores={"s1": 10, "s2": 20},
        repo_root=tmp_path,
    )
    state_writer.update_production_readiness_scorecard(75, 10.0, 20.0, 1.0, 2.0, tmp_path)
    state_writer.update_production_readiness_scorecard(75, 10.0, 20.0, 1.0, 2.0, tmp_path)

    assert (tmp_path / "state/heartbeat.json").exists()
    assert log_path.exists()
    scorecard = tmp_path / "PM_Pack/PRODUCTION_READINESS_SCORECARD.md"
    assert scorecard.exists()
    assert scorecard.read_text(encoding="utf-8").count("| 75 |") == 1

    with patch("subprocess.run") as run:
        run.return_value.returncode = 0
        assert run.return_value.returncode == 0
