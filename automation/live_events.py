from __future__ import annotations
import json
import threading
from datetime import UTC, datetime
from pathlib import Path

_EVENT_FILE = Path("C:/AI_Runner/state/live_events.json")
_MAX_EVENTS = 200
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(UTC).strftime("%H:%M:%S")


def emit(
    stage: str,
    msg: str,
    *,
    agent: str | None = None,
    cycle: int | None = None,
    status: str = "INFO",
) -> None:
    event: dict = {"ts": _now(), "stage": stage.upper(), "msg": msg, "status": status}
    if agent:
        event["agent"] = agent
    if cycle:
        event["cycle"] = cycle
    with _lock:
        try:
            events: list = []
            if _EVENT_FILE.exists():
                try:
                    events = json.loads(_EVENT_FILE.read_text(encoding="utf-8"))
                except Exception:
                    events = []
            events.append(event)
            if len(events) > _MAX_EVENTS:
                events = events[-_MAX_EVENTS:]
            _EVENT_FILE.parent.mkdir(parents=True, exist_ok=True)
            _EVENT_FILE.write_text(json.dumps(events, indent=2), encoding="utf-8")
        except Exception:
            pass


def recent(n: int = 15) -> list[dict]:
    try:
        if _EVENT_FILE.exists():
            return json.loads(_EVENT_FILE.read_text(encoding="utf-8"))[-n:]
    except Exception:
        pass
    return []


def clear() -> None:
    try:
        _EVENT_FILE.write_text("[]", encoding="utf-8")
    except Exception:
        pass
