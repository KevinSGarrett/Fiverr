"""
pm_pack_loader.py — Read and validate PM_Pack brain files.
Implements the brain-check command logic: load each file in registry order
and report PASS/FAIL per file.
"""
from __future__ import annotations

import json
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


# ITEM D-7: stub markers that mean a brain file is a placeholder, not real content.
_BRAIN_STUB_MARKERS = ("[STUB", "[FILL]", "populate from PM_Pack",
                       "<placeholder>", "TBD-PLACEHOLDER")


def _brain_file_content_ok(path: Path) -> tuple[bool, str]:
    """ITEM D-7: a brain file must carry REAL content, not merely exist. Returns
    (ok, reason). Empty/whitespace-only or stub-placeholder files FAIL; structured
    files (.json / .yml / .yaml) must additionally parse. Binary brain assets
    (.db etc.) only need to be non-empty. Conservative: only the strongest stub
    markers count, so incidental words don't false-fail a real doc."""
    try:
        suffix = path.suffix.lower()
        if suffix in (".db", ".sqlite", ".sqlite3", ".png", ".jpg", ".jpeg", ".pdf", ".zip"):
            return (path.stat().st_size > 0, "" if path.stat().st_size > 0 else "empty binary asset")
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            return (False, "empty / whitespace-only")
        low = text.lower()
        for marker in _BRAIN_STUB_MARKERS:
            if marker.lower() in low:
                return (False, f"stub placeholder ({marker})")
        if suffix == ".json":
            try:
                json.loads(text)
            except Exception as e:
                return (False, f"invalid JSON: {str(e)[:60]}")
        elif suffix in (".yml", ".yaml"):
            try:
                yaml.safe_load(text)
            except Exception as e:
                return (False, f"invalid YAML: {str(e)[:60]}")
        return (True, "")
    except Exception as e:
        return (False, f"unreadable: {str(e)[:60]}")


def brain_check(repo_root: Path) -> BrainCheckResult:
    """Load all brain files and return a structured result."""
    result = BrainCheckResult()

    registry_path = repo_root / REGISTRY_PATH
    if not registry_path.exists():
        result.failed.append(f"BRAIN_REGISTRY.yml missing: {registry_path}")
        return result

    registry = yaml.safe_load(registry_path.read_text()) or {}
    result.passed.append(f"BRAIN_REGISTRY.yml loaded: {registry_path}")

    # Check all load_order files. ITEM D-7: existence alone is NOT enough — a
    # file that exists but is empty or a stub placeholder would let a structurally
    # broken brain pass the gate (brain-check gates `plan-cycle --live`, so a false
    # green poisons the milestone observation). Validate CONTENT, not just presence.
    load_order: dict[str, list[str]] = registry.get("load_order", {})
    for section, files in load_order.items():
        for rel_path in files:
            full = _resolve(rel_path, repo_root)
            if not full.exists():
                result.failed.append(f"MISSING [{section}]: {rel_path}")
                continue
            ok, why = _brain_file_content_ok(full)
            if ok:
                result.passed.append(f"PASS [{section}]: {rel_path}")
            else:
                result.failed.append(f"INVALID [{section}]: {rel_path} — {why}")

    # Validate optional structured fiverr_project registry block when present.
    fiverr_registry = registry.get("fiverr_project", {})
    if isinstance(fiverr_registry, dict):
        fiverr_base = str(fiverr_registry.get("path", "PM_Pack/fiverr_project/")).strip()
        fiverr_files = fiverr_registry.get("files", [])
        required_for_build = bool(fiverr_registry.get("required_for_build", False))
        if isinstance(fiverr_files, list):
            for filename in fiverr_files:
                rel_path = f"{fiverr_base.rstrip('/')}/{filename}"
                full = _resolve(rel_path, repo_root)
                if not full.exists():
                    if required_for_build:
                        result.failed.append(f"MISSING [fiverr_project]: {rel_path}")
                    else:
                        result.warnings.append(f"WARNING [fiverr_project]: {rel_path}")
                    continue
                ok, why = _brain_file_content_ok(full)
                if ok:
                    result.passed.append(f"PASS [fiverr_project]: {rel_path}")
                elif required_for_build:
                    result.failed.append(f"INVALID [fiverr_project]: {rel_path} — {why}")
                else:
                    result.warnings.append(f"WARNING [fiverr_project]: {rel_path} — {why}")

    # Parse hydration header for cycle/wave/blockers — use exact key lines
    hydration_path = repo_root / "PM_Pack/07_hydration/HYDRATION_HEADER.md"
    if hydration_path.exists():
        text = hydration_path.read_text(encoding="utf-8", errors="replace")
        # Match key-value lines like "CYCLE_CURRENT: 075" — NOT filenames like cycle037_live.db
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


def _resolve(rel_path: str, repo_root: Path) -> Path:
    """Resolve a path that might be repo-relative or absolute."""
    p = Path(rel_path.replace("\\", "/"))
    if p.is_absolute():
        return p
    return repo_root / p


def _extract(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text)
    return m.group(1) if m else None


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}
