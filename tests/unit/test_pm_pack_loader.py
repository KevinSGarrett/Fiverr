from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from automation import pm_pack_loader


def _registry_text() -> str:
    return (
        "load_order:\n"
        "  core:\n"
        "    - PM_Pack/07_hydration/HYDRATION_HEADER.md\n"
    )


def test_brain_check_fails_without_registry(tmp_path: Path) -> None:
    result = pm_pack_loader.brain_check(tmp_path)
    assert result.ok is False


def test_brain_check_loads_registry(tmp_path: Path) -> None:
    reg = tmp_path / "PM_Pack/automation/BRAIN_REGISTRY.yml"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(_registry_text(), encoding="utf-8")
    (tmp_path / "PM_Pack/07_hydration").mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/07_hydration/HYDRATION_HEADER.md").write_text("CYCLE_CURRENT: 075", encoding="utf-8")
    (tmp_path / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md").write_text("x", encoding="utf-8")
    result = pm_pack_loader.brain_check(tmp_path)
    assert any("BRAIN_REGISTRY.yml loaded" in item for item in result.passed)


def test_cycle_detected_from_hydration(tmp_path: Path) -> None:
    reg = tmp_path / "PM_Pack/automation/BRAIN_REGISTRY.yml"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(_registry_text(), encoding="utf-8")
    (tmp_path / "PM_Pack/07_hydration").mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/07_hydration/HYDRATION_HEADER.md").write_text("CYCLE_CURRENT: 075\nWAVE_CURRENT: 4\n", encoding="utf-8")
    (tmp_path / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md").write_text("x", encoding="utf-8")
    result = pm_pack_loader.brain_check(tmp_path)
    assert result.cycle_detected == "75"


def test_post_cycle_prompt_presence_flag(tmp_path: Path) -> None:
    reg = tmp_path / "PM_Pack/automation/BRAIN_REGISTRY.yml"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(_registry_text(), encoding="utf-8")
    (tmp_path / "PM_Pack/07_hydration").mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/07_hydration/HYDRATION_HEADER.md").write_text("CYCLE_CURRENT: 075", encoding="utf-8")
    result = pm_pack_loader.brain_check(tmp_path)
    assert result.post_cycle_prompt_present is False


def test_load_file_returns_empty_for_missing(tmp_path: Path) -> None:
    assert pm_pack_loader.load_file("missing.md", tmp_path) == ""


def test_resolve_relative_path(tmp_path: Path) -> None:
    resolved = pm_pack_loader._resolve("PM_Pack/a.md", tmp_path)
    assert resolved == tmp_path / "PM_Pack/a.md"


def test_extract_returns_none_when_not_found() -> None:
    assert pm_pack_loader._extract("hello", r"CYCLE (\d+)") is None


def test_extract_returns_value_when_found() -> None:
    assert pm_pack_loader._extract("Cycle 075", r"Cycle (\d+)") == "075"


def test_brain_check_reports_missing_registry_files(tmp_path: Path) -> None:
    reg = tmp_path / "PM_Pack/automation/BRAIN_REGISTRY.yml"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(
        "load_order:\n"
        "  core:\n"
        "    - PM_Pack/07_hydration/HYDRATION_HEADER.md\n"
        "    - PM_Pack/07_hydration/MISSING.md\n",
        encoding="utf-8",
    )
    (tmp_path / "PM_Pack/07_hydration").mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/07_hydration/HYDRATION_HEADER.md").write_text("CYCLE_CURRENT: 075", encoding="utf-8")
    result = pm_pack_loader.brain_check(tmp_path)
    assert any("MISSING [core]" in item for item in result.failed)


def test_brain_check_uses_cycle_next_when_cycle_current_missing(tmp_path: Path) -> None:
    reg = tmp_path / "PM_Pack/automation/BRAIN_REGISTRY.yml"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(_registry_text(), encoding="utf-8")
    hydration = tmp_path / "PM_Pack/07_hydration/HYDRATION_HEADER.md"
    hydration.parent.mkdir(parents=True, exist_ok=True)
    hydration.write_text("CYCLE_NEXT: 076", encoding="utf-8")
    (tmp_path / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md").write_text("x", encoding="utf-8")
    result = pm_pack_loader.brain_check(tmp_path)
    assert result.cycle_detected == "76"


def test_brain_check_parses_next_cycle_format(tmp_path: Path) -> None:
    reg = tmp_path / "PM_Pack/automation/BRAIN_REGISTRY.yml"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(_registry_text(), encoding="utf-8")
    hydration = tmp_path / "PM_Pack/07_hydration/HYDRATION_HEADER.md"
    hydration.parent.mkdir(parents=True, exist_ok=True)
    hydration.write_text("NEXT CYCLE (C077)", encoding="utf-8")
    (tmp_path / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md").write_text("x", encoding="utf-8")
    result = pm_pack_loader.brain_check(tmp_path)
    assert result.cycle_detected == "77"


def test_brain_check_extracts_blocker_list(tmp_path: Path) -> None:
    reg = tmp_path / "PM_Pack/automation/BRAIN_REGISTRY.yml"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(_registry_text(), encoding="utf-8")
    hydration = tmp_path / "PM_Pack/07_hydration/HYDRATION_HEADER.md"
    hydration.parent.mkdir(parents=True, exist_ok=True)
    hydration.write_text(
        "CYCLE_CURRENT: 075\n"
        "Blockers:\n"
        "- Jira auth missing\n"
        "- Coverage gate red\n",
        encoding="utf-8",
    )
    (tmp_path / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md").write_text("x", encoding="utf-8")
    result = pm_pack_loader.brain_check(tmp_path)
    assert result.blockers_detected == ["Jira auth missing", "Coverage gate red"]


def test_brain_check_warns_when_model_status_unverified(tmp_path: Path) -> None:
    reg = tmp_path / "PM_Pack/automation/BRAIN_REGISTRY.yml"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(_registry_text(), encoding="utf-8")
    (tmp_path / "PM_Pack/07_hydration").mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/07_hydration/HYDRATION_HEADER.md").write_text("CYCLE_CURRENT: 075", encoding="utf-8")
    (tmp_path / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md").write_text("x", encoding="utf-8")
    with patch("automation.pm_pack_loader._load_json", return_value={}):
        result = pm_pack_loader.brain_check(tmp_path)
    assert any("Cursor model status" in warning for warning in result.warnings)
    assert any("Claude status" in warning for warning in result.warnings)


def test_resolve_absolute_path_passthrough() -> None:
    absolute = Path("C:/temp/file.md")
    resolved = pm_pack_loader._resolve(str(absolute), Path("C:/repo"))
    assert resolved == absolute


def test_load_json_invalid_returns_empty(tmp_path: Path) -> None:
    invalid = tmp_path / "bad.json"
    invalid.write_text("{bad", encoding="utf-8")
    assert pm_pack_loader._load_json(invalid) == {}


def test_load_policy_valid_yaml_returns_data(tmp_path: Path) -> None:
    policy = tmp_path / "policy.yml"
    policy.write_text("name: test\nenabled: true\n", encoding="utf-8")
    loaded = pm_pack_loader.load_policy(policy, required_fields=["name"])
    assert loaded["name"] == "test"


def test_load_policy_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        pm_pack_loader.load_policy(tmp_path / "missing.yml")


def test_load_policy_invalid_yaml_raises(tmp_path: Path) -> None:
    policy = tmp_path / "policy.yml"
    policy.write_text("name: [", encoding="utf-8")
    with pytest.raises(yaml.YAMLError):
        pm_pack_loader.load_policy(policy)


def test_load_policy_missing_required_fields_raises(tmp_path: Path) -> None:
    policy = tmp_path / "policy.yml"
    policy.write_text("name: test\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required fields"):
        pm_pack_loader.load_policy(policy, required_fields=["name", "owner"])


def test_check_cycle_consistency_detects_mismatch() -> None:
    findings = pm_pack_loader.check_cycle_consistency(
        "CYCLE_CURRENT: 075",
        "CYCLE_CURRENT: 076",
        "CYCLE_CURRENT: 075",
    )
    assert findings


def test_check_cycle_consistency_passes_when_matching() -> None:
    findings = pm_pack_loader.check_cycle_consistency(
        "CYCLE_CURRENT: 075",
        "CYCLE_CURRENT: 075",
        "CYCLE_CURRENT: 075",
    )
    assert findings == []


def test_brain_check_uses_registry_load_order(tmp_path: Path) -> None:
    reg = tmp_path / "PM_Pack/automation/BRAIN_REGISTRY.yml"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text(
        "load_order:\n  core:\n    - a.md\n    - b.md\n",
        encoding="utf-8",
    )
    (tmp_path / "a.md").write_text("a", encoding="utf-8")
    (tmp_path / "b.md").write_text("b", encoding="utf-8")
    (tmp_path / "PM_Pack/01_pm_instructions").mkdir(parents=True, exist_ok=True)
    (tmp_path / "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md").write_text("x", encoding="utf-8")
    result = pm_pack_loader.brain_check(tmp_path)
    core_entries = [line for line in result.passed if line.startswith("PASS [core]")]
    assert core_entries == ["PASS [core]: a.md", "PASS [core]: b.md"]
