"""
autopilot_logger.py -- Live terminal logging for the 24/7 autonomous build system.

Every stage writes colored timestamped output to the terminal AND to
C:/AI_Runner/logs/autopilot_YYYYMMDD.log so the operator can see exactly
what is happening, how long it is taking, and whether anything is broken.
"""
from __future__ import annotations

import threading
import time
from datetime import UTC, datetime
from pathlib import Path

try:
    import click as _click

    def _c(text: str, fg: str | None = None, bold: bool = False) -> str:
        return _click.style(str(text), fg=fg, bold=bold)

except ImportError:
    def _c(text: str, fg: str | None = None, bold: bool = False) -> str:  # type: ignore[misc]
        return str(text)


LOG_DIR = Path("C:/AI_Runner/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

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


def _ts() -> str:
    return datetime.now(UTC).strftime("%H:%M:%S")


def _write(line: str, plain: str | None = None) -> None:
    print(line, flush=True)
    try:
        _log_file().write(f"[{_ts()}] {plain or line}\n")
    except Exception:
        pass


def banner(title: str) -> None:
    sep = _c("=" * 64, fg="cyan", bold=True)
    _write(sep)
    _write(_c(f"  {title}", fg="cyan", bold=True))
    _write(sep)


def section(title: str) -> None:
    _write(_c(f"\n  ---- {title} ----", fg="blue", bold=True))


def ok(msg: str) -> None:
    _write(_c(f"  OK    {msg}", fg="green"))


def warn(msg: str) -> None:
    _write(_c(f"  WARN  {msg}", fg="yellow"))


def error(msg: str) -> None:
    _write(_c(f"  ERROR  {msg}", fg="red", bold=True))


def info(msg: str) -> None:
    _write(f"         {msg}")


def newline() -> None:
    print("", flush=True)


def state_change(old: str, new: str, cycle: int) -> None:
    _write(_c(f"\n  STATE  {old}  ->  {new}  (cycle {cycle})", fg="cyan", bold=True))


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
        f"\n{sep}"
    )


def agent_start(agent_id: str, cycle: int, prompt_bytes: int, n: int, total: int) -> None:
    kb = prompt_bytes // 1024 if prompt_bytes else 0
    _write(
        f"\n  [{_c(f'{n}/{total}', fg='cyan', bold=True)}]"
        f"  {_c(f'AGENT {agent_id} STARTING', fg='yellow', bold=True)}"
        f"  cycle={cycle}"
        f"  prompt={_c(f'{kb}KB', fg='cyan')}"
        f"  {_c(_ts(), fg='bright_black')}"
    )


def agent_done(agent_id: str, elapsed: float, passed: bool, n: int, total: int) -> None:
    result = _c("PASS", fg="green", bold=True) if passed else _c("FAIL", fg="red", bold=True)
    _write(
        f"  [{_c(f'{n}/{total}', fg='cyan', bold=True)}]"
        f"  AGENT {agent_id}  {result}"
        f"  elapsed={_c(f'{elapsed:.0f}s', fg='cyan')}"
        f"  {_c(_ts(), fg='bright_black')}"
    )


def agent_fail_detail(agent_id: str, detail: str) -> None:
    _write(_c(f"\n  AGENT {agent_id} FAILURE OUTPUT:", fg="red", bold=True))
    tail = (detail or "")[-800:]
    for ln in tail.splitlines()[-15:]:
        _write(_c(f"    {ln}", fg="red"))


def claude_pm_start(agent_id: str, cycle: int, n: int, total: int) -> None:
    _write(
        f"\n  [{_c(f'{n}/{total}', fg='magenta', bold=True)}]"
        f"  {_c(f'Claude PM generating Agent {agent_id} prompt', fg='magenta', bold=True)}"
        f"  cycle={cycle}  {_c(_ts(), fg='bright_black')}"
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
            f"  {_c(f'{kb}KB generated', fg='cyan')}"
        )
    else:
        _write(
            f"  [{_c(f'{n}/{total}', fg='magenta', bold=True)}]"
            f"  Claude PM Agent {agent_id}  {_c('FAILED -- template fallback', fg='yellow', bold=True)}"
            f"  {_c(f'{elapsed:.0f}s', fg='cyan')}"
        )


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
    _write(f"     {icon}  {label_str:<38}{detail_str}")


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
        + _c(grade, fg=color, bold=True)
    )


def blocker(msg: str, code: str = "") -> None:
    tag = f"  [{code}]" if code else ""
    _write(_c(f"\n  BLOCKER{tag}: {msg}", fg="red", bold=True))


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
