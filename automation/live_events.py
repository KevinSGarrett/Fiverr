from __future__ import annotations
import time as _time
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


def tail(interval: float = 2.0, max_lines: int = 20) -> None:
    """OBS-11: Follow live_events.json + current_activity.json in the terminal.

    Usage: python -m automation.live_events
    Prints the last `max_lines` events every `interval` seconds until Ctrl-C.
    """
    import json as _json
    from pathlib import Path as _P
    from datetime import UTC as _UTC, datetime as _dt

    _ACTIVITY = _P("C:/AI_Runner/state/current_activity.json")
    _EVENTS   = _P("C:/AI_Runner/state/live_events.json")

    print("OBS-11: live tail started (Ctrl-C to stop)")
    last_evt_count = 0
    while True:
        try:
            # Print current activity
            activity = {}
            if _ACTIVITY.exists():
                try:
                    activity = _json.loads(_ACTIVITY.read_text(encoding="utf-8"))
                except Exception:
                    pass
            stage_s = activity.get("stage", "?")
            agent_s = activity.get("agent") or "-"
            cycle_s = str(activity.get("cycle") or "?")
            hb = activity.get("last_heartbeat", "?")
            # Calculate heartbeat age
            hb_age = ""
            try:
                hb_dt = _dt.fromisoformat(hb)
                age_s = (_dt.now(_UTC) - hb_dt).total_seconds()
                hb_age = f"  hb_age={age_s:.0f}s"
                if age_s > 60:
                    hb_age += " [STALE?]"
            except Exception:
                pass
            print(f"\r  ACTIVITY: stage={stage_s} agent={agent_s} cycle={cycle_s}{hb_age}   ",
                  end="", flush=True)

            # Print new events
            evts: list = []
            if _EVENTS.exists():
                try:
                    evts = _json.loads(_EVENTS.read_text(encoding="utf-8"))
                except Exception:
                    pass
            if len(evts) != last_evt_count:
                print()  # newline after activity line
                new_evts = evts[last_evt_count:] if len(evts) > last_evt_count else evts[-max_lines:]
                for e in new_evts[-max_lines:]:
                    ts  = e.get("ts", "?")
                    stg = (e.get("stage") or "?")[:10]
                    ag  = e.get("agent") or "-"
                    msg = e.get("msg", "")[:80]
                    print(f"  {ts}  {stg:<10} {ag:<3}  {msg}")
                last_evt_count = len(evts)

            _time.sleep(interval)

        except KeyboardInterrupt:
            print("\nTail stopped.")
            break
        except Exception as _e:
            _time.sleep(interval)


if __name__ == "__main__":
    tail()
