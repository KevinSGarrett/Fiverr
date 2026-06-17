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

CLAUDE_MODEL  = "claude-sonnet-4-6"
CLAUDE_TIMEOUT = 480  # 8 min per agent — prompts are 3000-5000 lines


def _find_claude_binary() -> str | None:
    """Find the `claude` CLI binary — same logic as claude_post_cycle_adapter."""
    import shutil
    # Try full path first (verified location)
    known = Path(r"C:\Users\Windows 11\.local\bin\claude.EXE")
    if known.exists():
        return str(known)
    found = shutil.which("claude")
    if found:
        return found
    # Common install locations on Windows
    for candidate in [
        Path.home() / ".local/bin/claude.EXE",
        Path.home() / ".local/bin/claude",
        Path(r"C:\Users\Windows 11\AppData\Local\anthropic\claude\claude.EXE"),
    ]:
        if candidate.exists():
            return str(candidate)
    return None


def _verify_claude_subscription() -> dict[str, Any]:
    """Confirm no ANTHROPIC_API_KEY is set (must use subscription billing)."""
    import os
    for key in ["ANTHROPIC_API_KEY", "ANTHROPIC_API"]:
        val = os.environ.get(key, "")
        if val and not val.startswith("PLACEHOLDER"):
            return {"passed": False, "reason": f"{key} present — must use subscription billing only"}
    state = RUNNER_ROOT / "state/claude_model_state.json"
    if state.exists():
        s = json.loads(state.read_text())
        if s.get("billing_mode") != "claude_subscription_only":
            return {"passed": False, "reason": "claude_model_state billing_mode is not subscription_only"}
    return {"passed": True}


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
        lines += ["### Product Vision (excerpt)", _read(vision_path, 2000), ""]

    # Development roadmap
    roadmap = REF_ROOT / "08_roadmap/DEVELOPMENT_ROADMAP.md"
    if roadmap.exists():
        lines += ["### Development Roadmap", _read(roadmap, 3000), ""]

    # Wave schedule
    wave_sched = REF_ROOT / "00_meta/WAVE_SCHEDULE.md"
    if wave_sched.exists():
        lines += ["### Wave Schedule (current state)", _read(wave_sched, 2000), ""]

    # Enhancement wave schedule
    enh_sched = REF_ROOT / "00_meta/ENHANCEMENT_WAVE_SCHEDULE.md"
    if enh_sched.exists():
        lines += ["### Enhancement Waves", _read(enh_sched, 2000), ""]

    lines += [
        "",
        "=" * 70,
        f"## 2. CURRENT WAVE {wave} — DETAILED SPECIFICATIONS",
        "=" * 70,
    ]

    # All spec docs for current wave
    wave_folder_map = {11: "11_playbook", 12: "12_dashboard_ux"}
    wave_folder = REF_ROOT / wave_folder_map.get(wave, "11_playbook")
    if wave_folder.exists():
        for spec_file in sorted(wave_folder.iterdir()):
            if spec_file.suffix == ".md":
                lines += [f"### SPEC: {spec_file.name}", _read(spec_file, 2000), ""]

    # DOD for current wave
    dod_map = {11: "DOD_EPIC_08.md", 12: "DOD_EPIC_09.md"}
    dod_path = DOD_ROOT / dod_map.get(wave, "DOD_EPIC_08.md")
    if dod_path.exists():
        lines += ["### DOD (Definition of Done — ALL criteria must be met)", _read(dod_path, 2000), ""]

    # Epic TODO list
    todo_map = {11: "EPIC_08_PLAYBOOK.md", 12: "EPIC_09_DASHBOARD.md"}
    todo_path = TODO_ROOT / todo_map.get(wave, "EPIC_08_PLAYBOOK.md")
    if todo_path.exists():
        lines += ["### Epic Task Breakdown (implementation checklist)", _read(todo_path, 2000), ""]

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

    lines.append("### WAVE 11 TARGET STORIES (PRIMARY BUILD TARGET)")
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
        lines += ["### Hydration Header (current cycle state)", _read(hydration, 1500), ""]

    # Epic status tracker
    tracker = PM_PACK / "08_task_queue/EPIC_STATUS_TRACKER.md"
    if tracker.exists():
        lines += ["### Epic Status Tracker", _read(tracker, 2000), ""]

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

    return "\n".join(lines)


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

    return f"""You are the Project Manager for the Fiverr Research System autonomous build runner.

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
7. Tasks MUST reference PLAYBOOK stories (SCRUM-205, 206, 208, 209, 210, 211) FIRST
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
{pm_context[:8000]}

## OUTPUT FORMAT
Generate ONLY the agent prompt text. Start with the header line:
# CYCLE {cycle:03d} — AGENT {agent_id} PROMPT
# Wave 11 {branch}

Do not add preamble. Do not add explanation after the prompt.
The prompt should be 3,000-5,000 lines for implementation agents (B), 1,500-3,000 for others.
"""


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
    if not preflight["passed"]:
        return None

    # Build the full PM context document
    pm_context = _build_pm_context(cycle, branch, jira_issues, wave)

    # Save PM context as artifact
    prompts_dir.mkdir(parents=True, exist_ok=True)
    ctx_path = prompts_dir / f"CYCLE_{cycle:03d}_PM_CONTEXT.md"
    ctx_path.write_text(pm_context, encoding="utf-8")

    written: dict[str, Path] = {}

    import time as _t
    import automation.autopilot_logger as L

    L.section(f"Claude PM generating {len(agents)} agent prompts for Cycle {cycle:03d}")
    L.info(f"Model: {CLAUDE_MODEL}  Timeout: {CLAUDE_TIMEOUT}s per agent")
    L.info(f"Estimated time: {len(agents) * 3}-{len(agents) * 5} min total")

    for idx, agent_id in enumerate(agents, 1):
        request_text = _build_agent_prompt_request(
            agent_id=agent_id, cycle=cycle, branch=branch, pm_context=pm_context,
        )
        L.claude_pm_start(agent_id, cycle, idx, len(agents))

        t0 = _t.time()
        with L.Spinner(f"Claude PM -> Agent {agent_id} (timeout {CLAUDE_TIMEOUT//60}m)"):
            prompt_text = _call_claude_pm(agent_id, cycle, request_text)
        elapsed = _t.time() - t0

        if not prompt_text:
            L.claude_pm_done(agent_id, elapsed, 0, False, idx, len(agents))
            return None  # Signal fallback needed

        L.claude_pm_done(agent_id, elapsed, len(prompt_text), True, idx, len(agents))
        prompt_path = prompts_dir / f"CYCLE_{cycle:03d}_AGENT_{agent_id}_PROMPT.md"
        prompt_path.write_text(prompt_text, encoding="utf-8")
        written[agent_id] = prompt_path

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
        proc = subprocess.Popen(
            [claude_binary, "-p", instruction,
             "--output-format", "text",
             "--model", CLAUDE_MODEL],
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
        # Log stderr for debugging
        err = (stderr_bytes or b"").decode("utf-8", errors="replace").strip()
        if err:
            req_path.with_suffix(".err").write_text(err, encoding="utf-8")
        return None
    except subprocess.TimeoutExpired:
        proc.kill()
        return None
    except Exception:
        return None


def verify_jira_ac_completion(
    issue: dict,
    agent_report_text: str,
) -> dict[str, Any]:
    """
    Check if all Jira story AC items appear to be addressed in the agent report.
    Returns {passed: bool, missing_ac: list[str], verified_ac: list[str]}.
    """
    fields = issue.get("fields", {})
    description = fields.get("description", "") or issue.get("description", "")
    key = issue.get("key", "?")

    if not description:
        return {"passed": True, "key": key, "note": "No AC in Jira description"}

    # Extract AC items (look for checklist patterns)
    import re
    ac_items = re.findall(
        r"[-*•]\s*([^\n]{20,200})",
        description
    )

    verified, missing = [], []
    for ac in ac_items[:20]:  # check up to 20 AC items
        # Check if the AC item's key concepts appear in the agent report
        words = [w for w in ac.lower().split() if len(w) > 4][:5]
        if words and any(all(w in agent_report_text.lower() for w in words[:3]) for _ in [1]):
            verified.append(ac)
        else:
            missing.append(ac)

    return {
        "passed": len(missing) == 0,
        "key": key,
        "total_ac": len(ac_items),
        "verified": len(verified),
        "missing_count": len(missing),
        "missing_ac": missing[:5],  # first 5 unverified items
    }
