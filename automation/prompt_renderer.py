"""Render markdown prompts from prompt-contract JSON payloads."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

__version__ = "1.1.0"

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_PATH = REPO_ROOT / "PM_Pack" / "03_cursor_agent_system" / "PROMPT_TEMPLATE.md"
DEFAULT_DRAFTS_DIR = REPO_ROOT / "PM_Pack" / "automation" / "prompts" / "drafts"
DEFAULT_STOP_CONDITIONS = [
    "Stop immediately if secrets/credentials are exposed in outputs or artifacts.",
    "Stop if any blocked path must be modified to complete a task.",
    "Stop if FC-1 (frozen/autonomy block) is triggered by policy or state.",
    "Stop before attempting write-side Git operations.",
]
ADDITIONAL_TASKS_SECTION = """
ADDITIONAL TASKS — Checklist Completion (Items with no prior coverage)
Task 56: EXPORT-001 — Create automation/export_sanitizer_verify.py
Create the module automation/export_sanitizer_verify.py. It must export:
class ExportSecretError(Exception) — carries offending_paths: list[str]
def verify_staged_files(staged_files: list[str]) -> None — raises ExportSecretError if any path matches: *.env, runner.env, *.credentials, *.pem, *.key, any name containing _TOKEN or secret (case-insensitive)
def verify_zip(zip_path: Path) -> None — opens ZIP, runs same check on all member names, raises ExportSecretError if any match Clean input → returns None silently. Add if __name__ == "__main__": import sys; verify_zip(Path(sys.argv[1])) CLI entrypoint. Run python -c "from automation.export_sanitizer_verify import verify_staged_files, verify_zip, ExportSecretError; verify_staged_files([]); print('export_sanitizer_verify OK')". Must exit 0.
Task 57: BRAIN-021 — Complete post_cycle_review.py fact collection
Open automation/post_cycle_review.py. Locate or create _verify_github_facts(self) -> dict: must call subprocess.run(["gh","pr","list","--state","merged","--limit","5","--json","number,title,mergedAt"]), parse JSON, return {"merged_prs": [...], "collected_at": ISO}. Write result to PM_Pack/automation/post_cycle_reviews/current_run/github_verification.json (create dirs). Handle subprocess errors gracefully — on CalledProcessError or FileNotFoundError return {"merged_prs":[], "error":"gh_unavailable"}. Wire this into collect_facts().
Task 58: POSTCYCLE-010/011 — Complete Jira closeout facts
In automation/post_cycle_review.py, add _verify_jira_facts(self) -> dict: queries Jira for Done stories in the current cycle using jira_client.search_issues(f"project=SCRUM AND status=Done AND sprint in openSprints()"), returns {"done_stories": [list of keys], "collected_at": ISO}. On JiraAuthError or ConnectionError: return {"done_stories": [], "auth_error": "JIRA_AUTH_FAILED"} — never raises. Wire into collect_facts(). Write result to PM_Pack/automation/post_cycle_reviews/current_run/jira_verification.json. Run python -c "from automation.post_cycle_review import PostCycleReview; r=PostCycleReview(); print('PostCycleReview importable')". Must exit 0.
Task 59: MODEL-014 — Add model verification section to daily report
Open automation/report_generator.py. Add _get_model_status_section(self) -> str: reads C:\\AI_Runner\\state\\cursor_model_state.json (and claude_model_state.json if it exists). Computes age in days from verified_at. Returns a formatted markdown block: `## Model Verification Status
Cursor: {model} | effort: {effort} | age: {N} days | expires: {date}
Claude: {model} | effort: {effort} | billing: {billingmode}. Wire intogeneratedailyreport(). Runpython automation/aicycle_controller.py daily-report 2>&1 | grep -i model` — must show at least one model line.
Task 60: GJCI-031 — Add CI timing benchmark to daily report
In automation/report_generator.py, add _get_ci_timing_section(self) -> str: runs subprocess.run(["gh","run","list","--workflow=ci.yml","--limit","5","--json","conclusion,createdAt,updatedAt"]), parses the JSON, computes average duration in seconds, returns `## CI Timing
Last 5 runs avg: {N}s | last run: {conclusion} ({duration}s). Handle gh unavailable gracefully. Wire intogeneratedailyreport()`. Document the output.
Task 61: PASS4-P1-010 — Health check ORANGE on stale heartbeat
Create C:\\AI_Runner\\scripts\\health_check.ps1 if it doesn't already exist. The script must:
Read C:\\AI_Runner\\state\\heartbeat.json — get last_seen timestamp
Compute age in minutes: (Get-Date) - [datetime]::Parse($heartbeat.last_seen)
If age > 120 minutes AND controller_state.json status is ACTIVE: write RED and exit 2
If age > 30 minutes AND controller_state.json status is ACTIVE: write ORANGE and exit 1
Otherwise: write GREEN and exit 0 Document the script. Verify it exists at the correct path.
Task 62: STATE-010 — Implement local notification logging on BLOCKED severity
Open automation/notification_router.py (create if not exists). Implement class NotificationRouter with:
send_local_notification(self, message: str, channel: str, severity: str) -> None: writes local jsonl entries, no external network calls.
route_notification(self, severity: str, message: str, context: dict) -> None: calls send_local_notification only when severity in ('BLOCKED', 'RED', 'CRITICAL'). Run python -c "from automation.notification_router import NotificationRouter; r=NotificationRouter(); r.route_notification('INFO','test',{}); print('NotificationRouter OK')". Must not crash.
Task 63: Run ruff + mypy on all new Agent B files
Run ruff check automation/export_sanitizer_verify.py automation/post_cycle_review.py automation/report_generator.py automation/notification_router.py --output-format=concise. Must exit 0. Run mypy automation/export_sanitizer_verify.py automation/notification_router.py --ignore-missing-imports --no-error-summary. Must exit 0. Document any type issues found and fixed.
""".strip()


class PromptRenderer:
    def __init__(self, template_path: Path | None = None) -> None:
        self.template_path = template_path or DEFAULT_TEMPLATE_PATH
        if not self.template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {self.template_path}")
        self.template_text = self.template_path.read_text(encoding="utf-8")
        DEFAULT_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    def render(self, contract: dict[str, Any]) -> str:
        return self.render_with_overrides(contract=contract)

    def render_with_overrides(
        self,
        contract: dict[str, Any],
        extra_tasks: list[dict[str, Any]] | None = None,
        stop_conditions: list[str] | None = None,
    ) -> str:
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
        if extra_tasks:
            start_index = len(task_blocks) + 1
            for idx, task in enumerate(extra_tasks):
                task_blocks.append(
                    {
                        "index": start_index + idx,
                        "title": _get_str(task, "title", "Additional task"),
                        "jira_key": _get_str(task, "jira_key", "SCRUM-UNKNOWN"),
                        "description": _get_str(task, "description", "No description provided."),
                        "files": _get_list(task, "files"),
                        "validation": _get_str(task, "validation", "Validation command/output evidence."),
                    }
                )
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
            "You MUST NOT run any write-side Git command or PR merge command.",
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
        effective_stop_conditions = stop_conditions or DEFAULT_STOP_CONDITIONS
        lines.extend(
            [
                "",
                "## FINAL REPORT REQUIREMENT",
                f"Write final report to {final_report_path}.",
                "",
                "## STOP CONDITIONS",
            ]
        )
        lines.extend(_render_list(effective_stop_conditions))
        lines.extend(
            [
                "",
                ADDITIONAL_TASKS_SECTION,
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
        if not jira_scope:
            stories = [{"key": "SCRUM-000", "summary": "Fallback story", "files_or_modules": []}]
        else:
            stories = jira_scope
        tasks: list[dict[str, Any]] = []
        index = 1
        if not jira_scope:
            tasks.append(
                {
                    "index": index,
                    "title": "No Jira stories assigned — verify contract generation.",
                    "jira_key": "SCRUM-000",
                    "description": (
                        f"Agent {agent} must validate why jira_scope is empty and confirm contract inputs "
                        "before continuing with generic quality and safety work."
                    ),
                    "files": [],
                    "validation": "Inspect contract generator output and record remediation notes.",
                }
            )
            index += 1
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


SCHEMA_PATH = Path(__file__).parent / "schemas" / "prompt_contract.schema.json"


def get_schema_path() -> Path:
    return SCHEMA_PATH


def render_with_overrides(
    contract: dict[str, Any],
    extra_tasks: list[dict[str, Any]] | None = None,
    stop_conditions: list[str] | None = None,
) -> str:
    renderer = PromptRenderer()
    return renderer.render_with_overrides(contract, extra_tasks=extra_tasks, stop_conditions=stop_conditions)


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
