"""
deterministic_checker.py -- Non-LLM verification: runs validation_commands,
checks file existence, git commit, report marker. Source of truth.

ICV-DET-1..6: Determinism first, LLM second.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from automation.codex_verifier.schemas import (
    ChecklistItem,
    ChecklistStatus,
    EvidenceBundle,
    ItemClassification,
)

REPO_ROOT = Path("C:/Fiverr/Fiverr")
CMD_TIMEOUT = 60  # seconds per validation command


class DeterministicChecker:
    """Run all machine-verifiable checks and update checklist item statuses."""

    @staticmethod
    def run(
        checklist: list[ChecklistItem],
        evidence: EvidenceBundle,
    ) -> list[ChecklistItem]:
        """
        Returns the checklist with status + evidence populated for every item
        that can be machine-verified. LLM-only items remain UNVERIFIABLE.
        """
        updated = [_check_item(item, evidence) for item in checklist]
        # Run validation commands (H5 fix: C3.5 wire contract validation_commands)
        _run_validation_commands(evidence)
        # Re-check VCMD items with fresh results
        for item in updated:
            if item.id.startswith("VCMD-"):
                item = _check_vcmd(item, evidence)
        return updated

    @staticmethod
    def all_blocking_pass(checklist: list[ChecklistItem]) -> bool:
        return all(
            i.status == ChecklistStatus.SATISFIED
            for i in checklist
            if i.is_blocking
        )


def _check_item(item: ChecklistItem, ev: EvidenceBundle) -> ChecklistItem:
    item = ChecklistItem(**vars(item))  # shallow copy

    if item.id == "REPORT-COMPLETE":
        if ev.report_exists and ev.report_has_complete_marker:
            item.status = ChecklistStatus.SATISFIED
            item.evidence = "report exists + AGENT_COMPLETE marker found"
        elif ev.report_exists:
            item.status = ChecklistStatus.PARTIAL
            item.evidence = "report exists but no AGENT_COMPLETE marker"
        else:
            item.status = ChecklistStatus.MISSING
            item.evidence = f"report file not found (finalreportpath={ev.contract.get('finalreportpath','')})"
        return item

    if item.id == "GIT-COMMIT":
        if ev.committed_this_run:
            item.status = ChecklistStatus.SATISFIED
            item.evidence = f"{len(ev.changed_files)} files changed this run"
        else:
            item.status = ChecklistStatus.MISSING
            item.evidence = "no commits found for this run"
        return item

    if item.id.startswith("FILE-"):
        # Extract path from description
        desc = item.description
        for fpath, exists in ev.deliverable_exists.items():
            if fpath in desc:
                if exists:
                    item.status = ChecklistStatus.SATISFIED
                    item.evidence = f"file exists: {fpath}"
                else:
                    item.status = ChecklistStatus.MISSING
                    item.evidence = f"file not found: {fpath}"
                return item
        # If not in deliverable_exists map, check directly
        try:
            p_str = desc.replace("File/module must exist: ", "").strip()
            full = REPO_ROOT / p_str
            if full.exists():
                item.status = ChecklistStatus.SATISFIED
                item.evidence = f"exists: {full}"
            else:
                item.status = ChecklistStatus.MISSING
                item.evidence = f"not found: {full}"
        except Exception as exc:
            item.status = ChecklistStatus.UNVERIFIABLE
            item.evidence = f"file check error: {exc}"
        return item

    if item.id.startswith("AC-") or item.id.startswith("DOD-"):
        # Check if the AC/DOD keywords appear in the report
        if ev.report_text:
            # Extract the key concepts from the description
            words = [w for w in item.description.lower().split() if len(w) > 4][:5]
            if words and sum(1 for w in words if w in ev.report_text.lower()) >= 3:
                item.status = ChecklistStatus.SATISFIED
                item.evidence = "keywords found in agent report"
            else:
                item.status = ChecklistStatus.UNVERIFIABLE
                item.evidence = "insufficient keyword overlap in report (LLM needed for full AC check)"
        else:
            item.status = ChecklistStatus.UNVERIFIABLE
            item.evidence = "no report text to check against"
        return item

    # VCMD items handled separately after _run_validation_commands
    return item


def _check_vcmd(item: ChecklistItem, ev: EvidenceBundle) -> ChecklistItem:
    item = ChecklistItem(**vars(item))
    idx = int(item.id.replace("VCMD-", "")) - 1
    results = ev.validation_command_results
    if 0 <= idx < len(results):
        r = results[idx]
        if r.get("rc") == 0:
            item.status = ChecklistStatus.SATISFIED
            item.evidence = f"command passed (rc=0): {r.get('cmd','')[:80]}"
        else:
            item.status = ChecklistStatus.MISSING
            item.classification = ItemClassification.FIXABLE_IN_SCOPE
            item.evidence = (
                f"command failed (rc={r.get('rc')}): {r.get('cmd','')[:60]} "
                f"stderr={r.get('stderr','')[:100]}"
            )
    return item


def _run_validation_commands(ev: EvidenceBundle) -> None:
    """
    H5.3 / C3.5: Run contract.validationcommands and store results in
    ev.validation_command_results so the deterministic checker can use them.
    Skip in PYTEST env.
    """
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    commands = ev.contract.get("validationcommands", [])
    if not commands:
        return
    ev.validation_command_results = []
    for cmd_entry in commands:
        cmd = cmd_entry.get("command", cmd_entry) if isinstance(cmd_entry, dict) else str(cmd_entry)
        try:
            r = subprocess.run(
                cmd, shell=True, cwd=str(REPO_ROOT),
                capture_output=True, text=True, timeout=CMD_TIMEOUT,
            )
            ev.validation_command_results.append({
                "cmd": cmd,
                "rc": r.returncode,
                "stdout": r.stdout[-500:],
                "stderr": r.stderr[-500:],
            })
        except subprocess.TimeoutExpired:
            ev.validation_command_results.append({
                "cmd": cmd, "rc": -1,
                "stdout": "", "stderr": f"TIMEOUT after {CMD_TIMEOUT}s",
            })
        except Exception as exc:
            ev.validation_command_results.append({
                "cmd": cmd, "rc": -1,
                "stdout": "", "stderr": f"ERROR: {exc}",
            })
