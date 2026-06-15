from __future__ import annotations

from pathlib import Path

from automation.prompt_promotion import PromptPromoter
from automation.prompt_validator import PromptValidationResult


def _passing_result(path: str | Path, agent: str, cycle: int) -> PromptValidationResult:
    return PromptValidationResult(
        prompt_path=str(path),
        agent=agent,
        cycle=cycle,
        passed=True,
        task_count=55,
    )


def _failing_result(path: str | Path, agent: str, cycle: int) -> PromptValidationResult:
    return PromptValidationResult(
        prompt_path=str(path),
        agent=agent,
        cycle=cycle,
        passed=False,
        errors=["Task floor violation"],
    )


def test_promote_all_promotes_when_validator_passes(tmp_path: Path) -> None:
    drafts = tmp_path / "drafts"
    validated = tmp_path / "validated"
    prompts = tmp_path / "prompts"
    drafts.mkdir(parents=True)
    for agent in ["A", "B", "E", "C", "F", "D"]:
        (drafts / f"CYCLE_080_AGENT_{agent}_DRAFT.md").write_text(
            "END OF PROMPT\n### Task 1\n",
            encoding="utf-8",
        )

    promoter = PromptPromoter(
        drafts_dir=drafts,
        validated_dir=validated,
        prompts_dir=prompts,
        validator=_passing_result,
    )
    summary = promoter.promote_all("080")
    assert summary.promoted == 6
    assert summary.rejected == 0
    assert (validated / "CYCLE_080_AGENT_A_PROMPT.md").exists()


def test_promote_all_writes_rejection_files(tmp_path: Path) -> None:
    drafts = tmp_path / "drafts"
    validated = tmp_path / "validated"
    prompts = tmp_path / "prompts"
    drafts.mkdir(parents=True)
    for agent in ["A", "B", "E", "C", "F", "D"]:
        (drafts / f"CYCLE_080_AGENT_{agent}_DRAFT.md").write_text(
            "bad draft",
            encoding="utf-8",
        )

    promoter = PromptPromoter(
        drafts_dir=drafts,
        validated_dir=validated,
        prompts_dir=prompts,
        validator=_failing_result,
    )
    summary = promoter.promote_all("080")
    assert summary.promoted == 0
    assert summary.rejected == 6
    assert (drafts / "CYCLE_080_AGENT_A_REJECTION.json").exists()
