"""Prompt promotion pipeline (draft -> validated)."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from automation.prompt_validator import PromptValidationResult, validate


def promote_prompt(
    draft_path: Path,
    validated_dir: Path,
    validator_fn: Callable[[Path], PromptValidationResult] | None = None,
) -> tuple[bool, list[str]]:
    """Validate a draft prompt and copy to validated dir when passing."""
    validator = validator_fn or _default_validator
    result = validator(draft_path)
    if not result.passed:
        return False, list(result.errors)

    validated_dir.mkdir(parents=True, exist_ok=True)
    validated_name = draft_path.name.replace("_DRAFT", "")
    validated_path = validated_dir / validated_name
    validated_path.write_text(draft_path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    return True, []


def write_validated_manifest(cycle: int, validated_dir: Path, agent_results: dict[str, dict[str, Any]]) -> Path:
    """Write CYCLE manifest for validated prompts."""
    validated_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "cycle": cycle,
        "generated_at": datetime.now(UTC).isoformat(),
        "overall": "PASS" if all(v.get("status") == "PASS" for v in agent_results.values()) else "FAIL",
        "agents": agent_results,
    }
    manifest_path = validated_dir / f"CYCLE_{cycle:03d}_MANIFEST.json"
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return manifest_path


def _default_validator(path: Path) -> PromptValidationResult:
    match = re.search(r"CYCLE_(\d{3})_AGENT_([A-Z])_PROMPT", path.name)
    if not match:
        result = PromptValidationResult(
            prompt_path=str(path),
            agent="?",
            cycle=0,
            passed=False,
            errors=[f"Unrecognized prompt filename: {path.name}"],
        )
        return result
    cycle = int(match.group(1))
    agent = match.group(2)
    return validate(path, agent, cycle)
