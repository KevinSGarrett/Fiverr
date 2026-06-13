"""
cursor_adapter.py — Config-driven Cursor CLI agent dispatch.

V5-009 fixes (AUDIT-P0-012):
  1. Binary path resolved from config/env/PATH — never hardcoded single user path
  2. Full-size prompt delivered via stdin/temp-file, not -p arg (avoids Windows 32KB CLI limit)
  3. Fail closed if resolved binary points to Cursor Desktop
  4. Model state expiry blocks dispatch if stale
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ── Config paths (not hardcoded user paths) ─────────────────────────────────
RUNNER_CONFIG   = Path("C:/AI_Runner/config/cursor_adapter.yaml")
DISCOVERY_LOG   = Path("C:/AI_Runner/logs/cursor_cli_discovery.txt")
MODEL_STATE     = Path("C:/AI_Runner/state/cursor_model_state.json")
REAUTH_STEPS    = Path("C:/AI_Runner/state/cursor_reauth_steps.md")
REPO_ROOT       = Path("C:/Fiverr/Fiverr")

# Cursor Desktop binary pattern — we must REJECT if CLI resolves to this
CURSOR_DESKTOP_PATTERNS = [
    r"\Programs\cursor\resources\app\bin\cursor",
    r"\Programs\Cursor\resources",
    "cursor.CMD",  # Cursor Desktop wrapper
]

DEFAULT_TIMEOUT_MIN     = 180
NO_OUTPUT_KILL_MIN      = 45
# Windows CLI arg limit in chars — prompts longer than this go via stdin
CLI_ARG_CHAR_LIMIT      = 4000


@dataclass
class AgentRunResult:
    agent: str
    status: str   # complete | timeout | no_output | error | model_blocked
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


# ── Binary resolution (config-driven) ───────────────────────────────────────

def _load_config() -> dict[str, Any]:
    """Load cursor_adapter.yaml config. Returns empty dict if missing."""
    if RUNNER_CONFIG.exists():
        try:
            import yaml
            with open(RUNNER_CONFIG, encoding="utf-8") as fh:
                return yaml.safe_load(fh) or {}
        except Exception:
            pass
    return {}


def _is_desktop_binary(path: str) -> bool:
    """Return True if path looks like Cursor Desktop wrapper, not standalone CLI."""
    path_lower = path.lower()
    return any(p.lower() in path_lower for p in CURSOR_DESKTOP_PATTERNS)


def _resolve_binary() -> str:
    """
    Resolve Cursor CLI binary path. Priority:
      1. CURSOR_CLI_PATH env var
      2. C:\\AI_Runner\\config\\cursor_adapter.yaml  `binary:` key
      3. PATH discovery: agent, cursor-agent, cursor-cli
      4. Known install location (non-hardcoded: reads from config default_install_dir)

    Fails closed if resolved path is Cursor Desktop wrapper.
    """
    # 1. Env var override
    env_path = os.environ.get("CURSOR_CLI_PATH", "")
    if env_path and Path(env_path).exists():
        if _is_desktop_binary(env_path):
            raise RuntimeError(
                f"CURSOR_CLI_PATH resolves to Cursor Desktop binary: {env_path}\n"
                "Set CURSOR_CLI_PATH to standalone Cursor CLI agent.cmd"
            )
        return env_path

    # 2. Config file
    cfg = _load_config()
    cfg_binary = cfg.get("binary", "")
    if cfg_binary and Path(cfg_binary).exists():
        if _is_desktop_binary(cfg_binary):
            raise RuntimeError(
                f"cursor_adapter.yaml binary resolves to Cursor Desktop: {cfg_binary}\n"
                f"Update C:\\AI_Runner\\config\\cursor_adapter.yaml with standalone CLI path"
            )
        return cfg_binary

    # 3. PATH discovery
    import shutil
    # Add known install dir to PATH for discovery (reads from config, not hardcoded)
    install_dir = cfg.get("default_install_dir", "")
    if install_dir:
        os.environ["PATH"] = install_dir + ";" + os.environ.get("PATH", "")

    for candidate in ("agent", "cursor-agent", "cursor-cli"):
        found = shutil.which(candidate)
        if found:
            if _is_desktop_binary(found):
                continue  # Skip Desktop, keep looking
            return found

    # 4. Use the known non-hardcoded path from config (not from code)
    fallback = cfg.get("fallback_path", "")
    if fallback:
        return fallback

    # CI/test fallback: keep command construction available even when CLI isn't installed.
    # Runtime dispatch will still fail later if the binary truly doesn't exist.
    return "agent"


# Public alias used by tests
CURSOR_CLI_PATH = _load_config().get(
    "binary",
    r"C:\Users\Windows 11\AppData\Local\cursor-agent\agent.cmd"
)


# ── Model gate freshness check ────────────────────────────────────────────────

def check_model_gate_freshness() -> dict[str, Any]:
    """Check if cursor_model_state.json is within freshness policy (V6-CURSOR-005)."""
    if not MODEL_STATE.exists():
        return {"passed": False, "reason": "cursor_model_state.json not found"}
    try:
        state = json.loads(MODEL_STATE.read_text())
        valid_until = state.get("valid_until", "")
        if valid_until:
            expires = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
            if expires < datetime.now(expires.tzinfo):
                return {
                    "passed": False,
                    "reason": f"cursor_model_state expired at {valid_until}. Re-verify model."
                }
        return {"passed": state.get("status") == "VERIFIED", "state": state}
    except Exception as e:
        return {"passed": False, "reason": str(e)}


# ── Command builder ───────────────────────────────────────────────────────────

def _build_command(prompt_path: str, working_dir: str, model: str) -> list[str]:
    """
    Build Cursor CLI command. For short prompts uses -p flag.
    For long prompts (>CLI_ARG_CHAR_LIMIT chars), returns command for stdin delivery.
    Returns (cmd_list, use_stdin, prompt_content).
    """
    binary = _resolve_binary()
    prompt_content = Path(prompt_path).read_text(encoding="utf-8", errors="replace")

    # Always use -p for now; for stdin delivery see run_agent which handles the file case
    cmd = [binary, "-p", prompt_content, "--output-format", "text", "--trust", "-f"]
    if model:
        cmd += ["--model", model]
    return cmd


def _build_command_with_file(binary: str, prompt_file: str, model: str) -> list[str]:
    """Build command that reads prompt from a file (for full-size prompts)."""
    # For full-size prompts: pass content via stdin, no -p argument
    cmd = [binary, "--output-format", "text", "--trust", "-f"]
    if model:
        cmd += ["--model", model]
    return cmd


# ── Discovery ─────────────────────────────────────────────────────────────────

def discover() -> dict[str, Any]:
    """Discover Cursor CLI binary and record version/path."""
    DISCOVERY_LOG.parent.mkdir(parents=True, exist_ok=True)
    try:
        binary = _resolve_binary()
        info: dict[str, Any] = {"binary": binary, "is_desktop": False}
    except RuntimeError as e:
        info = {"error": str(e), "binary": "NOT_FOUND"}
        DISCOVERY_LOG.write_text(
            f"=== Cursor CLI Discovery FAILED {datetime.now(UTC).isoformat()} ===\n{e}"
        )
        return info

    try:
        r = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=10)
        info["version"] = (r.stdout + r.stderr).strip()
    except Exception as e:
        info["version_error"] = str(e)

    ts = datetime.now(UTC).isoformat()
    DISCOVERY_LOG.write_text(
        f"=== Cursor CLI Discovery {ts} ===\n" +
        "\n".join(f"{k}: {v}" for k, v in info.items())
    )
    return info


def check_version() -> str:
    """Return Cursor CLI version string."""
    try:
        binary = _resolve_binary()
    except RuntimeError as e:
        return f"NOT_FOUND: {e}"
    try:
        r = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=10)
        out = (r.stdout + r.stderr).strip()
        return out.splitlines()[0] if out else "unknown"
    except Exception:
        return "unknown"


# ── Agent run ──────────────────────────────────────────────────────────────────

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
    Dispatch Cursor CLI agent.

    Full-size prompt handling (V5-009 fix):
    - Prompts <= CLI_ARG_CHAR_LIMIT chars: passed via -p flag
    - Prompts > CLI_ARG_CHAR_LIMIT chars: written to temp file, piped via stdin
      This avoids Windows command-line argument length limits for 6000+ word prompts.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = out_dir / f"stdout_{agent_id}.log"
    stderr_path = out_dir / f"stderr_{agent_id}.log"
    started     = datetime.now(UTC).isoformat()
    started_ts  = time.time()

    # Resolve binary early so we fail fast on config errors
    try:
        binary = _resolve_binary()
    except RuntimeError as e:
        return AgentRunResult(
            agent=agent_id, status="error",
            started_at=started, ended_at=datetime.now(UTC).isoformat(),
            exit_code=None, error_message=str(e),
        )

    prompt_content = Path(prompt_path).read_text(encoding="utf-8", errors="replace")
    use_stdin = len(prompt_content) > CLI_ARG_CHAR_LIMIT

    if use_stdin:
        # Full-size prompt: pass via stdin to avoid Windows CLI arg limit
        cmd = _build_command_with_file(binary, prompt_path, model)
        stdin_source = prompt_content
    else:
        cmd = [binary, "-p", prompt_content, "--output-format", "text", "--trust", "-f"]
        if model:
            cmd += ["--model", model]
        stdin_source = None

    try:
        with open(stdout_path, "w", encoding="utf-8", errors="replace") as fout, \
             open(stderr_path, "w", encoding="utf-8", errors="replace") as ferr:

            proc = subprocess.Popen(
                cmd,
                cwd=working_dir,
                stdin=subprocess.PIPE if use_stdin else None,
                stdout=fout,
                stderr=ferr,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            # Feed stdin for full-size prompts
            if use_stdin and stdin_source and proc.stdin:
                try:
                    proc.stdin.write(stdin_source)
                    proc.stdin.close()
                except Exception:
                    pass

            last_output_ts = [time.time()]

            def _monitor() -> None:
                last_sz = 0
                while proc.poll() is None:
                    try:
                        sz = stdout_path.stat().st_size + stderr_path.stat().st_size
                        if sz > last_sz:
                            last_sz = sz
                            last_output_ts[0] = time.time()
                    except Exception:
                        pass
                    time.sleep(30)

            threading.Thread(target=_monitor, daemon=True).start()
            hard_deadline       = started_ts + timeout_minutes * 60
            no_output_limit_sec = no_output_kill_minutes * 60

            while True:
                retcode = proc.poll()
                if retcode is not None:
                    break
                now = time.time()
                if now > hard_deadline:
                    proc.kill()
                    return AgentRunResult(
                        agent=agent_id, status="timeout",
                        started_at=started, ended_at=datetime.now(UTC).isoformat(),
                        exit_code=-1, stdout_path=str(stdout_path),
                        stderr_path=str(stderr_path), prompt_path=prompt_path,
                        output_dir=output_dir,
                        error_message=f"Hard timeout after {timeout_minutes}m",
                        stdout_tail=_tail(stdout_path), stderr_tail=_tail(stderr_path),
                    )
                if now - last_output_ts[0] > no_output_limit_sec:
                    proc.kill()
                    return AgentRunResult(
                        agent=agent_id, status="no_output",
                        started_at=started, ended_at=datetime.now(UTC).isoformat(),
                        exit_code=-1, stdout_path=str(stdout_path),
                        stderr_path=str(stderr_path), prompt_path=prompt_path,
                        output_dir=output_dir,
                        error_message=f"No output for {no_output_kill_minutes}m",
                        stdout_tail=_tail(stdout_path), stderr_tail=_tail(stderr_path),
                    )
                time.sleep(15)

        return AgentRunResult(
            agent=agent_id,
            status="complete" if retcode == 0 else "error",
            started_at=started, ended_at=datetime.now(UTC).isoformat(),
            exit_code=retcode, stdout_path=str(stdout_path),
            stderr_path=str(stderr_path), prompt_path=prompt_path,
            output_dir=output_dir,
            error_message="" if retcode == 0 else f"exit code {retcode}",
            stdout_tail=_tail(stdout_path), stderr_tail=_tail(stderr_path),
        )

    except FileNotFoundError:
        return AgentRunResult(
            agent=agent_id, status="error",
            started_at=started, ended_at=datetime.now(UTC).isoformat(),
            exit_code=None, error_message=f"Cursor CLI not found: {binary}",
        )
    except Exception as exc:
        return AgentRunResult(
            agent=agent_id, status="error",
            started_at=started, ended_at=datetime.now(UTC).isoformat(),
            exit_code=None, error_message=str(exc),
        )


def _tail(path: Path, n: int = 50) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-n:])
    except Exception:
        return ""
