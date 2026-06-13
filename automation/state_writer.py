"""State/document writers for runner state and PM_Pack updates."""
from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

RUNNER_STATE_DIR = Path("C:/AI_Runner/state")
RUNNER_RUNS_DIR = Path("C:/AI_Runner/runs")
HEARTBEAT_PATH = RUNNER_STATE_DIR / "heartbeat.json"
CONTROLLER_STATE_PATH = RUNNER_STATE_DIR / "controller_state.json"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def write_heartbeat(
    status: str,
    cycle: int | None,
    agent: str | None = None,
    runner_root: Path = Path("C:/AI_Runner"),
) -> None:
    """Write the runner heartbeat file with UTC timestamp and active process details."""
    state_dir = runner_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_seen": datetime.now(UTC).isoformat(),
        "status": status,
        "active_cycle": cycle,
        "active_agent": agent,
        "pid": os.getpid(),
    }
    (state_dir / "heartbeat.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_controller_state(state: str, cycle: int | None = None,
                            branch: str | None = None,
                            pr: int | None = None,
                            run_id: str | None = None,
                            last_successful: str | None = None) -> None:
    RUNNER_STATE_DIR.mkdir(parents=True, exist_ok=True)
    existing = _load_json(CONTROLLER_STATE_PATH)
    payload = {
        **existing,
        "runner": "fiverr-runner-local-01",
        "last_heartbeat": _now(),
        "status": state,
    }
    if run_id:
        payload["last_run_id"] = run_id
    if cycle:
        payload["active_cycle"] = cycle
    if branch:
        payload["active_branch"] = branch
    if pr:
        payload["active_pr"] = pr
    if last_successful:
        payload["last_successful_state"] = last_successful
    CONTROLLER_STATE_PATH.write_text(json.dumps(payload, indent=2))


def update_hydration_header(
    cycle: int,
    scores: dict[str, Any],
    branch: str,
    blockers: list[str],
    repo_root: Path,
) -> None:
    """Apply targeted regex replacements in HYDRATION_HEADER.md."""
    path = repo_root / "PM_Pack/07_hydration/HYDRATION_HEADER.md"
    if not path.exists():
        return

    text = path.read_text(encoding="utf-8")
    text = re.sub(r"Active cycle:\s*\d+", f"Active cycle: {cycle}", text)
    text = re.sub(
        r"Score 1[^:]*:\s*~?\d+%",
        f"Score 1 (Internal Build Progress): ~{scores.get('s1', 0)}%",
        text,
    )
    text = re.sub(
        r"Score 2[^:]*:\s*~?\d+%",
        f"Score 2 (Production Readiness): ~{scores.get('s2', 0)}%",
        text,
    )
    text = re.sub(r"cycle/\d+/integration", branch, text)
    if blockers:
        text = re.sub(r"Blockers:[^\n]*", f"Blockers: {', '.join(blockers)}", text)
    path.write_text(text, encoding="utf-8")


def update_current_state_canonical(
    cycle: int,
    status: str,
    scores: dict[str, Any],
    repo_root: Path,
) -> None:
    """Update cycle/status/score fields in CURRENT_STATE_CANONICAL.md."""
    path = repo_root / "PM_Pack/CURRENT_STATE_CANONICAL.md"
    if not path.exists():
        return

    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(Cycle[:\s]+)\d+", rf"\g<1>{cycle}", text)
    text = re.sub(r"(Status[:\s]+)[A-Z_]+", rf"\g<1>{status}", text)
    text = re.sub(r"(Score 1[:\s]+)~?\d+%?", rf"\g<1>~{scores.get('s1', 0)}%", text)
    text = re.sub(r"(Score 2[:\s]+)~?\d+%?", rf"\g<1>~{scores.get('s2', 0)}%", text)
    path.write_text(text, encoding="utf-8")


def write_cycle_log_entry(
    cycle: int,
    run_id: str,
    commit_shas: list[str],
    agents_complete: list[str],
    scores: dict[str, Any],
    repo_root: Path,
) -> Path:
    """Create or append a per-cycle log entry in CYCLE_XXX_LOG.md idempotently."""
    log_dir = repo_root / "PM_Pack/10_cycle_log"
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"CYCLE_{cycle:03d}_LOG.md"
    section_header = f"## Run {run_id}"

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if section_header in existing:
            return path
        text = existing.rstrip() + "\n\n"
    else:
        text = f"# Cycle {cycle:03d} Log\n\n"

    section = [
        section_header,
        f"- Timestamp: {_now()}",
        f"- Commits: {', '.join(commit_shas) if commit_shas else 'none'}",
        f"- Agents complete: {', '.join(agents_complete) if agents_complete else 'none'}",
        f"- Scores: S1={scores.get('s1', 0)} S2={scores.get('s2', 0)}",
    ]
    text += "\n".join(section) + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def update_production_readiness_scorecard(
    cycle: int,
    score1: float,
    score2: float,
    delta1: float,
    delta2: float,
    repo_root: Path,
) -> None:
    """Upsert a cycle row in PRODUCTION_READINESS_SCORECARD.md."""
    path = repo_root / "PM_Pack/PRODUCTION_READINESS_SCORECARD.md"
    row = f"| {cycle} | {score1:.1f} | {score2:.1f} | {delta1:+.1f} | {delta2:+.1f} |"
    if not path.exists():
        header = (
            "| Cycle | Score1 | Score2 | Delta1 | Delta2 |\n"
            "| --- | --- | --- | --- | --- |\n"
        )
        path.write_text(header + row + "\n", encoding="utf-8")
        return

    lines = path.read_text(encoding="utf-8").splitlines()
    replaced = False
    for idx, line in enumerate(lines):
        if f"| {cycle} |" in line:
            lines[idx] = row
            replaced = True
            break
    if not replaced:
        lines.append(row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_epic_status_tracker(
    cycle: int,
    completed_story_keys: list[str],
    repo_root: Path,
) -> None:
    """Mark completed stories as COMPLETE in EPIC_STATUS_TRACKER.md."""
    _ = cycle
    path = repo_root / "PM_Pack/08_task_queue/EPIC_STATUS_TRACKER.md"
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    updated: list[str] = []
    for line in lines:
        changed = line
        for key in completed_story_keys:
            if key in changed:
                changed = changed.replace("IN_PROGRESS", "COMPLETE").replace("TODO", "COMPLETE")
        updated.append(changed)
    path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def write_run_summary(cycle: int, run_id: str, summary: dict[str, Any], output_dir: Path) -> Path:
    """Write markdown summary for a cycle run."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"CYCLE_{cycle:03d}_RUN_SUMMARY.md"
    lines = [f"# Cycle {cycle:03d} Run Summary", f"Run ID: {run_id}", ""]
    for key, value in summary.items():
        lines.append(f"## {key}")
        lines.append(str(value))
        lines.append("")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return path


def write_validation_summary(cycle: int, results: dict[str, Any], output_dir: Path) -> Path:
    """Write markdown validation summary artifact."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"CYCLE_{cycle:03d}_VALIDATION_SUMMARY.md"
    lines = [f"# Cycle {cycle:03d} Validation Summary", ""]
    for key in ("ruff", "mypy", "pytest", "coverage"):
        lines.append(f"- {key}: {results.get(key, 'N/A')}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_agent_run_record(run_dir: Path, agent: str, cycle: int,
                            prompt_path: str, result: Any,
                            validation: dict | None = None,
                            jira_updates: list[str] | None = None) -> Path:
    """Write per-agent run record JSON."""
    run_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "agent": agent,
        "cycle": cycle,
        "prompt_path": prompt_path,
        "started_at": getattr(result, "started_at", _now()),
        "ended_at": getattr(result, "ended_at", _now()),
        "status": getattr(result, "status", "unknown"),
        "exit_code": getattr(result, "exit_code", None),
        "files_changed": [],
        "validation": validation or {},
        "jira_updates": jira_updates or [],
        "commit_sha": None,
        "report_path": None,
    }
    path = run_dir / f"agent_{agent}_run_record.json"
    path.write_text(json.dumps(record, indent=2))
    return path


def write_repair_record(run_dir: Path, agent: str, cycle: int,
                         attempt: int, failure_type: str,
                         result: str) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "cycle": cycle,
        "agent": agent,
        "attempt": attempt,
        "failure_type": failure_type,
        "repair_started_at": _now(),
        "result": result,
    }
    path = run_dir / f"repair_{attempt:02d}_{agent}.json"
    path.write_text(json.dumps(record, indent=2))
    return path


def write_run_summary_for_run_dir(run_dir: Path, cycle: int, agents: list[str],
                                  results: dict[str, Any]) -> Path:
    """Write human-readable RUN_SUMMARY.md for the cycle."""
    lines = [
        f"# Run Summary — Cycle {cycle:03d}",
        f"Generated: {_now()}",
        "",
        "## Agents",
    ]
    for agent in agents:
        r = results.get(agent, {})
        status = r.get("status", "unknown") if isinstance(r, dict) else getattr(r, "status", "unknown")
        lines.append(f"- Agent {agent}: {status}")
    lines += ["", "## Artifacts", f"Run directory: {run_dir}"]
    path = run_dir / "RUN_SUMMARY.md"
    path.write_text("\n".join(lines))
    return path


def make_run_dir(cycle: int, run_id: str) -> Path:
    """Create and return the per-cycle run directory under C:\\AI_Runner\\runs."""
    run_dir = RUNNER_RUNS_DIR / f"CYCLE_{cycle:03d}" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    for subdir in ("prompts", "agent_runs", "validations", "github", "jira", "repair"):
        (run_dir / subdir).mkdir(exist_ok=True)
    return run_dir


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}
