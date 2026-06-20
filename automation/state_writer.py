"""
state_writer.py — Write heartbeat, run records, controller state, and cycle logs.
All runner-side state lives in C:\\AI_Runner\\; repo-visible state in PM_Pack/automation/.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from automation import runner_paths


def _atomic_write_text(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` atomically via a same-dir temp file + os.replace.

    Writing to a temp file in the same directory and then ``os.replace`` makes
    the swap atomic on the same filesystem, so a reader never sees a partial
    file. The temp file is cleaned up on failure.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp_path, path)
    except Exception:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise

# Resolved from runner_paths at import; kept as module attributes for backward
# compatibility. Writes resolve the directory lazily (see write functions) so a
# test that sets AUTOPILOT_RUNNER_ROOT redirects correctly.
RUNNER_STATE_DIR = runner_paths.state_dir()
RUNNER_RUNS_DIR = runner_paths.runs_dir()
HEARTBEAT_PATH = RUNNER_STATE_DIR / "heartbeat.json"
CONTROLLER_STATE_PATH = RUNNER_STATE_DIR / "controller_state.json"

# Frozen import-time defaults. Resolvers compare the public constants against
# THESE (not the live env value) so a monkeypatched constant is honoured while
# an unmodified constant defers to the live env -- making a late
# AUTOPILOT_RUNNER_ROOT change (any import order) always win (no stale live path).
_ORIG_RUNNER_STATE_DIR = RUNNER_STATE_DIR
_ORIG_RUNNER_RUNS_DIR = RUNNER_RUNS_DIR
_ORIG_HEARTBEAT_PATH = HEARTBEAT_PATH
_ORIG_CONTROLLER_STATE_PATH = CONTROLLER_STATE_PATH


def _state_dir() -> Path:
    """Lazy state dir: honour a monkeypatched RUNNER_STATE_DIR, else live env."""
    return (
        RUNNER_STATE_DIR
        if RUNNER_STATE_DIR != _ORIG_RUNNER_STATE_DIR
        else runner_paths.state_dir()
    )


def _runs_dir() -> Path:
    """Lazy runs dir: honour a monkeypatched RUNNER_RUNS_DIR, else live env."""
    return (
        RUNNER_RUNS_DIR
        if RUNNER_RUNS_DIR != _ORIG_RUNNER_RUNS_DIR
        else runner_paths.runs_dir()
    )


def _heartbeat_path() -> Path:
    """Honour a monkeypatched HEARTBEAT_PATH, else derive from the live state dir."""
    return (
        HEARTBEAT_PATH
        if HEARTBEAT_PATH != _ORIG_HEARTBEAT_PATH
        else _state_dir() / "heartbeat.json"
    )


def _controller_state_path() -> Path:
    """Honour a monkeypatched CONTROLLER_STATE_PATH, else derive from live state dir."""
    return (
        CONTROLLER_STATE_PATH
        if CONTROLLER_STATE_PATH != _ORIG_CONTROLLER_STATE_PATH
        else _state_dir() / "controller_state.json"
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()


def write_heartbeat(state: str, cycle: int | None = None,
                    agent: str | None = None) -> None:
    """Update the heartbeat file. Called frequently during active runs."""
    heartbeat_path = _heartbeat_path()
    heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_seen": _now(),
        "state": state,
        "cycle": cycle,
        "agent": agent,
        "pid": os.getpid(),
    }
    heartbeat_path.write_text(json.dumps(payload, indent=2))


def write_controller_state(state: str, cycle: int | None = None,
                            branch: str | None = None,
                            pr: int | None = None,
                            run_id: str | None = None,
                            last_successful: str | None = None,
                            *, allow_lower: bool = False,
                            clear_pr: bool = False) -> None:
    """Read-merge-write controller_state.json atomically and monotonically.

    The ``active_cycle`` is monotonic by default: a ``cycle`` arg lower than the
    existing ``active_cycle`` is ignored (the existing value is kept) so a stale
    reading can never roll the authoritative cycle backwards. All other field
    updates still apply. Pass ``allow_lower=True`` to bypass the guard for an
    explicit operator override (e.g. force_set).

    ``active_pr`` is sticky once set (so a retry tick can re-read it). Item 3.2:
    pass ``clear_pr=True`` to DROP ``active_pr`` after a PR has been merged, so
    the next cycle does not inherit the previous cycle's PR number. ``clear_pr``
    is applied after the ``pr`` set, so passing both is a no-op clear.
    """
    controller_state_path = _controller_state_path()
    controller_state_path.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_json(controller_state_path)
    payload = {
        **existing,
        "runner": "fiverr-runner-local-01",
        "last_heartbeat": _now(),
        "status": state,
    }
    if run_id:
        payload["last_run_id"] = run_id
    if cycle:
        existing_cycle = existing.get("active_cycle")
        if (
            not allow_lower
            and existing_cycle is not None
            and int(cycle) < int(existing_cycle)
        ):
            print(
                f"[state_writer] monotonic guard: refusing to lower active_cycle "
                f"{existing_cycle} -> {cycle}; keeping {existing_cycle}",
                file=sys.stderr,
            )
            # keep existing active_cycle (carried over from **existing)
        else:
            payload["active_cycle"] = cycle
    if branch:
        payload["active_branch"] = branch
    if pr:
        payload["active_pr"] = pr
    if clear_pr:
        payload.pop("active_pr", None)
    if last_successful:
        payload["last_successful_state"] = last_successful
    _atomic_write_text(controller_state_path, json.dumps(payload, indent=2))


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
    run_dir = _runs_dir() / f"CYCLE_{cycle:03d}" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    for subdir in ("prompts", "agent_runs", "validations", "github", "jira", "repair"):
        (run_dir / subdir).mkdir(exist_ok=True)
    return run_dir


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}
