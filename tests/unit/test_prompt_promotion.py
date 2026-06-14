from __future__ import annotations

import json
from pathlib import Path

import pytest
from automation.prompt_promotion import promote_prompt, write_validated_manifest


def test_promotion_succeeds_when_prompt_valid(tmp_path: Path) -> None:
    draft = tmp_path / "CYCLE_078_AGENT_A_PROMPT_DRAFT.md"
    draft.write_text("content", encoding="utf-8")

    class Result:
        passed = True
        errors: list[str] = []

    success, errors = promote_prompt(
        draft,
        tmp_path / "validated",
        validator_fn=lambda _: Result(),
    )
    assert success is True
    assert errors == []
    assert (tmp_path / "validated" / "CYCLE_078_AGENT_A_PROMPT.md").exists()


def test_promotion_fails_when_prompt_invalid(tmp_path: Path) -> None:
    draft = tmp_path / "CYCLE_078_AGENT_A_PROMPT_DRAFT.md"
    draft.write_text("content", encoding="utf-8")

    class Result:
        passed = False
        errors = ["bad prompt"]

    success, errors = promote_prompt(
        draft,
        tmp_path / "validated",
        validator_fn=lambda _: Result(),
    )
    assert success is False
    assert errors == ["bad prompt"]
    assert not (tmp_path / "validated" / "CYCLE_078_AGENT_A_PROMPT.md").exists()


def test_manifest_written_after_all_agents_promoted(tmp_path: Path) -> None:
    results = {
        "A": {"status": "PASS", "task_count": 55},
        "B": {"status": "PASS", "task_count": 56},
        "E": {"status": "PASS", "task_count": 57},
        "C": {"status": "PASS", "task_count": 58},
        "F": {"status": "PASS", "task_count": 59},
        "D": {"status": "PASS", "task_count": 60},
    }
    path = write_validated_manifest(78, tmp_path, results)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["cycle"] == 78
    assert payload["overall"] == "PASS"
    assert len(payload["agents"]) == 6


def test_default_validator_rejects_unrecognized_filename(tmp_path: Path) -> None:
    draft = tmp_path / "bad_name.md"
    draft.write_text("content", encoding="utf-8")
    success, errors = promote_prompt(draft, tmp_path / "validated")
    assert success is False
    assert errors and "Unrecognized prompt filename" in errors[0]


def test_default_validator_parses_cycle_and_agent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    draft = tmp_path / "CYCLE_078_AGENT_A_PROMPT_DRAFT.md"
    draft.write_text("content", encoding="utf-8")

    class Result:
        passed = True
        errors: list[str] = []

    def fake_validate(path: Path, agent: str, cycle: int) -> Result:
        assert str(path).endswith("CYCLE_078_AGENT_A_PROMPT_DRAFT.md")
        assert agent == "A"
        assert cycle == 78
        return Result()

    monkeypatch.setattr("automation.prompt_promotion.validate", fake_validate)
    success, errors = promote_prompt(draft, tmp_path / "validated")
    assert success is True
    assert errors == []
