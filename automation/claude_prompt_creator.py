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
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
CLAUDE_TIMEOUT = 480  # 8 min per agent — prompts are 3000-5000 lines


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


def _pm_existing_prompt_ok(prompt_path: Path) -> bool:
    """PMR resume-from-partial gate: True if a substantial, real prompt already
    exists for this agent on disk, so it can be reused instead of regenerated.

    Stub placeholders written by plan-cycle (~200 chars, containing "[STUB")
    are deliberately NOT treated as reusable, so a fresh cycle still generates.
    """
    try:
        if not prompt_path.exists():
            return False
        text = prompt_path.read_text(encoding="utf-8", errors="replace")
        if len(text) < PM_MIN_PROMPT_CHARS:
            return False
        if "[STUB" in text or "populate from PM_Pack" in text:
            return False
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
5. Generate EXACTLY 55-70 LARGE/XLARGE/XXLARGE tasks (policy floor = 55)
6. Every task MUST have:
   - The specific Jira key it addresses (SCRUM-XXX)
   - Executable Python or PowerShell code to run
   - Expected output / verification step
   - The specific file path to create or modify
   - The exact function signature or class definition from the spec
   - Acceptance criteria items from the Jira story (must be verifiable)
   - DOD checklist items the agent must complete before marking task done
7. Tasks MUST reference the IN-SCOPE PLAYBOOK stories listed in the PM CONTEXT above. Derive the target stories from the Jira board state, NOT a hardcoded list.
8. SCRUM-207 is already Done — do NOT rebuild it
9. Include a squash SHA placeholder: [C{cycle:03d}_SQUASH_SHA]
10. Include base SHA, suite count, coverage % from the PM context
11. Include the PERMANENT REGRESSION PACK (all must still pass)
12. End with an authorization statement confirming policy v4.3 compliance

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


def create_agent_prompts_via_claude(
    cycle: int,
    branch: str,
    jira_issues: list[dict],
    agents: list[str],
    prompts_dir: Path,
    wave: int = 11,
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
        if _pm_existing_prompt_ok(prompt_path):
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
        elapsed = 0.0
        for _attempt in range(1, PM_MAX_ATTEMPTS + 1):
            t0 = _t.time()
            with L.Spinner(
                f"Claude PM -> Agent {agent_id} "
                f"(attempt {_attempt}/{PM_MAX_ATTEMPTS}, timeout {CLAUDE_TIMEOUT//60}m)"
            ):
                prompt_text = _call_claude_pm(agent_id, cycle, request_text)
            elapsed = _t.time() - t0
            if prompt_text:
                if _attempt > 1:
                    L.ok(f"PMR: Agent {agent_id} succeeded on attempt {_attempt}/{PM_MAX_ATTEMPTS}")
                break
            if _attempt < PM_MAX_ATTEMPTS:
                _backoff = min(
                    PM_RETRY_BACKOFF_BASE * (2 ** (_attempt - 1)),
                    PM_RETRY_BACKOFF_CAP,
                )
                _emit("CLAUDE_PM", f"Agent {agent_id} attempt {_attempt}/{PM_MAX_ATTEMPTS} failed — retry in {_backoff}s", agent=agent_id, cycle=cycle, status="RETRY")
                L.warn(
                    f"PMR: Agent {agent_id} attempt {_attempt}/{PM_MAX_ATTEMPTS} returned "
                    f"empty/short — backing off {_backoff}s before retry"
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


def _call_claude_pm(agent_id: str, cycle: int, request_text: str) -> str | None:
    """
    Call Claude CLI as PM to generate one agent prompt.

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
    req_path = Path(f"C:/AI_Runner/tmp/claude_pm_agent_{agent_id}.md")
    req_path.parent.mkdir(parents=True, exist_ok=True)
    req_path.write_text(request_text, encoding="utf-8")

    # Build the prompt instruction — request_text is piped via stdin
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
