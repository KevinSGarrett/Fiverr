"""Prompt contract builder for cycle agent prompts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from automation.prompt_generator import PlanningIncompleteError


@dataclass(frozen=True)
class LaneScope:
    """Resolved lane ownership/prohibition scope."""

    owned_paths: list[str]
    prohibited_paths: list[str]
    description: str


def build_prompt_contract(
    agent: str,
    cycle: int,
    stories: list[dict[str, Any]],
    lanes: dict[str, Any],
    pp_catalog: dict[str, Any] | None = None,
    dod_catalog: dict[str, Any] | None = None,
    preamble_text: str = "",
) -> str:
    """
    Build a complete prompt contract string.

    The generated contract includes:
      - canonical environment and path preamble
      - lane identity block
      - model policy block
      - Jira scope with AC/DoD snippets
      - >=55 tasks
      - validation command block
      - final END OF PROMPT marker
    """
    _validate_story_planning(stories)
    scope = _resolve_lane_scope(agent, lanes)
    now = datetime.now(UTC).isoformat()
    report_path = f"docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent}.md"

    lines: list[str] = [
        f"Cycle {cycle:03d} — Agent {agent} Prompt",
        "",
        preamble_text.strip() if preamble_text.strip() else _default_preamble(),
        "",
        "## Agent Identity and Lane",
        f"You are Agent {agent} for Cycle {cycle:03d} on branch cycle/{cycle:03d}/integration.",
        f"Lane description: {scope.description}",
        "Your lane owns:",
    ]
    lines.extend([f"- {path}" for path in scope.owned_paths] or ["- (defined by agent_lanes.yml)"])
    lines.append("You MUST NOT touch:")
    lines.extend([f"- {path}" for path in scope.prohibited_paths] or ["- (none explicitly declared)"])
    lines.extend(
        [
            "",
            "## Model Policy (MANDATORY)",
            "- Model: Codex 5.3",
            "- Effort: medium",
            "- Auto model selection: DISABLED",
            "",
            "## Autonomy rule",
            "- Proceed autonomously through all tasks without pausing for confirmation.",
            "- If blocked, document blocker and continue with next executable task.",
            "- Do not include git add/commit/push instructions in this prompt.",
            "",
            "## Jira Scope",
        ]
    )
    lines.extend(_render_jira_scope(stories))
    lines.extend(["", "## Tasks"])
    lines.extend(_render_tasks(agent, cycle, stories, pp_catalog, dod_catalog))
    task_count = sum(1 for line in lines if line.startswith("### TASK "))
    if task_count < 55:
        raise ValueError(f"Task floor not met: {task_count} < 55")

    lines.extend(
        [
            "",
            "## Validation Commands",
            "- ruff check automation/ src/ tests/",
            "- mypy src/ automation/ --ignore-missing-imports",
            "- pytest tests/unit/ --timeout=30 --tb=no -q",
            "- python automation/ai_cycle_controller.py brain-check",
            "- python automation/ai_cycle_controller.py pm-pack-audit --check-only",
            "",
            "## Report",
            f"- Write: {report_path}",
            "- Final line must be: AGENT_COMPLETE",
            "",
            f"Generated at: {now}",
            "",
            "---",
            "",
            "END OF PROMPT",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def _resolve_lane_scope(agent: str, lanes: dict[str, Any]) -> LaneScope:
    lane_cfg = (lanes or {}).get("lanes", {}).get(agent, {})
    prohibited = lane_cfg.get("prohibited", lane_cfg.get("prohibited_without_explicit_task", []))
    return LaneScope(
        owned_paths=[str(path) for path in lane_cfg.get("owns", [])],
        prohibited_paths=[str(path) for path in prohibited],
        description=str(lane_cfg.get("description", "No lane description provided")),
    )


def _validate_story_planning(stories: list[dict[str, Any]]) -> None:
    for story in stories:
        ac = str(story.get("acceptance_criteria", "") or "").strip()
        dod = str(story.get("definition_of_done", "") or "").strip()
        if not ac and not dod:
            key = story.get("key", "UNKNOWN")
            raise PlanningIncompleteError(
                f"PLANNING_INCOMPLETE {key}: missing acceptance_criteria and definition_of_done"
            )


def _render_jira_scope(stories: list[dict[str, Any]]) -> list[str]:
    if not stories:
        return ["No stories assigned."]
    lines: list[str] = []
    for story in stories:
        key = str(story.get("key", "SCRUM-UNKNOWN"))
        summary = str(story.get("summary", "") or "")[:80]
        ac = str(story.get("acceptance_criteria", "") or "")[:200]
        dod = str(story.get("definition_of_done", "") or "")[:200]
        lines.extend([f"- {key}: {summary}", f"  - AC: {ac}", f"  - DoD: {dod}"])
    return lines


def _render_tasks(
    agent: str,
    cycle: int,
    stories: list[dict[str, Any]],
    pp_catalog: dict[str, Any] | None,
    dod_catalog: dict[str, Any] | None,
) -> list[str]:
    _ = dod_catalog
    tasks: list[str] = []
    story_count = max(1, len(stories))
    for idx in range(1, 56):
        story = stories[(idx - 1) % story_count] if stories else {}
        key = str(story.get("key", f"SCRUM-{cycle}{idx:02d}"))
        summary = str(story.get("summary", "Prompt contract task"))[:70]
        ac = str(story.get("acceptance_criteria", "Validate behavior from Jira AC")).strip()
        dod = str(story.get("definition_of_done", "Meet DoD evidence for this story")).strip()
        catalog_hint = _catalog_hint(pp_catalog, key)
        tasks.extend(
            [
                f"### TASK {idx:02d} — Agent {agent} delivery for {key}: {summary}",
                f"- Story: {key}",
                f"- AC Focus: {ac}",
                f"- DoD Focus: {dod}",
                f"- Project Plan Context: {catalog_hint}",
                "- Validation: run targeted unit tests and record evidence in cycle report.",
                "",
            ]
        )
    return tasks


def _catalog_hint(pp_catalog: dict[str, Any] | None, issue_key: str) -> str:
    if not isinstance(pp_catalog, dict):
        return "PM_Pack/ref/project_plan (catalog unavailable)"
    entries = pp_catalog.get("entries")
    if not isinstance(entries, list):
        return "PM_Pack/ref/project_plan (catalog malformed)"
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        jira_keys = entry.get("jira_keys", [])
        if isinstance(jira_keys, list) and issue_key in jira_keys:
            return str(entry.get("source_path", "PM_Pack/ref/project_plan"))
    return "PM_Pack/ref/project_plan (no direct SCRUM mapping)"


def _default_preamble() -> str:
    return "\n".join(
        [
            "## Canonical Secrets Reference",
            "- Master .env: C:\\Fiverr\\Fiverr\\.env",
            "- Runner secrets: C:\\AI_Runner\\secrets\\runner.env",
            "- Required keys: OPENAI_API_KEY, SCRAPFLY_API_KEY, JIRA_API_TOKEN, JIRA_EMAIL, JIRA_BASE_URL, GH_AUTOMATION_TOKEN",
            "- ANTHROPIC_API_KEY must be ABSENT",
            "",
            "## Exact Directory Map",
            "- Repo root: C:\\Fiverr\\Fiverr",
            "- Automation modules: C:\\Fiverr\\Fiverr\\automation\\",
            "- PM_Pack root: C:\\Fiverr\\Fiverr\\PM_Pack\\",
            "- Runner root: C:\\AI_Runner\\",
            "",
            "## PM_Pack Structure",
            "- Post-cycle review prompt: C:\\Fiverr\\Fiverr\\PM_Pack\\01_pm_instructions\\POST_CYCLE_PM_REVIEW_v4.md",
            "- PM_Pack/ref project plans: C:\\Fiverr\\Fiverr\\PM_Pack\\ref\\project_plan\\",
            "- PM_Pack/ref DoD: C:\\Fiverr\\Fiverr\\PM_Pack\\ref\\dod\\",
            "- PM_Pack/ref TODO: C:\\Fiverr\\Fiverr\\PM_Pack\\ref\\todo\\",
            "",
            "## Model Verification",
            "- Verify C:\\AI_Runner\\state\\cursor_model_state.json is VERIFIED and unexpired before dispatch.",
        ]
    )
