"""
pm_pack_loader.py Ã¢â‚¬â€ Read and validate PM_Pack brain files.
Implements the brain-check command logic: load each file in registry order
and report PASS/FAIL per file.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REGISTRY_PATH = Path("PM_Pack/automation/BRAIN_REGISTRY.yml")
POST_CYCLE_PROMPT_REL = "PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md"


@dataclass
class BrainCheckResult:
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    cycle_detected: str | None = None
    wave_detected: str | None = None
    blockers_detected: list[str] = field(default_factory=list)
    cursor_model_status: str = "UNVERIFIED"
    claude_model_status: str = "UNVERIFIED"
    post_cycle_prompt_present: bool = False

    @property
    def ok(self) -> bool:
        return len(self.failed) == 0


def brain_check(repo_root: Path) -> BrainCheckResult:
    """Load all brain files and return a structured result."""
    result = BrainCheckResult()

    registry_path = repo_root / REGISTRY_PATH
    if not registry_path.exists():
        result.failed.append(f"BRAIN_REGISTRY.yml missing: {registry_path}")
        return result

    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8", errors="replace")) or {}
    result.passed.append(f"BRAIN_REGISTRY.yml loaded: {registry_path}")

    # Check all load_order files
    load_order: dict[str, list[str]] = registry.get("load_order", {})
    for section, files in load_order.items():
        for rel_path in files:
            full = _resolve(rel_path, repo_root)
            if full.exists():
                result.passed.append(f"PASS [{section}]: {rel_path}")
            else:
                # In CI, runner-side paths (C:/AI_Runner) do not exist â€” skip as warning
                _norm_path = rel_path.replace("\\", "/").replace("\\", "/")
                if os.environ.get("CI", "").strip() and _norm_path.startswith("C:/AI_Runner"):
                    result.warnings.append(f"SKIPPED [ci] [{section}]: {rel_path}")
                else:
                    result.failed.append(f"MISSING [{section}]: {rel_path}")

    # Parse hydration header for cycle/wave/blockers Ã¢â‚¬â€ use exact key lines
    hydration_path = repo_root / "PM_Pack/07_hydration/HYDRATION_HEADER.md"
    if hydration_path.exists():
        text = hydration_path.read_text(encoding="utf-8", errors="replace")
        # Match key-value lines like "CYCLE_CURRENT: 075" Ã¢â‚¬â€ NOT filenames like cycle037_live.db
        m_cycle = re.search(r"^CYCLE_CURRENT:\s*0*(\d+)", text, re.MULTILINE)
        if not m_cycle:
            m_cycle = re.search(r"^CYCLE_NEXT:\s*0*(\d+)", text, re.MULTILINE)
        if not m_cycle:
            m_cycle = re.search(r"NEXT CYCLE \(C0*(\d+)\)", text)
        result.cycle_detected = m_cycle.group(1) if m_cycle else None

        m_wave = re.search(r"^WAVE_CURRENT:\s*(\d+)", text, re.MULTILINE)
        result.wave_detected = m_wave.group(1) if m_wave else None

        blocker_section = re.search(r"(?i)blocker[s]?.*?\n((?:[-*].+\n?)*)", text)
        if blocker_section:
            result.blockers_detected = [
                re.sub(r"^[-*\s]+", "", ln).strip()
                for ln in blocker_section.group(1).splitlines()
                if ln.strip() and ln.strip() not in ("-", "*")
            ]

    # Verify post-cycle prompt
    pcp = repo_root / POST_CYCLE_PROMPT_REL
    result.post_cycle_prompt_present = pcp.exists()
    if result.post_cycle_prompt_present:
        result.passed.append(f"PASS [required]: POST_CYCLE_PM_REVIEW_v4.md ({pcp.stat().st_size} bytes)")
    else:
        result.failed.append(f"MISSING [required]: {POST_CYCLE_PROMPT_REL}")

    # Check model state files
    cursor_state = _load_json(Path("C:/AI_Runner/state/cursor_model_state.json"))
    result.cursor_model_status = cursor_state.get("status", "MISSING")
    if result.cursor_model_status == "VERIFIED":
        result.passed.append(f"PASS [model]: Cursor model VERIFIED ({cursor_state.get('observed_model')})")
    else:
        result.warnings.append(f"WARNING [model]: Cursor model status = {result.cursor_model_status}")

    claude_state = _load_json(Path("C:/AI_Runner/state/claude_model_state.json"))
    result.claude_model_status = claude_state.get("status", "MISSING")
    if "VERIFIED" in result.claude_model_status or "SUBSCRIPTION" in result.claude_model_status:
        result.passed.append(f"PASS [model]: Claude billing = {claude_state.get('billing_mode')}")
    else:
        result.warnings.append(f"WARNING [model]: Claude status = {result.claude_model_status}")

    return result


def load_file(rel_path: str, repo_root: Path) -> str:
    """Load a single PM_Pack file as text."""
    full = _resolve(rel_path, repo_root)
    return full.read_text(encoding="utf-8", errors="replace") if full.exists() else ""


def load_policy(policy_path: Path, required_fields: list[str] | None = None) -> dict[str, Any]:
    """Load and validate a YAML policy file."""
    if not policy_path.exists():
        raise FileNotFoundError(f"Policy file not found: {policy_path}")
    data = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Policy YAML must map to an object: {policy_path}")
    required = required_fields or []
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"Policy missing required fields: {', '.join(missing)}")
    return data


def check_cycle_consistency(
    hydration_header: str,
    state_snapshot: str,
    current_state_canonical: str,
) -> list[str]:
    """Return consistency findings between cycle markers across PM pack files."""
    findings: list[str] = []
    hyd_cycle = _extract(hydration_header, r"CYCLE_CURRENT:\s*0*(\d+)")
    snapshot_cycle = _extract(state_snapshot, r"CYCLE_CURRENT:\s*0*(\d+)")
    canonical_cycle = _extract(current_state_canonical, r"CYCLE_CURRENT:\s*0*(\d+)")
    if hyd_cycle and snapshot_cycle and hyd_cycle != snapshot_cycle:
        findings.append(f"Hydration cycle {hyd_cycle} != state snapshot cycle {snapshot_cycle}")
    if hyd_cycle and canonical_cycle and hyd_cycle != canonical_cycle:
        findings.append(f"Hydration cycle {hyd_cycle} != canonical cycle {canonical_cycle}")
    return findings


def _resolve(rel_path: str, repo_root: Path) -> Path:
    """Resolve a path that might be repo-relative or absolute (cross-platform).

    On Linux, Windows-style absolute paths like C:/AI_Runner/... are not absolute
    per pathlib, so we detect the drive-letter pattern explicitly.
    """
    norm = rel_path.replace("\\", "/")
    p = Path(norm)
    # Windows-style absolute path on any platform (drive letter like C:/)
    if p.is_absolute() or (len(norm) >= 2 and norm[1] == ":"):
        return Path(norm)
    return repo_root / p


def _extract(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text)
    return m.group(1) if m else None


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}

