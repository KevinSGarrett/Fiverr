"""
pm_intelligence.py — Project Manager Intelligence Layer (v2)
=============================================================
Prevents agents from building the wrong section of the project by:

1. Reading EVERY epic file in PM_Pack/ref/project_plan to understand full scope
2. Reading the wave schedule to understand the build sequence
3. Reading the full Jira board (ALL pages, Done + Pending) to map build status
4. Cross-referencing to pinpoint EXACTLY what is incomplete and needs building next
5. Loading the specific ref docs (implementation spec + DOD) for the target stories
6. Injecting a SECTION 0 "PM Intelligence Brief" into every agent prompt that:
   - States the current wave and target stories
   - Provides the exact ref doc content agents need
   - Lists what already exists (so agents don't rebuild it)
   - Gives hard constraints to prevent stub/wrapper generation

WITHOUT this layer → agents receive vague Jira summaries like "Story 1 for FIVERR-E6"
and build generic automation runner wrappers.

WITH this layer → agents receive full Wave 11 context, exact file targets, method
signatures from spec docs, and a clear warning not to build automation infra.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

REPO_ROOT = Path("C:/Fiverr/Fiverr")
PM_PACK   = REPO_ROOT / "PM_Pack"
REF_ROOT  = PM_PACK / "ref" / "project_plan"
DOD_ROOT  = PM_PACK / "ref" / "dod"      # PM_Pack/ref/dod/DOD_EPIC_08.md
TODO_ROOT = PM_PACK / "ref" / "todo"     # PM_Pack/ref/todo/EPIC_08_PLAYBOOK.md

# ─── Wave → reference folder mapping ─────────────────────────────────────────
WAVE_REF_FOLDER: dict[int, str] = {
    1:  "01_vision",
    2:  "02_architecture",
    3:  "03_data",
    4:  "04_collection",
    5:  "05_scoring",
    6:  "06_analysis",
    7:  "07_reporting",
    8:  "07_reporting",
    9:  "09_pricing",
    10: "10_discovery",
    11: "11_playbook",
    12: "12_dashboard_ux",
}

# ─── Wave → epic TODO file ────────────────────────────────────────────────────
WAVE_EPIC_FILE: dict[int, str] = {
    1:  "EPIC_01_FOUNDATION.md",
    2:  "EPIC_02_COLLECTION.md",
    3:  "EPIC_03_ANALYSIS.md",
    4:  "EPIC_04_SCORING.md",
    5:  "EPIC_05_RECOMMENDATIONS.md",
    6:  "EPIC_06_PRICING.md",
    7:  "EPIC_07_DISCOVERY.md",
    8:  "EPIC_07_DISCOVERY.md",
    9:  "EPIC_06_PRICING.md",
    10: "EPIC_07_DISCOVERY.md",
    11: "EPIC_08_PLAYBOOK.md",
    12: "EPIC_09_DASHBOARD.md",
}

# ─── Wave → DOD file ──────────────────────────────────────────────────────────
WAVE_DOD_FILE: dict[int, str] = {
    11: "DOD_EPIC_08.md",
    12: "DOD_EPIC_09.md",
}

# ─── Known Wave 11 story → file target ───────────────────────────────────────
WAVE11_STORY_TARGETS: dict[str, dict[str, str]] = {
    "SCRUM-205": {
        "story_id": "S8.1",
        "title": "Gig Visual Analysis",
        "target_file": "src/analysis/visual_analysis.py",
        "ref_doc": "11_playbook/GIG_VISUAL_ANALYSIS.md",
    },
    "SCRUM-206": {
        "story_id": "S8.2",
        "title": "Seller Profile Optimization",
        "target_file": "src/analysis/seller_profile.py",
        "ref_doc": "11_playbook/SELLER_PROFILE_OPTIMIZATION.md",
    },
    "SCRUM-207": {
        "story_id": "S8.3",
        "title": "Seller Setup Playbook Generator",
        "target_file": "src/analysis/seller_playbook.py",
        "ref_doc": "11_playbook/SELLER_SETUP_PLAYBOOK.md",
    },
    "SCRUM-208": {
        "story_id": "S8.4",
        "title": "Playbook PDF Export",
        "target_file": "src/analysis/playbook_export.py",
        "ref_doc": "11_playbook/SELLER_SETUP_PLAYBOOK.md",
    },
    "SCRUM-209": {
        "story_id": "S8.5",
        "title": "Visual Recommendations",
        "target_file": "src/analysis/visual_recommendations.py",
        "ref_doc": "11_playbook/GIG_VISUAL_ANALYSIS.md",
    },
    "SCRUM-210": {
        "story_id": "S8.6",
        "title": "Playbook Stage Wiring",
        "target_file": "src/stages/stage_playbook.py",
        "ref_doc": "11_playbook/SELLER_SETUP_PLAYBOOK.md",
    },
    "SCRUM-211": {
        "story_id": "S8.7",
        "title": "Playbook Dashboard Data Layer",
        "target_file": "src/dashboard/playbook_data.py",
        "ref_doc": "11_playbook/SELLER_SETUP_PLAYBOOK.md",
    },
}


@dataclass
class WaveStory:
    jira_key:    str
    story_id:    str
    title:       str
    target_file: str
    ref_doc:     str
    status:      str          # "To Do" | "In Progress" | "Done"
    description: str = ""     # Full story description from Jira


@dataclass
class ProjectSnapshot:
    """
    Full read of the project board and plan files — built once per cycle.
    All downstream logic reads from this object.
    """
    # Jira data
    total_issues:     int              = 0
    done_count:       int              = 0
    pending_count:    int              = 0
    all_stories:      list[dict]       = field(default_factory=list)   # all stories with status
    pending_stories:  list[dict]       = field(default_factory=list)   # not-Done stories

    # Wave analysis
    current_wave:     int              = 11
    wave_name:        str              = "Gig Creation Playbook"
    current_stories:  list[WaveStory]  = field(default_factory=list)   # current wave stories

    # Project plan excerpts (filename → content)
    ref_doc_excerpts: dict[str, str]   = field(default_factory=dict)
    dod_excerpt:      str              = ""
    epic_excerpt:     str              = ""
    wave_schedule:    str              = ""

    # src/ scan
    existing_src:     list[str]        = field(default_factory=list)

    # Build sequence (all waves summary)
    build_sequence:   str              = ""


@dataclass
class CycleBrief:
    """Rendered brief injected as SECTION 0 into every agent prompt."""
    snapshot: ProjectSnapshot

    def to_prompt_section(self) -> str:
        snap = self.snapshot
        to_do = [s for s in snap.current_stories if s.status != "Done"]
        done  = [s for s in snap.current_stories if s.status == "Done"]

        lines: list[str] = [
            "=" * 72,
            "SECTION 0: PROJECT MANAGER INTELLIGENCE BRIEF",
            "THIS SECTION OVERRIDES ALL OTHER INSTRUCTIONS.",
            "READ EVERY LINE BEFORE WRITING A SINGLE FILE.",
            "=" * 72,
            "",
            f"## CURRENT TARGET: Wave {snap.current_wave} — {snap.wave_name}",
            "",
            "## WHAT THIS PROJECT IS",
            "The Fiverr Research System is a real Python application that:",
            "  • Scrapes Fiverr with Playwright to collect gig/seller data",
            "  • Scores niches across 11 dimensions (competition, demand, profitability...)",
            "  • Generates recommendations for new sellers on which niches to enter",
            "  • Runs a Streamlit dashboard to browse results",
            "  • Builds Gig Creation Playbooks telling sellers exactly what to do",
            "",
        ]

        # Build sequence
        lines += [
            "## FULL BUILD SEQUENCE (waves 1–12)",
            snap.build_sequence or "(see PM_Pack/ref/project_plan/00_meta/WAVE_SCHEDULE.md)",
            "",
        ]

        # Jira board summary
        lines += [
            "## JIRA BOARD SUMMARY (FULL BOARD — ALL PAGES FETCHED)",
            f"  Total issues:   {snap.total_issues}",
            f"  Done:           {snap.done_count}",
            f"  Pending:        {snap.pending_count}",
            "",
        ]
        if snap.pending_stories:
            lines.append("  Open stories (next to build in priority order):")
            for s in snap.pending_stories[:20]:
                lines.append(f"    [{s['key']}] {s['summary']}  — {s['status']}")
            if len(snap.pending_stories) > 20:
                lines.append(f"    ...and {len(snap.pending_stories) - 20} more")
            lines.append("")

        # Current wave stories
        lines += [
            f"## WAVE {snap.current_wave} STORY STATUS (your build target this cycle)",
        ]
        if done:
            lines.append("  Already Done — DO NOT REBUILD:")
            for s in done:
                lines.append(f"    ✅ [{s.jira_key}] {s.story_id}: {s.title}")
                lines.append(f"       File: {s.target_file}")
        if to_do:
            lines.append("  TO DO — build these this cycle:")
            for s in to_do:
                lines.append(f"    🔨 [{s.jira_key}] {s.story_id}: {s.title}")
                lines.append(f"       Target file: {s.target_file}")
                lines.append(f"       Full spec:   PM_Pack/ref/project_plan/{s.ref_doc}")
                if s.description:
                    # First 400 chars of Jira description
                    desc_snippet = s.description[:400].replace("\n", " ").strip()
                    lines.append(f"       Jira AC:     {desc_snippet}")
                lines.append("")

        # Already-built src files
        lines += [
            "## FILES ALREADY IN src/ — DO NOT REBUILD OR STUB THESE",
        ]
        for f in snap.existing_src[:40]:
            lines.append(f"  - {f}")
        if len(snap.existing_src) > 40:
            lines.append(f"  ...and {len(snap.existing_src) - 40} more")
        lines.append("")

        # DOD excerpt
        if snap.dod_excerpt:
            lines += [
                "## DEFINITION OF DONE (from project plan — ALL criteria must be met)",
                snap.dod_excerpt[:3500],
                "",
            ]

        # Ref doc excerpts (spec content agents need to implement correctly)
        if snap.ref_doc_excerpts:
            lines += ["## REFERENCE SPEC EXCERPTS (read before writing code)"]
            for doc_name, excerpt in list(snap.ref_doc_excerpts.items())[:3]:
                lines += [f"### {doc_name}", excerpt[:2500], ""]

        # Epic excerpt
        if snap.epic_excerpt:
            lines += [
                "## EPIC TASK BREAKDOWN (your task list for this epic)",
                snap.epic_excerpt[:3000],
                "",
            ]

        # Hard constraints
        lines += [
            "=" * 72,
            "HARD CONSTRAINTS — VIOLATION = CYCLE FAIL",
            "=" * 72,
            "1. BUILD ONLY WHAT'S IN THE TO DO LIST ABOVE. Nothing else.",
            "2. DO NOT create cycle_083_*, story_slice_*, cycle_story_runtime.py,",
            "   fiverr_e*__imp.py, or pipeline.py automation stubs in src/.",
            "   Those are automation runner internals. They do NOT belong in src/.",
            "3. DO NOT implement SCRUM-1088 or any CYCLE-0XX ticket.",
            "   Those are automation runner control tickets, NOT Fiverr features.",
            "4. EVERY .py file you create must contain REAL, EXECUTABLE BUSINESS LOGIC.",
            "   No stubs. No pass-through wrappers. No placeholder classes.",
            "5. Read PM_Pack/ref/project_plan/11_playbook/ files BEFORE writing code.",
            "6. All new code must pass: ruff check, mypy, pytest (run them, show output).",
            "7. Minimum agent run time: 20 minutes. If you finish sooner,",
            "   it means you skipped tasks. Go back and implement them fully.",
            "=" * 72,
        ]
        return "\n".join(lines)


# ─── File I/O helpers ─────────────────────────────────────────────────────────

def _read(path: Path, max_chars: int = 8000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n[...truncated — full file at {path}]"
        return text
    except Exception:
        return ""


def _find_file(name: str, within: Path) -> Path | None:
    """Recursively find a file by name within a directory tree."""
    for p in within.rglob(name):
        return p
    return None


# ─── Jira analysis ────────────────────────────────────────────────────────────

def _parse_jira_board(jira_issues: list[dict]) -> tuple[int, int, int, list[dict], list[dict]]:
    """
    Returns (total, done_count, pending_count, all_stories, pending_stories).
    `jira_issues` is the raw list from board_inventory() or board_inventory_all().
    Handles dual-format: top-level 'status' key OR 'fields.status.name' dict.
    """
    def _status_name(issue: dict) -> str:
        """Get status name from either top-level or fields dict."""
        # Top-level (backward-compat from new normalise_issue)
        top = issue.get("status", "")
        if isinstance(top, str) and top:
            return top
        # Nested under fields
        return issue.get("fields", {}).get("status", {}).get("name", "")

    def _issuetype_name(issue: dict) -> str:
        top = issue.get("issuetype", "")
        if isinstance(top, str) and top:
            return top
        return issue.get("fields", {}).get("issuetype", {}).get("name", "")

    all_stories = [i for i in jira_issues if _issuetype_name(i) == "Story"]
    done_count    = sum(1 for i in jira_issues if _status_name(i).lower() == "done")
    pending_count = len(jira_issues) - done_count
    pending_stories = [
        {
            "key":     i["key"],
            "summary": i.get("summary") or i.get("fields", {}).get("summary", ""),
            "status":  _status_name(i),
            "labels":  i.get("labels") or i.get("fields", {}).get("labels", []),
        }
        for i in all_stories
        if _status_name(i).lower() != "done"
    ]
    return len(jira_issues), done_count, pending_count, all_stories, pending_stories


def _resolve_wave11_story_statuses(jira_issues: list[dict]) -> list[WaveStory]:
    """
    Build the list of Wave 11 WaveStory objects with real Jira statuses.

    Priority order for status resolution:
    1. Direct Jira fetch for SCRUM-205-211 (most accurate — bypasses board_inventory ordering issues)
    2. Filesystem check — if the target file already exists, mark as Done
    3. jira_issues list from board_inventory (may not include all Wave 11 stories)
    4. Default: To Do
    """
    # Index raw Jira by key for quick lookup
    jira_by_key: dict[str, dict] = {i["key"]: i for i in jira_issues}

    # Try to fetch Wave 11 stories directly from Jira
    wave11_keys = list(WAVE11_STORY_TARGETS.keys())
    live_statuses: dict[str, str] = {}
    live_descriptions: dict[str, str] = {}
    try:
        from automation.jira_client import _search_all, _adf_to_text
        jql = f"project = SCRUM AND key in ({','.join(wave11_keys)})"
        raw_issues = _search_all(jql)
        for raw in raw_issues:
            key = raw.get("key", "")
            fields = raw.get("fields", {})
            live_statuses[key] = fields.get("status", {}).get("name", "To Do")
            # Convert ADF description to plain text
            raw_desc = fields.get("description")
            if raw_desc and isinstance(raw_desc, dict):
                live_descriptions[key] = _adf_to_text(raw_desc)
            elif isinstance(raw_desc, str):
                live_descriptions[key] = raw_desc
            else:
                live_descriptions[key] = ""
    except Exception:
        pass  # Fall back to jira_issues list

    stories: list[WaveStory] = []
    for jira_key, spec in WAVE11_STORY_TARGETS.items():
        # 1. Live Jira status (most accurate)
        if jira_key in live_statuses:
            status_name = live_statuses[jira_key]
            description = live_descriptions.get(jira_key, "")
        elif jira_key in jira_by_key:
            raw = jira_by_key[jira_key]
            status_name = raw["fields"]["status"].get("name", "To Do")
            description = raw["fields"].get("description", "")
        else:
            status_name = "To Do"
            description = ""

        # 2. Filesystem check — if target file already exists, it's effectively Done
        # (even if Jira says To Do — Jira may be out of date)
        target_path = REPO_ROOT / spec["target_file"]

        # Also check alternate locations (e.g. src/playbook/ for S8.3)
        alt_paths: list[Path] = []
        if "analysis/seller_playbook" in spec["target_file"]:
            alt_paths.append(REPO_ROOT / "src/playbook/generator.py")
        if "analysis/seller_profile" in spec["target_file"]:
            alt_paths.append(REPO_ROOT / "src/playbook/seed_guidance.py")

        filesystem_done = target_path.exists() or any(p.exists() for p in alt_paths)
        if filesystem_done and status_name == "To Do":
            status_name = "In Progress (file exists)"

        stories.append(WaveStory(
            jira_key=jira_key,
            story_id=spec["story_id"],
            title=spec["title"],
            target_file=spec["target_file"],
            ref_doc=spec["ref_doc"],
            status=status_name,
            description=description[:600],
        ))

    return stories


# ─── Project plan file readers ────────────────────────────────────────────────

def _read_wave_schedule() -> str:
    """Read the wave schedule for full build-sequence context."""
    # Primary: ref/project_plan/00_meta/WAVE_SCHEDULE.md
    path = REF_ROOT / "00_meta" / "WAVE_SCHEDULE.md"
    if not path.exists():
        # Fallback: anywhere under ref/
        path = _find_file("WAVE_SCHEDULE.md", PM_PACK / "ref")
    return _read(path, max_chars=3000) if (path and path.exists()) else ""


def _build_sequence_summary() -> str:
    """
    Build a compact one-line-per-wave summary of the full build sequence.
    Pulled from the wave schedule and enhancement schedule.
    """
    sched = _read_wave_schedule()
    if not sched:
        return (
            "Wave 1-8: Foundation, Collection, Analysis, Scoring, "
            "Recommendations, Pricing, Discovery, Reporting (COMPLETE)\n"
            "Wave 9: Pricing Strategy Engine (COMPLETE)\n"
            "Wave 10: LLM-Powered Niche Discovery (COMPLETE)\n"
            "Wave 11: Gig Creation Playbook ← CURRENT\n"
            "Wave 12: Dashboard UX Overhaul (NOT STARTED)"
        )

    # Extract the Implementation Breakdown table rows
    rows = re.findall(r"\|\s*(TD-\d+)\s*\|.*?\|\s*(COMPLETE|IN PROGRESS|NOT STARTED)\s*\|",
                      sched, re.IGNORECASE)
    lines = []
    for row in rows:
        td, status = row
        lines.append(f"  {td}: {status}")

    # Append enhancement waves
    enhance = _read(REF_ROOT / "00_meta" / "ENHANCEMENT_WAVE_SCHEDULE.md", max_chars=1500)
    wave_rows = re.findall(r"\|\s*(Wave \d+)\s*\|\s*([^|]+?)\s*\|", enhance)
    for wave, name in wave_rows:
        lines.append(f"  {wave}: {name.strip()}")

    return "\n".join(lines) if lines else sched[:1500]


def _read_ref_docs_for_wave(wave: int) -> dict[str, str]:
    """
    Read the spec documents from PM_Pack/ref for the given wave.
    Returns filename → content (truncated).
    """
    folder_name = WAVE_REF_FOLDER.get(wave)
    if not folder_name:
        return {}
    folder = REF_ROOT / folder_name
    if not folder.exists():
        return {}

    docs: dict[str, str] = {}
    # Sort so the most relevant come first (files named GIG_, SELLER_ etc.)
    for p in sorted(folder.iterdir()):
        if p.suffix == ".md" and len(docs) < 4:
            content = _read(p, max_chars=5000)
            if content:
                docs[p.name] = content
    return docs


def _read_dod(wave: int) -> str:
    dod_name = WAVE_DOD_FILE.get(wave)
    if not dod_name:
        return ""
    # Primary: PM_Pack/ref/dod/
    path = DOD_ROOT / dod_name
    if path.exists():
        return _read(path, max_chars=4000)
    # Fallback: anywhere under ref/
    path = _find_file(dod_name, PM_PACK / "ref")
    return _read(path, max_chars=4000) if path else ""


def _read_epic(wave: int) -> str:
    epic_name = WAVE_EPIC_FILE.get(wave)
    if not epic_name:
        return ""
    # Primary: PM_Pack/ref/todo/
    path = TODO_ROOT / epic_name
    if path.exists():
        return _read(path, max_chars=3000)
    # Fallback: anywhere under ref/
    path = _find_file(epic_name, PM_PACK / "ref")
    return _read(path, max_chars=3000) if path else ""


# ─── src/ scanner ────────────────────────────────────────────────────────────

def _scan_existing_src() -> list[str]:
    """List real src/ files that already exist, excluding stubs from C083."""
    src = REPO_ROOT / "src"
    if not src.exists():
        return []
    stub_patterns = {
        "cycle_083", "cycle_story_runtime", "story_slice_factory",
        "fiverr_e3", "fiverr_e4", "fiverr_e5", "fiverr_e6",
        "pipeline",   # automation runner pipeline stub
    }
    files = []
    for p in sorted(src.rglob("*.py")):
        if "__pycache__" in str(p):
            continue
        rel = str(p.relative_to(REPO_ROOT)).replace("\\", "/")
        stem = p.stem.lower()
        if any(pat in stem for pat in stub_patterns):
            continue
        files.append(rel)
    return files


# ─── Current wave detection ───────────────────────────────────────────────────

def _detect_current_wave() -> int:
    """Read HYDRATION_HEADER or EPIC_STATUS_TRACKER to find current wave."""
    hydration = PM_PACK / "07_hydration" / "HYDRATION_HEADER.md"
    if hydration.exists():
        text = _read(hydration, max_chars=2000)
        m = re.search(r"WAVE_CURRENT:\s*(\d+)", text)
        if m:
            return int(m.group(1))

    tracker = PM_PACK / "08_task_queue" / "EPIC_STATUS_TRACKER.md"
    if tracker.exists():
        text = _read(tracker, max_chars=3000)
        m = re.search(r"WAVE_CURRENT:\s*(\d+)", text)
        if m:
            return int(m.group(1))

    return 11  # default


WAVE_NAMES: dict[int, str] = {
    9:  "Pricing Strategy Engine",
    10: "LLM-Powered Niche Discovery",
    11: "Gig Creation Playbook",
    12: "Dashboard UX Overhaul",
}


# ─── Main entry point ─────────────────────────────────────────────────────────

def build_cycle_brief(
    jira_issues: list[dict] | None = None,
    current_wave: int | None = None,
) -> CycleBrief:
    """
    Build the complete PM intelligence brief for injection into agent prompts.

    Parameters
    ----------
    jira_issues:
        Raw issue list from jira_client.board_inventory() or board_inventory_all().
        If None, the brief is built without live Jira data (uses known Jira keys).
    current_wave:
        Override the detected current wave. If None, auto-detected from
        HYDRATION_HEADER / EPIC_STATUS_TRACKER.
    """
    issues = jira_issues or []
    wave   = current_wave or _detect_current_wave()

    # ── Jira analysis ──────────────────────────────────────────────────────
    total, done_c, pending_c, all_stories, pending_stories = _parse_jira_board(issues)

    # ── Wave 11 stories ────────────────────────────────────────────────────
    wave_stories = _resolve_wave11_story_statuses(issues)

    # ── Project plan files ─────────────────────────────────────────────────
    ref_docs     = _read_ref_docs_for_wave(wave)
    dod_excerpt  = _read_dod(wave)
    epic_excerpt = _read_epic(wave)
    build_seq    = _build_sequence_summary()

    # ── src/ scan ──────────────────────────────────────────────────────────
    existing_src = _scan_existing_src()

    snap = ProjectSnapshot(
        total_issues=total,
        done_count=done_c,
        pending_count=pending_c,
        all_stories=all_stories,
        pending_stories=pending_stories,
        current_wave=wave,
        wave_name=WAVE_NAMES.get(wave, f"Wave {wave}"),
        current_stories=wave_stories,
        ref_doc_excerpts=ref_docs,
        dod_excerpt=dod_excerpt,
        epic_excerpt=epic_excerpt,
        wave_schedule=build_seq,
        existing_src=existing_src,
        build_sequence=build_seq,
    )

    log.info(
        "PM brief built: wave=%d (%s) | jira=%d total, %d pending | "
        "%d wave stories | %d ref docs | %d src files",
        wave, snap.wave_name, total, pending_c,
        len(wave_stories), len(ref_docs), len(existing_src),
    )

    return CycleBrief(snapshot=snap)
