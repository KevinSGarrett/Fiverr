"""
state_writer.py — Write heartbeat, run records, controller state, and cycle logs.
All runner-side state lives in C:\\AI_Runner\\; repo-visible state in PM_Pack/automation/.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUNNER_STATE_DIR = Path("C:/AI_Runner/state")
RUNNER_RUNS_DIR = Path("C:/AI_Runner/runs")
HEARTBEAT_PATH = RUNNER_STATE_DIR / "heartbeat.json"
CONTROLLER_STATE_PATH = RUNNER_STATE_DIR / "controller_state.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_heartbeat(state: str, cycle: int | None = None,
                    agent: str | None = None) -> None:
    """Update the heartbeat file. Called frequently during active runs."""
    RUNNER_STATE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_seen": _now(),
        "state": state,
        "cycle": cycle,
        "agent": agent,
        "pid": os.getpid(),
    }
    HEARTBEAT_PATH.write_text(json.dumps(payload, indent=2))


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
    if run_id:     payload["last_run_id"] = run_id
    if cycle:      payload["active_cycle"] = cycle
    if branch:     payload["active_branch"] = branch
    if pr:         payload["active_pr"] = pr
    if last_successful: payload["last_successful_state"] = last_successful
    CONTROLLER_STATE_PATH.write_text(json.dumps(payload, indent=2))


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


def write_run_summary(run_dir: Path, cycle: int, agents: list[str],
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
