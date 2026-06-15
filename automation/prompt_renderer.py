"""Render markdown prompts from prompt-contract JSON payloads."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_PATH = REPO_ROOT / "PM_Pack" / "03_cursor_agent_system" / "PROMPT_TEMPLATE.md"
DEFAULT_DRAFTS_DIR = REPO_ROOT / "PM_Pack" / "automation" / "prompts" / "drafts"


class PromptRenderer:
    def __init__(self, template_path: Path | None = None) -> None:
        self.template_path = template_path or DEFAULT_TEMPLATE_PATH
        if not self.template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {self.template_path}")
        self.template_text = self.template_path.read_text(encoding="utf-8")
        DEFAULT_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    def render(self, contract: dict[str, Any]) -> str:
        cycle = _get_str(contract, "cycle", "000")
        agent = _get_str(contract, "agent", "X")
        lane_name = _get_str(contract, "agent_lane", _get_str(contract, "agentlane", "General"))
        branch = _get_str(contract, "branch", f"cycle/{cycle}/integration")
        built_at = _get_str(contract, "built_at", _get_str(contract, "builtat", datetime.now(tz=UTC).isoformat()))
        model_policy = _get_dict(contract, "model_policy", fallback_key="modelpolicy")
        allowed_paths = _get_list(contract, "allowed_paths", fallback_key="allowedpaths")
        blocked_paths = _get_list(contract, "blocked_paths", fallback_key="blockedpaths")
        jira_scope = _get_list_of_dicts(contract, "jira_scope", fallback_key="jirascope")
        validation_commands = _get_list(contract, "validation_commands", fallback_key="validationcommands")
        final_report_path = _get_str(
            contract,
            "final_report_path",
            _get_str(contract, "finalreportpath", f"docs/cycle_reports/CYCLE_{cycle}_AGENT_{agent}.md"),
        )

        task_blocks = self._generate_task_blocks(jira_scope, agent)
        if not validation_commands:
            validation_commands = [
                "ruff check automation/ --output-format=concise",
                "mypy src/ automation/ --ignore-missing-imports",
                "pytest tests/unit/ -q",
            ]
        elif not any("mypy" in command and "src/" in command for command in validation_commands):
            validation_commands.append("mypy src/ automation/ --ignore-missing-imports")

        lines: list[str] = [
            f"# CYCLE {cycle} — Agent {agent}: {lane_name}",
            f"Generated: {built_at}",
            f"Cycle: {cycle}",
            f"Agent: {agent}",
            f"Branch: {branch}",
            "Repo Root: C:/Fiverr/Fiverr",
            "",
            "## MODEL POLICY — MANDATORY",
            f"Worker: {_policy_value(model_policy, 'worker', 'Cursor CLI')}",
            f"Model: {_policy_value(model_policy, 'model', 'codex-5.3')}",
            f"Effort: {_policy_value(model_policy, 'effort', 'medium')}",
            f"Auto: {_bool_text(model_policy.get('auto'), default='DISABLED')}",
            f"Fallback: {_bool_text(model_policy.get('fallback'), default='DISABLED')}",
            "",
            "## GIT RULES — MANDATORY",
            "You MUST NOT run git add, git commit, git push, gh pr merge, or any force push command.",
            "Controller owns all git operations.",
            "",
            "## AUTONOMY RULE",
            "Complete all assigned tasks autonomously without confirmation prompts unless a hard blocker appears.",
            "",
            "## ALLOWED PATHS",
        ]
        lines.extend(_render_list(allowed_paths, placeholder="(No allowed paths specified in contract)"))
        lines.extend(["", "## BLOCKED PATHS"])
        lines.extend(_render_list(blocked_paths, placeholder="(No blocked paths specified in contract)"))
        lines.extend(["", "## JIRA SCOPE"])
        lines.extend(self._render_jira_scope(jira_scope))
        lines.extend(["", "## TASKS"])
        for task in task_blocks:
            lines.extend(
                [
                    f"### Task {task['index']}: {task['title']}",
                    f"- Jira key: {task['jira_key']}",
                    f"- Description: {task['description']}",
                    f"- Files: {', '.join(task['files']) if task['files'] else '(none)'}",
                    f"- Validation: {task['validation']}",
                    "",
                ]
            )
        lines.extend(["## REQUIRED VALIDATION STEPS"])
        lines.extend(_render_list(validation_commands))
        lines.extend(
            [
                "",
                "## FINAL REPORT REQUIREMENT",
                f"Write final report to {final_report_path}.",
                "",
                "## STOP CONDITIONS",
                "- Stop if a blocked path must be modified.",
                "- Stop if a required external prerequisite is missing.",
                "- Stop before executing any forbidden git write operation.",
                "",
                "END OF PROMPT",
            ]
        )
        return "\n".join(lines) + "\n"

    def render_to_draft(self, contract: dict[str, Any]) -> Path:
        rendered_prompt = self.render(contract)
        cycle = _get_str(contract, "cycle", "000")
        agent = _get_str(contract, "agent", "X")
        draft_path = DEFAULT_DRAFTS_DIR / f"CYCLE_{cycle}_AGENT_{agent}_DRAFT.md"
        prompt_path = DEFAULT_DRAFTS_DIR / f"CYCLE_{cycle}_AGENT_{agent}_PROMPT.md"
        draft_path.write_text(rendered_prompt, encoding="utf-8")
        prompt_path.write_text(rendered_prompt, encoding="utf-8")
        return draft_path

    def _render_jira_scope(self, jira_scope: list[dict[str, Any]]) -> list[str]:
        if not jira_scope:
            return ["- No jira_scope items provided."]
        lines: list[str] = []
        for story in jira_scope:
            key = _get_str(story, "key", "SCRUM-UNKNOWN")
            summary = _get_str(story, "summary", "No summary")
            status = _get_str(story, "status", "In Progress")
            priority = _get_str(story, "priority", "Medium")
            spec_path = _get_str(story, "project_plan_path", _get_str(story, "projectplanpath", "Not provided"))
            acceptance = _get_list(story, "acceptance_criteria", fallback_key="acceptancecriteria")
            definition_of_done = _get_list(story, "definition_of_done", fallback_key="definitionofdone")
            files_or_modules = _get_list(story, "files_or_modules", fallback_key="filesormodules")
            lines.extend(
                [
                    f"### {key}: {summary}",
                    f"Status: {status}",
                    f"Priority: {priority}",
                    f"Spec path: {spec_path}",
                    "Acceptance Criteria:",
                ]
            )
            lines.extend(_render_list(acceptance, placeholder="(No AC entries provided)"))
            lines.append("Definition of Done:")
            lines.extend(_render_list(definition_of_done, placeholder="(No DoD entries provided)"))
            lines.append("Files or modules:")
            lines.extend(_render_list(files_or_modules, placeholder="(No files listed)"))
            lines.append("")
        return lines

    def _generate_task_blocks(self, jira_scope: list[dict[str, Any]], agent: str) -> list[dict[str, Any]]:
        stories = jira_scope or [{"key": "SCRUM-000", "summary": "Fallback story", "files_or_modules": []}]
        tasks: list[dict[str, Any]] = []
        index = 1
        for story in stories:
            key = _get_str(story, "key", "SCRUM-UNKNOWN")
            summary = _get_str(story, "summary", "Story workstream")
            files = _get_list(story, "files_or_modules", fallback_key="filesormodules")
            phases = [
                "Review specification and acceptance requirements",
                "Implement routing and control logic",
                "Verify acceptance criteria coverage",
                "Write and run focused unit validation checks",
                "Verify definition-of-done artifacts",
                "Run full validation command set",
            ]
            for phase in phases:
                tasks.append(
                    {
                        "index": index,
                        "title": f"{summary} — {phase}",
                        "jira_key": key,
                        "description": (
                            f"Agent {agent} executes '{phase}' for {key}, records evidence, "
                            "and updates implementation notes for downstream agents."
                        ),
                        "files": files,
                        "validation": "Record command outputs and state transition evidence.",
                    }
                )
                index += 1
        while len(tasks) < 55:
            key = _get_str(stories[(index - 1) % len(stories)], "key", "SCRUM-UNKNOWN")
            tasks.append(
                {
                    "index": index,
                    "title": "General quality gate execution",
                    "jira_key": key,
                    "description": (
                        "Run ruff, mypy, pytest, schema checks, and reporting validation to maintain "
                        "regression safety while finalizing delivery artifacts."
                    ),
                    "files": [],
                    "validation": "ruff + mypy + pytest + jsonschema + report update",
                }
            )
            index += 1
        return tasks


def _get_str(payload: dict[str, Any], key: str, default: str, fallback_key: str | None = None) -> str:
    value = payload.get(key)
    if value is None and fallback_key is not None:
        value = payload.get(fallback_key)
    return str(value) if value is not None else default


def _get_dict(payload: dict[str, Any], key: str, fallback_key: str | None = None) -> dict[str, Any]:
    value = payload.get(key)
    if value is None and fallback_key is not None:
        value = payload.get(fallback_key)
    return value if isinstance(value, dict) else {}


def _get_list(payload: dict[str, Any], key: str, fallback_key: str | None = None) -> list[str]:
    value = payload.get(key)
    if value is None and fallback_key is not None:
        value = payload.get(fallback_key)
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _get_list_of_dicts(payload: dict[str, Any], key: str, fallback_key: str | None = None) -> list[dict[str, Any]]:
    value = payload.get(key)
    if value is None and fallback_key is not None:
        value = payload.get(fallback_key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _policy_value(policy: dict[str, Any], key: str, default: str) -> str:
    value = policy.get(key)
    return str(value) if value is not None else default


def _bool_text(value: Any, default: str = "DISABLED") -> str:
    if isinstance(value, bool):
        return "ENABLED" if value else "DISABLED"
    return default


def _render_list(items: list[str], placeholder: str = "(none)") -> list[str]:
    if not items:
        return [f"- {placeholder}"]
    return [f"- {item}" for item in items]
