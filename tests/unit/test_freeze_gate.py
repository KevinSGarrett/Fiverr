from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from automation.freeze_gate import FreezeBlockedError, check_freeze, is_frozen, load_freeze_policy


def test_load_freeze_policy_defaults_when_missing(tmp_path: Path) -> None:
    assert load_freeze_policy(tmp_path)["frozen"] is False


def test_load_freeze_policy_reads_yaml(tmp_path: Path) -> None:
    path = tmp_path / "PM_Pack/automation/policies/autonomy_freeze.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"frozen": True}), encoding="utf-8")
    assert load_freeze_policy(tmp_path)["frozen"] is True


def test_is_frozen_true_when_policy_true(tmp_path: Path) -> None:
    path = tmp_path / "PM_Pack/automation/policies/autonomy_freeze.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("frozen: true\n", encoding="utf-8")
    assert is_frozen(tmp_path) is True


def test_check_freeze_allows_when_not_frozen(tmp_path: Path) -> None:
    check_freeze("run-agent", tmp_path)


def test_check_freeze_raises_when_frozen(tmp_path: Path) -> None:
    path = tmp_path / "PM_Pack/automation/policies/autonomy_freeze.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("frozen: true\nreason: INCIDENT\nincident_ref: X1\n", encoding="utf-8")
    with pytest.raises(FreezeBlockedError):
        check_freeze("run-agent", tmp_path)


def test_check_freeze_allows_permitted_command(tmp_path: Path) -> None:
    path = tmp_path / "PM_Pack/automation/policies/autonomy_freeze.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "frozen: true\nreason: INCIDENT\nincident_ref: X1\npermitted_while_frozen:\n  - brain-check\n",
        encoding="utf-8",
    )
    check_freeze("brain-check", tmp_path)


def test_load_freeze_policy_fail_closed_on_unreadable(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "PM_Pack/automation/policies/autonomy_freeze.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("frozen: true", encoding="utf-8")
    monkeypatch.setattr("automation.freeze_gate.yaml.safe_load", lambda _x: (_ for _ in ()).throw(ValueError("bad")))
    payload = load_freeze_policy(tmp_path)
    assert payload["frozen"] is True


def test_blocked_error_message_contains_incident(tmp_path: Path) -> None:
    path = tmp_path / "PM_Pack/automation/policies/autonomy_freeze.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("frozen: true\nreason: INCIDENT\nincident_ref: INC-1\n", encoding="utf-8")
    with pytest.raises(FreezeBlockedError, match="INC-1"):
        check_freeze("merge-gate-execute", tmp_path)
