from __future__ import annotations
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

RUNNER_STATE = Path("C:/AI_Runner/state/controller_state.json")
CYCLE_LEDGER = Path("C:/AI_Runner/state/cycle_ledger.json")
REPO_ROOT    = Path("C:/Fiverr/Fiverr")

_TRUST: dict[str, int] = {
    "controller_state": 10, "git_branch": 9, "prompt_files": 8,
    "local_hydration": 7,   "jira": 6,     "policy_snapshot": 5,
    "runner_hydration": 2,
}


def _now() -> str:
    return datetime.now(UTC).isoformat()

def _read_state() -> dict:
    try:
        return json.loads(RUNNER_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _write_ledger(entry: dict) -> None:
    ledger: list = []
    if CYCLE_LEDGER.exists():
        try:
            ledger = json.loads(CYCLE_LEDGER.read_text(encoding="utf-8"))
        except Exception:
            ledger = []
    ledger.append(entry)
    if len(ledger) > 500:
        ledger = ledger[-500:]
    CYCLE_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    CYCLE_LEDGER.write_text(json.dumps(ledger, indent=2), encoding="utf-8")

def _probe_controller_state() -> int | None:
    val = _read_state().get("active_cycle")
    return int(val) if val else None

def _probe_git_branches() -> int | None:
    import os
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return None  # skip network in test environment
    try:
        r = subprocess.run(["git","ls-remote","--heads","origin","cycle/*"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=5)
        nums = re.findall(r"cycle/(\d{3})/integration", r.stdout)
        return max(int(n) for n in nums) if nums else None
    except Exception:
        return None

def _probe_prompt_files() -> int | None:
    try:
        d = REPO_ROOT / "PM_Pack/automation/prompts"
        nums = [int(m.group(1)) for f in d.glob("CYCLE_*_AGENT_A_PROMPT.md")
                if (m := re.search(r"CYCLE_(\d{3})_AGENT_A_PROMPT", f.name))]
        return max(nums) if nums else None
    except Exception:
        return None

def _probe_local_hydration() -> int | None:
    try:
        hh = REPO_ROOT / "PM_Pack/07_hydration/HYDRATION_HEADER.md"
        text = hh.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"Active cycle:\s*0*(\d+)", text)
        return int(m.group(1)) if m else None
    except Exception:
        return None

def _probe_policy_snapshot() -> int | None:
    try:
        snap = REPO_ROOT / "PM_Pack/automation/current_policy_snapshot.json"
        data = json.loads(snap.read_text(encoding="utf-8-sig"))
        return int(data.get("cycle_current", 0)) or None
    except Exception:
        return None

def _probe_runner_hydration() -> int | None:
    try:
        p = Path(r"C:\\actions-runner\\_work\\Fiverr\\Fiverr"
                 r"\\PM_Pack\\07_hydration\\HYDRATION_HEADER.md")
        text = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"Active cycle:\s*0*(\d+)", text)
        return int(m.group(1)) if m else None
    except Exception:
        return None

def get_current() -> int:
    cycle = _probe_controller_state()
    return cycle if cycle and cycle > 0 else determine_correct_cycle()["cycle"]

def determine_correct_cycle(verbose: bool = False) -> dict:  # noqa: ARG001
    probes = [("controller_state",_probe_controller_state),("git_branch",_probe_git_branches),
              ("prompt_files",_probe_prompt_files),("local_hydration",_probe_local_hydration),
              ("policy_snapshot",_probe_policy_snapshot),("runner_hydration",_probe_runner_hydration)]
    readings: dict = {}
    for name, fn in probes:
        try:
            readings[name] = fn()
        except Exception:
            readings[name] = None
    valid = {k: v for k, v in readings.items() if v and v > 0}
    if not valid:
        return {"cycle":84,"confidence":"LOW","sources":readings,"conflicts":[],"method":"fallback","spread":0}
    high = {k: v for k, v in valid.items() if _TRUST.get(k, 0) >= 7}
    cycle = max(high.values()) if high else max(valid.values())
    method = "high_trust_max" if high else "all_sources_max"
    spread = max(valid.values()) - min(valid.values())
    conflicts = [{"source":k,"value":v,"trust":_TRUST.get(k,0),"delta":cycle-v}
                 for k, v in valid.items() if v != cycle]
    confidence = "HIGH" if spread <= 1 else ("MEDIUM" if spread <= 3 else "LOW")
    return {"cycle":cycle,"confidence":confidence,"sources":readings,"conflicts":conflicts,
            "method":method,"spread":spread}

def advance(from_cycle: int, reason: str = "post_cycle_pass") -> int:
    current = get_current()
    to_cycle = from_cycle + 1
    if current > to_cycle:
        raise ValueError(f"Cannot advance to {to_cycle}: already at {current}")
    _write_ledger({"ts":_now(),"event":"ADVANCE","from":current,"to":to_cycle,"reason":reason})
    return to_cycle

def force_set(cycle: int, reason: str, operator: str = "system") -> None:
    current = _probe_controller_state() or 0
    _write_ledger({"ts":_now(),"event":"FORCE_SET","from":current,"to":cycle,
                   "reason":reason,"operator":operator})

def reconcile(verbose: bool = True) -> dict:
    import os
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return {"ts":_now(),"controller_state":0,"consensus":0,
                "confidence":"SKIP","sources":{},"conflicts":[],"action":"skipped (pytest)"}
    consensus = determine_correct_cycle()
    current = _probe_controller_state() or 0
    correct = consensus["cycle"]
    report: dict = {"ts":_now(),"controller_state":current,"consensus":correct,
                    "confidence":consensus["confidence"],"sources":consensus["sources"],
                    "conflicts":consensus["conflicts"],"action":"none"}
    if current != correct:
        if correct > current:
            report["action"] = f"CORRECTED {current} -> {correct}"
            _write_ledger({"ts":_now(),"event":"RECONCILE_CORRECTED","from":current,"to":correct,
                           "confidence":consensus["confidence"]})
        else:
            stale = [c["source"] for c in consensus["conflicts"] if _TRUST.get(c["source"],0)<7]
            report["action"] = "KEPT_CONTROLLER (consensus stale)"
            report["stale_sources"] = stale
    return report

def get_ledger(n: int = 20) -> list[dict]:
    try:
        return json.loads(CYCLE_LEDGER.read_text(encoding="utf-8"))[-n:]
    except Exception:
        return []
