"""Cycle 062 strict smoke alias tests for Agent A preflight command."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_config_check_passes() -> None:
    result = _run_command(["run.py", "config-check"])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Config OK" in result.stdout


def test_golden_anchor_kw110_62_7() -> None:
    result = _run_command(
        [
            "run.py",
            "score",
            "--golden",
            "--config-override",
            "relevance.enable_stage_3_5=false",
            "--config-override",
            "analysis.external_signals_enabled=false",
        ]
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert '"110"' in output
    assert '"final_score": 62.7' in output
    assert '"confidence_modifier": 1.0' in output
    assert '"tag": "CONDITIONAL_GO"' in output
