from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_controller_command(*args: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "automation/ai_cycle_controller.py", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, f"{proc.stdout}\n{proc.stderr}"


def test_brain_check_passes() -> None:
    rc, output = _run_controller_command("brain-check")
    assert rc == 0
    assert "BRAIN CHECK PASS" in output


def test_pm_pack_audit_passes() -> None:
    rc, output = _run_controller_command("pm-pack-audit")
    assert rc == 0
    assert "PM_PACK_AUDIT PASS" in output


def test_stage_status_executes_without_error() -> None:
    rc, _ = _run_controller_command("stage-status")
    assert rc == 0
