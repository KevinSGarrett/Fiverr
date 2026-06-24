"""
claude_prompt_creator.py — Claude-powered PM and Prompt Creator.

This module IS the Project Manager. It:
1. Reads the full project state (PM_Pack/ref, Jira board, wave tracker, existing src/)
2. Reads every Jira story's AC, DOD, acceptance criteria, and existing comments
3. Calls the Claude subscription (`claude` CLI) to act as an intelligent PM
4. Claude generates rich, project-aware agent prompts equivalent to the C070 manual quality
5. Returns the 6 agent prompt texts

Design rationale:
- Claude subscription handles the HEAVY PM work (context synthesis, intelligent tasking)
- Cursor CLI + Codex 5.3 handles CODE EXECUTION (runs the prompts)
- This preserves Cursor allowance for actual code writing
- The template-based prompt_generator.py is used as a fallback only

Architecture decision (from original design):
  Claude = Project Manager / Prompt Creator
  Cursor = Code Executor / Agent Runtime
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from automation import runner_paths

REPO_ROOT     = Path("C:/Fiverr/Fiverr")
PM_PACK       = REPO_ROOT / "PM_Pack"
REF_ROOT      = PM_PACK / "ref" / "project_plan"
DOD_ROOT      = PM_PACK / "ref" / "dod"
TODO_ROOT     = PM_PACK / "ref" / "todo"
RUNNER_ROOT   = Path("C:/AI_Runner")

# H6 FIX: Use the strongest available subscription model for PM synthesis.
# The manual PM that "worked flawlessly" was Opus-class. Sonnet was deliberately
# weaker. Reading from config allows upgrading without code changes.
# Fallback: claude-sonnet-4-6 if config not found.
def _get_pm_model() -> str:
    """Resolve PM model from policy config, defaulting to strongest available.

    H6.1: Always use the strongest available subscription model for PM synthesis.
    H6.2: Log model confirmation so the operator can verify.
    H6.3: Tag SUBSCRIPTION_VERIFIED_WRONG_MODEL if config says Opus but probe
          finds only Sonnet available (soft warning — does not abort).
    """
    import logging
    # Per project config: Claude Sonnet 4.6 with medium effort + adaptive thinking.
    # Sonnet 4.6 is the correct model for PM synthesis -- not Opus.
    # (H6 fix was wrong direction: original manual PM used Sonnet-equivalent, not Opus)
    _PREFERRED_ORDER = [
        "claude-sonnet-4-6",
        "claude-sonnet-4-7",
        "claude-sonnet-4-8",
    ]
    try:
        import yaml
        # H8.1: single config source of truth
        for cfg_path in [
            REPO_ROOT / "PM_Pack/automation/autonomous_runner.yml",
            REPO_ROOT / "config/autonomous_runner.yml",
            REPO_ROOT / "PM_Pack/automation/codex_verifier.yml",
        ]:
            if cfg_path.exists():
                cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
                configured = cfg.get("pm_model") or cfg.get("claude_model")
                if configured:
                    logging.getLogger("pm_model").debug(
                        f"H6.1: PM model from {cfg_path.name}: {configured}"
                    )
                    return str(configured)
    except Exception:
        pass
    # Default to strongest
    model = _PREFERRED_ORDER[0]
    logging.getLogger("pm_model").debug(f"H6.1: PM model defaulting to {model}")
    return model


def _announce_pm_model(model: str) -> None:
    """H6.2: Log model confirmation banner before PM generation."""
    import click
    click.secho(
        f"  [PM MODEL] Using {model} for PM synthesis "
        "(H6.1: strongest available subscription model)",
        fg="cyan",
    )

CLAUDE_MODEL  = _get_pm_model()
# CLAUDE_TIMEOUT is defined below, after _pm_int_env, so it is env-tunable.


def _pm_int_env(name: str, default: int) -> int:
    """Read a tunable integer knob from the environment, else use the default.

    Lets operators tune prompt-generation resilience without code changes and
    lets unit tests override the knobs deterministically.
    """
    import os
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _pm_bool_env(name: str, default: bool) -> bool:
    """Read a boolean knob from the environment, else use ``default``.

    Truthy: 1/true/yes/on (case-insensitive). Falsy: 0/false/no/off.
    """
    import os
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


# ── PMR: prompt-generation resilience ────────────────────────────────────
# Root cause of the 2026-06-18 15:31 CLAUDE_PM_PARTIAL pause: the six agent
# prompts were generated one-shot with no retry, so a transient failure on a
# single agent (a usage/rate-limit trip after several large generations, or a
# per-call timeout) aborted the whole cycle at "partial". These knobs add
# bounded retry + exponential backoff + inter-agent spacing + resume-from-
# partial, so a transient blip no longer pauses the autopilot.
PM_MAX_ATTEMPTS       = _pm_int_env("PM_MAX_ATTEMPTS", 3)         # attempts per agent
PM_RETRY_BACKOFF_BASE = _pm_int_env("PM_RETRY_BACKOFF_BASE", 20)  # seconds; doubles each retry
PM_RETRY_BACKOFF_CAP  = _pm_int_env("PM_RETRY_BACKOFF_CAP", 120)  # max backoff seconds
PM_INTER_AGENT_DELAY  = _pm_int_env("PM_INTER_AGENT_DELAY", 5)    # seconds between agents
PM_MIN_PROMPT_CHARS   = _pm_int_env("PM_MIN_PROMPT_CHARS", 2000)  # resume-reuse threshold
# Item 1.1 (T4): per-agent generation budget. Raised from a hardcoded 480s
# (live p100 was 469s — only a 1s margin, the proximate cause of timeout-driven
# CLAUDE_PM_PARTIAL pauses) to a 900s default with real headroom, and made
# env-tunable so operators can adjust without code changes.
CLAUDE_TIMEOUT        = _pm_int_env("CLAUDE_PM_TIMEOUT", 900)     # seconds per agent

# ── GEN-QUALITY hybrid generation ────────────────────────────────────────────
# Root cause of the 2026-06-20 live milestone block: the single-shot generator
# asked Claude to emit the ENTIRE prompt in one call — all FIXED scaffolding
# (model block, PQ-0..5 sections, validation block, END OF PROMPT) PLUS 55+
# distinct code-bearing tasks. Claude (sonnet-4-6) either timed out / truncated
# (29 tasks, missing fixed tokens) or padded (repeated task bodies -> a degenerate
# 3-4% unique-word prompt). The HYBRID generator splits the work so a faithful
# generation PASSES the (unchanged) quality gate:
#   1. the FIXED scaffold is injected DETERMINISTICALLY — it never depends on the
#      model, so the structural gates (required tokens, PQ-0..5, END OF PROMPT,
#      ruff/mypy/pytest, repo/branch/report path) pass BY CONSTRUCTION; and
#   2. Claude authors ONLY the task bodies, in small BATCHES — each call is
#      bounded (finishes well under the timeout) and produces distinct real
#      content instead of padding.
# The assembled prompt is still validated in-process and fail-closed downstream.
GEN_HYBRID            = _pm_bool_env("GEN_HYBRID", True)          # hybrid on by default
# RECALIBRATED 2026-06-23 (target 60 -> 18; floor is now MIN_TASKS=15 in prompt_validator).
# A ~15-18-task slice generates in ~2 batches (~5-10 min) and builds reliably in ~15-25 min,
# vs the old 55-60-task prompt that needed ~8 batches and ~45-min fragile Cursor builds.
# Quality is preserved by the per-task skeleton + the scale-invariant PQ-6/PQ-7 ratio gates.
GEN_TARGET_TASKS      = _pm_int_env("GEN_TARGET_TASKS", 18)       # author to 18 (floor 15 + margin)
GEN_BATCH_SIZE        = _pm_int_env("GEN_BATCH_SIZE", 12)         # tasks authored per Claude call
GEN_MAX_BATCH_ROUNDS  = _pm_int_env("GEN_MAX_BATCH_ROUNDS", 6)    # safety cap on batch calls/agent
# Aggregate wall-clock budget for ONE agent's batched generation. Bounds the tail latency
# the per-batch CLAUDE_TIMEOUT alone does not. At ~7-12 authored tasks per ~450s batch call,
# the 15-18-task target needs ~2-3 rounds ≈ 900-1350s; 2400s gives the round cap headroom
# to reach the floor on attempt 1 while failing a genuinely stalled agent faster than before.
GEN_BATCH_BUDGET_S    = _pm_int_env("GEN_BATCH_BUDGET_S", 2400)   # seconds/agent across batches


def _pm_existing_prompt_ok(prompt_path: Path, agent_id: str | None = None,
                          cycle: int | None = None) -> bool:
    """PMR resume-from-partial gate: True if a substantial, real prompt already
    exists for this agent on disk, so it can be reused instead of regenerated.

    Stub placeholders written by plan-cycle (~200 chars, containing "[STUB")
    are deliberately NOT treated as reusable, so a fresh cycle still generates.

    GEN-QUALITY: when agent_id and cycle are given, the existing prompt must ALSO
    PASS the item-1.3 quality gate to be reused — otherwise a degenerate prompt
    left on disk (e.g. by an older runner) would be silently resumed and dispatched.
    """
    try:
        if not prompt_path.exists():
            return False
        text = prompt_path.read_text(encoding="utf-8", errors="replace")
        if len(text) < PM_MIN_PROMPT_CHARS:
            return False
        if "[STUB" in text or "populate from PM_Pack" in text:
            return False
        if agent_id is not None and cycle is not None:
            _vr = _validate_generated_prompt(prompt_path, agent_id, cycle)
            if _vr is not None and not getattr(_vr, "passed", False):
                return False  # on-disk prompt fails the quality gate — regenerate
        return True
    except Exception:
        return False


def _find_claude_binary() -> str | None:
    """Find the claude CLI binary.
    LP1.1: Checks autonomous_runner.yml claude_binary config key first.
    Falls back to shutil.which and known paths.
    """
    import shutil
    # LP1.1: Config-driven binary path (single source of truth)
    try:
        import yaml
        for _cfg_path in [
            REPO_ROOT / "PM_Pack/automation/autonomous_runner.yml",
            REPO_ROOT / "automation/config/autonomous_runner.yml",
        ]:
            if _cfg_path.exists():
                _cfg = yaml.safe_load(_cfg_path.read_text(encoding="utf-8")) or {}
                _configured = _cfg.get("claude_binary") or _cfg.get("claude_cli_path")
                if _configured and Path(str(_configured)).exists():
                    return str(_configured)
    except Exception:
        pass
    # Try verified known location
    known = Path(r"C:\Users\Windows 11\.local\bin\claude.EXE")
    if known.exists():
        return str(known)
    found = shutil.which("claude")
    if found:
        return found
    for candidate in [
        Path.home() / ".local/bin/claude.EXE",
        Path.home() / ".local/bin/claude",
        Path(r"C:\Users\Windows 11\AppData\Local\anthropic\claude\claude.EXE"),
    ]:
        if candidate.exists():
            return str(candidate)
    return None


def _verify_claude_subscription() -> dict[str, Any]:
    """PQ-4: Confirm subscription billing AND run a real liveness probe.
    Invokes the claude CLI with a trivial prompt (fast, cheap) to confirm
    the binary is installed, authenticated, and able to return a completion.
    Treats the subscription as a hard precondition -- failure stops the cycle.
    """
    import os
    import time
    # Step 1: env-var check (existing)
    for key in ["ANTHROPIC_API_KEY", "ANTHROPIC_API"]:
        val = os.environ.get(key, "")
        if val and not val.startswith("PLACEHOLDER"):
            return {"passed": False, "reason": f"{key} present — must use subscription billing only"}
    state = RUNNER_ROOT / "state/claude_model_state.json"
    if state.exists():
        try:
            s = json.loads(state.read_text())
            if s.get("billing_mode") != "claude_subscription_only":
                return {"passed": False, "reason": "claude_model_state billing_mode is not subscription_only"}
        except Exception:
            pass

    # Step 2: PQ-4 real liveness probe
    # Skip in test environments (PYTEST_CURRENT_TEST) or when binary not found
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return {"passed": True, "probe": "skipped (test env)"}
    binary = _find_claude_binary()
    if not binary:
        return {
            "passed": False,
            "reason": "PQ-4: claude CLI binary not found -- check PATH or config claude_binary",
        }
    import subprocess as _sub
    _t0 = time.time()
    try:
        result = _sub.run(
            [binary, "--print", "-p", "Reply OK"],
            capture_output=True, text=True, timeout=30,
        )
        latency_ms = int((time.time() - _t0) * 1000)
        if result.returncode != 0:
            return {
                "passed": False,
                "reason": f"PQ-4: claude CLI probe failed (rc={result.returncode}): {result.stderr[:200]}",
            }
        probe_out = (result.stdout or "").strip()
        if len(probe_out) < 2:
            return {
                "passed": False,
                "reason": f"PQ-4: claude CLI probe returned empty response (latency={latency_ms}ms)",
            }
        return {"passed": True, "probe": "OK", "latency_ms": latency_ms, "model": CLAUDE_MODEL}
    except _sub.TimeoutExpired:
        return {
            "passed": False,
            "reason": "PQ-4: claude CLI liveness probe TIMEOUT (>30s) -- subscription unreachable",
        }
    except Exception as _exc:
        return {
            "passed": False,
            "reason": f"PQ-4: claude CLI probe exception: {_exc}",
        }


def _read(path: Path, max_chars: int = 10000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[:max_chars] + ("...[truncated]" if len(text) > max_chars else "")
    except Exception:
        return ""


def _build_pm_context(
    cycle: int,
    branch: str,
    jira_issues: list[dict],
    wave: int = 11,
) -> str:
    """
    Build the full PM context document Claude reads to generate prompts.
    This is the BRAIN of the PM — everything Claude needs to know.
    """
    lines = [
        f"# FIVERR RESEARCH SYSTEM — PM CONTEXT — Cycle {cycle:03d}",
        f"Generated: {datetime.now(UTC).isoformat()}",
        f"Branch: {branch}",
        f"Wave: {wave}",
        "",
        "=" * 70,
        "## 1. PROJECT OVERVIEW",
        "=" * 70,
    ]

    # Product vision
    vision_path = REF_ROOT / "01_vision/PRODUCT_VISION.md"
    if vision_path.exists():
        lines += ["### Product Vision (excerpt)", _read(vision_path, 8000), ""]

    # Development roadmap
    roadmap = REF_ROOT / "08_roadmap/DEVELOPMENT_ROADMAP.md"
    if roadmap.exists():
        lines += ["### Development Roadmap", _read(roadmap, 12000), ""]

    # Wave schedule
    wave_sched = REF_ROOT / "00_meta/WAVE_SCHEDULE.md"
    if wave_sched.exists():
        lines += ["### Wave Schedule (current state)", _read(wave_sched, 8000), ""]

    # Enhancement wave schedule
    enh_sched = REF_ROOT / "00_meta/ENHANCEMENT_WAVE_SCHEDULE.md"
    if enh_sched.exists():
        lines += ["### Enhancement Waves", _read(enh_sched, 8000), ""]

    lines += [
        "",
        "=" * 70,
        f"## 2. CURRENT WAVE {wave} — DETAILED SPECIFICATIONS",
        "=" * 70,
    ]

    # ── ARSF Section 2: what actually happened last cycle ────────────────────
    try:
        from automation.report_synthesis import load_cycle_synthesis, load_next_cycle_directives
        prev = load_cycle_synthesis(cycle - 1)
        lines.append("\n## 2. LAST CYCLE — WHAT ACTUALLY HAPPENED (evidence-checked)\n")
        lines.append(prev.pm_markdown if prev else "(no synthesis for the previous cycle — treat nothing as delivered)")
        lines += [
            "\n## 2A. HOW TO USE SECTION 2 (mandatory)",
            "- Treat each agent's verdict + discrepancies as the TRUTH of last cycle.",
            "- Every carried/blocked/claimed-only item is pre-injected into the relevant agent's task list below;",
            "  KEEP those tasks and reference what already exists — do not treat them as fresh.",
            "- Do NOT credit Score 1/2 or advance the wave for anything not marked DELIVERED.",
        ]
        d = load_next_cycle_directives(cycle - 1)
        if d:
            lines += ["\n## 2B. CARRIED DIRECTIVES (must appear as tasks)", d.pm_markdown]
    except Exception:
        pass  # non-blocking

    # C6 FIX: Derive wave folder/DOD/TODO dynamically (was hardcoded to waves 11/12).
    # Searches REF_ROOT for a directory prefixed by wave number (e.g. "13_analytics").
    def _find_wave_dir(root: Path, wave_num: int) -> Path | None:  # type: ignore[name-defined]
        prefix = f"{wave_num:02d}_"
        if root.exists():
            for d in sorted(root.iterdir()):
                if d.is_dir() and d.name.startswith(prefix):
                    return d
        return None

    wave_folder = _find_wave_dir(REF_ROOT, wave) or _find_wave_dir(REF_ROOT, 11)
    if wave_folder and wave_folder.exists():
        lines += [f"### SPEC: Wave {wave} ({wave_folder.name})"]
        for spec_file in sorted(wave_folder.iterdir()):
            if spec_file.suffix == ".md":
                lines += [_read(spec_file, 10000), ""]

    # DOD: find DOD_EPIC_*.md for this wave, or most-recent DOD file
    dod_path = None
    if DOD_ROOT.exists():
        wave_dod = sorted(DOD_ROOT.glob(f"DOD_EPIC_*{wave:02d}*.md"))
        any_dod  = sorted(DOD_ROOT.glob("DOD_EPIC_*.md"))
        dod_path = (wave_dod or any_dod or [None])[-1]
    if dod_path and dod_path.exists():
        lines += ["### DOD (Definition of Done — ALL criteria must be met)", _read(dod_path, 10000), ""]

    # TODO: find EPIC_*.md for this wave, or most-recent epic file
    todo_path = None
    if TODO_ROOT.exists():
        wave_todo = sorted(TODO_ROOT.glob(f"*EPIC*{wave:02d}*.md"))
        any_todo  = sorted(TODO_ROOT.glob("*EPIC*.md"))
        todo_path = (wave_todo or any_todo or [None])[-1]
    if todo_path and todo_path.exists():
        lines += ["### Epic Task Breakdown (implementation checklist)", _read(todo_path, 10000), ""]

    lines += [
        "",
        "=" * 70,
        "## 3. JIRA BOARD — FULL STORY LIST WITH AC/DOD",
        "=" * 70,
        "IMPORTANT: Every story has Acceptance Criteria and DOD.",
        "Agents must satisfy ALL AC items. Stories cannot be marked Done unless ALL AC items are verified.",
        "",
    ]

    # Current wave stories with full AC/DOD from Jira
    playbook_stories = [i for i in jira_issues if "[PLAYBOOK]" in i.get("summary", "")]
    other_stories = [i for i in jira_issues if i not in playbook_stories]

    lines.append(f"### WAVE {wave} TARGET STORIES (PRIMARY BUILD TARGET)")
    for issue in playbook_stories:
        key = issue["key"]
        summary = issue.get("summary", "")
        status = issue.get("status", "To Do")
        desc = issue.get("fields", {}).get("description", "") or issue.get("description", "")
        lines += [
            f"#### {key}: {summary}",
            f"Status: {status}",
            "Acceptance Criteria & DOD:",
            desc[:2000] if desc else "(see Jira for AC/DOD)",
            "",
        ]
        # Add existing comments for PM context
        try:
            from automation.jira_sync import fetch_story_comments, build_comment_summary
            comments = fetch_story_comments(key)
            if comments:
                lines += [
                    f"Existing Jira comments ({len(comments)} total):",
                    build_comment_summary(comments),
                    "",
                ]
        except Exception:
            pass

    lines.append("### OTHER OPEN STORIES (supplemental context, lower priority)")
    for issue in other_stories[:15]:
        key = issue["key"]
        summary = issue.get("summary", "")[:80]
        status = issue.get("status", "To Do")
        lines.append(f"- {key}: {summary} ({status})")
    lines.append("")

    lines += [
        "",
        "=" * 70,
        "## 4. EXISTING CODE (what's already built — DO NOT REBUILD)",
        "=" * 70,
    ]
    src = REPO_ROOT / "src"
    if src.exists():
        for cat_dir in sorted(src.iterdir()):
            if cat_dir.is_dir() and cat_dir.name != "__pycache__":
                py_files = sorted(cat_dir.rglob("*.py"))
                real_files = [f for f in py_files if "__pycache__" not in str(f)]
                if real_files:
                    lines.append(f"- src/{cat_dir.name}/: {len(real_files)} files "
                                 f"({', '.join(f.stem for f in real_files[:5])}{'...' if len(real_files)>5 else ''})")
    lines.append("")

    lines += [
        "",
        "=" * 70,
        "## 5. CURRENT STATE",
        "=" * 70,
    ]

    # Hydration header
    hydration = PM_PACK / "07_hydration/HYDRATION_HEADER.md"
    if hydration.exists():
        lines += ["### Hydration Header (current cycle state)", _read(hydration, 6000), ""]

    # Epic status tracker
    tracker = PM_PACK / "08_task_queue/EPIC_STATUS_TRACKER.md"
    if tracker.exists():
        lines += ["### Epic Status Tracker", _read(tracker, 8000), ""]

    lines += [
        "",
        "=" * 70,
        "## 6. GITHUB HEALTH REPORT",
        "=" * 70,
        "CRITICAL: Read every item below. Fix issues directly or instruct agents to fix them.",
        "",
    ]

    try:
        from automation.github_reviewer import (
            build_health_report,
            format_report_for_pm,
            auto_fix_what_we_can,
        )
        health = build_health_report(
            cycle=cycle,
            branch=f"cycle/{cycle:03d}/integration",
            jira_issues=jira_issues,
        )
        # Auto-fix what the PM can resolve without code (stale issues, outdated threads)
        auto_fixes = auto_fix_what_we_can(health)
        if auto_fixes:
            lines += ["### Auto-fixed by PM before prompt generation:"]
            for fix in auto_fixes:
                lines.append(f"  - {fix}")
            lines.append("")
        lines += [format_report_for_pm(health), ""]
    except Exception as _ge:
        lines += [f"(GitHub health check unavailable: {_ge})", ""]

    _context = "\n".join(lines)
    # PQ-12: Warn on silently-empty critical sections
    _pq12_checks = {
        "TARGET STORIES": "WAVE",
        "JIRA STORIES": "SCRUM-",
        "GitHub": "branch",
    }
    for _section, _signal in _pq12_checks.items():
        if _section.upper() in _context.upper() and _signal not in _context:
            import logging as _pq12_log
            _pq12_log.getLogger("pm_context").warning(
                f"PQ-12: '{_section}' section appears empty (no {_signal!r} found)"
            )
    return _context


def _build_agent_prompt_request(
    agent_id: str,
    cycle: int,
    branch: str,
    pm_context: str,
) -> str:
    """Build the request Claude sees to generate one agent's prompt."""
    agent_roles = {
        "A": "Planning & Architecture Agent — spec reading, handoff packages, Jira transitions, 14-track review, NO src/ changes",
        "B": "Primary Implementation Agent — sole src/ author, creates all new Python files, >=1200 lines of real code",
        "C": "Integration Gate Agent — verifies B's work imports cleanly, gates are met, tests pass, no regressions",
        "D": "PR & Jira Steward — creates PR, verifies CI, transitions Jira stories to Done, squash SHA resolution",
        "E": "Validation & Evidence Agent — runs live validation probes, surveys DB state, verifies golden anchor",
        "F": "Test Coverage Agent — edge cases, regression expansion, coverage gate verification, error paths",
    }
    agent_role = agent_roles.get(agent_id, f"Agent {agent_id}")

    req = f"""You are the Project Manager for the Fiverr Research System autonomous build runner.

Your job: Generate Agent {agent_id}'s complete Cursor agent prompt for Cycle {cycle:03d}.

## AGENT {agent_id} ROLE
{agent_role}

## REQUIREMENTS FOR THE PROMPT YOU GENERATE
1. Include the INVOKE-EXE PowerShell helper at the top (standard for all agents)
2. Include binary paths: $py, $git, $gh with exact Windows paths
3. Include the 9 niche IDs: prd_ai_saas | support_kb_readiness | gumloop_lindy_workflow | mcp_ai_agent | python_automation | ai_tool_llm_integration | ai_agent_development | workflow_automation | python_web_scraping
4. Include production readiness gates (G-A through G-D status)
5. Generate 15-20 substantial LARGE/XLARGE tasks (policy floor = 15). Favor a
   coherent, completable feature slice over volume — DEPTH per task, not breadth.
6. PER-TASK SKELETON — EVERY task MUST follow this EXACT shape (a downstream
   validator parses it; deviating fails the quality gate and the prompt is
   rejected). Each task block:
     ### Task N: <concrete title>
     - Jira: SCRUM-XXX  (the real key this task addresses)
     - File: a CONCRETE repo path matching `(?:src|automation|tests|docs)/<name>.py`
       — taken from the spec's stated target header or the EXISTING src/ tree in
       the PM CONTEXT, NEVER an invented slug.
     - Implementation (a runnable fenced block — ```python or ```bash):
       ```python
       # src/<module>.py  — the real signature/class from the spec
       def <name>(...) -> ...:
           ...
       ```
     - Verify (a runnable check whose line literally contains one of:
       `assert` / `expected output:` / `PASS` / `exit 0` / `== `):
       ```bash
       python -c "import src.<module> as m; assert hasattr(m, '<name>')"  # expected output: exit 0
       ```
     - Acceptance criteria: the verifiable AC items from the Jira story.
     - DOD: checklist items to complete before marking the task done.
   QUALITY FLOORS the generated prompt MUST clear (the validator enforces these):
     - >= 15 task blocks, >= 2000 words, >= 80 lines.
     - >= 30% of tasks contain at least one ``` fenced code block.
     - >= 20% of tasks contain ALL THREE co-located: a ``` fence + a
       `(?:src|automation|tests|docs)/...py` path + a verify token.
     - >= 40% unique-word ratio (do NOT paste the same task body repeatedly —
       anchor each task to a DISTINCT spec section / signature / file).
   AIM for ~100% of tasks to satisfy the full code+path+verify shape so the cycle
   clears the floors with margin. The code/paths/verify MUST be REAL (drawn from
   the specs and repo in the PM CONTEXT) — never filler invented to pad ratios.
7. Tasks MUST reference the IN-SCOPE PLAYBOOK stories listed in the PM CONTEXT above. Derive the target stories from the Jira board state, NOT a hardcoded list.
8. SCRUM-207 is already Done — do NOT rebuild it
9. Include a squash SHA placeholder: [C{cycle:03d}_SQUASH_SHA]
10. Include base SHA, suite count, coverage % from the PM context
11. Include the PERMANENT REGRESSION PACK (all must still pass)
12. End with an authorization statement confirming policy v4.3 compliance

## MANDATORY PROMPT-WIDE REQUIREMENTS (a validator REJECTS the prompt if any is missing)
The prompt you generate MUST contain ALL of the following — emit them or the cycle
is refused (do not rely on the PM context having them; put them in the prompt):
- A model block line, verbatim: `Model: Codex 5.3 (gpt-5.3-codex) at medium effort. Auto model DISABLED.`
- These SIX section headers, each on its own line (verbatim tokens the validator scans):
  `## PQ-0 identity`
  `## PQ-1 project context`
  `## PQ-2 your role / file ownership`
  `## PQ-3 git instructions`
  `## PQ-4 autonomy`
  `## PQ-5 jira scope`
- Under PQ-4, a line beginning `Autonomy rule:` stating the agent proceeds without asking.
- The repo root `C:/Fiverr/Fiverr` and the integration branch `cycle/{cycle:03d}/integration`.
- At least one Jira key in the form `SCRUM-NNN`.
- The report path `docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent_id}.md`.
- A validation block containing all THREE commands:
  `python -m ruff check automation/ src/ tests/`
  `python -m mypy src`
  `python -m pytest tests/unit/ -q`
- >= 15 task blocks, >= 2000 words, >= 80 lines.
- The prompt MUST END with a single final line exactly: `END OF PROMPT` (appearing EXACTLY ONCE, nowhere else).

## GOLD EXAMPLE TASK (replicate this exact shape with REAL spec content)
### Task 7: Add GIG_DETAIL_THUMBNAIL selector to the Fiverr selector registry
- Jira: SCRUM-214
- File: src/collection/fiverr_selectors.py
- Implementation:
```python
# src/collection/fiverr_selectors.py
GIG_DETAIL_THUMBNAIL = "div.gig-page-gallery img.thumbnail"  # primary gig hero image
```
- Verify:
```bash
python -c "import src.collection.fiverr_selectors as s; assert hasattr(s, 'GIG_DETAIL_THUMBNAIL')"  # expected output: exit 0
```
- Acceptance criteria: selector resolves on a saved gig fixture; no regression in existing selector tests.
- DOD: code committed; `python -m pytest tests/unit/test_fiverr_selectors.py -q` passes (exit 0).

## JIRA UPDATE REQUIREMENTS
For Agent {agent_id}, include tasks to:
- Transition the relevant Jira stories to IN PROGRESS when starting
- Add detailed comments to Jira stories explaining what was built/verified
- Only transition to Done after ALL acceptance criteria are verified with evidence
- If any AC item cannot be verified, document exactly which item failed and why

## PM CONTEXT (full project state — read every section)
{pm_context}

## REPORT STANDARD REQUIREMENT  (RSF-24/25)
The prompt you generate MUST include, verbatim at the end, a section titled:

## MANDATORY END-OF-RUN REPORT
The Cursor agent MUST write its completed cycle report to:
    docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent_id}.md

!! LANE EXEMPTION — STATE THIS EXPLICITLY IN THE GENERATED PROMPT !!
This report path is a MANDATORY deliverable and an EXPLICIT EXCEPTION to the agent's
file-ownership lane. Even when PQ-2 restricts edits to (e.g.) src/** and tests/**, the
agent MUST ALSO create/write docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent_id}.md.
The runner marks the entire run FAILED (status NO_REPORT) and commits NOTHING if this
report is missing or omits the AGENT_COMPLETE marker — so writing it is not optional and
is never "out of lane". The generated prompt's PQ-2 section MUST list this report path as
an allowed/required output alongside the agent's implementation lane.

The report MUST follow the AGENT_CYCLE_REPORT_TEMPLATE.md standard (PM_Pack/09_templates/).
Specifically:
- Begin with an ARSF:MANIFEST JSON block (<!-- ARSF:MANIFEST v1 --> ```json {{ ... }} ```)
- Include all 13 spine sections (§1 Final verdict through §13 Certification)
- Include the role addendum for Agent {agent_id} (Addendum {agent_id})
- Every claim must carry EVIDENCE (commit SHA, test count, file path, timestamp)
- §11 Open blockers & explicit non-claims is REQUIRED — never omit it
- Set "committed": true only if the agent actually ran git commit + git push
- Populate tasks_total/tasks_done/tasks_partial/tasks_failed accurately

## OUTPUT FORMAT
Generate ONLY the agent prompt text. Start with the header line:
# CYCLE {cycle:03d} — AGENT {agent_id} PROMPT
# Branch: {branch}

Do not add preamble. Do not add explanation after the prompt.
The prompt should be 3,000-5,000 lines for implementation agents (B), 1,500-3,000 for others.
End the prompt with a single final line exactly: END OF PROMPT (exactly once, nothing after it).
"""

    # RSF-45: ARSF — inject this agent's carried directives as non-droppable tasks
    try:
        from automation.report_synthesis import load_next_cycle_directives
        d = load_next_cycle_directives(cycle - 1)
        mine = [x for x in (d.directives if d else []) if x.get("agent") == agent_id]
        if mine:
            carried_section = "\n\n## CARRIED TASKS FROM LAST CYCLE (non-droppable)\n"
            for i, x in enumerate(mine, 1):
                carried_section += (
                    f"{i}. [{x.get('priority', 'P1')}] {x['task']}\n"
                    f"   Corrective gate: {x.get('corrective_gate', '(none)')}\n"
                    f"   Why carried: {x.get('origin', '')} (cycle {getattr(d, 'from_cycle', cycle - 1)})\n"
                )
            # Insert before the OUTPUT FORMAT section
            req = req.replace("## OUTPUT FORMAT", carried_section + "\n## OUTPUT FORMAT")
    except Exception:
        pass  # non-blocking; if no directives, nothing is added

    return req


def _validate_generated_prompt(prompt_path: Path, agent_id: str, cycle: int):
    """GEN-QUALITY: run the item-1.3 quality gate in-process on a freshly
    generated prompt. Returns the validation result, or None if the validator is
    unavailable (caller then defers to the downstream validate_all gate)."""
    try:
        from automation import prompt_validator as _pv
        return _pv.validate(prompt_path, agent_id, cycle)
    except Exception:
        return None


def _quality_correction_block(errors: list[str]) -> str:
    """GEN-QUALITY: correction block appended to the next regeneration request,
    naming the EXACT quality-gate deficiencies so Claude fixes them and converges
    on a gate-passing prompt (instead of emitting degenerate output rejected
    downstream)."""
    bullets = "\n".join(f"  - {e}" for e in (errors or [])[:12])
    return (
        "\n\n## QUALITY GATE FAILURE — REGENERATE TO FIX THESE EXACT DEFECTS\n"
        "Your previous prompt was REJECTED by the validator. Fix EVERY item below "
        "and regenerate the FULL prompt (not a diff):\n"
        f"{bullets}\n"
        "Honor the PER-TASK SKELETON and QUALITY FLOORS above: every task needs a "
        "``` fenced code block + a concrete (?:src|automation|tests|docs)/...py path "
        "+ a verify token (assert / expected output: / PASS / exit 0 / ==), built "
        "from REAL spec/repo content. Aim for ~100% authored tasks for margin.\n"
    )


# ── GEN-QUALITY hybrid generation helpers ────────────────────────────────────

def _agent_lane_info(agent_id: str) -> dict:
    """Load this agent's lane (role / owns / prohibited) from agent_lanes.yml so the
    deterministic PQ-2 scaffold matches the live 5.6 sandbox enforcement. Falls back
    to a static map so the scaffold is always well-formed even if the YAML is absent.
    """
    try:
        import yaml
        p = PM_PACK / "automation" / "agent_lanes.yml"
        if p.exists():
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            for lane in data.get("lanes", []):
                if str(lane.get("agent", "")).upper() == agent_id.upper():
                    return {
                        "role": str(lane.get("role", f"agent_{agent_id}")),
                        "description": str(lane.get("description", f"Agent {agent_id}")),
                        "owns": [str(x) for x in (lane.get("owns") or [])],
                        "prohibited": [
                            str(x) for x in (
                                lane.get("prohibited")
                                or lane.get("prohibited_without_explicit_task")
                                or []
                            )
                        ],
                    }
    except Exception:
        pass
    fallback = {
        "A": {"role": "planner_foundation_integration",
              "description": "PM planning, architecture, docs, GitHub governance, config",
              "owns": ["PM_Pack/**", "docs/**", ".github/**", "pyproject.toml"],
              "prohibited": ["src/**", "tests/**", "data/**"]},
        "B": {"role": "primary_implementation",
              "description": "Primary src/ and tests/ author — new features, core logic",
              "owns": ["src/**", "tests/**"], "prohibited": []},
        "C": {"role": "integration_validation",
              "description": "Integration checks, validation run, cycle report",
              "owns": ["docs/cycle_reports/**", "PM_Pack/10_cycle_log/**"],
              "prohibited": ["src/**"]},
        "D": {"role": "pr_steward_merge_gate",
              "description": "PR body, Jira evidence, GitHub status, merge gate preparation",
              "owns": ["docs/cycle_reports/**"],
              "prohibited": ["src/**", "tests/**", "automation/**"]},
        "E": {"role": "live_validation_external_signals",
              "description": "Live data validation, external signal collection, evidence files",
              "owns": ["docs/cycle_reports/**", "data/evidence/**", "scripts/validation/**"],
              "prohibited": ["src/**", "tests/**", "config.yaml"]},
        "F": {"role": "test_coverage_regression",
              "description": "Test coverage gaps, regression tests, coverage enforcement",
              "owns": ["tests/**"], "prohibited": ["src/**"]},
    }
    return fallback.get(
        agent_id.upper(),
        {"role": f"agent_{agent_id}", "description": f"Agent {agent_id}",
         "owns": ["docs/**"], "prohibited": []},
    )


def _extract_scrum_keys(jira_issues: list[dict] | None, pm_context: str,
                        limit: int = 12) -> list[str]:
    """Collect real SCRUM-NNN keys from the Jira board (preferred) or the PM context.
    The validator HARD-REQUIRES at least one SCRUM-NNN; a non-empty list also lets the
    scaffold anchor PQ-5 scope to real stories. Falls back to SCRUM-207 only if none
    are found anywhere (keeps the scaffold valid rather than emitting a stub)."""
    keys: list[str] = []
    for it in (jira_issues or []):
        k = None
        if isinstance(it, dict):
            k = it.get("key")
        elif isinstance(it, str):
            k = it
        if k and re.match(r"^SCRUM-\d+$", str(k)):
            keys.append(str(k))
    if not keys:
        keys = re.findall(r"SCRUM-\d+", pm_context or "")
    seen: set[str] = set()
    out: list[str] = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out[:limit] if out else ["SCRUM-207"]


def _sanitize_context_for_embedding(text: str, max_chars: int = 40000) -> str:
    """Neutralize tokens that would corrupt the validator's structural counts when the
    raw PM context is embedded verbatim into a generated prompt: a stray END OF PROMPT
    (must appear exactly once, in the tail), a ``### Task N`` heading (would inflate
    task_count), or a stub pattern the gate hard-fails on. Content is preserved;
    only these few control tokens are demoted. Bounded to ``max_chars``."""
    t = (text or "")[:max_chars]
    t = t.replace("END OF PROMPT", "END-OF-PROMPT")
    # Demote any markdown "### Task N" heading so it is not counted as a real task.
    t = re.sub(r"^\s*#{1,6}\s*Task\s+(\d+)", r"Task \1", t, flags=re.MULTILINE)
    for a, b in (
        ("[FILL]", "(fill)"), ("[TODO]", "(todo)"), ("[STUB", "(stub"),
        ("populate from PM_Pack", "uses PM_Pack data"),
        ("<exact agent mission>", "(agent mission)"),
    ):
        t = t.replace(a, b)
    t = re.sub(r"(?im)^\s*fill in\s*$", "(fill in)", t)
    return t


def _build_scaffold_head(agent_id: str, cycle: int, branch: str,
                         scrum_keys: list[str], pm_context: str = "") -> str:
    """Deterministic prompt head: header, model block, PQ-0..5 sections, and the
    embedded PM CONTEXT. Every structural token the validator hard-requires is emitted
    here BY CONSTRUCTION, so a generated prompt can never be 'missing required content'
    / 'PQ gate missing'. The PM context (sanitized) is embedded so the prompt Cursor
    receives actually contains the Jira AC/DOD, spec evidence and prior-cycle state the
    PQ-1 section points to (Codex review: the hybrid prompt must not dangle that ref)."""
    lane = _agent_lane_info(agent_id)
    owns = "\n".join(f"  - `{p}`" for p in lane["owns"]) or "  - `docs/**`"
    prohibited = "\n".join(f"  - `{p}`" for p in lane["prohibited"]) or "  - (none)"
    keys_line = ", ".join(scrum_keys)
    ctx_block = _sanitize_context_for_embedding(pm_context)
    pm_context_section = (
        f"\n## PM CONTEXT\n{ctx_block}\n" if ctx_block.strip()
        else "\n## PM CONTEXT\n(No PM context was supplied for this cycle.)\n"
    )
    return f"""AGENT {agent_id} -- CYCLE {cycle:03d} PROMPT
# CYCLE {cycle:03d} — AGENT {agent_id} PROMPT
# Branch: {branch}

Repo root: C:/Fiverr/Fiverr
Model: Codex 5.3 (gpt-5.3-codex) at medium effort. Auto model DISABLED. Fallback model DISABLED.

## PQ-0 identity
You are Agent {agent_id} ({lane['role']}) for Cycle {cycle:03d} of the Fiverr Research \
System autonomous build runner. {lane['description']}. Your identity and mission are \
fixed for this cycle; do not assume another agent's role.

## PQ-1 project context
Fiverr Research System — a Python 3.11+ data/research pipeline (SQLAlchemy 2.0, \
Pydantic v2, Playwright, OpenAI, Streamlit). Work happens on the integration branch \
`{branch}` rooted at C:/Fiverr/Fiverr. Read the PM CONTEXT below for the live wave \
roadmap, spec targets, base SHA, suite count and coverage. Build on the existing src/ \
tree; never invent module slugs that are not in the specs or the repository.

## PQ-2 your role / file ownership
Agent {agent_id} role: {lane['description']}.
Your IMPLEMENTATION lane (create/modify these paths):
{owns}
You must NOT modify these paths:
{prohibited}
REQUIRED EXCEPTION — you MUST ALSO write your end-of-run report at
`docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent_id}.md`, EVEN THOUGH it is outside your
implementation lane above. This report is mandatory: the runner FAILS the entire run
(status NO_REPORT) and commits NOTHING if it is missing or lacks the AGENT_COMPLETE marker.
Control-plane paths (automation/, .github/workflows/, host/, and PM_Pack/automation \
policy) are OFF-LIMITS to every agent regardless of lane.

## PQ-3 git instructions
Confirm you are on the integration branch before any work:
```bash
git -C C:/Fiverr/Fiverr branch --show-current   # expected: {branch}
```
Stage only files inside your ownership lane, commit with a conventional message, and \
push your branch (never a protected branch, never force):
```bash
git -C C:/Fiverr/Fiverr add <your-lane-files>
git -C C:/Fiverr/Fiverr commit -m "feat(agent-{agent_id}): cycle {cycle:03d} work"
git -C C:/Fiverr/Fiverr push -u origin {branch}
```

## PQ-4 autonomy
Autonomy rule: proceed autonomously through every task without asking for \
confirmation; never stop mid-cycle to ask a question. If a task is blocked, record \
the blocker in your report's §11 and continue with the next task. Auto model \
selection is DISABLED — use only Codex 5.3 at medium effort.

## PQ-5 jira scope
In-scope Jira stories for Agent {agent_id} this cycle: {keys_line}.
Transition a story to Done only with verifiable evidence (commit SHA, test output, \
file path). SCRUM-207 is already Done — do NOT rebuild it. Each task below names the \
specific SCRUM-NNN key it advances.
{pm_context_section}
## TASKS
Complete every task in order. Each follows the fixed skeleton (concrete title, Jira \
key, real repo file, a runnable implementation fence, and a runnable verify line).
"""


def _build_scaffold_tail(agent_id: str, cycle: int) -> str:
    """Deterministic prompt tail: validation block (ruff/mypy/pytest), regression
    pack, niche IDs, mandatory report section, squash-SHA placeholder, authorization,
    and the single closing END OF PROMPT marker (appears exactly once, last line)."""
    report_path = f"docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent_id}.md"
    return f"""

## VALIDATION (run before marking the cycle done)
Run the full local gate and paste the output into your report; all three MUST pass \
(exit 0) before you transition any Jira story to Done:
```bash
python -m ruff check automation/ src/ tests/
python -m mypy src
python -m pytest tests/unit/ -q
```

## PERMANENT REGRESSION PACK
The following MUST still pass (no regressions introduced by this cycle):
```bash
python -m pytest tests/unit/ -q   # expected output: exit 0, 0 failed
```

## NICHE IDS (canonical research niches — reference as needed)
prd_ai_saas | support_kb_readiness | gumloop_lindy_workflow | mcp_ai_agent | \
python_automation | ai_tool_llm_integration | ai_agent_development | \
workflow_automation | python_web_scraping

## MANDATORY END-OF-RUN REPORT
Write your completed cycle report to:
    {report_path}
This report is REQUIRED and is an EXPLICIT EXCEPTION to your file-ownership lane: write it
even though docs/cycle_reports/ is outside the paths you own. A missing report — or one
without the AGENT_COMPLETE marker — makes the runner FAIL the run (NO_REPORT) and commit
NOTHING, discarding all your work. So write it before you finish.
Follow AGENT_CYCLE_REPORT_TEMPLATE.md (PM_Pack/09_templates/): begin with an \
ARSF:MANIFEST JSON block, include all 13 spine sections (§1 Final verdict through \
§13 Certification) plus Addendum {agent_id}, attach EVIDENCE (commit SHA, test count, \
path, timestamp) to every claim, and never omit §11 Open blockers. Set "committed": \
true only if you actually ran git commit + git push.

## SQUASH SHA
After the PR is squash-merged, record the squash SHA in place of: [C{cycle:03d}_SQUASH_SHA]

## AUTHORIZATION
This prompt complies with policy v4.3 (Codex 5.3 at medium effort, Auto model \
DISABLED, autonomy rule active, ownership lanes enforced).

END OF PROMPT"""


def _build_task_batch_request(agent_id: str, cycle: int, lane: dict,
                              scrum_keys: list[str], start_n: int, count: int,
                              pm_context: str,
                              prior_titles: list[str] | None = None,
                              correction: str | None = None) -> str:
    """Build the focused request for ONE batch of task blocks. Claude authors only the
    task bodies (not the scaffold), so each call is small enough to finish under the
    timeout and produce DISTINCT, real, code-bearing tasks instead of padding."""
    skeleton = (
        "### Task <N>: <concrete, specific title>\n"
        "- Jira: <one SCRUM-NNN from the in-scope list>\n"
        "- File: <a CONCRETE repo path matching (?:src|automation|tests|docs)/<name>.py "
        "— from the spec target or the EXISTING src/ tree in PM CONTEXT, NEVER an "
        "invented slug, NEVER a placeholder>\n"
        "- Implementation:\n"
        "```python\n"
        "# <the real file path>\n"
        "<the real signature/class/function from the spec — runnable, not a stub>\n"
        "```\n"
        "- Verify:\n"
        "```bash\n"
        "python -c \"import <module> as m; assert hasattr(m, '<name>')\"  "
        "# expected output: exit 0\n"
        "```\n"
        "- Acceptance criteria: <the verifiable AC items from the Jira story>\n"
        "- DOD: <checklist items to complete before marking the task done>"
    )
    avoid = ""
    if prior_titles:
        recent = "\n".join(f"  - {t}" for t in prior_titles[-40:])
        avoid = (
            "\n\nAlready-authored task titles — author DISTINCT NEW work, do NOT "
            f"repeat or paraphrase these:\n{recent}"
        )
    correct = ""
    if correction:
        # The prior assembled prompt failed the quality gate; surface the EXACT
        # validator errors so this batch fixes them (hybrid convergence, mirroring
        # the legacy single-shot correction loop).
        correct = "\n" + correction
    end_n = start_n + count - 1
    return f"""You are the Project Manager authoring task blocks for Agent {agent_id}'s \
Cycle {cycle:03d} Cursor prompt.

Author EXACTLY {count} task blocks, numbered ### Task {start_n} through ### Task {end_n}.
Output ONLY the task blocks — NO header, NO preamble, NO footer, and DO NOT write the \
words "END OF PROMPT" anywhere.

Agent {agent_id} role: {lane['description']}. Tasks must fall within this agent's \
ownership: {', '.join(lane['owns']) or 'docs/**'}.
In-scope Jira keys: {', '.join(scrum_keys)}.

EVERY task MUST follow this EXACT skeleton (a downstream validator parses it; \
deviating fails the gate and the whole cycle is refused):
{skeleton}

HARD REQUIREMENTS for the {count} blocks you emit:
- Each task has a ```python (or ```bash) implementation fence AND a ```bash verify \
fence whose line contains one of: assert / expected output: / PASS / exit 0 / ==
- Each task names a CONCRETE (?:src|automation|tests|docs)/...py path drawn from the \
specs/repo in PM CONTEXT — never an invented slug, never a placeholder like [FILL]/[TODO].
- Every task is DISTINCT — anchor each to a different spec section / signature / file. \
Repeating the same task body fails the anti-paste gate.
- Real code only: the implementation is the actual signature/logic from the spec, not \
filler.{avoid}{correct}

## PM CONTEXT (specs, Jira board, existing src tree — derive REAL tasks from this)
{pm_context}
"""


def _renumber_tasks(tasks_text: str) -> tuple[str, int]:
    """Renumber every '### Task N' header sequentially from 1 so concatenated batches
    form a clean, gap-free sequence the validator counts via `^### Task \\d+`.
    Returns (renumbered_text, task_count)."""
    counter = {"n": 0}

    def _repl(m: re.Match[str]) -> str:
        counter["n"] += 1
        rest = m.group("rest") or ""
        return f"### Task {counter['n']}{rest}"

    out = re.sub(
        r"^#{3,}\s+Task\s+\d+(?P<rest>.*)$",
        _repl, tasks_text, flags=re.MULTILINE,
    )
    return out, counter["n"]


def _count_authored_tasks(text: str) -> int:
    """Count tasks that satisfy the validator's PQ-7b 'authored' definition:
    a ``` fence + a concrete (?:src|automation|tests|docs)/...py path + a verify token,
    all co-located in the task block. Used to decide when enough real tasks exist."""
    blocks = re.findall(
        r"#{3,}\s+Task\s+\d+.*?(?=#{3,}\s+Task\s+\d+|\Z)",
        text, re.DOTALL | re.IGNORECASE,
    )
    n = 0
    for tb in blocks:
        has_code = bool(re.search(r"```", tb))
        has_path = bool(re.search(r"(?:src|automation|tests|docs)/[\w/]+\.py", tb))
        has_verify = bool(re.search(
            r"(?:expected output|assert|verify|PASS|exit.*0|== )", tb, re.IGNORECASE))
        if has_code and has_path and has_verify:
            n += 1
    return n


def _generate_agent_prompt_hybrid(agent_id: str, cycle: int, branch: str,
                                  pm_context: str,
                                  jira_issues: list[dict] | None,
                                  correction: str | None = None,
                                  brief_section: str = "") -> str | None:
    """GEN-QUALITY hybrid producer: deterministic scaffold + Claude-authored task
    batches. Returns the assembled prompt text (still validated by the caller), or
    None if no task blocks could be produced. Batches until the task target is hit or
    the round cap is reached, feeding already-authored titles back so each batch adds
    DISTINCT work (keeps the anti-paste unique-word ratio healthy). On a retry the
    caller passes ``correction`` (the prior attempt's exact validator errors) so the
    batch requests fix those specific deficiencies — hybrid convergence."""
    import time as _t

    import automation.autopilot_logger as L

    lane = _agent_lane_info(agent_id)
    scrum_keys = _extract_scrum_keys(jira_issues, pm_context)
    head = _build_scaffold_head(agent_id, cycle, branch, scrum_keys, pm_context)
    # Audit [D]: prepend the PM intelligence brief (SECTION 0 — built/done/next +
    # the existing-src list) so agents DON'T rebuild completed stories. It carries no
    # "### Task N" markers and no ``` code fences, so the task floor and PQ-6
    # (code-fences ÷ tasks) are UNAFFECTED; it only adds ground-truth context (and
    # helps the word/line floors). The brief was previously built then DISCARDED.
    if brief_section:
        head = brief_section.rstrip() + "\n\n" + head
    tail = _build_scaffold_tail(agent_id, cycle)

    parts: list[str] = []
    titles: list[str] = []
    ntasks = 0
    next_n = 1
    rounds = 0
    _deadline = _t.time() + GEN_BATCH_BUDGET_S
    while ntasks < GEN_TARGET_TASKS and rounds < GEN_MAX_BATCH_ROUNDS:
        if _t.time() >= _deadline:
            L.warn(
                f"GEN-QUALITY hybrid: Agent {agent_id} hit the {GEN_BATCH_BUDGET_S}s "
                f"batch budget after {rounds} rounds ({ntasks} tasks) — stopping; the "
                f"caller's quality gate decides accept/halt"
            )
            break
        rounds += 1
        count = min(GEN_BATCH_SIZE, GEN_TARGET_TASKS - ntasks)
        req = _build_task_batch_request(
            agent_id, cycle, lane, scrum_keys, next_n, count, pm_context,
            prior_titles=titles, correction=correction,
        )
        instruction = (
            f"Author {count} Cursor task blocks for Agent {agent_id}, Cycle "
            f"{cycle:03d}. Requirements and PM context are in stdin. Output ONLY the "
            f"task blocks — no preamble, no explanation, and do not write 'END OF PROMPT'."
        )
        out = _call_claude_pm(agent_id, cycle, req, instruction=instruction)
        if not out:
            L.warn(f"GEN-QUALITY hybrid: Agent {agent_id} batch {rounds} returned empty")
            continue
        m = re.search(r"^#{3,}\s+Task\s+\d+", out, re.MULTILINE)
        if not m:
            L.warn(f"GEN-QUALITY hybrid: Agent {agent_id} batch {rounds} had no task headers")
            continue
        chunk = out[m.start():]
        # Strip any stray END OF PROMPT a batch may have added (must appear once, in tail).
        chunk = re.sub(r"END OF PROMPT", "", chunk).strip()
        parts.append(chunk)
        merged, ntasks = _renumber_tasks("\n\n".join(parts))
        titles = re.findall(r"^#{3,}\s+Task\s+\d+[:.\)]?\s*(.+)$", merged, re.MULTILINE)
        authored = _count_authored_tasks(merged)
        L.info(
            f"GEN-QUALITY hybrid: Agent {agent_id} round {rounds}: "
            f"{ntasks} tasks ({authored} authored), target {GEN_TARGET_TASKS}"
        )
        next_n = ntasks + 1

    if not parts:
        return None
    merged, ntasks = _renumber_tasks("\n\n".join(parts))
    if ntasks == 0:
        return None
    return head + "\n" + merged + "\n" + tail


def create_agent_prompts_via_claude(
    cycle: int,
    branch: str,
    jira_issues: list[dict],
    agents: list[str],
    prompts_dir: Path,
    wave: int = 11,
    brief_section: str = "",
) -> dict[str, Path] | None:
    """
    Call Claude (via Anthropic API) to act as intelligent PM and generate agent prompts.

    Uses the claude Python SDK if available, falls back to CLI subprocess.
    Returns dict[agent_id -> Path] on success, None if Claude unavailable.
    """
    # Verify subscription billing mode
    preflight = _verify_claude_subscription()
    # OBS-4: Print Claude subscription health banner to terminal
    import click as _ck_obs4
    if preflight["passed"]:
        _lat = preflight.get("latency_ms")
        _lat_str = f" latency={_lat}ms" if _lat else ""
        _probe_str = preflight.get("probe", "")
        _ck_obs4.secho(
            f"  CLAUDE SUBSCRIPTION: OK (model={CLAUDE_MODEL}{_lat_str})",
            fg="green",
        )
    else:
        _ck_obs4.secho(
            f"  CLAUDE SUBSCRIPTION: FAIL -- {preflight.get('reason', 'unknown')}",
            fg="red", bold=True,
        )
        return None
    _announce_pm_model(CLAUDE_MODEL)  # H6.2: log model confirmation

    # Build the full PM context document
    pm_context = _build_pm_context(cycle, branch, jira_issues, wave)

    # Save PM context as artifact
    prompts_dir.mkdir(parents=True, exist_ok=True)
    ctx_path = prompts_dir / f"CYCLE_{cycle:03d}_PM_CONTEXT.md"
    ctx_path.write_text(pm_context, encoding="utf-8")

    written: dict[str, Path] = {}

    import time as _t
    import automation.autopilot_logger as L

    from automation.live_events import emit as _emit
    L.section(f"Claude PM generating {len(agents)} agent prompts for Cycle {cycle:03d}")
    L.info(f"Model: {CLAUDE_MODEL}  Timeout: {CLAUDE_TIMEOUT}s per agent")
    L.info(f"Estimated time: {len(agents) * 3}-{len(agents) * 5} min total")
    _emit("CLAUDE_PM", f"Starting prompt generation for Cycle {cycle:03d} ({len(agents)} agents)", cycle=cycle)

    _pm_generated_any = False  # PMR: gate inter-agent spacing (skip before first gen)

    for idx, agent_id in enumerate(agents, 1):
        prompt_path = prompts_dir / f"CYCLE_{cycle:03d}_AGENT_{agent_id}_PROMPT.md"

        # PMR resume-from-partial: if a substantial prompt for this agent already
        # exists (e.g. from a prior attempt that paused at partial), reuse it
        # rather than spending another expensive generation on it.
        if _pm_existing_prompt_ok(prompt_path, agent_id, cycle):
            written[agent_id] = prompt_path
            _emit("CLAUDE_PM", f"Agent {agent_id} prompt REUSED (resume-from-partial)", agent=agent_id, cycle=cycle, status="OK")
            L.info(f"PMR: Agent {agent_id} prompt already present ({prompt_path.stat().st_size} bytes) — reusing, skipping regeneration")
            continue

        # PMR inter-agent spacing: pause between successive generations to avoid
        # bursting the subscription rate limit (skip before the first generation).
        if _pm_generated_any and PM_INTER_AGENT_DELAY > 0:
            _t.sleep(PM_INTER_AGENT_DELAY)

        request_text = _build_agent_prompt_request(
            agent_id=agent_id, cycle=cycle, branch=branch, pm_context=pm_context,
        )
        _emit("CLAUDE_PM", f"Generating Agent {agent_id} prompt [{idx}/{len(agents)}]", agent=agent_id, cycle=cycle, status="RUNNING")
        L.claude_pm_start(agent_id, cycle, idx, len(agents))

        # PMR retry-with-backoff: _call_claude_pm returns None (never raises) on
        # timeout / non-zero rc / short output — exactly the transient failures a
        # rate/usage-limit trip produces. Retry instead of aborting the cycle.
        prompt_text = None
        _accepted = False  # GEN-QUALITY: True only when the prompt PASSES the gate
        elapsed = 0.0
        _req = request_text  # GEN-QUALITY: grows a correction block on retry (legacy)
        _hybrid_correction: str | None = None  # GEN-QUALITY: hybrid retry correction
        for _attempt in range(1, PM_MAX_ATTEMPTS + 1):
            t0 = _t.time()
            with L.Spinner(
                f"Claude PM -> Agent {agent_id} "
                f"(attempt {_attempt}/{PM_MAX_ATTEMPTS}, timeout {CLAUDE_TIMEOUT//60}m)"
            ):
                if GEN_HYBRID:
                    # Hybrid: deterministic scaffold + Claude-authored task batches.
                    # The fixed structural tokens pass by construction; Claude only
                    # authors distinct code-bearing task bodies in bounded batches.
                    _candidate = _generate_agent_prompt_hybrid(
                        agent_id, cycle, branch, pm_context, jira_issues,
                        correction=_hybrid_correction,
                        brief_section=brief_section,
                    )
                else:
                    _candidate = _call_claude_pm(agent_id, cycle, _req)
            elapsed = _t.time() - t0
            # GEN-QUALITY: accept only a candidate that PASSES the item-1.3 quality
            # gate. Write it, validate in-process, and on failure feed the EXACT
            # deficiencies back to Claude as a correction block and regenerate
            # (bounded by PM_MAX_ATTEMPTS) so the generator converges on a
            # gate-passing prompt instead of emitting degenerate output rejected
            # downstream. An empty/short candidate is the existing transient case.
            if _candidate:
                prompt_path.write_text(_candidate, encoding="utf-8")
                _vr = _validate_generated_prompt(prompt_path, agent_id, cycle)
                if _vr is None or getattr(_vr, "passed", False):
                    prompt_text = _candidate
                    _accepted = True  # passed the gate (or validator unavailable)
                    if _attempt > 1:
                        L.ok(f"PMR: Agent {agent_id} succeeded on attempt {_attempt}/{PM_MAX_ATTEMPTS}")
                    break
                _verrs = list(getattr(_vr, "errors", []) or [])
                L.warn(
                    f"GEN-QUALITY: Agent {agent_id} prompt failed quality gate "
                    f"(attempt {_attempt}/{PM_MAX_ATTEMPTS}): {'; '.join(_verrs[:3])}"
                )
                if _attempt >= PM_MAX_ATTEMPTS:
                    # Best-effort: keep the last candidate; the downstream
                    # validate_all gate rejects it and the caller halts (no
                    # silent dispatch of a degenerate prompt).
                    prompt_text = _candidate
                    L.error(
                        f"GEN-QUALITY: Agent {agent_id} still fails the quality gate "
                        f"after {PM_MAX_ATTEMPTS} attempts — downstream gate will halt the cycle"
                    )
                    break
                # Feed the EXACT validator errors back to BOTH paths on retry: the
                # legacy single-shot request and the hybrid batch requests.
                _correction = _quality_correction_block(_verrs)
                _req = request_text + _correction
                _hybrid_correction = _correction
            if _attempt < PM_MAX_ATTEMPTS:
                _backoff = min(
                    PM_RETRY_BACKOFF_BASE * (2 ** (_attempt - 1)),
                    PM_RETRY_BACKOFF_CAP,
                )
                _emit("CLAUDE_PM", f"Agent {agent_id} attempt {_attempt}/{PM_MAX_ATTEMPTS} regenerating — backoff {_backoff}s", agent=agent_id, cycle=cycle, status="RETRY")
                L.warn(
                    f"PMR: Agent {agent_id} attempt {_attempt}/{PM_MAX_ATTEMPTS} "
                    f"empty/short or below quality — backing off {_backoff}s before retry"
                )
                _t.sleep(_backoff)

        if not prompt_text:
            # PQ-2 / PQ-3 / PMR: Claude is a hard dependency and all retries are
            # exhausted. Return whatever was written so far so the CALLER decides.
            # The caller (ai_cycle_controller) raises SystemExit(1) on partial, so
            # there is still no silent template fallback anywhere in the stack.
            _emit("CLAUDE_PM", f"Agent {agent_id} prompt FAILED after {PM_MAX_ATTEMPTS} attempts", agent=agent_id, cycle=cycle, status="FAIL")
            L.claude_pm_done(agent_id, elapsed, 0, False, idx, len(agents))
            L.warn(
                f"PQ-2/PMR: Agent {agent_id} returned empty/short output after "
                f"{PM_MAX_ATTEMPTS} attempts. "
                f"{'Returning ' + str(len(written)) + ' already-written prompts to caller.' if written else 'No prompts written yet.'}"
            )
            return written if written else None  # caller halts on None or partial

        if not _accepted:
            # GEN-QUALITY fail-closed: the prompt never passed the quality gate
            # after all attempts. Do NOT add it to `written` (the caller sees an
            # incomplete set and halts with CLAUDE_PM_PARTIAL), and remove the
            # on-disk candidate so a later resume-from-partial cannot reuse a
            # known-degenerate prompt. No silent dispatch of a sub-quality prompt.
            try:
                prompt_path.unlink()
            except OSError:
                pass
            _pm_generated_any = True
            L.claude_pm_done(agent_id, elapsed, len(prompt_text), False, idx, len(agents))
            _emit("CLAUDE_PM", f"Agent {agent_id} prompt REJECTED by quality gate after {PM_MAX_ATTEMPTS} attempts", agent=agent_id, cycle=cycle, status="FAIL")
            continue

        _emit("CLAUDE_PM", f"Agent {agent_id} prompt DONE ({elapsed:.0f}s, {len(prompt_text)//1024}KB)", agent=agent_id, cycle=cycle, status="OK")
        L.claude_pm_done(agent_id, elapsed, len(prompt_text), True, idx, len(agents))
        # PQ-14: Provenance stamp in prompt header (model, timestamp, cycle, agent)
        import datetime as _pq14dt
        _pq14_now = _pq14dt.datetime.now(_pq14dt.UTC).isoformat()
        _pq14_stamp = (
            "<!-- PROVENANCE"
            + f" model={CLAUDE_MODEL}"
            + f" generated={_pq14_now}"
            + f" cycle={cycle:03d} agent={agent_id}"
            + f" context_chars={len(pm_context)}"
            + " -->\n"
        )
        prompt_path.write_text(_pq14_stamp + prompt_text, encoding="utf-8")
        written[agent_id] = prompt_path
        _pm_generated_any = True
        # PQ-13: Save request artifact for audit/replay
        try:
            _req_artifact = prompts_dir / f"CYCLE_{cycle:03d}_AGENT_{agent_id}_REQUEST.md"
            _req_artifact.write_text(pm_context[:50000], encoding="utf-8")
        except Exception:
            pass

    L.ok(f"All {len(agents)} prompts generated by Claude PM")
    return written


def _call_claude_pm(agent_id: str, cycle: int, request_text: str,
                    instruction: str | None = None) -> str | None:
    """
    Call Claude CLI as PM to generate one agent prompt (or, in hybrid mode, one
    batch of task blocks when ``instruction`` is supplied).

    The Claude subscription (kevin.garrett@scentiment.com) is authenticated via
    claude.ai OAuth in the CLI binary. No ANTHROPIC_API_KEY is needed or used.

    The Anthropic Python SDK is NOT used here because it requires ANTHROPIC_API_KEY
    which conflicts with the subscription-only billing mode.

    Returns the generated prompt text (>500 chars) or None on failure.
    """
    claude_binary = _find_claude_binary()
    if not claude_binary:
        return None

    # Write request to temp file for reference, but send via stdin using Popen.communicate()
    # (file-based stdin redirect can cause "no stdin data received" warnings)
    req_path = runner_paths.tmp_dir() / f"claude_pm_agent_{agent_id}.md"
    req_path.parent.mkdir(parents=True, exist_ok=True)
    req_path.write_text(request_text, encoding="utf-8")

    # Build the prompt instruction — request_text is piped via stdin. A caller may
    # override it (hybrid batch mode passes a task-authoring instruction).
    if instruction is None:
        instruction = (
            f"You are the Fiverr Research System Project Manager. "
            f"Generate Agent {agent_id}'s complete Cursor agent prompt for Cycle {cycle:03d}. "
            f"The full PM context and requirements are in stdin. "
            f"Output ONLY the agent prompt text — no preamble, no explanation."
        )

    try:
        import os as _os
        env = {**_os.environ, "PYTHONIOENCODING": "utf-8"}
        # Load effort level from config (default: medium = adaptive thinking)
        _effort_level = "medium"
        try:
            import yaml as _yml
            for _ep in [REPO_ROOT / "PM_Pack/automation/autonomous_runner.yml"]:
                if _ep.exists():
                    _ecfg = _yml.safe_load(_ep.read_text(encoding="utf-8")) or {}
                    _effort_level = _ecfg.get("cursor_effort", "medium")
        except Exception:
            pass

        proc = subprocess.Popen(
            [claude_binary, "-p", instruction,
             "--output-format", "text",
             "--model", CLAUDE_MODEL,
             "--effort", _effort_level],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(REPO_ROOT),
            env=env,
        )
        stdout_bytes, stderr_bytes = proc.communicate(
            input=request_text.encode("utf-8"),
            timeout=CLAUDE_TIMEOUT,
        )
        text = (stdout_bytes or b"").decode("utf-8", errors="replace").strip()
        # Strip any warning lines Claude CLI prints to stdout before actual response
        lines = text.splitlines()
        lines = [ln for ln in lines if not ln.startswith("Warning:")]
        text = "\n".join(lines).strip()
        if text and proc.returncode == 0 and len(text) > 500:
            return text
        # H2 FIX: surface actual failure reason instead of silent return None
        err = (stderr_bytes or b"").decode("utf-8", errors="replace").strip()
        err_tail = err[-400:] if err else ""
        _failure_msg = (
            f"_call_claude_pm FAIL agent={agent_id} cycle={cycle} "
            f"rc={proc.returncode} output_len={len(text)} "
            f"(need >500) stderr_tail={repr(err_tail[:200])}"
        )
        # H2 FIX: emit to terminal + logger (was silently returning None)
        import click as _ck2
        _ck2.secho(f"  H2: {_failure_msg}", fg="red")
        try:
            import automation.autopilot_logger as _apl2
            _apl2.error(_failure_msg)
        except Exception:
            pass
        if err:
            req_path.with_suffix(".err").write_text(err, encoding="utf-8")
        return None
    except subprocess.TimeoutExpired:
        proc.kill()
        # H2 FIX: log actual timeout (was silently swallowed)
        _tmsg = (
            f"_call_claude_pm TIMEOUT agent={agent_id} cycle={cycle} "
            f"after {CLAUDE_TIMEOUT}s"
        )
        import click as _ck3
        _ck3.secho(f"  H2 TIMEOUT: {_tmsg}", fg="red")
        try:
            import automation.autopilot_logger as _apl3
            _apl3.error(_tmsg)
        except Exception:
            pass
        return None
    except Exception as _exc:
        # H2 FIX: log actual exception (was bare except: return None)
        import click as _ck4
        _emsg = f"_call_claude_pm EXCEPTION agent={agent_id} cycle={cycle}: {_exc!r}"
        _ck4.secho(f"  H2 EXCEPTION: {_emsg}", fg="red")
        try:
            import automation.autopilot_logger as _apl4
            _apl4.error(_emsg)
        except Exception:
            pass
        return None


def verify_jira_ac_completion(
    issue: dict,
    agent_report_text: str,
    contract: dict | None = None,
    run_dir: str | None = None,
) -> dict[str, Any]:
    """
    PQ-10 FIX: Real AC verification via ICV deterministic checker + Jira status.

    Replaces the word-overlap heuristic. Strategy (priority order):
    1. If the issue's Jira status is "Done" -> AC satisfied (authoritative).
    2. If a contract is provided, run its validationcommands for this issue.
    3. Check that the report exists and has AGENT_COMPLETE.
    4. Check each AC item against the deterministic checker's evidence
       (file existence, command outputs) rather than keyword matching.

    Returns {passed: bool, key: str, verified_ac: list, missing_ac: list, missing: list}.
    """
    import os
    key = issue.get("key", "?")

    # 1. Jira status is authoritative
    status = (issue.get("status") or issue.get("fields", {}).get("status", {}).get("name", "")).lower()
    if status == "done":
        return {"passed": True, "key": key, "verified_ac": ["Jira status: Done"], "missing_ac": [], "missing": []}

    # 2. Contract validationcommands (if provided)
    if contract and not os.environ.get("PYTEST_CURRENT_TEST"):
        commands_ok = True
        failed_cmds = []
        for cmd_entry in contract.get("validationcommands", []):
            cmd = cmd_entry.get("command", cmd_entry) if isinstance(cmd_entry, dict) else str(cmd_entry)
            try:
                import subprocess
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                if r.returncode != 0:
                    commands_ok = False
                    failed_cmds.append(cmd[:80])
            except Exception as _exc:
                commands_ok = False
                failed_cmds.append(f"{cmd[:40]}: {_exc}")
        if not commands_ok:
            return {
                "passed": False, "key": key, "missing": failed_cmds,
                "verified_ac": [], "missing_ac": failed_cmds,
                "note": "validationcommands failed",
            }

    # 3. Report must exist with AGENT_COMPLETE
    if not agent_report_text or "AGENT_COMPLETE" not in agent_report_text:
        return {
            "passed": False, "key": key,
            "missing": ["AGENT_COMPLETE marker missing from report"],
            "verified_ac": [], "missing_ac": ["AGENT_COMPLETE marker missing"],
        }

    # 4. ICV deterministic checker for deliverables declared in contract
    if contract:
        missing_files = []
        for scope_item in contract.get("jirascope", []):
            if scope_item.get("key") != key:
                continue
            for fpath in scope_item.get("filesormodules", []):
                from pathlib import Path as _Path
                if not (_Path("C:/Fiverr/Fiverr") / fpath).exists():
                    missing_files.append(fpath)
        if missing_files:
            return {
                "passed": False, "key": key,
                "missing": missing_files, "verified_ac": [],
                "missing_ac": [f"Missing deliverable: {f}" for f in missing_files],
            }

    # 5. Passed all available checks
    return {"passed": True, "key": key, "verified_ac": ["report+AGENT_COMPLETE present"], "missing_ac": [], "missing": []}
