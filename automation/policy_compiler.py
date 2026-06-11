"""
policy_compiler.py — Compile PM_Pack rules into a machine-readable policy snapshot.
Output: PM_Pack/automation/current_policy_snapshot.json
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


SNAPSHOT_PATH = Path("PM_Pack/automation/current_policy_snapshot.json")


def compile_policy(repo_root: Path) -> dict[str, Any]:
    """Read PM_Pack files and produce a policy snapshot dict."""
    snapshot: dict[str, Any] = {
        "compiled_at": datetime.now(timezone.utc).isoformat(),
        "runner": "fiverr-runner-local-01",
        "repo": "KevinSGarrett/Fiverr",
        "local_path": "C:/Fiverr/Fiverr",
    }

    # --- Hydration: detect cycle, wave, scores ---
    hydration = _read(repo_root / "PM_Pack/07_hydration/HYDRATION_HEADER.md")

    # Use exact key=value matches first (CYCLE_CURRENT: 075),
    # NOT loose pattern which would match filenames like data/cycle037_live.db
    snapshot["cycle_current"] = (
        _extract_int(hydration, r"^CYCLE_CURRENT:\s*0*(\d+)", from_line_start=True)
        or _extract_int(hydration, r"^CYCLE_NEXT:\s*0*(\d+)", from_line_start=True)
        or _extract_int(hydration, r"NEXT CYCLE \(C0*(\d+)\)")
    )
    snapshot["active_wave"] = (
        _extract_int(hydration, r"^WAVE_CURRENT:\s*(\d+)", from_line_start=True)
        or _extract_int(hydration, r"[Ww]ave[:\s#]*(\d+)")
    )
    snapshot["e2e_score_pct"] = _extract_float(hydration, r"END_TO_END[^:]*:\s*~?(\d+(?:\.\d+)?)\s*%")
    snapshot["internal_score_pct"] = _extract_float(hydration, r"INTERNAL_BUILD_PROGRESS:\s*~?(\d+(?:\.\d+)?)\s*%")

    # --- State snapshot ---
    state = _read(repo_root / "PM_Pack/07_hydration/STATE_SNAPSHOT.md")
    snapshot["last_completed_cycle"] = _extract_str(state, r"[Cc]ompleted[:\s]*([Cc]\d{3})")

    # --- Agent lanes ---
    lanes_path = repo_root / "PM_Pack/automation/agent_lanes.yml"
    if lanes_path.exists():
        lanes_cfg = yaml.safe_load(lanes_path.read_text()) or {}
        snapshot["active_agent_lanes"] = lanes_cfg.get("default_order", ["A", "B", "E", "C", "F", "D"])
        snapshot["agent_model"] = lanes_cfg.get("active_model", "six_lane")
    else:
        snapshot["active_agent_lanes"] = ["A", "B", "E", "C", "F", "D"]
        snapshot["agent_model"] = "six_lane_fallback"

    # --- Branch policy (from GitHub rules) ---
    snapshot["branch_policy"] = {
        "cycle_branch_pattern": "cycle/{NNN}/integration",
        "target_branch": "develop",
        "main_direct_push_allowed": False,
        "release_to_main_requires_release_gate": True,
        "force_push_allowed": False,
    }

    # --- Quality gates ---
    snapshot["quality_gates"] = {
        "ruff": True, "mypy": True, "pytest": True,
        "coverage_floor": 90,
        "config_check": True, "foundation_gate": True, "phase2_smoke": True,
        "codecov_project_required": True, "codecov_patch_required": True,
        "codex_disposition_required": True,
    }

    # --- Jira policy ---
    snapshot["jira_policy"] = {
        "board_first": True,
        "exact_issue_keys_required": True,
        "ac_dod_required_per_task": True,
        "done_requires_merge_and_full_dod": True,
        "cloud_id": "eae77257-a572-4e19-b746-8b184ba2d01f",
        "project_key": "SCRUM",
        "done_transition_id": "41",
    }

    # --- Model policy ---
    cursor_state_path = Path("C:/AI_Runner/state/cursor_model_state.json")
    if cursor_state_path.exists():
        cs = json.loads(cursor_state_path.read_text())
        snapshot["cursor_model"] = {
            "requested": cs.get("requested_model"),
            "observed": cs.get("observed_model"),
            "status": cs.get("status"),
            "auto_disabled": cs.get("auto_model_disabled"),
        }

    snapshot["claude_billing_mode"] = "claude_subscription_only"
    snapshot["access_profile"] = "lenient_autonomous_development"

    # Write snapshot to repo
    out_path = repo_root / SNAPSHOT_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snapshot, indent=2))

    return snapshot


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _extract_int(text: str, pattern: str, default: int = 0,
                 from_line_start: bool = False) -> int:
    flags = re.MULTILINE if from_line_start else 0
    m = re.search(pattern, text, flags)
    return int(m.group(1)) if m else default


def _extract_float(text: str, pattern: str) -> float | None:
    m = re.search(pattern, text)
    return float(m.group(1)) if m else None


def _extract_str(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text)
    return m.group(1) if m else None
