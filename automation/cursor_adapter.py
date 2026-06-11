"""
cursor_adapter.py — Wraps Cursor CLI for agent dispatch.
Command syntax is config-driven; exact invocation is finalized after CLI discovery.
"""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CURSOR_BINARY = "cursor"
DISCOVERY_LOG = Path("C:/AI_Runner/logs/cursor_cli_discovery.txt")


@dataclass
class AgentRunResult:
    agent: str
    status: str          # "complete" | "timeout" | "error" | "no_output"
    started_at: str
    ended_at: str
    exit_code: int | None
    stdout: str = ""
    stderr: str = ""
    prompt_path: str = ""
    output_dir: str = ""
    error_message: str = ""


def discover() -> dict[str, Any]:
    """Run cursor --version and --help; write discovery log."""
    DISCOVERY_LOG.parent.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {}
    for cmd in [
        [CURSOR_BINARY, "--version"],
        [CURSOR_BINARY, "--help"],
    ]:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            key = cmd[1].lstrip("-")
            result[key] = r.stdout.strip() or r.stderr.strip()
        except FileNotFoundError:
            result["error"] = f"{cmd[0]} not found on PATH"
            break
        except subprocess.TimeoutExpired:
            result["timeout"] = cmd

    lines = [f"=== Cursor CLI Discovery {datetime.now(timezone.utc).isoformat()} ===\n"]
    for k, v in result.items():
        lines.append(f"\n--- {k} ---\n{v}\n")
    DISCOVERY_LOG.write_text("".join(lines))
    return result


def check_version() -> str:
    try:
        r = subprocess.run([CURSOR_BINARY, "--version"], capture_output=True, text=True, timeout=10)
        return (r.stdout.strip() or r.stderr.strip()).splitlines()[0]
    except Exception as e:
        return f"ERROR: {e}"


def run_agent(
    agent_id: str,
    prompt_path: str,
    working_dir: str,
    output_dir: str,
    model: str = "codex-5.3",
    timeout_minutes: int = 180,
) -> AgentRunResult:
    """
    Dispatch Cursor CLI with the given prompt file.
    Exact invocation depends on installed Cursor version.
    Currently uses: cursor --prompt-file <path> (subject to CLI discovery).
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()

    cmd = [
        CURSOR_BINARY,
        "--prompt-file", prompt_path,
        "--output-dir", output_dir,
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout_minutes * 60,
        )
        ended = datetime.now(timezone.utc).isoformat()
        status = "complete" if proc.returncode == 0 else "error"
        return AgentRunResult(
            agent=agent_id, status=status,
            started_at=started, ended_at=ended,
            exit_code=proc.returncode,
            stdout=proc.stdout, stderr=proc.stderr,
            prompt_path=prompt_path, output_dir=output_dir,
        )
    except subprocess.TimeoutExpired:
        ended = datetime.now(timezone.utc).isoformat()
        return AgentRunResult(
            agent=agent_id, status="timeout",
            started_at=started, ended_at=ended,
            exit_code=None, prompt_path=prompt_path, output_dir=output_dir,
            error_message=f"Timeout after {timeout_minutes} minutes",
        )
    except Exception as e:
        ended = datetime.now(timezone.utc).isoformat()
        return AgentRunResult(
            agent=agent_id, status="error",
            started_at=started, ended_at=ended,
            exit_code=None, prompt_path=prompt_path, output_dir=output_dir,
            error_message=str(e),
        )
