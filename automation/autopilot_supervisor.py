"""autopilot_supervisor.py — process-level 24/7 keep-alive for the autonomous runner.

``cmd_start_autopilot`` already loops ticks with an in-loop circuit breaker, but the
autopilot *process itself* can die — a terminated host shell, OOM, an OS kill, or an
unhandled crash (all observed live: the autopilot vanished mid-``plan-cycle`` with no
error because its hosting shell was terminated). For genuine unattended 24/7 operation
*something* must bring it back. This thin, crash-resistant supervisor is that something:

  run ``start-autopilot``; when it exits, log why and restart it —
    * SINGLETON-guarded (a PID lock; never two autopilots racing the same repo),
    * STORM-protected (exponential backoff when the autopilot keeps dying fast, so a
      hard-failing run can't hot-loop and burn quota),
    * FREEZE-aware:
        - a circuit-breaker freeze (``reason`` starts with ``circuit_breaker``) is a
          transient COOLDOWN — after a long backoff the supervisor CLEARS it and retries,
          so the runner self-heals with ZERO human intervention (the explicit goal);
        - any OTHER freeze (a deliberate human kill-switch) is RESPECTED — the supervisor
          idles and keeps checking, because a human chose to stop the runner.

Stop cleanly by creating the ``supervisor.stop`` sentinel (or SIGINT/SIGTERM): the
supervisor kills the running autopilot process tree and releases its lock.

This file is intentionally tiny and dependency-light so it is far less likely to crash
than the thing it supervises. The heavy lifting (cycle logic, gates, recovery) stays in
ai_cycle_controller; this only owns PROCESS liveness.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _force_utf8_io() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


def _state_dir() -> Path:
    try:
        from automation import runner_paths
        return runner_paths.state_dir()
    except Exception:
        p = Path("C:/AI_Runner/state")
        p.mkdir(parents=True, exist_ok=True)
        return p


def _lock_path() -> Path:
    return _state_dir() / "supervisor.lock"


def _stop_path() -> Path:
    return _state_dir() / "supervisor.stop"


def _log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    line = f"[SUPERVISOR {ts}] {msg}"
    print(line, flush=True)


# ── singleton ───────────────────────────────────────────────────────────────
def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if os.name == "nt":
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True, text=True, timeout=15,
            )
            return str(pid) in (out.stdout or "")
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def acquire_singleton() -> bool:
    """Write our PID to the lock if no live supervisor holds it. Returns True on success."""
    lock = _lock_path()
    try:
        if lock.exists():
            try:
                existing = int((lock.read_text(encoding="utf-8") or "0").strip() or 0)
            except Exception:
                existing = 0
            if existing and existing != os.getpid() and _pid_alive(existing):
                _log(f"another supervisor is alive (pid {existing}) — exiting")
                return False
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(str(os.getpid()), encoding="utf-8")
        return True
    except Exception as exc:
        _log(f"could not acquire singleton lock ({exc}) — proceeding without it")
        return True


def release_singleton() -> None:
    try:
        lock = _lock_path()
        if lock.exists() and (lock.read_text(encoding="utf-8") or "").strip() == str(os.getpid()):
            lock.unlink()
    except Exception:
        pass


# ── freeze handling ───────────────────────────────────────────────────────────
def freeze_state() -> tuple[bool, str]:
    """Return (frozen, reason) from the autonomy-freeze policy. Fail-safe to NOT frozen."""
    try:
        import yaml
        from automation.ai_cycle_controller import _autonomy_freeze_path
        p = _autonomy_freeze_path()
        if not p.exists():
            return False, "policy_missing"
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            return False, "policy_malformed"
        return bool(data.get("frozen", False)), str(data.get("reason") or "no_reason")
    except Exception as exc:
        return False, f"unreadable:{exc}"


def is_breaker_freeze(reason: str) -> bool:
    """A circuit-breaker freeze is auto-recoverable; a human kill-switch is not."""
    return (reason or "").strip().lower().startswith("circuit_breaker")


def clear_freeze() -> None:
    try:
        from automation.ai_cycle_controller import _write_autonomy_freeze
        _write_autonomy_freeze(False, "supervisor auto-clear after breaker cooldown")
        _log("cleared circuit-breaker freeze after cooldown")
    except Exception as exc:
        _log(f"could not clear freeze ({exc})")


# ── autopilot child ───────────────────────────────────────────────────────────
def build_autopilot_cmd(interval: int) -> list[str]:
    # max-cycles 0 = run indefinitely; the supervisor owns restarts.
    return [sys.executable, "automation/ai_cycle_controller.py", "start-autopilot",
            "--interval", str(interval), "--max-cycles", "0"]


def _child_env() -> dict:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    # Force the gh keyring-auth path (PR #153) and dodge a stale/invalid GITHUB_TOKEN by
    # not leaking token env vars into the child; _ensure_gh_token falls back to gh's keyring.
    for k in ("GH_TOKEN", "GH_AUTOMATION_TOKEN", "GITHUB_TOKEN"):
        env.pop(k, None)
    return env


def run_autopilot_once(cmd: list[str], env: dict) -> int:
    """Spawn the autopilot, stream its output, wait for exit, return its exit code.

    Launched in its own session/process group (POSIX) so we can reap the whole tree on
    stop; Windows uses taskkill /T via _kill_process_tree.

    Codex P1: the autopilot runs ``--max-cycles 0`` (forever), so the stdout read below
    would block indefinitely and ``supervise()`` would never re-check ``supervisor.stop``
    — the documented graceful stop wouldn't actually stop the running autopilot. A daemon
    poller watches the stop sentinel WHILE the child runs and reaps the child's tree when
    it appears (closing the pipe → ending the read loop → returning to ``supervise``).
    """
    import threading
    popen_kw: dict = {}
    if os.name != "nt":
        popen_kw["start_new_session"] = True
    proc = subprocess.Popen(
        cmd, cwd=str(REPO_ROOT), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", **popen_kw,
    )
    done = threading.Event()

    def _stop_poller():
        # poll the stop sentinel every few seconds while the long-lived child runs
        while not done.wait(3):
            if _stop_path().exists():
                _log("stop sentinel detected — reaping running autopilot tree")
                _kill_tree(proc.pid)
                return

    poller = threading.Thread(target=_stop_poller, daemon=True)
    poller.start()
    try:
        for line in proc.stdout:  # type: ignore[union-attr]
            s = line.rstrip()
            if s:
                print(f"  {s}", flush=True)
        proc.wait()
    except KeyboardInterrupt:
        _kill_tree(proc.pid)
        raise
    finally:
        done.set()
    return int(proc.returncode or 0)


def _kill_tree(pid: int | None) -> None:
    try:
        from automation.claude_prompt_creator import _kill_process_tree
        _kill_process_tree(pid)
    except Exception:
        try:
            if pid:
                os.kill(pid, 9)
        except Exception:
            pass


# ── the supervise loop ────────────────────────────────────────────────────────
def supervise(
    interval: int = 60,
    base_backoff: int = 30,
    fast_window_s: int = 600,
    max_fast_restarts: int = 5,
    breaker_cooldown_s: int = 1800,
    manual_freeze_idle_s: int = 300,
    max_loops: int | None = None,
    runner=run_autopilot_once,
    sleeper=time.sleep,
    clock=time.monotonic,
) -> int:
    """Run the autopilot forever, restarting it on exit. Returns when the stop sentinel
    appears (or after ``max_loops`` iterations, for tests).

    Storm guard: if the autopilot exits within ``fast_window_s`` and there have already
    been ``max_fast_restarts`` such fast restarts in the window, back off exponentially
    (capped) instead of restarting immediately — so a hard-failing autopilot cannot
    hot-loop. A long-lived run resets the counter.
    """
    if not acquire_singleton():
        return 0
    _log(f"supervising autopilot (interval={interval}s, base_backoff={base_backoff}s, "
         f"fast_window={fast_window_s}s, max_fast_restarts={max_fast_restarts})")
    cmd = build_autopilot_cmd(interval)
    env = _child_env()
    fast_restarts: deque[float] = deque()
    loops = 0
    try:
        while True:
            if _stop_path().exists():
                _log("stop sentinel present — shutting down supervisor")
                break
            if max_loops is not None and loops >= max_loops:
                break
            loops += 1

            frozen, reason = freeze_state()
            if frozen:
                if is_breaker_freeze(reason):
                    _log(f"circuit-breaker freeze ({reason!r}) — cooldown {breaker_cooldown_s}s "
                         "then auto-clear + retry")
                    sleeper(breaker_cooldown_s)
                    clear_freeze()
                    continue
                _log(f"manual/other freeze ({reason!r}) — RESPECTING; idling {manual_freeze_idle_s}s "
                     "(create supervisor.stop to exit, or unfreeze to resume)")
                sleeper(manual_freeze_idle_s)
                continue

            started = clock()
            _log("starting autopilot")
            try:
                rc = runner(cmd, env)
            except KeyboardInterrupt:
                _log("interrupted — stopping")
                break
            except Exception as exc:
                rc = -1
                _log(f"runner raised: {exc!r}")
            dur = clock() - started
            _log(f"autopilot exited rc={rc} after {int(dur)}s")

            now = clock()
            if dur < fast_window_s:
                fast_restarts.append(now)
            else:
                fast_restarts.clear()  # a healthy long run resets the storm counter
            while fast_restarts and now - fast_restarts[0] > fast_window_s:
                fast_restarts.popleft()

            if len(fast_restarts) >= max_fast_restarts:
                over = len(fast_restarts) - max_fast_restarts
                backoff = min(base_backoff * (2 ** (over + 1)), 1800)
                _log(f"restart storm ({len(fast_restarts)} fast exits in {fast_window_s}s) — "
                     f"backing off {backoff}s")
                sleeper(backoff)
            else:
                sleeper(base_backoff)
    finally:
        release_singleton()
    return 0


def main(argv: list[str] | None = None) -> int:
    _force_utf8_io()
    import argparse
    ap = argparse.ArgumentParser(description="24/7 keep-alive supervisor for the autonomous runner")
    ap.add_argument("--interval", type=int, default=int(os.environ.get("AUTOPILOT_INTERVAL", "60")))
    ap.add_argument("--base-backoff", type=int, default=int(os.environ.get("SUPERVISOR_BASE_BACKOFF", "30")))
    ap.add_argument("--breaker-cooldown", type=int,
                    default=int(os.environ.get("SUPERVISOR_BREAKER_COOLDOWN", "1800")))
    ap.add_argument("--stop", action="store_true", help="signal a running supervisor to stop")
    args = ap.parse_args(argv)
    if args.stop:
        _stop_path().write_text("stop", encoding="utf-8")
        _log("wrote stop sentinel — a running supervisor will exit shortly")
        return 0
    # clear any stale stop sentinel from a prior shutdown before starting
    try:
        if _stop_path().exists():
            _stop_path().unlink()
    except Exception:
        pass
    return supervise(interval=args.interval, base_backoff=args.base_backoff,
                     breaker_cooldown_s=args.breaker_cooldown)


if __name__ == "__main__":
    raise SystemExit(main())
