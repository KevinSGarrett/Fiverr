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
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CURSOR_BINARY = "agent"
# Cursor CLI (standalone, separate from Cursor Desktop)
# Installed via: irm 'https://cursor.com/install?win32=true' | iex
# Binary: C:\Users\Windows 11\AppData\Local\cursor-agent\agent.cmd
CURSOR_CLI_DIR  = r"C:\Users\Windows 11\AppData\Local\cursor-agent"
CURSOR_CLI_PATH = r"C:\Users\Windows 11\AppData\Local\cursor-agent\agent.cmd"
DISCOVERY_LOG   = Path("C:/AI_Runner/logs/cursor_cli_discovery.txt")
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


def _resolve_binary() -> str:
    """Return the Cursor CLI agent.cmd path."""
    # Cursor CLI installed by: irm 'https://cursor.com/install?win32=true' | iex
    # This is the standalone CLI, NOT the Cursor Desktop IDE.
    if Path(CURSOR_CLI_PATH).exists():
        return CURSOR_CLI_PATH
    # Fallback: check if 'agent' is on PATH (in case CLI dir is in PATH)
    import shutil
    os.environ["PATH"] = CURSOR_CLI_DIR + ";" + os.environ.get("PATH", "")
    found = shutil.which("agent")
    return found if found else CURSOR_CLI_PATH


def discover() -> dict[str, Any]:
    """Discover Cursor CLI binary and record version."""
    DISCOVERY_LOG.parent.mkdir(parents=True, exist_ok=True)
    binary = _resolve_binary()
    info: dict[str, Any] = {"binary": binary}
    try:
        r = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=10)
        info["version"] = (r.stdout + r.stderr).strip()
    except Exception as e:
        info["error"] = str(e)
    ts = datetime.now(UTC).isoformat()
    DISCOVERY_LOG.write_text(f"=== Cursor CLI Discovery {ts} ===\n" +
                             "\n".join(f"{k}: {v}" for k, v in info.items()))
    return info


def check_version() -> str:
    binary = _resolve_binary()
    try:
        r = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=10)
        return (r.stdout + r.stderr).strip().splitlines()[0]
    except FileNotFoundError:
        return f"NOT_FOUND: {binary}"
    except Exception as e:
        return f"ERROR: {e}"


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
    Dispatch cursor agent with the prompt piped via stdin.

    Invocation: cursor agent  (prompt content written to stdin)

    The cursor CLI agent reads the prompt from stdin, operates on the
    working_dir repo, makes code changes, and exits when done.
    Stdout/stderr are captured live. Hard timeout and no-output timeout
    both kill the process safely.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = out_dir / f"stdout_{agent_id}.log"
    stderr_path = out_dir / f"stderr_{agent_id}.log"
    started = datetime.now(UTC).isoformat()
    started_ts = time.time()

    # Build the CLI command: agent -p "prompt" --output-format text --trust [--model ...]
    # _build_command reads the prompt file content and passes it as the -p value
    cmd = _build_command(prompt_path, working_dir, model)

    try:
        with open(stdout_path, "w", encoding="utf-8", errors="replace") as fout, \
             open(stderr_path, "w", encoding="utf-8", errors="replace") as ferr:

            proc = subprocess.Popen(
                cmd,
                cwd=working_dir,
                stdout=fout,
                stderr=ferr,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            last_output_ts = [time.time()]

            def _monitor():
                """Watch stdout/stderr size; update last_output_ts when files grow."""
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
                    break

                now = time.time()
                if now > hard_deadline:
                    proc.kill()
                    ended = datetime.now(UTC).isoformat()
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
                    ended = datetime.now(UTC).isoformat()
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

        ended = datetime.now(UTC).isoformat()
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
        ended = datetime.now(UTC).isoformat()
        return AgentRunResult(
            agent=agent_id, status="error",
            started_at=started, ended_at=ended,
            exit_code=None,
            error_message=f"Cursor CLI not found: {cmd[0]}",
        )
    except Exception as e:
        ended = datetime.now(UTC).isoformat()
        return AgentRunResult(
            agent=agent_id, status="error",
            started_at=started, ended_at=ended,
            exit_code=None, error_message=str(e),
        )


def _build_command(prompt_path: str, working_dir: str, model: str) -> list[str]:
    """
    Build the Cursor CLI non-interactive command.

    Correct invocation (from cursor.com/docs/cli/overview):
        agent -p "prompt text" --output-format text --trust

    --trust  : grants workspace access without interactive prompt
    -p       : non-interactive print mode (for automation/CI)
    --output-format text : plain text output, no ANSI codes
    """
    binary = _resolve_binary()
    prompt_content = Path(prompt_path).read_text(encoding="utf-8", errors="replace")
    cmd = [binary, "-p", prompt_content, "--output-format", "text", "--trust"]
    if model:
        cmd += ["--model", model]
    return cmd


def _tail(path: Path, n: int = 50) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-n:])
    except Exception:
        return ""
