"""
autopilot_logger.py -- Observability layer for the 24/7 autonomous build system.

OBS-1 : stage() context manager (PLAN/PROMPT-GEN/DISPATCH/AGENT-RUN/etc.)
OBS-2 : current_activity.json -- always-on "what is running right now"
OBS-3 : log_exception() -- no more bare except; every failure is named + traced
OBS-5 : per-run JSONL (events.jsonl) + transcript.log under C:/AI_Runner/runs/<run_id>/
OBS-6 : heartbeat thread -- long ops emit "still running" lines every N seconds
OBS-7 : cycle_summary() -- end-of-cycle table to terminal + JSON + MD
OBS-9 : LOG_LEVEL env var (DEBUG/INFO/WARN/ERROR); INFO default
OBS-12: every _write line carries ts + cycle + stage + agent correlation
OBS-13: stage_matrix() -- one-line visual: PLAN checkmark PROMPT checkmark A checkmark B arrow E dot
OBS-15: stall detection -- warn when current_activity.last_heartbeat ages past threshold

All existing public symbols preserved for drop-in compatibility.
"""
from __future__ import annotations

import json
import os
import threading
import time
import traceback as _traceback
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Generator

try:
    import click as _click

    def _c(text: str, fg: str | None = None, bold: bool = False) -> str:
        return _click.style(str(text), fg=fg, bold=bold)

except ImportError:
    def _c(text: str, fg: str | None = None, bold: bool = False) -> str:  # type: ignore[misc]
        return str(text)


# -- Directories ---------------------------------------------------------------
LOG_DIR   = Path("C:/AI_Runner/logs")
RUNS_DIR  = Path("C:/AI_Runner/runs")
STATE_DIR = Path("C:/AI_Runner/state")
LOG_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

# -- Log level (OBS-9) ---------------------------------------------------------
_LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}
_log_level_name = os.environ.get("AUTOPILOT_LOG_LEVEL", "INFO").upper()
LOG_LEVEL: int = _LEVELS.get(_log_level_name, 20)

# -- Per-day log file ----------------------------------------------------------
_log_state: dict = {"path": None, "handle": None}


def _log_file():
    today = datetime.now().strftime("%Y%m%d")
    p = LOG_DIR / f"autopilot_{today}.log"
    if p != _log_state["path"]:
        if _log_state["handle"] is not None:
            try:
                _log_state["handle"].close()
            except Exception:
                pass
        _log_state["handle"] = open(p, "a", encoding="utf-8", buffering=1)  # noqa: SIM115
        _log_state["path"] = p
    return _log_state["handle"]


# -- Per-run sinks (OBS-5) -----------------------------------------------------
_run_state: dict = {
    "run_id": None,
    "cycle": None,
    "transcript": None,
    "jsonl": None,
    "run_dir": None,
}


def init_run(run_id: str, cycle: int | None = None) -> Path:
    """Call once at run start; creates per-run transcript.log + events.jsonl."""
    run_dir = RUNS_DIR / (run_id or "unknown")
    run_dir.mkdir(parents=True, exist_ok=True)
    for key in ("transcript", "jsonl"):
        h = _run_state.get(key)
        if h is not None:
            try:
                h.close()
            except Exception:
                pass
    _run_state["run_id"] = run_id
    _run_state["cycle"] = cycle
    _run_state["run_dir"] = run_dir
    _run_state["transcript"] = open(  # noqa: SIM115
        run_dir / "transcript.log", "a", encoding="utf-8", buffering=1
    )
    _run_state["jsonl"] = open(  # noqa: SIM115
        run_dir / "events.jsonl", "a", encoding="utf-8", buffering=1
    )
    return run_dir


def _ts() -> str:
    return datetime.now(UTC).strftime("%H:%M:%S")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


# -- Correlation context (OBS-12) ----------------------------------------------
_ctx = threading.local()


def _get_ctx() -> dict:
    if not hasattr(_ctx, "data"):
        _ctx.data = {"cycle": None, "stage": None, "agent": None}
    return _ctx.data


def _set_ctx(
    cycle: int | None = None,
    stage: str | None = None,
    agent: str | None = None,
) -> None:
    d = _get_ctx()
    if cycle is not None:
        d["cycle"] = cycle
    if stage is not None:
        d["stage"] = stage
    if agent is not None:
        d["agent"] = agent


def _clear_ctx_agent() -> None:
    _get_ctx()["agent"] = None


def _clear_ctx_stage() -> None:
    d = _get_ctx()
    d["stage"] = None
    d["agent"] = None


# -- Core write ----------------------------------------------------------------
def _write(line: str, plain: str | None = None, level: int = 20) -> None:
    if level < LOG_LEVEL:
        return
    ctx = _get_ctx()
    cycle_v = ctx.get("cycle")
    cycle_s = f"C{cycle_v:03d}" if cycle_v else "C???"
    stage_s = (ctx.get("stage") or "?")[:12]
    agent_s = ctx.get("agent") or "-"
    corr = f"{_ts()} {cycle_s} {stage_s:<12} {agent_s:<3}"
    plain_line = plain or line
    print(line, flush=True)
    try:
        _log_file().write(f"[{corr}] {plain_line}\n")
    except Exception:
        pass
    if _run_state.get("transcript"):
        try:
            _run_state["transcript"].write(f"[{corr}] {plain_line}\n")
        except Exception:
            pass
    if _run_state.get("jsonl"):
        try:
            evt: dict[str, Any] = {
                "ts": _ts(),
                "cycle": cycle_v,
                "stage": ctx.get("stage"),
                "agent": ctx.get("agent"),
                "level": level,
                "msg": plain_line,
            }
            _run_state["jsonl"].write(json.dumps(evt) + "\n")
        except Exception:
            pass


# -- Current activity (OBS-2) --------------------------------------------------
_ACTIVITY_FILE = STATE_DIR / "current_activity.json"
_activity_lock = threading.Lock()


def _write_activity(data: dict) -> None:
    data["last_heartbeat"] = _now_iso()
    with _activity_lock:
        try:
            _ACTIVITY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass


def set_activity(
    stage: str,
    cycle: int | None = None,
    agent: str | None = None,
    lane: str | None = None,
    attempt: int = 1,
) -> None:
    """Update current_activity.json; call at every pipeline transition."""
    _set_ctx(cycle=cycle, stage=stage, agent=agent)
    _write_activity({
        "stage": stage,
        "cycle": cycle,
        "agent": agent,
        "lane": lane,
        "attempt": attempt,
        "started_at": _now_iso(),
        "last_heartbeat": _now_iso(),
    })


def clear_activity() -> None:
    """Call at cycle end / error to mark nothing running."""
    _clear_ctx_stage()
    _write_activity({"stage": "IDLE", "cycle": None, "agent": None})


def bump_heartbeat() -> None:
    """Update last_heartbeat in current_activity.json without changing other fields."""
    with _activity_lock:
        try:
            if _ACTIVITY_FILE.exists():
                data = json.loads(_ACTIVITY_FILE.read_text(encoding="utf-8"))
                data["last_heartbeat"] = _now_iso()
                _ACTIVITY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass


# -- OBS-3: log_exception ------------------------------------------------------
def log_exception(component: str, exc: Exception, detail: str = "") -> None:
    """Emit component name + exception type + traceback tail to terminal and log."""
    tb = _traceback.format_exc()
    tb_tail = tb[-600:] if tb.strip() not in ("", "NoneType: None") else ""
    msg = (
        f"EXCEPTION in {component}: {type(exc).__name__}: {exc}"
        + (f"  detail: {detail}" if detail else "")
        + (f"\n    {tb_tail}" if tb_tail else "")
    )
    _write(
        _c(f"\n  [EXCEPTION] {msg}", fg="red", bold=True),
        plain=f"[EXCEPTION] {msg}",
        level=40,
    )


# -- OBS-1: stage() context manager --------------------------------------------
_stage_results: dict[str, dict] = {}


@contextmanager
def stage(name: str, cycle: int | None = None) -> Generator[None, None, None]:
    """Context manager that prints stage enter/exit banners and tracks timing."""
    set_activity(name.upper(), cycle=cycle)
    _write(
        _c(
            f"\n  STAGE {name.upper()}"
            + (f"  (cycle {cycle})" if cycle else "")
            + f"  [{_ts()}]",
            fg="cyan",
            bold=True,
        ),
        plain=f"STAGE {name.upper()}" + (f"  cycle={cycle}" if cycle else ""),
        level=20,
    )
    t0 = time.time()
    passed = True
    try:
        yield
    except (SystemExit, KeyboardInterrupt):
        passed = False
        raise
    except Exception as exc:
        passed = False
        log_exception(name, exc)
        raise
    finally:
        elapsed = time.time() - t0
        result_s = "DONE" if passed else "FAILED"
        result_icon = _c(result_s, fg="green") if passed else _c(result_s, fg="red", bold=True)
        _write(
            _c(f"  STAGE {name.upper()} ", fg="cyan") + result_icon
            + _c(f"  {elapsed:.1f}s", fg="cyan"),
            plain=f"STAGE {name.upper()} {result_s}  {elapsed:.1f}s",
            level=20,
        )
        _stage_results[name.upper()] = {"passed": passed, "elapsed": elapsed}
        _clear_ctx_stage()


# -- OBS-6: heartbeat thread ---------------------------------------------------
class HeartbeatThread:
    """Emits 'still running' lines every `interval` seconds for long operations."""

    def __init__(self, label: str, interval: float = 30.0) -> None:
        self.label = label
        self.interval = interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        start = time.time()
        while not self._stop.wait(self.interval):
            elapsed = time.time() - start
            _write(
                _c(
                    f"  HEARTBEAT  {self.label}  elapsed={elapsed:.0f}s  [{_ts()}]",
                    fg="bright_black",
                ),
                plain=f"HEARTBEAT {self.label} elapsed={elapsed:.0f}s",
                level=20,
            )
            bump_heartbeat()
            _check_stall()

    def start(self) -> HeartbeatThread:
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2)

    def __enter__(self) -> HeartbeatThread:
        return self.start()

    def __exit__(self, *_: object) -> None:
        self.stop()


# -- OBS-15: stall detection ---------------------------------------------------
STALL_THRESHOLD_S: float = 300.0  # 5 min


def _check_stall() -> None:
    try:
        if not _ACTIVITY_FILE.exists():
            return
        data = json.loads(_ACTIVITY_FILE.read_text(encoding="utf-8"))
        last_hb = data.get("last_heartbeat")
        if not last_hb:
            return
        stage_name = data.get("stage", "?")
        agent_s = data.get("agent") or ""
        try:
            dt = datetime.fromisoformat(last_hb)
            age_s = (datetime.now(UTC) - dt).total_seconds()
        except Exception:
            return
        if age_s > STALL_THRESHOLD_S:
            _write(
                _c(
                    f"\n  STALL DETECTED: no activity for {age_s:.0f}s "
                    f"in stage={stage_name} agent={agent_s}. "
                    "Check for deadlock or crashed worker.",
                    fg="red",
                    bold=True,
                ),
                plain=f"STALL: {age_s:.0f}s in {stage_name}/{agent_s}",
                level=40,
            )
    except Exception:
        pass


# -- OBS-13: stage matrix ------------------------------------------------------
_PIPELINE_STAGES = ["PLAN", "PROMPT-GEN", "A", "B", "E", "C", "F", "D", "VERIFY", "POST-CYCLE"]


def stage_matrix(
    current: str | None = None,
    agents: list[str] | None = None,
    agent_results: dict[str, bool] | None = None,
) -> str:
    """Return a one-line status string like: PLAN+ PROMPT+ A+ B> E. C. F. D."""
    stages = _PIPELINE_STAGES if not agents else (
        ["PLAN", "PROMPT-GEN"] + list(agents) + ["VERIFY", "POST-CYCLE"]
    )
    parts = []
    agent_res = agent_results or {}
    for s in stages:
        res = _stage_results.get(s)
        if res is not None:
            sym = "+" if res["passed"] else "!"
            parts.append(_c(f"{s}{sym}", fg="green" if res["passed"] else "red"))
        elif s == (current or "").upper():
            parts.append(_c(f"{s}>", fg="yellow", bold=True))
        elif s in agent_res:
            sym = "+" if agent_res[s] else "!"
            parts.append(_c(f"{s}{sym}", fg="green" if agent_res[s] else "red"))
        else:
            parts.append(_c(f"{s}.", fg="bright_black"))
    return "  " + " ".join(parts)


def print_stage_matrix(current: str | None = None, agents: list[str] | None = None) -> None:
    """Print the stage matrix to terminal and log."""
    line = stage_matrix(current=current, agents=agents)
    _write(line, plain="STAGE_MATRIX", level=20)


# -- OBS-7: run summary --------------------------------------------------------
def cycle_summary(
    cycle: int,
    agent_outcomes: dict[str, dict],
    gate_result: str = "UNKNOWN",
    blocker_name: str | None = None,
) -> None:
    """Print end-of-cycle summary table; write CYCLE_NNN_RUN_SUMMARY.json + .md."""
    sep = _c("=" * 68, fg="cyan")
    _write(sep, level=20)
    _write(_c(f"  CYCLE {cycle:03d} SUMMARY  gate={gate_result}", fg="cyan", bold=True), level=20)
    _write(sep, level=20)

    header = f"  {'Agent':<8} {'Status':<22} {'Commit':<10} {'Files':<6} {'Time':>7}"
    _write(_c(header, fg="white", bold=True), plain=header, level=20)

    for agent_id, out in sorted(agent_outcomes.items()):
        status  = out.get("status", "?")
        commit  = (out.get("commit_sha") or "")[:8] or "-"
        files   = str(out.get("files_changed", "-"))
        elapsed = f"{out.get('elapsed', 0):.0f}s"
        color   = "green" if status in ("COMPLETE", "PASS") else "red"
        row = f"  {agent_id:<8} {status:<22} {commit:<10} {files:<6} {elapsed:>7}"
        _write(_c(row, fg=color), plain=row, level=20)

    if blocker_name:
        _write(_c(f"\n  BLOCKED BY: {blocker_name}", fg="red", bold=True), level=40)
    _write(sep, level=20)

    run_dir = _run_state.get("run_dir") or RUNS_DIR / "latest"
    Path(run_dir).mkdir(parents=True, exist_ok=True)
    summary_data: dict[str, Any] = {
        "cycle": cycle,
        "gate_result": gate_result,
        "blocker": blocker_name,
        "agents": agent_outcomes,
        "generated_at": _now_iso(),
    }
    try:
        (Path(run_dir) / f"CYCLE_{cycle:03d}_RUN_SUMMARY.json").write_text(
            json.dumps(summary_data, indent=2), encoding="utf-8"
        )
        md: list[str] = [
            f"# Cycle {cycle:03d} Run Summary\n\n",
            f"**Gate:** {gate_result}  \n",
        ]
        if blocker_name:
            md.append(f"**Blocked by:** {blocker_name}  \n")
        md.extend([
            "\n| Agent | Status | Commit | Files | Time |\n",
            "|-------|--------|--------|-------|------|\n",
        ])
        for ag_id, out in sorted(agent_outcomes.items()):
            md.append(
                f"| {ag_id} | {out.get('status','?')} "
                f"| {(out.get('commit_sha') or '')[:8] or '-'} "
                f"| {out.get('files_changed','-')} "
                f"| {out.get('elapsed', 0):.0f}s |\n"
            )
        (Path(run_dir) / f"CYCLE_{cycle:03d}_RUN_SUMMARY.md").write_text(
            "".join(md), encoding="utf-8"
        )
    except Exception:
        pass


# -- All existing symbols (preserved for backward compatibility) ---------------
def banner(title: str) -> None:
    sep = _c("=" * 64, fg="cyan", bold=True)
    _write(sep)
    _write(_c(f"  {title}", fg="cyan", bold=True))
    _write(sep)


def section(title: str) -> None:
    _write(_c(f"\n  ---- {title} ----", fg="blue", bold=True), level=20)


def ok(msg: str) -> None:
    _write(_c(f"  OK    {msg}", fg="green"), level=20)


def warn(msg: str) -> None:
    _write(_c(f"  WARN  {msg}", fg="yellow"), level=30)


def error(msg: str) -> None:
    _write(_c(f"  ERROR  {msg}", fg="red", bold=True), level=40)


def info(msg: str) -> None:
    _write(f"         {msg}", level=20)


def debug(msg: str) -> None:
    _write(_c(f"  DEBUG  {msg}", fg="bright_black"), level=10)


def newline() -> None:
    print("", flush=True)


def state_change(old: str, new: str, cycle: int) -> None:
    _write(
        _c(f"\n  STATE  {old}  ->  {new}  (cycle {cycle})", fg="cyan", bold=True),
        level=20,
    )


def tick_header(num: int, status: str, cycle: int) -> None:
    _STATUS_COLOR: dict[str, str] = {
        "PLANNED": "cyan",
        "READY_TO_DISPATCH": "cyan",
        "DISPATCHING": "yellow",
        "AGENT_DISPATCH": "yellow",
        "AGENT_COMPLETE": "green",
        "POST_CYCLE_PASS": "green",
        "POST_CYCLE_FAIL": "red",
        "MODEL_BLOCKED": "red",
        "BRANCH_MISMATCH_BLOCKED": "red",
    }
    sc = _STATUS_COLOR.get(status, "white")
    ts = _ts()
    sep = _c("=" * 64, fg="blue")
    _write(
        f"\n{sep}\n"
        f"  {_c(f'TICK #{num:04d}', fg='blue', bold=True)}"
        f"  status={_c(status, fg=sc, bold=True)}"
        f"  cycle={_c(str(cycle), fg='cyan')}"
        f"  {_c(ts, fg='bright_black')}"
        f"\n{sep}",
        plain=f"TICK #{num:04d}  status={status}  cycle={cycle}",
        level=20,
    )
    _set_ctx(cycle=cycle, stage="TICK")
    set_activity("TICK", cycle=cycle)


def agent_start(agent_id: str, cycle: int, prompt_bytes: int, n: int, total: int) -> None:
    kb = prompt_bytes // 1024 if prompt_bytes else 0
    _set_ctx(cycle=cycle, stage="AGENT-RUN", agent=agent_id)
    set_activity("AGENT-RUN", cycle=cycle, agent=agent_id)
    _write(
        f"\n  [{_c(f'{n}/{total}', fg='cyan', bold=True)}]"
        f"  {_c(f'AGENT {agent_id} STARTING', fg='yellow', bold=True)}"
        f"  cycle={cycle}"
        f"  prompt={_c(f'{kb}KB', fg='cyan')}"
        f"  {_c(_ts(), fg='bright_black')}",
        plain=f"AGENT {agent_id} STARTING  cycle={cycle}  prompt={kb}KB",
        level=20,
    )


def agent_done(agent_id: str, elapsed: float, passed: bool, n: int, total: int) -> None:
    result = _c("PASS", fg="green", bold=True) if passed else _c("FAIL", fg="red", bold=True)
    _write(
        f"  [{_c(f'{n}/{total}', fg='cyan', bold=True)}]"
        f"  AGENT {agent_id}  {result}"
        f"  elapsed={_c(f'{elapsed:.0f}s', fg='cyan')}"
        f"  {_c(_ts(), fg='bright_black')}",
        plain=f"AGENT {agent_id}  {'PASS' if passed else 'FAIL'}  elapsed={elapsed:.0f}s",
        level=20,
    )
    _clear_ctx_agent()


def agent_fail_detail(agent_id: str, detail: str) -> None:
    _write(_c(f"\n  AGENT {agent_id} FAILURE OUTPUT:", fg="red", bold=True), level=40)
    tail = (detail or "")[-800:]
    for ln in tail.splitlines()[-15:]:
        _write(_c(f"    {ln}", fg="red"), level=40)


def claude_pm_start(agent_id: str, cycle: int, n: int, total: int) -> None:
    _set_ctx(cycle=cycle, stage="PROMPT-GEN", agent=agent_id)
    set_activity("PROMPT-GEN", cycle=cycle, agent=agent_id)
    _write(
        f"\n  [{_c(f'{n}/{total}', fg='magenta', bold=True)}]"
        f"  {_c(f'Claude PM generating Agent {agent_id} prompt', fg='magenta', bold=True)}"
        f"  cycle={cycle}  {_c(_ts(), fg='bright_black')}",
        plain=f"Claude PM Agent {agent_id}  cycle={cycle}",
        level=20,
    )


def claude_pm_done(
    agent_id: str, elapsed: float, chars: int, passed: bool, n: int, total: int
) -> None:
    if passed:
        kb = chars // 1024
        _write(
            f"  [{_c(f'{n}/{total}', fg='magenta', bold=True)}]"
            f"  Claude PM Agent {agent_id}  {_c('DONE', fg='green', bold=True)}"
            f"  {_c(f'{elapsed:.0f}s', fg='cyan')}"
            f"  {_c(f'{kb}KB generated', fg='cyan')}",
            plain=f"Claude PM Agent {agent_id} DONE  {elapsed:.0f}s  {kb}KB",
            level=20,
        )
    else:
        _write(
            f"  [{_c(f'{n}/{total}', fg='magenta', bold=True)}]"
            f"  Claude PM Agent {agent_id}  {_c('FAILED', fg='yellow', bold=True)}"
            f"  {_c(f'{elapsed:.0f}s', fg='cyan')}",
            plain=f"Claude PM Agent {agent_id} FAILED  {elapsed:.0f}s",
            level=30,
        )
    _clear_ctx_agent()


def post_cycle_check(label: str, passed: bool | None, detail: str = "") -> None:
    if passed is True:
        icon = _c("OK  ", fg="green")
        label_str = _c(label, fg="green")
    elif passed is False:
        icon = _c("FAIL", fg="red", bold=True)
        label_str = _c(label, fg="red", bold=True)
    else:
        icon = _c("SKIP", fg="yellow")
        label_str = _c(label, fg="yellow")
    detail_str = f"  {detail}" if detail else ""
    _write(
        f"     {icon}  {label_str:<38}{detail_str}",
        plain=f"CHECK {'OK' if passed else 'FAIL'} {label}{detail_str}",
        level=20,
    )


def post_cycle_grade(grade: str, cycle: int) -> None:
    _GRADE_COLOR: dict[str, str] = {
        "PASS": "green",
        "ADVISORY_ONLY": "cyan",
        "CONDITIONAL_PASS": "cyan",
        "FAIL": "red",
    }
    color = _GRADE_COLOR.get(grade, "yellow")
    _write(
        _c(f"\n  CYCLE {cycle:03d} REVIEW: ", fg="white", bold=True)
        + _c(grade, fg=color, bold=True),
        plain=f"CYCLE {cycle:03d} REVIEW: {grade}",
        level=20,
    )


def blocker(msg: str, code: str = "") -> None:
    tag = f"  [{code}]" if code else ""
    _write(
        _c(f"\n  BLOCKER{tag}: {msg}", fg="red", bold=True),
        plain=f"BLOCKER{tag}: {msg}",
        level=40,
    )


def countdown(seconds_remaining: int) -> None:
    mins, secs = divmod(seconds_remaining, 60)
    label = f"{mins}m {secs:02d}s" if mins else f"{secs}s"
    print(f"\r  Next tick in {label}   ", end="", flush=True)


class Spinner:
    """Shows a spinning elapsed-time indicator during a long blocking call."""

    def __init__(self, label: str) -> None:
        self.label = label
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        start = time.time()
        chars = ["|", "/", "-", "\\"]
        i = 0
        while not self._stop.is_set():
            elapsed = time.time() - start
            mins, secs = divmod(int(elapsed), 60)
            t = f"{mins}m{secs:02d}s" if mins else f"{secs}s"
            print(
                f"\r  {chars[i % 4]}  {self.label}  {_c(t, fg='cyan')}   ",
                end="",
                flush=True,
            )
            i += 1
            self._stop.wait(0.5)
        print("", flush=True)

    def __enter__(self) -> Spinner:
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        self._thread.join(timeout=1)

# ── OBS-14: Provider routing + budget visible at dispatch time ────────────
def print_provider_budget(cycle: int | None = None) -> None:
    """OBS-14: Print current provider routing and daily spend against budget caps.
    Called at agent dispatch so the operator can see routing + cost in the terminal.
    """
    try:
        from automation.provider_usage_ledger import get_daily_spend, SUMMARY_PROVIDERS
        from automation.provider_health import load_provider_health

        HARD_CAP = {"openaiapi": 10.0, "claudesubscription": 0.0, "cursorcli": 0.0, "codexsubscription": 0.0}
        SOFT_CAP = {"openaiapi": 5.0}

        lines = [f"  {'─'*55}"]
        lines.append(f"  PROVIDER BUDGET — {'cycle ' + str(cycle) if cycle else 'today'}")
        lines.append(f"  {'─'*55}")

        health = load_provider_health()
        for provider in SUMMARY_PROVIDERS:
            spend = get_daily_spend(provider)
            hard = HARD_CAP.get(provider, 0.0)
            soft = SOFT_CAP.get(provider, 0.0)
            status = (health.get(provider, {}) or {}).get("status", "UNKNOWN")
            color_tag = ""
            if hard > 0 and spend >= hard:
                color_tag = " [HARD CAP HIT]"
            elif soft > 0 and spend >= soft:
                color_tag = " [soft cap]"
            bar_width = 20
            bar_fill = int(min(spend / hard, 1.0) * bar_width) if hard > 0 else 0
            bar = "#" * bar_fill + "." * (bar_width - bar_fill)
            lines.append(
                f"  {provider:<22} [{bar}] ${spend:.3f}"
                + (f"/${hard:.0f}" if hard > 0 else "       ")
                + f"  {status}{color_tag}"
            )
        lines.append(f"  {'─'*55}")
        _click.echo("\n".join(lines))
    except Exception as _obs14_exc:
        debug(f"OBS-14 provider budget display skipped: {_obs14_exc}")
