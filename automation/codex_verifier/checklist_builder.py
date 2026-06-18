"""
checklist_builder.py -- Builds a machine-checkable checklist from contract + prompt.

ICV-CHECKLIST-1..4: Derives required items from jirascope AC/DoD,
validation_commands, deliverables, and prompt task headings.
"""
from __future__ import annotations

import re
from pathlib import Path

from automation.codex_verifier.schemas import (
    ChecklistItem,
)


class ChecklistBuilder:
    """Build the checklist for one agent from its contract + prompt text."""

    @staticmethod
    def build(prompt_text: str, contract: dict) -> list[ChecklistItem]:
        items: list[ChecklistItem] = []
        seen_ids: set[str] = set()

        def _add(item: ChecklistItem) -> None:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                items.append(item)

        # 1. Jira scope AC/DoD items
        for scope in contract.get("jirascope", []):
            key = scope.get("key", "UNKNOWN")
            for i, ac in enumerate(scope.get("acceptancecriteria", []), 1):
                _add(ChecklistItem(
                    id=f"AC-{key}-{i}",
                    source=f"contract.jirascope[{key}].acceptancecriteria",
                    description=str(ac)[:200],
                    is_blocking=True,
                ))
            for i, dod in enumerate(scope.get("dod", []), 1):
                _add(ChecklistItem(
                    id=f"DOD-{key}-{i}",
                    source=f"contract.jirascope[{key}].dod",
                    description=str(dod)[:200],
                    is_blocking=True,
                ))
            # Deliverable files
            for fpath in scope.get("filesormodules", []):
                _add(ChecklistItem(
                    id=f"FILE-{key}-{Path(fpath).name}",
                    source=f"contract.jirascope[{key}].filesormodules",
                    description=f"File/module must exist: {fpath}",
                    is_blocking=False,
                ))

        # 2. Validation commands
        for i, cmd in enumerate(contract.get("validationcommands", []), 1):
            cmd_str = str(cmd.get("command", cmd) if isinstance(cmd, dict) else cmd)
            _add(ChecklistItem(
                id=f"VCMD-{i}",
                source="contract.validationcommands",
                description=f"Validation command must pass: {cmd_str[:100]}",
                is_blocking=True,
            ))

        # 3. Report marker
        _add(ChecklistItem(
            id="REPORT-COMPLETE",
            source="agent.report",
            description="Agent report file must exist and contain AGENT_COMPLETE marker",
            is_blocking=True,
        ))

        # 4. At least one commit
        _add(ChecklistItem(
            id="GIT-COMMIT",
            source="git.commit",
            description="Agent must have committed at least one change this run",
            is_blocking=True,
        ))

        # 5. Prompt task headings (non-blocking, informational completeness)
        if prompt_text:
            tasks = re.findall(r"^#{2,4}\s+Task\s+(\d+)[:\s]+(.{10,100})", prompt_text, re.MULTILINE)
            for task_num, task_desc in tasks[:30]:  # cap at 30 to avoid noise
                _add(ChecklistItem(
                    id=f"TASK-{int(task_num):03d}",
                    source="prompt.task",
                    description=f"Task {task_num}: {task_desc.strip()[:100]}",
                    is_blocking=False,  # prompt tasks are informational; report is the truth
                ))

        return items
