from __future__ import annotations

from pathlib import Path

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
