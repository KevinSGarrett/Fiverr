"""
cursor_adapter.py — Wraps Cursor CLI for agent dispatch.
Uses Popen with live stdout/stderr streaming and no-output timeout detection.
Command syntax is config-driven; exact invocation finalized after CLI discovery.
"""
from __future__ import annotations

import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CURSOR_BINARY = "cursor"
DISCOVERY_LOG = Path("C:/AI_Runner/logs/cursor_cli_discovery.txt")
DEFAULT_TIMEOUT_MIN = 180
NO_OUTPUT_KILL_MIN = 45
REPO_ROOT = Path("C:/Fiverr/Fiverr")


@dataclass
class AgentRunResult:
    agent: str
    status: str        # complete | timeout | no_output | error | model_blocked
    started_at: str
    ended_at: str
    exit_code: int | None
    stdout_path: str = ""
    stderr_path: str = ""
    prompt_path: str = ""
    output_dir: str = ""
    error_message: str = ""
    stdout_tail: str = ""
    stderr_tail: str = ""


def discover() -> dict[str, Any]:
    """Discover Cursor CLI binary and capabilities. Write to discovery log."""
    DISCOVERY_LOG.parent.mkdir(parents=True, exist_ok=True)
    info: dict[str, Any] = {}
    for cmd_name in ["cursor", "cursor-agent"]:
        for flag in ["--version", "--help"]:
            try:
                r = subprocess.run(
                    [cmd_name, flag], capture_output=True, text=True, timeout=10
                )
                info[f"{cmd_name}_{flag.strip('-')}"] = (r.stdout + r.stderr).strip()[:500]
                break  # found this binary
            except FileNotFoundError:
                info[f"{cmd_name}_found"] = False
                break
            except subprocess.TimeoutExpired:
                info[f"{cmd_name}_timeout"] = True

    ts = datetime.now(timezone.utc).isoformat()
    log_lines = [f"=== Cursor CLI Discovery {ts} ===\n"]
    for k, v in info.items():
        log_lines.append(f"\n--- {k} ---\n{v}\n")
    DISCOVERY_LOG.write_text("".join(log_lines))
    return info


def check_version() -> str:
    for binary in ["cursor", "cursor-agent"]:
        try:
            r = subprocess.run(
                [binary, "--version"], capture_output=True, text=True, timeout=10
            )
            v = (r.stdout + r.stderr).strip().splitlines()
            return v[0] if v else "unknown"
        except FileNotFoundError:
            continue
        except Exception as e:
            return f"ERROR: {e}"
    return "NOT_FOUND"


def run_agent(
    agent_id: str,
    prompt_path: str,
    working_dir: str,
    output_dir: str,
    model: str = "codex-5.3",
    timeout_minutes: int = DEFAULT_TIMEOUT_MIN,
    no_output_kill_minutes: int = NO_OUTPUT_KILL_MIN,
) -> AgentRunResult:
    """
    Dispatch Cursor CLI with the given prompt file using Popen for live capture.
    Kills process on hard timeout or no-output timeout.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = out_dir / f"stdout_{agent_id}.log"
    stderr_path = out_dir / f"stderr_{agent_id}.log"
    started = datetime.now(timezone.utc).isoformat()
    started_ts = time.time()

    # Build command — will be refined once exact CLI syntax is known
    cmd = _build_command(prompt_path, working_dir, model)

    try:
        with open(stdout_path, "w", encoding="utf-8", errors="replace") as fout, \
             open(stderr_path, "w", encoding="utf-8", errors="replace") as ferr:

            proc = subprocess.Popen(
                cmd, cwd=working_dir,
                stdout=fout, stderr=ferr,
                text=True, encoding="utf-8", errors="replace"
            )

            last_output_ts = [time.time()]

            def _monitor():
                """Watch stdout size; update last_output_ts when file grows."""
                last_size = 0
                while proc.poll() is None:
                    try:
                        size = stdout_path.stat().st_size + stderr_path.stat().st_size
                        if size > last_size:
                            last_size = size
                            last_output_ts[0] = time.time()
                    except Exception:
                        pass
                    time.sleep(30)

            mon = threading.Thread(target=_monitor, daemon=True)
            mon.start()

            hard_deadline = started_ts + timeout_minutes * 60
            no_output_deadline_sec = no_output_kill_minutes * 60

            while True:
                retcode = proc.poll()
                if retcode is not None:
                    break  # process finished

                now = time.time()
                if now > hard_deadline:
                    proc.kill()
                    ended = datetime.now(timezone.utc).isoformat()
                    return AgentRunResult(
                        agent=agent_id, status="timeout",
                        started_at=started, ended_at=ended,
                        exit_code=-1,
                        stdout_path=str(stdout_path),
                        stderr_path=str(stderr_path),
                        prompt_path=prompt_path, output_dir=output_dir,
                        error_message=f"Hard timeout after {timeout_minutes}m",
                        stdout_tail=_tail(stdout_path),
                        stderr_tail=_tail(stderr_path),
                    )

                no_output_age = now - last_output_ts[0]
                if no_output_age > no_output_deadline_sec:
                    proc.kill()
                    ended = datetime.now(timezone.utc).isoformat()
                    return AgentRunResult(
                        agent=agent_id, status="no_output",
                        started_at=started, ended_at=ended,
                        exit_code=-1,
                        stdout_path=str(stdout_path),
                        stderr_path=str(stderr_path),
                        prompt_path=prompt_path, output_dir=output_dir,
                        error_message=f"No output for {no_output_kill_minutes}m",
                        stdout_tail=_tail(stdout_path),
                        stderr_tail=_tail(stderr_path),
                    )
                time.sleep(15)

        ended = datetime.now(timezone.utc).isoformat()
        status = "complete" if retcode == 0 else "error"
        return AgentRunResult(
            agent=agent_id, status=status,
            started_at=started, ended_at=ended,
            exit_code=retcode,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            prompt_path=prompt_path, output_dir=output_dir,
            error_message="" if retcode == 0 else f"exit code {retcode}",
            stdout_tail=_tail(stdout_path),
            stderr_tail=_tail(stderr_path),
        )

    except FileNotFoundError:
        ended = datetime.now(timezone.utc).isoformat()
        return AgentRunResult(
            agent=agent_id, status="error",
            started_at=started, ended_at=ended,
            exit_code=None,
            error_message=f"Cursor binary not found: {cmd[0]}",
        )
    except Exception as e:
        ended = datetime.now(timezone.utc).isoformat()
        return AgentRunResult(
            agent=agent_id, status="error",
            started_at=started, ended_at=ended,
            exit_code=None, error_message=str(e),
        )


def _build_command(prompt_path: str, working_dir: str, model: str) -> list[str]:
    """Build the Cursor CLI command. Update this after running discover()."""
    # Primary attempt: cursor --prompt-file
    return [CURSOR_BINARY, "--prompt-file", prompt_path, "--cwd", working_dir]


def _tail(path: Path, n: int = 50) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-n:])
    except Exception:
        return ""
