"""
repair_prompt_builder.py -- Builds scoped, policy-bounded repair prompts.

ICV-REPAIR-1..4: Only targets FIXABLE_IN_SCOPE items; never exceeds agent lane.
"""
from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from automation.codex_verifier.schemas import (
    ChecklistItem,
    RepairDirective,
)

REPO_ROOT = Path("C:/Fiverr/Fiverr")


class RepairPromptBuilder:
    @staticmethod
    def build(
        original_prompt_text: str,
        contract: dict,
        fixable_items: list[ChecklistItem],
        attempt: int,
        cycle: int,
        agent: str,
        run_dir: Path,
    ) -> RepairDirective | None:
        """
        Build a scoped repair prompt targeting only fixable items.
        Returns None if no safe repair can be built.
        """
        if not fixable_items:
            return None

        cycle_s = f"{cycle:03d}"
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        prompt_path = run_dir / f"icv/repair_{cycle_s}_{agent}_attempt{attempt}_{ts}.md"
        prompt_path.parent.mkdir(parents=True, exist_ok=True)

        # Allowed paths from contract
        allowed_paths = contract.get("allowedpaths", [])
        blocked_paths = contract.get("blockedpaths", [])

        lines = [
            f"# ICV REPAIR PROMPT — Cycle {cycle_s} Agent {agent} Attempt {attempt}",
            f"Generated: {datetime.now(UTC).isoformat()}",
            "",
            "## IMPORTANT CONSTRAINTS",
            "- This is a TARGETED REPAIR. You must complete ONLY the specific items listed below.",
            "- Do NOT re-do work that was already completed correctly.",
            "- Stay strictly within your assigned file ownership.",
            f"- Allowed paths: {allowed_paths or '(inherit from original)'}",
            f"- Blocked paths: {blocked_paths or '(none)'}",
            "- After completing repairs, commit your changes and mark AGENT_COMPLETE in your report.",
            "",
            "## ORIGINAL CONTEXT (abbreviated)",
        ]

        # Include first 500 chars of original prompt for context
        if original_prompt_text:
            header_match = re.search(
                r"# CYCLE.*?AGENT.*?PROMPT.*?\n", original_prompt_text, re.IGNORECASE
            )
            if header_match:
                lines.append(header_match.group(0).strip())

        lines += [
            "",
            "## ITEMS TO REPAIR (in priority order)",
        ]

        for i, item in enumerate(fixable_items[:15], 1):  # cap at 15 items
            lines += [
                f"### Repair Item {i}: [{item.id}]",
                f"**Description:** {item.description}",
                f"**Evidence of failure:** {item.evidence or '(see checklist)'}",
                "**What to do:** Fix the issue described above. Provide evidence of completion.",
                "",
            ]

        lines += [
            "## COMPLETION REQUIREMENTS",
            "1. Complete ALL repair items listed above.",
            "2. Run validation to confirm each fix (command outputs in your report).",
            "3. Commit your changes to the integration branch.",
            "4. Update your agent report with the repairs made.",
            "5. End with AGENT_COMPLETE in your report.",
            "",
            "END OF REPAIR PROMPT",
        ]

        prompt_text = "\n".join(lines)
        prompt_path.write_text(prompt_text, encoding="utf-8")

        return RepairDirective(
            prompt_text=prompt_text,
            prompt_path=str(prompt_path),
            target_items=fixable_items,
            estimated_tokens=len(prompt_text.split()),
        )
