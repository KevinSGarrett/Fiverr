"""
repair_loop.py — Repair loop dispatcher for failed agent runs.

When run-agent lifecycle returns VALIDATION_FAILED, this module:
  1. Classifies the failure (lint / type / test / report missing / ownership)
  2. Generates a targeted repair prompt scoped only to broken files
  3. Dispatches Cursor CLI with the repair prompt
  4. Caps at MAX_REPAIR_ATTEMPTS before escalating to BLOCKED

Wave 04 design: repair loop is NOT a full re-run.
It passes only the failing files and error context back to Cursor.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path("C:/Fiverr/Fiverr")
MAX_REPAIR_ATTEMPTS = 3
REPAIR_RECORD_FILE = "repair_record.json"


@dataclass
class RepairResult:
    agent: str
    cycle: int
    attempt: int
    status: str = "IN_PROGRESS"  # REPAIRED | FAILED | BLOCKED | SKIPPED | IN_PROGRESS
    errors_in: list[str] = field(default_factory=list)
    errors_out: list[str] = field(default_factory=list)
    repair_prompt_path: str = ""
    commit_sha: str = ""


def dispatch_repair(
    agent_id: str,
    cycle: int,
    run_dir: Path,
    errors: list[str],
) -> RepairResult:
    """
    Attempt to repair a failed agent run.
    Called by run-agent lifecycle after VALIDATION_FAILED.
    """
    # Check attempt count
    record_path = run_dir / REPAIR_RECORD_FILE
    record = _load_record(record_path)
    attempt = record.get("attempt", 0) + 1

    result = RepairResult(
        agent=agent_id,
        cycle=cycle,
        attempt=attempt,
        errors_in=errors,
    )

    if attempt > MAX_REPAIR_ATTEMPTS:
        result.status = "BLOCKED"
        _notify_repair_blocked(agent_id, cycle, attempt, errors)
        _save_record(record_path, result, record)
        return result

    # Classify failure
    failure_type = _classify_failure(errors)

    # Generate repair prompt
    repair_prompt = _generate_repair_prompt(
        agent_id, cycle, errors, failure_type, attempt
    )
    prompt_path = run_dir / f"REPAIR_{agent_id}_attempt_{attempt:02d}.md"
    prompt_path.write_text(repair_prompt, encoding="utf-8")
    result.repair_prompt_path = str(prompt_path)

    # Dispatch Cursor with repair prompt
    from automation.cursor_adapter import run_agent as cursor_run
    agent_dir = run_dir / "repair_runs" / f"attempt_{attempt:02d}"
    cursor_result = cursor_run(
        agent_id=f"{agent_id}_repair_{attempt}",
        prompt_path=str(prompt_path),
        working_dir=str(REPO_ROOT),
        output_dir=str(agent_dir),
    )

    if cursor_result.status == "complete":
        # Re-run validation
        from automation.run_agent_lifecycle import _run_validation
        passed, details = _run_validation(agent_id)
        if passed:
            # Commit
            from automation.run_agent_lifecycle import _commit_agent_work, _get_changed_files
            files = _get_changed_files()
            sha = _commit_agent_work(agent_id, cycle, files)
            result.commit_sha = sha
            # Audit #15: REPAIRED requires a REAL commit. A re-validation that passes
            # with NO file change yields an empty sha; calling that REPAIRED would
            # report success with nothing committed (downstream then re-fails it).
            if sha:
                result.status = "REPAIRED"
                # Audit #4 / Codex P1 (#141): the agent's ORIGINAL run-record still
                # says VALIDATION_FAILED. run-agent now exits 0 on REPAIRED, but
                # cmd_run_cycle's work-proof cross-check re-reads that record and
                # treats VALIDATION_FAILED as a failed agent → POST_CYCLE_FAIL. Persist
                # the repaired status to the run-record so the cross-check sees success.
                _mark_run_record_repaired(agent_id, cycle, run_dir, sha)
            else:
                result.status = "FAILED"
                result.errors_out = ["repair re-validation passed but produced no commit"]
        else:
            result.status = "FAILED"
            result.errors_out = [details]
    else:
        result.status = "FAILED"
        result.errors_out = [f"Cursor returned: {cursor_result.status}"]

    _save_record(record_path, result, record)

    # Notify
    from automation.notification_router import notify_blocked, notify_info
    if result.status == "REPAIRED":
        notify_info(f"Repair PASS: Agent {agent_id} cycle {cycle} attempt {attempt}")
    else:
        notify_blocked(
            f"Repair FAIL: Agent {agent_id} attempt {attempt}/{MAX_REPAIR_ATTEMPTS}",
            incident_code="REPAIR_FAILED", cycle=cycle
        )

    return result


def _mark_run_record_repaired(agent_id: str, cycle: int, run_dir: Path, sha: str) -> None:
    """Rewrite the agent's run-record so its lifecycle status reflects the REPAIR.

    The original record (written by run_agent_lifecycle._write_record at
    ``run_dir/agent_<id>_run_record.json``) still carries VALIDATION_FAILED. The
    controller's work-proof cross-check reads ``lifecycle_status`` (falling back to
    ``status``) and treats VALIDATION_FAILED as a failed agent. After a successful
    repair we set both to REPAIRED (NOT in the failed set) and stamp the commit_sha
    so the cross-check counts the agent as completed. Best-effort: never raises.
    """
    try:
        path = run_dir / f"agent_{agent_id}_run_record.json"
        data: dict = {}
        if path.exists():
            try:
                data = json.loads(path.read_text())
            except Exception:
                data = {}
        data["lifecycle_status"] = "REPAIRED"
        data["status"] = "REPAIRED"
        data["commit_sha"] = sha
        data["repaired"] = True
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


def _classify_failure(errors: list[str]) -> str:
    """Classify failure type from error messages."""
    err_text = " ".join(errors).lower()
    if "ruff" in err_text or "lint" in err_text:
        return "lint"
    if "mypy" in err_text or "type" in err_text:
        return "typecheck"
    if "pytest" in err_text or "test" in err_text:
        return "test"
    if "no_report" in err_text or "report" in err_text:
        return "report"
    if "ownership" in err_text:
        return "ownership"
    return "general"


def _generate_repair_prompt(
    agent_id: str,
    cycle: int,
    errors: list[str],
    failure_type: str,
    attempt: int,
) -> str:
    """Generate a targeted repair prompt — scope limited to failing files only."""
    now = datetime.now(UTC).isoformat()
    error_text = "\n".join(f"  - {e}" for e in errors[:10])

    return f"""# REPAIR PROMPT — Agent {agent_id} Cycle {cycle:03d} Attempt {attempt}

## Context
A previous agent run failed validation. This is a targeted repair run.
Do NOT re-implement features. Fix ONLY the specific errors listed below.

## Model Policy
- Model: Codex 5.3
- Effort: medium
- Auto model selection: DISABLED

## Failure Type: {failure_type.upper()}

## Errors to Fix
{error_text}

## Instructions
1. Confirm you are on branch: `cycle/{cycle:03d}/integration`
2. Fix ONLY the files causing the errors above
3. Do NOT modify files outside your scope
4. Run validation after fixing:
   - `python -m ruff check src/ automation/ --output-format=text`
   - `python -m mypy src/ --ignore-missing-imports`
   - `python -m pytest tests/ -q --tb=short -x`
5. Commit the fix: `git commit -m "fix(repair): Agent {agent_id} repair attempt {attempt} [autonomous]"`

## Autonomy Rule
Proceed without confirmation. Fix the errors and commit.

====================================================================
END OF PROMPT — AGENT {agent_id} REPAIR ATTEMPT {attempt}
====================================================================

<!-- Generated: {now} -->
"""


def _load_record(path: Path) -> dict:
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}


def _save_record(path: Path, result: RepairResult, existing: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        **existing,
        "attempt": result.attempt,
        "last_status": result.status,
        "last_errors": result.errors_in,
        "updated_at": datetime.now(UTC).isoformat(),
        "history": existing.get("history", []) + [{
            "attempt": result.attempt,
            "status": result.status,
            "prompt": result.repair_prompt_path,
        }],
    }
    path.write_text(json.dumps(data, indent=2))


def _notify_repair_blocked(agent_id: str, cycle: int, attempt: int, errors: list[str]) -> None:
    try:
        from automation.notification_router import notify_blocked
        notify_blocked(
            f"REPAIR BLOCKED: Agent {agent_id} cycle {cycle} exceeded {MAX_REPAIR_ATTEMPTS} attempts.\n"
            f"Last errors: {errors[:2]}",
            incident_code="REPAIR_MAX_ATTEMPTS_EXCEEDED",
            cycle=cycle,
        )
    except Exception:
        pass
