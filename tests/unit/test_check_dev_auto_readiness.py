from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from automation import check_dev_auto_readiness as readiness


def _mk_completed(code: int, out: str = "") -> MagicMock:
    return MagicMock(returncode=code, stdout=out, stderr="")


def test_check_all_returns_summary_dict(tmp_path: Path) -> None:
    with patch.object(readiness, "REPO_ROOT", tmp_path), patch.object(readiness, "RUNNER_ROOT", tmp_path), patch(
        "automation.check_dev_auto_readiness.subprocess.run", return_value=_mk_completed(0, "PASS")
    ), patch.dict("os.environ", {}, clear=True):
        result = readiness.check_all()
    assert "checks" in result
    assert "ready_for_dev_auto" in result


def test_freeze_missing_fails_gate(tmp_path: Path) -> None:
    with patch.object(readiness, "REPO_ROOT", tmp_path), patch.object(readiness, "RUNNER_ROOT", tmp_path), patch(
        "automation.check_dev_auto_readiness.subprocess.run", return_value=_mk_completed(0, "PASS")
    ), patch.dict("os.environ", {}, clear=True):
        result = readiness.check_all()
    freeze_gate = next(item for item in result["checks"] if item["gate"] == "FREEZE_OFF")
    assert freeze_gate["passed"] is False


def test_no_anthropic_key_gate_passes_when_absent(tmp_path: Path) -> None:
    freeze = tmp_path / "PM_Pack/automation/policies/autonomy_freeze.yml"
    freeze.parent.mkdir(parents=True, exist_ok=True)
    freeze.write_text("frozen: false\n", encoding="utf-8")
    with patch.object(readiness, "REPO_ROOT", tmp_path), patch.object(readiness, "RUNNER_ROOT", tmp_path), patch(
        "automation.check_dev_auto_readiness.subprocess.run", return_value=_mk_completed(0, "PASS")
    ), patch.dict("os.environ", {}, clear=True):
        result = readiness.check_all()
    gate = next(item for item in result["checks"] if item["gate"] == "NO_ANTHROPIC_API_KEY")
    assert gate["passed"] is True


def test_no_anthropic_key_gate_fails_when_present(tmp_path: Path) -> None:
    freeze = tmp_path / "PM_Pack/automation/policies/autonomy_freeze.yml"
    freeze.parent.mkdir(parents=True, exist_ok=True)
    freeze.write_text("frozen: false\n", encoding="utf-8")
    with patch.object(readiness, "REPO_ROOT", tmp_path), patch.object(readiness, "RUNNER_ROOT", tmp_path), patch(
        "automation.check_dev_auto_readiness.subprocess.run", return_value=_mk_completed(0, "PASS")
    ), patch.dict("os.environ", {"ANTHROPIC_API_KEY": "x"}, clear=True):
        result = readiness.check_all()
    gate = next(item for item in result["checks"] if item["gate"] == "NO_ANTHROPIC_API_KEY")
    assert gate["passed"] is False


def test_repo_clean_gate_fails_when_dirty(tmp_path: Path) -> None:
    freeze = tmp_path / "PM_Pack/automation/policies/autonomy_freeze.yml"
    freeze.parent.mkdir(parents=True, exist_ok=True)
    freeze.write_text("frozen: false\n", encoding="utf-8")
    calls = [
        _mk_completed(0, "PM_PACK_AUDIT PASS"),
        _mk_completed(0, "BRAIN CHECK PASS"),
        _mk_completed(0, " M automation/x.py"),
        _mk_completed(0, ""),
        _mk_completed(0, "PASS"),
    ]
    with patch.object(readiness, "REPO_ROOT", tmp_path), patch.object(readiness, "RUNNER_ROOT", tmp_path), patch(
        "automation.check_dev_auto_readiness.subprocess.run", side_effect=calls
    ), patch.dict("os.environ", {}, clear=True):
        result = readiness.check_all()
    gate = next(item for item in result["checks"] if item["gate"] == "REPO_CLEAN")
    assert gate["passed"] is False


def test_writes_output_json(tmp_path: Path) -> None:
    freeze = tmp_path / "PM_Pack/automation/policies/autonomy_freeze.yml"
    freeze.parent.mkdir(parents=True, exist_ok=True)
    freeze.write_text("frozen: false\n", encoding="utf-8")
    with patch.object(readiness, "REPO_ROOT", tmp_path), patch.object(readiness, "RUNNER_ROOT", tmp_path), patch(
        "automation.check_dev_auto_readiness.subprocess.run", return_value=_mk_completed(0, "PASS")
    ), patch.dict("os.environ", {}, clear=True):
        readiness.check_all()
    output = tmp_path / "reports/validation/dev_auto_readiness.json"
    assert output.exists()
    assert "checks" in json.loads(output.read_text(encoding="utf-8"))


def test_model_state_missing_fails_gate(tmp_path: Path) -> None:
    freeze = tmp_path / "PM_Pack/automation/policies/autonomy_freeze.yml"
    freeze.parent.mkdir(parents=True, exist_ok=True)
    freeze.write_text("frozen: false\n", encoding="utf-8")
    with patch.object(readiness, "REPO_ROOT", tmp_path), patch.object(readiness, "RUNNER_ROOT", tmp_path), patch(
        "automation.check_dev_auto_readiness.subprocess.run", return_value=_mk_completed(0, "PASS")
    ), patch.dict("os.environ", {}, clear=True):
        result = readiness.check_all()
    gate = next(item for item in result["checks"] if item["gate"] == "CURSOR_MODEL_VERIFIED")
    assert gate["passed"] is False


def test_model_state_verified_passes_gate(tmp_path: Path) -> None:
    freeze = tmp_path / "PM_Pack/automation/policies/autonomy_freeze.yml"
    freeze.parent.mkdir(parents=True, exist_ok=True)
    freeze.write_text("frozen: false\n", encoding="utf-8")
    state = tmp_path / "state/cursor_model_state.json"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text('{"status":"VERIFIED","valid_until":"2999-01-01T00:00:00+00:00"}', encoding="utf-8")
    with patch.object(readiness, "REPO_ROOT", tmp_path), patch.object(readiness, "RUNNER_ROOT", tmp_path), patch(
        "automation.check_dev_auto_readiness.subprocess.run", return_value=_mk_completed(0, "PASS")
    ), patch.dict("os.environ", {}, clear=True):
        result = readiness.check_all()
    gate = next(item for item in result["checks"] if item["gate"] == "CURSOR_MODEL_VERIFIED")
    assert gate["passed"] is True
