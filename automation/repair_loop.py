"""
repair_loop.py â€” Repair loop dispatcher for failed agent runs.

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
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).parent.parent
MAX_REPAIR_ATTEMPTS: int = 3
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
    run_dir: Path | None = None,
    errors: list[str] | None = None,
    failure_type: str | None = None,
    original_prompt_path: str | None = None,
    changed_files: list[str] | None = None,
    validation_output: str | None = None,
    repo_root: Path = REPO_ROOT,
    runner_root: Path = Path("C:/AI_Runner"),
) -> RepairResult:
    """
    Attempt to repair a failed agent run.
    Called by run-agent lifecycle after VALIDATION_FAILED.
    """
    run_dir = run_dir or (runner_root / "runs" / f"CYCLE_{cycle:03d}" / "repair")
    errors = errors or []

    state_path = runner_root / "state" / f"repair_state_{agent_id}_{cycle}.json"
    repair_state = _load_record(state_path)
    attempt = int(repair_state.get("attempt_count", 0)) + 1

    result = RepairResult(
        agent=agent_id,
        cycle=cycle,
        attempt=attempt,
        errors_in=errors,
    )

    if attempt >= MAX_REPAIR_ATTEMPTS:
        result.status = "BLOCKED"
        quarantine_agent_work(agent_id, cycle, repo_root, runner_root)
        _notify_repair_blocked(agent_id, cycle, attempt, errors)
        _save_repair_state(state_path, agent_id, cycle, attempt, errors)
        return result

    # Classify failure
    failure_type = failure_type or _classify_failure(errors)

    # Generate repair prompt
    repair_prompt = _generate_repair_prompt(
        agent_id=agent_id,
        cycle=cycle,
        errors=errors,
        failure_type=failure_type,
        attempt=attempt,
        original_prompt_path=original_prompt_path,
        validation_output=validation_output,
        report_path=str(run_dir / "repair_report.md"),
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
            result.status = "REPAIRED"
            # Commit
            from automation.run_agent_lifecycle import _commit_agent_work, _get_changed_files

            files = _get_changed_files()
            sha = _commit_agent_work(agent_id, cycle, files)
            result.commit_sha = sha
        else:
            result.status = "FAILED"
            result.errors_out = [details]
    else:
        result.status = "FAILED"
        result.errors_out = [f"Cursor returned: {cursor_result.status}"]

    record_path = run_dir / REPAIR_RECORD_FILE
    _save_record(record_path, result, _load_record(record_path))
    _save_repair_state(state_path, agent_id, cycle, attempt, errors)

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
    original_prompt_path: str | None = None,
    validation_output: str | None = None,
    report_path: str | None = None,
) -> str:
    """Generate a targeted repair prompt â€” scope limited to failing files only."""
    now = datetime.now(UTC).isoformat()
    error_text = "\n".join(f"  - {e}" for e in errors[:10])
    failure_label = {
        "ruff_failure": "Ruff lint failure",
        "lint": "Ruff lint failure",
        "mypy_failure": "Mypy type error",
        "typecheck": "Mypy type error",
        "pytest_failure": "Pytest failure",
        "test": "Pytest failure",
        "coverage_failure": "Coverage below threshold",
        "missing_report": "Agent report not found",
        "report": "Agent report not found",
    }.get(failure_type.lower(), failure_type.upper())
    original_prompt = ""
    if original_prompt_path and Path(original_prompt_path).exists():
        original_prompt = Path(original_prompt_path).read_text(encoding="utf-8", errors="replace")[:500]
    validation_tail = (validation_output or "")[-2000:]

    return f"""# REPAIR PROMPT â€” Agent {agent_id} Cycle {cycle:03d} Attempt {attempt}

## Context
A previous agent run failed validation. This is a targeted repair run.
Do NOT re-implement features. Fix ONLY the specific errors listed below.

## Model Policy
- Model: Codex 5.3
- Effort: medium
- Auto model selection: DISABLED

## Failure Type: {failure_label}

## Original Mission (first 500 chars)
{original_prompt or "N/A"}

## Errors to Fix
{error_text}

## Exact Error Output (last 2000 chars)
{validation_tail or "N/A"}

## Instructions
1. Confirm you are on branch: `cycle/{cycle:03d}/integration`
2. Fix ONLY the files causing the errors above
3. Do NOT modify files outside your scope
4. Run validation after fixing:
   - `python -m ruff check src/ automation/ --output-format=full`
   - `python -m mypy src/ --ignore-missing-imports`
   - `python -m pytest tests/ -q --tb=short -x`
5. Stop conditions:
   - Stop after validation passes and report is written
   - Stop immediately if unauthorized files would be changed
6. Write report to: `{report_path or 'N/A'}`

## Autonomy Rule
Proceed without confirmation. Fix the errors and commit.

====================================================================
END OF PROMPT â€” AGENT {agent_id} REPAIR ATTEMPT {attempt}
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


def _save_repair_state(
    path: Path,
    agent: str,
    cycle: int,
    attempt: int,
    errors: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_record(path)
    history = existing.get("failures", [])
    history.extend(errors)
    payload = {
        "agent": agent,
        "cycle": cycle,
        "attempt_count": attempt,
        "failures": history,
        "started_at": existing.get("started_at", datetime.now(UTC).isoformat()),
        "last_attempt_at": datetime.now(UTC).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def quarantine_agent_work(agent: str, cycle: int, repo_root: Path, runner_root: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    subprocess.run(
        [
            "git",
            "stash",
            "push",
            "--include-untracked",
            "-m",
            f"quarantine-cycle-{cycle:03d}-agent-{agent}-{timestamp}",
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    stash_ref_cmd = subprocess.run(
        ["git", "stash", "list"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    stash_reference = stash_ref_cmd.stdout.splitlines()[0] if stash_ref_cmd.stdout else "unknown"
    incident_dir = runner_root / "reports/incidents"
    incident_dir.mkdir(parents=True, exist_ok=True)
    incident = incident_dir / f"QUARANTINE_{cycle:03d}_{agent}_{timestamp}.md"
    state_path = runner_root / "state" / f"repair_state_{agent}_{cycle}.json"
    state_payload = _load_record(state_path)
    failures = state_payload.get("failures", [])
    incident.write_text(
        "\n".join(
            [
                f"# Quarantine Incident cycle {cycle:03d} agent {agent}",
                f"- Timestamp: {datetime.now(UTC).isoformat()}",
                f"- Stash reference: {stash_reference}",
                "- Reason: max attempts exceeded",
                f"- Failures: {failures}",
            ]
        ),
        encoding="utf-8",
    )
    from automation import notification_router

    notification_router.notify_blocked(
        f"Agent {agent} quarantined after repair limit",
        incident_code="MAX_REPAIR_ATTEMPTS_EXCEEDED",
        cycle=cycle,
    )
    return incident


def revert_accepted_agent(commit_sha: str, reason: str, repo_root: Path) -> str:
    _ = (commit_sha, reason)
    subprocess.run(
        ["git", "revert", "HEAD", "--no-edit"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=True,
    )
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=True,
    )
    return sha.stdout.strip()


def update_pr_after_repair(
    pr_number: int,
    repair_attempt: int,
    validation_result: str,
    client: Any,
) -> None:
    client.add_pr_comment(
        pr_number,
        f"Repair attempt {repair_attempt}: {validation_result}. See run log for details.",
    )


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
