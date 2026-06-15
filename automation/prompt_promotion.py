"""Promotion workflow for prompt drafts to validated prompts."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from automation.prompt_validator import PromptValidationResult, validate


REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = REPO_ROOT / "PM_Pack" / "automation" / "prompts"
DRAFTS_DIR = PROMPTS_DIR / "drafts"
VALIDATED_DIR = PROMPTS_DIR / "validated"
DEFAULT_AGENTS = ["A", "B", "E", "C", "F", "D"]


@dataclass
class PromotionSummary:
    promoted: int
    rejected: int
    results: list[dict[str, object]]


class PromptPromoter:
    """Validate and promote drafts into validated prompt artifacts."""

    def __init__(
        self,
        drafts_dir: Path | None = None,
        validated_dir: Path | None = None,
        prompts_dir: Path | None = None,
        validator: Callable[[str | Path, str, int], PromptValidationResult] | None = None,
    ) -> None:
        self.drafts_dir = drafts_dir or DRAFTS_DIR
        self.validated_dir = validated_dir or VALIDATED_DIR
        self.prompts_dir = prompts_dir or PROMPTS_DIR
        self.validator = validator or validate

    def _draft_path(self, cycle: str, agent: str) -> Path:
        primary = self.drafts_dir / f"CYCLE_{cycle}_AGENT_{agent}_DRAFT.md"
        if primary.exists():
            return primary
        fallback = self.drafts_dir / f"CYCLE_{cycle}_AGENT_{agent}_PROMPT.md"
        return fallback

    def promote_all(self, cycle: str, agents: list[str] | None = None) -> PromotionSummary:
        self.validated_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        selected_agents = agents or list(DEFAULT_AGENTS)

        promoted = 0
        rejected = 0
        results: list[dict[str, object]] = []

        for agent in selected_agents:
            draft_path = self._draft_path(cycle=cycle, agent=agent)
            validation = self.validator(draft_path, agent, int(cycle))
            if validation.passed:
                promoted += 1
                validated_path = self.validated_dir / f"CYCLE_{cycle}_AGENT_{agent}_PROMPT.md"
                root_path = self.prompts_dir / f"CYCLE_{cycle}_AGENT_{agent}_PROMPT.md"
                shutil.copyfile(draft_path, validated_path)
                shutil.copyfile(draft_path, root_path)
                results.append(
                    {
                        "agent": agent,
                        "status": "PROMOTED",
                        "task_count": validation.task_count,
                        "warnings": validation.warnings,
                    }
                )
                continue

            rejected += 1
            rejection = {
                "cycle": cycle,
                "agent": agent,
                "status": "REJECTED",
                "errors": validation.errors,
                "warnings": validation.warnings,
                "generated_at": datetime.now(UTC).isoformat(),
            }
            rejection_path = self.drafts_dir / f"CYCLE_{cycle}_AGENT_{agent}_REJECTION.json"
            rejection_path.write_text(json.dumps(rejection, indent=2) + "\n", encoding="utf-8")
            results.append(
                {
                    "agent": agent,
                    "status": "REJECTED",
                    "rejection_path": str(rejection_path),
                }
            )

        return PromotionSummary(promoted=promoted, rejected=rejected, results=results)


def promote_all(cycle: str, agents: list[str] | None = None) -> PromotionSummary:
    return PromptPromoter().promote_all(cycle=cycle, agents=agents)
