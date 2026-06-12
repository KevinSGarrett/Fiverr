from __future__ import annotations

import json
from pathlib import Path

from automation import policy_compiler


def test_compile_policy_writes_snapshot(tmp_path: Path) -> None:
    (tmp_path / "PM_Pack/07_hydration").mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/07_hydration/HYDRATION_HEADER.md").write_text("CYCLE_CURRENT: 075\n", encoding="utf-8")
    snapshot = policy_compiler.compile_policy(tmp_path)
    assert (tmp_path / "PM_Pack/automation/current_policy_snapshot.json").exists()
    assert snapshot["cycle_current"] == 75


def test_compile_policy_reads_wave(tmp_path: Path) -> None:
    (tmp_path / "PM_Pack/07_hydration").mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/07_hydration/HYDRATION_HEADER.md").write_text("WAVE_CURRENT: 4\n", encoding="utf-8")
    snapshot = policy_compiler.compile_policy(tmp_path)
    assert snapshot["active_wave"] == 4


def test_extract_int_from_line_start() -> None:
    assert policy_compiler._extract_int("CYCLE_CURRENT: 075", r"^CYCLE_CURRENT:\s*0*(\d+)", from_line_start=True) == 75


def test_extract_int_default_when_missing() -> None:
    assert policy_compiler._extract_int("none", r"CYCLE (\d+)") == 0


def test_extract_float_parses_percentage() -> None:
    assert policy_compiler._extract_float("END_TO_END: ~92.5%", r"END_TO_END:\s*~?(\d+(?:\.\d+)?)%") == 92.5


def test_extract_str_returns_group() -> None:
    assert policy_compiler._extract_str("completed: C074", r"completed:\s*(C\d+)") == "C074"


def test_compile_policy_has_quality_gates(tmp_path: Path) -> None:
    (tmp_path / "PM_Pack/07_hydration").mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/07_hydration/HYDRATION_HEADER.md").write_text("", encoding="utf-8")
    snapshot = policy_compiler.compile_policy(tmp_path)
    assert snapshot["quality_gates"]["coverage_floor"] == 90


def test_compile_policy_snapshot_is_valid_json(tmp_path: Path) -> None:
    (tmp_path / "PM_Pack/07_hydration").mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/07_hydration/HYDRATION_HEADER.md").write_text("", encoding="utf-8")
    policy_compiler.compile_policy(tmp_path)
    payload = json.loads((tmp_path / "PM_Pack/automation/current_policy_snapshot.json").read_text(encoding="utf-8"))
    assert "compiled_at" in payload
