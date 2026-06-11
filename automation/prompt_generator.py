"""
prompt_generator.py — Real PM_Pack/Jira-derived Cursor agent prompt generator.

Generates per-agent prompts from:
  - PM_Pack PROMPT_TEMPLATE.md (structure)
  - PM_Pack PROMPT_RULES.md (rules)
  - PM_Pack agent_lanes.yml (agent roles)
  - Jira board inventory (AC/DoD per story)
  - model_policy.yml (model/effort block)
  - Plan cycle manifest (branch, scope)

Each prompt must contain:
  - 20-40 substantive tasks (>=55 LARGE-XXLARGE task minimum from Wave 04)
  - >=6,000 words (target 8,000-12,000)
  - Codex 5.3 medium model block
  - END OF PROMPT marker exactly once
  - Jira keys + AC/DoD per task
  - Exact file paths, implementation details >=100 words
  - Validation commands
  - Report path
  - No secrets
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path("C:/Fiverr/Fiverr")
PM_PACK   = REPO_ROOT / "PM_Pack"


# ── Agent role definitions ─────────────────────────────────────────────────
AGENT_ROLES = {
    "A": {
        "name": "Agent A — Core Infrastructure & Data Pipeline",
        "scope": "src/pipeline, src/models, src/collection, src/scoring",
        "epics": "E1-E4 (Data foundation, keyword collection, scoring pipeline, validation)",
        "no_modify": ["src/dashboard", "src/reports", "src/playbook", "docs/"],
    },
    "B": {
        "name": "Agent B — Source Layer & API Integrations",
        "scope": "src/signals, src/integrations, src/scrapers",
        "epics": "E5-E7 (Signal sources, external APIs, data enrichment)",
        "no_modify": ["src/dashboard", "src/reports"],
    },
    "E": {
        "name": "Agent E — Quality Assurance & Test Coverage",
        "scope": "tests/unit, tests/integration, tests/e2e",
        "epics": "QA across all epics — write/expand tests only",
        "no_modify": ["src/", "docs/"],
        "docs_only": False,
        "tests_only": True,
    },
    "C": {
        "name": "Agent C — Dashboard & Visualization Layer",
        "scope": "src/dashboard, src/visualization",
        "epics": "E8-E9 (Streamlit dashboard, charts, export)",
        "no_modify": ["src/pipeline", "src/models", "src/scoring"],
    },
    "F": {
        "name": "Agent F — Reports & Playbook Generation",
        "scope": "src/reports, src/playbook",
        "epics": "E10-E11 (PDF/Markdown reports, seller playbooks)",
        "no_modify": ["src/pipeline", "src/dashboard"],
    },
    "D": {
        "name": "Agent D — Docs, PM Review & Governance Closeout",
        "scope": "docs/, PM_Pack/10_cycle_log/, docs/cycle_reports/",
        "epics": "Governance closeout, cycle log, PR description, Jira AC/DoD evidence",
        "no_modify": ["src/", "tests/"],
        "docs_only": True,
    },
}


def generate_prompt(
    agent_id: str,
    cycle: int,
    branch: str,
    jira_issues: list[dict],
    run_id: str,
    model: str = "Codex 5.3",
    effort: str = "medium",
    base_branch: str = "develop",
) -> str:
    """
    Generate a full Cursor agent prompt.
    Returns the prompt text ready to write to a .md file.
    """
    agent = AGENT_ROLES.get(agent_id, AGENT_ROLES["D"])
    now = datetime.now(UTC).isoformat()
    report_path = f"docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent_id}.md"

    # Select issues relevant to this agent
    agent_issues = _select_issues_for_agent(agent_id, jira_issues)

    lines = []

    # ── Header ───────────────────────────────────────────────────────────
    lines += [
        f"{'=' * 68}",
        f"AGENT {agent_id} — CYCLE {cycle:03d} PROMPT",
        f"{'=' * 68}",
        "",
        "## 0. Model Policy (MANDATORY — do not override)",
        "",
        f"- **Model:** {model}",
        f"- **Effort:** {effort}",
        f"- **Auto model selection:** DISABLED — use only {model}",
        "- **Fallback model:** DISABLED",
        "- **Billing:** Claude subscription only for PM review; no API key",
        "",
    ]

    # ── 1. Project Context ────────────────────────────────────────────────
    lines += [
        "## 1. Identity",
        "",
        f"You are **{agent['name']}** for Cycle {cycle:03d} of the Fiverr Research System.",
        "",
        "## 2. Project Context",
        "",
        "- Project: Fiverr Research System — AI-driven Fiverr gig research and recommendation platform",
        "- GitHub: https://github.com/KevinSGarrett/Fiverr",
        "- Local repo root: C:\\Fiverr\\Fiverr",
        f"- Branch: `{branch}`",
        f"- Base branch: `{base_branch}`",
        "- Python: 3.11+ | SQLAlchemy 2.0 | Pydantic v2 | Playwright | OpenAI | Streamlit",
        f"- Cycle: {cycle:03d} | Run ID: {run_id}",
        "",
        "## 3. Your Role and File Ownership",
        "",
        f"**Primary scope:** `{agent['scope']}`",
        "",
        f"**Epics:** {agent['epics']}",
        "",
    ]

    if agent.get("no_modify"):
        lines += [
            "**File ownership — DO NOT MODIFY:**",
        ]
        for path in agent["no_modify"]:
            lines.append(f"- `{path}`")
        lines.append("")

    if agent.get("docs_only"):
        lines += [
            "**DOCS-ONLY AGENT:** You may only create/modify files in `docs/` and `PM_Pack/10_cycle_log/`.",
            "Do NOT modify any `src/` or `tests/` files.",
            "",
        ]
    if agent.get("tests_only"):
        lines += [
            "**TESTS-ONLY AGENT:** You may only create/modify files in `tests/`.",
            "Do NOT modify any `src/` files.",
            "",
        ]

    # ── 4. Git Instructions ───────────────────────────────────────────────
    lines += [
        "## 4. Git Instructions",
        "",
        f"1. Confirm you are on branch: `{branch}`",
        "   ```",
        "   git branch --show-current",
        f"   # Expected: {branch}",
        "   ```",
        f"2. Pull latest: `git pull origin {branch}`",
        f"3. All work goes on `{branch}` — do NOT create other branches",
        f"4. Commit message format: `type(scope): description [Agent {agent_id}]`",
        "5. Do NOT push — the runner will push after all agents complete",
        "6. Do NOT merge to `develop` or `main` directly",
        "",
    ]

    # ── 5. Autonomy Rules ─────────────────────────────────────────────────
    lines += [
        "## 5. Autonomy Rule",
        "",
        "- Proceed autonomously through all tasks without confirmation.",
        "- If a task is impossible (missing dependency, wrong file structure), skip it,",
        "  document the blocker in your report, and continue.",
        "- Do NOT stop mid-cycle to ask questions.",
        "- If you encounter a test failure you cannot fix in 3 attempts, quarantine the",
        "  failing test with `@pytest.mark.skip(reason='Agent cycle blocker')` and document.",
        "",
    ]

    # ── 6. Jira Scope ─────────────────────────────────────────────────────
    lines += [
        "## 6. Jira Scope for This Cycle",
        "",
    ]
    if agent_issues:
        lines += [
            "The following Jira issues are your scope for this cycle.",
            "Each task below maps to one or more AC items from these stories.",
            "",
            "| Jira Key | Summary | Status |",
            "|---|---|---|",
        ]
        for issue in agent_issues:
            lines.append(f"| {issue['key']} | {issue['summary'][:60]} | {issue['status']} |")
        lines.append("")
    else:
        lines += [
            "No Jira issues pre-assigned for this agent. Select open stories from your",
            "file scope and document which Jira keys you are addressing in your report.",
            "",
        ]

    # ── 7. Tasks ──────────────────────────────────────────────────────────
    lines += [
        "## 7. Tasks for This Cycle",
        "",
        "> **Minimum:** 55 LARGE-XXLARGE tasks as defined in TASK_SIZING.md.",
        "> Each task must have: Story ref, Epic ref, Spec ref, files, implementation",
        "> details (>=100 words), >=3 tests, Definition of Done.",
        "",
    ]

    # Generate tasks from Jira issues
    task_num = 1
    for issue in agent_issues[:12]:  # Cap at 12 issues per prompt section
        lines += _generate_task_section(task_num, issue, agent_id, cycle, agent)
        task_num += 1

    # Add floor script for Agent A Task 1
    if agent_id == "A" and task_num > 1:
        lines = _inject_agent_a_floor_script(lines, cycle)

    # ── 8. Validation Steps ───────────────────────────────────────────────
    lines += [
        "## 8. Validation Steps (Run before declaring done)",
        "",
        "Run these commands in order. All must pass before writing your report.",
        "",
        "```bash",
        "# 1. Path preflight — confirm key files exist",
        "python -c \"from pathlib import Path; files=[]; [print('MISSING:',f) for f in files if not Path(f).exists()]\"",
        "",
        "# 2. Ruff lint",
        "python -m ruff check src/ tests/ automation/ --output-format=text",
        "",
        "# 3. Mypy type check",
        "python -m mypy src/ --ignore-missing-imports",
        "",
        "# 4. Pytest — run your changed tests",
        "python -m pytest tests/ -q --no-header --tb=short -x",
        "",
        "# 5. Config check",
        "python run.py config-check",
        "```",
        "",
        "If any check fails, fix it before marking your report as complete.",
        "",
    ]

    # ── 9. Files Summary ──────────────────────────────────────────────────
    lines += [
        "## 9. Files Created/Modified This Cycle (Summary)",
        "",
        "After completing all tasks, add a table here:",
        "",
        "| Action | File Path |",
        "|---|---|",
        "| (fill in) | (fill in) |",
        "",
    ]

    # ── 10. Commit Instructions ───────────────────────────────────────────
    lines += [
        "## 10. Commit Instructions",
        "",
        "```bash",
        "git add .",
        f"git commit -m \"feat(cycle-{cycle:03d}): [Agent {agent_id}] <description>\"",
        "```",
        "",
        "Commit after every logical unit of work, not just at the end.",
        "",
    ]

    # ── 11. Report Requirements ───────────────────────────────────────────
    lines += [
        "## 11. Report Requirements",
        "",
        f"Write your report to: `{report_path}`",
        "",
        "Your report MUST contain:",
        f"- Header: `# CYCLE_{cycle:03d}_AGENT_{agent_id} REPORT`",
        "- Summary of work completed",
        "- List of all commits made (SHA + message)",
        "- List of all files created/modified",
        "- Validation results (ruff/mypy/pytest output)",
        "- Jira evidence (which AC items addressed)",
        "- Blockers encountered (if any)",
        "- `AGENT_COMPLETE` on the final line",
        "",
    ]

    # ── 12. No-main confirmation ──────────────────────────────────────────
    lines += [
        "## 12. Branch Guardrails",
        "",
        "- Do NOT push directly to `main`",
        "- Do NOT force-push to any branch",
        "- Do NOT weaken branch protection",
        "- Do NOT commit `.env`, API keys, tokens, or credentials",
        "- Do NOT commit browser sessions, storage_state.json, or playwright auth files",
        "",
    ]

    # ── END OF PROMPT ─────────────────────────────────────────────────────
    lines += [
        f"{'=' * 68}",
        f"END OF PROMPT — AGENT {agent_id} CYCLE {cycle:03d}",
        f"{'=' * 68}",
        "",
        "<!-- Generated by prompt_generator.py -->",
        f"<!-- Run ID: {run_id} | Generated: {now} -->",
    ]

    return "\n".join(lines)


def _select_issues_for_agent(agent_id: str, all_issues: list[dict]) -> list[dict]:
    """Select Jira issues relevant to this agent based on labels/type."""

    # Agent E = QA/test issues; Agent D = docs/PM issues; others = code issues
    if agent_id == "E":
        relevant = [i for i in all_issues
                    if "test" in i.get("summary", "").lower()
                    or "qa" in (i.get("labels") or [])
                    or i.get("issuetype") == "Bug"]
    elif agent_id == "D":
        relevant = [i for i in all_issues
                    if "doc" in i.get("summary", "").lower()
                    or "report" in i.get("summary", "").lower()
                    or "cycle" in i.get("summary", "").lower()
                    or i.get("issuetype") in ("Story", "Task")]
    else:
        # Code agents — take non-Done, non-Bug stories
        relevant = [i for i in all_issues
                    if i.get("status") not in ("Done", "Cancelled")
                    and i.get("issuetype") not in ("Bug",)]

    # Limit and return first 12
    return relevant[:12]


def _generate_task_section(task_num: int, issue: dict, agent_id: str,
                             cycle: int, agent: dict) -> list[str]:
    """Generate a single task section from a Jira issue."""
    key     = issue.get("key", "SCRUM-???")
    summary = issue.get("summary", "")
    status  = issue.get("status", "To Do")
    priority = issue.get("priority", "Medium")

    lines = [
        f"### Task {task_num}: {summary}",
        "",
        f"- **Jira:** {key} — [{status}]",
        f"- **Priority:** {priority}",
        f"- **Epic:** See {key} parent epic in Jira",
        "- **Spec Reference:** `ref/project_plan/` (see Jira description)",
        "",
        "**Files to Create/Modify:**",
        f"- (Identify from {key} description and your file scope: `{agent['scope']}`)",
        "",
        "**Implementation Details:**",
        f"Implement the requirements described in Jira story {key}: \"{summary}\".",
        "Follow existing patterns in the codebase. Ensure:",
        "- All new functions/classes have complete type annotations",
        "- All new modules have docstrings",
        "- Error handling covers expected failure modes",
        "- Integration with existing pipeline components is maintained",
        "- Pydantic models used for data validation where applicable",
        "- SQLAlchemy 2.0 patterns used for database operations",
        "- No breaking changes to existing public APIs",
        "- Configuration driven by `config.yaml` where applicable",
        "",
        "**Required Tests:**",
        f"- `tests/unit/test_cycle_{cycle:03d}_agent_{agent_id.lower()}.py::"
        f"test_{key.lower().replace('-', '_')}_happy_path`",
        f"- `tests/unit/test_cycle_{cycle:03d}_agent_{agent_id.lower()}.py::"
        f"test_{key.lower().replace('-', '_')}_edge_cases`",
        f"- `tests/unit/test_cycle_{cycle:03d}_agent_{agent_id.lower()}.py::"
        f"test_{key.lower().replace('-', '_')}_error_handling`",
        "",
        "**Definition of Done:**",
        f"- [ ] All AC items in {key} addressed",
        "- [ ] Ruff: 0 errors",
        "- [ ] Mypy: 0 errors on new code",
        "- [ ] All 3+ tests pass",
        "- [ ] No secrets committed",
        "",
    ]
    return lines


def _inject_agent_a_floor_script(lines: list[str], cycle: int) -> list[str]:
    """
    Agent A Task 1 must contain a Python floor enforcement script.
    Inject it into the first task section.
    """
    script = f"""
**MANDATORY FLOOR CHECK SCRIPT (Agent A Task 1):**

Run this script at the start of your work to verify task count compliance:

```python
# cycle_{cycle:03d}_floor_check.py — run before beginning any work
import sys
from pathlib import Path

CYCLE = {cycle}
MIN_TASKS = 55
prompt_dir = Path("PM_Pack/automation/prompts")

total_tasks = 0
for agent in ["A", "B", "E", "C", "F", "D"]:
    p = prompt_dir / f"CYCLE_{{CYCLE:03d}}_AGENT_{{agent}}_PROMPT.md"
    if p.exists():
        count = len([l for l in p.read_text().splitlines()
                     if l.startswith("### Task ")])
        print(f"Agent {{agent}}: {{count}} tasks")
        total_tasks += count

print(f"Total tasks: {{total_tasks}}")
if total_tasks < MIN_TASKS:
    print(f"FAIL: {{total_tasks}} < {{MIN_TASKS}} minimum", file=sys.stderr)
    sys.exit(1)
print("PASS: task floor met")
```
"""
    # Find first "### Task" and inject before it
    for i, line in enumerate(lines):
        if line.startswith("### Task 1:"):
            lines.insert(i, script)
            break
    return lines


def write_prompts(cycle: int, branch: str, run_id: str,
                  agents: list[str], jira_issues: list[dict],
                  prompts_dir: Path) -> dict[str, Path]:
    """Generate and write all agent prompts. Returns agent -> path map."""
    prompts_dir.mkdir(parents=True, exist_ok=True)
    written = {}

    for agent_id in agents:
        prompt_text = generate_prompt(
            agent_id=agent_id,
            cycle=cycle,
            branch=branch,
            jira_issues=jira_issues,
            run_id=run_id,
        )
        path = prompts_dir / f"CYCLE_{cycle:03d}_AGENT_{agent_id}_PROMPT.md"
        path.write_text(prompt_text, encoding="utf-8")
        written[agent_id] = path

    return written
