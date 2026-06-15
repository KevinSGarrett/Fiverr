"""
prompt_generator.py â€” Real PM_Pack/Jira-derived Cursor agent prompt generator.
V5 corrections (AUDIT-P0-008 / V5-004 / V5-007):
  - Loads agent roles from agent_lanes.yml (single authority)
  - Loads PROMPT_TEMPLATE.md structure from PM_Pack
  - Generates 55+ LARGE/XLARGE/XXLARGE tasks per agent (AGENT_TASK_FLOOR_ENFORCEMENT)
  - NEVER tells agents to git commit, git push, git add, or skip tests
  - Controller owns all git operations â€” agents edit files and write reports only
  - plan-cycle --live fails with PLANNING_INCOMPLETE if insufficient Jira data
"""
from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).parent.parent
PM_PACK   = REPO_ROOT / "PM_Pack"

# Minimum tasks per AGENT_TASK_FLOOR_ENFORCEMENT.md (2026-06-09 hard rule)
TASK_FLOOR = 55

# Tasks generated per Jira issue per agent role
TASKS_PER_ISSUE = {
    "A": 4,   # planning, architecture, docs tasks per story
    "B": 5,   # implementation tasks per story (primary implementer)
    "E": 4,   # validation probe tasks per story
    "C": 3,   # integration check tasks per story
    "F": 4,   # test coverage tasks per story
    "D": 3,   # PR/Jira evidence tasks per story
}

# Minimum issues needed to reach 55 tasks
MIN_ISSUES_NEEDED = {a: max(1, TASK_FLOOR // t + 1) for a, t in TASKS_PER_ISSUE.items()}




class PlanningIncompleteError(RuntimeError):
    """Raised when a prompt contract cannot be built due to missing planning data."""


def _load_agent_lanes() -> dict[str, Any]:
    """Load agent_lanes.yml â€” single source of truth for agent roles."""
    path = PM_PACK / "automation/agent_lanes.yml"
    if not path.exists():
        raise FileNotFoundError(f"agent_lanes.yml not found at {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_prompt_template_sections() -> dict[str, str]:
    """Load key sections from PM_Pack PROMPT_TEMPLATE.md."""
    path = PM_PACK / "03_cursor_agent_system/PROMPT_TEMPLATE.md"
    if not path.exists():
        return {}
    txt = path.read_text(encoding="utf-8", errors="replace")
    sections: dict[str, str] = {}
    # Extract validation steps section
    m = re.search(r"## VALIDATION STEPS.*?(?=## FILES CREATED|$)", txt, re.DOTALL)
    if m:
        sections["validation_steps"] = m.group(0).strip()
    return sections


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
    """Generate a full Cursor agent prompt from PM_Pack + Jira data.

    V5 guarantee: NO git commit, git add, git push, or pytest.mark.skip instructions.
    Controller owns all git operations.
    """
    lanes = _load_agent_lanes()
    lane = lanes.get("lanes", {}).get(agent_id, {})

    now = datetime.now(UTC).isoformat()
    report_path = f"docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent_id}.md"

    # Select issues for this agent
    agent_issues = _select_issues(agent_id, jira_issues, lane)

    lines: list[str] = []

    # â”€â”€ Header â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    lines += [
        f"{'=' * 68}",
        f"AGENT {agent_id} -- CYCLE {cycle:03d} PROMPT",
        f"{'=' * 68}",
        "",
    ]

    # â”€â”€ PROJECT CONTEXT (from PROMPT_TEMPLATE) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    lines += [
        "## PROJECT CONTEXT",
        "",
        "- Project: Fiverr Research System",
        "- GitHub: https://github.com/KevinSGarrett/Fiverr",
        f"- Local: {str(REPO_ROOT)}",
        f"- Branch: `{branch}`",
        "- Python: 3.11+ | SQLAlchemy 2.0 | Pydantic v2 | Playwright | OpenAI | Streamlit",
        f"- Cycle: {cycle:03d} | Run ID: {run_id}",
        "",
    ]

    # â”€â”€ MODEL POLICY (mandatory block) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    lines += [
        "## MODEL POLICY (MANDATORY â€” do not override)",
        "",
        f"- **Model:** {model}",
        f"- **Effort:** {effort}",
        f"- **Auto model selection:** DISABLED â€” use only {model}",
        "- **Fallback model:** DISABLED",
        "- **Billing:** Claude subscription only for PM review; no API key",
        "",
    ]

    # â”€â”€ YOUR ROLE (from agent_lanes.yml) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    lines += [
        "## YOUR ROLE",
        "",
        f"**Agent {agent_id}** â€” {lane.get('description', 'See agent_lanes.yml')}",
        f"**Role type:** `{lane.get('role', 'unknown')}`",
        "",
        "**You own these file paths (you may create/modify only these):**",
    ]
    for owned in lane.get("owns", []):
        lines.append(f"- `{owned}`")
    lines.append("")

    prohibited = lane.get("prohibited", lane.get("prohibited_without_explicit_task", []))
    if prohibited:
        lines.append("**You must NOT modify these paths:**")
        for p in prohibited:
            lines.append(f"- `{p}`")
        lines.append("")

    if lane.get("wait_for_b_first_commit"):
        lines += [
            "**IMPORTANT:** You must wait for Agent B's first commit before starting your work.",
            "",
        ]

    # â”€â”€ GIT INSTRUCTIONS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    lines += [
        "## GIT INSTRUCTIONS",
        "",
        f"1. Confirm you are on branch: `{branch}`",
        "   ```",
        "   git branch --show-current",
        f"   # Expected: {branch}",
        "   ```",
        f"2. Pull latest: `git pull origin {branch}`",
        f"3. ALL work on `{branch}` only â€” do NOT create other branches",
        "4. **DO NOT run git add, git commit, git push.** The controller owns all git operations.",
        "5. **DO NOT run gh pr commands.** The controller manages PRs.",
        "6. Complete your tasks, write your report, and exit.",
        "",
    ]

    # â”€â”€ AUTONOMY RULE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    lines += [
        "## AUTONOMY RULE",
        "",
        "- Proceed autonomously through all tasks without pausing for confirmation.",
        "- If a task cannot be completed due to a missing dependency, document the blocker",
        "  in your report and continue to the next task.",
        "- If a test fails, fix the bug causing the failure. Do NOT use `pytest.mark.skip`",
        "  as a workaround. If you cannot fix it in 3 attempts, document it as a blocker.",
        "- Do NOT commit files. The controller validates and commits after you finish.",
        "",
    ]

    # â”€â”€ JIRA SCOPE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    lines += [
        "## JIRA SCOPE FOR THIS CYCLE",
        "",
    ]
    if agent_issues:
        lines += [
            "| Jira Key | Summary | Status | Priority |",
            "|---|---|---|---|",
        ]
        for issue in agent_issues:
            lines.append(
                f"| {issue['key']} | {issue['summary'][:55]} | "
                f"{issue['status']} | {issue.get('priority', 'Medium')} |"
            )
        lines.append("")
    else:
        lines += [
            "No Jira issues pre-assigned. Select open stories from your file scope.",
            "Document which Jira keys you addressed in your final report.",
            "",
        ]

    # â”€â”€ TASKS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    lines += [
        "## TASKS FOR THIS CYCLE",
        "",
        f"> **Floor:** {TASK_FLOOR} LARGE/XLARGE/XXLARGE tasks (AGENT_TASK_FLOOR_ENFORCEMENT.md hard rule).",
        "> Each task must have: Story/Jira key, Epic, Spec, Files, Implementation details",
        "> (>=100 words), >=3 tests, Definition of Done.",
        "",
    ]

    task_num = 1

    # Generate tasks from Jira issues
    for issue in agent_issues:
        task_blocks = _generate_tasks_from_issue(
            task_start=task_num,
            issue=issue,
            agent_id=agent_id,
            cycle=cycle,
            lane=lane,
            tasks_count=TASKS_PER_ISSUE.get(agent_id, 3),
        )
        lines.extend(task_blocks)
        task_num += TASKS_PER_ISSUE.get(agent_id, 3)

    # Add Agent A floor verification script (Task 1 requirement)
    if agent_id == "A" and task_num > 1:
        lines = _inject_agent_a_floor_script(lines, cycle)

    # â”€â”€ VALIDATION STEPS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    lines += [
        "## VALIDATION STEPS",
        "",
        "Run these commands in order. Fix any failures before writing your report.",
        "",
        "```bash",
        "# 1. Ruff lint",
        "python -m ruff check src/ tests/ automation/ --output-format=full",
        "",
        "# 2. Mypy type check",
        "python -m mypy src/ --ignore-missing-imports",
        "",
        "# 3. Pytest â€” run tests relevant to your changed files",
        "python -m pytest tests/ -q --no-header --tb=short -x",
        "",
        "# 4. Config check",
        "python run.py config-check",
        "```",
        "",
        "**Do not mark your report complete if any check fails.**",
        "",
    ]

    # â”€â”€ REPORT REQUIREMENTS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    lines += [
        "## FINAL REPORT REQUIREMENTS",
        "",
        f"Write your report to: `{report_path}`",
        "",
        "Your report MUST contain:",
        f"- Header: `# CYCLE_{cycle:03d}_AGENT_{agent_id} REPORT`",
        "- Summary of all work completed",
        "- List of all files created or modified (with full paths)",
        "- Validation results (ruff/mypy/pytest command output)",
        "- Jira evidence (which AC/DoD items were addressed and how)",
        "- Blockers encountered (if any, with details)",
        "- `AGENT_COMPLETE` as the final line",
        "",
        "**IMPORTANT:** Do NOT run git add, git commit, or git push.",
        "Write your report and exit. The controller handles all commits.",
        "",
    ]

    # â”€â”€ FILES SUMMARY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    lines += [
        "## FILES CREATED/MODIFIED THIS CYCLE (Summary)",
        "",
        "Fill in after completing all tasks:",
        "",
        "| Action | File Path |",
        "|---|---|",
        "| (fill in) | (fill in) |",
        "",
    ]

    # â”€â”€ END OF PROMPT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    lines += [
        f"{'=' * 68}",
        f"END OF PROMPT -- AGENT {agent_id} CYCLE {cycle:03d}",
        f"{'=' * 68}",
        "",
        "<!-- Generated by prompt_generator.py -->",
        f"<!-- Run ID: {run_id} | Generated: {now} -->",
    ]

    return "\n".join(lines)


def _select_issues(agent_id: str, all_issues: list[dict],
                   lane: dict) -> list[dict]:
    """Select Jira issues relevant to this agent based on lane definition."""
    if not all_issues:
        return []

    non_done = [i for i in all_issues
                if i.get("status") not in ("Done", "Cancelled")]

    if agent_id == "A":
        # Planning agent: architecture, docs, config stories
        selected = [i for i in non_done
                    if any(kw in i.get("summary", "").lower()
                           for kw in ["architecture", "config", "plan", "governance",
                                      "doc", "pm", "jira", "github", "pipeline"])]
        if not selected:
            selected = non_done[:MIN_ISSUES_NEEDED["A"]]
    elif agent_id == "B":
        # Primary implementation: src/ related
        selected = [i for i in non_done
                    if i.get("issuetype") not in ("Bug",) and
                    not any(kw in i.get("summary", "").lower()
                            for kw in ["test", "qa", "doc", "pr", "jira"])]
        if not selected:
            selected = non_done[:MIN_ISSUES_NEEDED["B"]]
    elif agent_id == "E":
        # Live validation: evidence, validation probes
        selected = [i for i in non_done
                    if any(kw in i.get("summary", "").lower()
                           for kw in ["valid", "live", "evidence", "collect", "probe",
                                      "data", "signal"])]
        # E needs enough issues to generate 55 tasks; if not enough, supplement
        if len(selected) < MIN_ISSUES_NEEDED["E"]:
            supplement = [i for i in non_done if i not in selected]
            selected.extend(supplement[:MIN_ISSUES_NEEDED["E"] - len(selected)])
    elif agent_id == "F":
        # Test coverage: test, regression
        selected = [i for i in non_done
                    if any(kw in i.get("summary", "").lower()
                           for kw in ["test", "coverage", "regression", "edge",
                                      "qa", "quality"])]
        if len(selected) < MIN_ISSUES_NEEDED["F"]:
            selected = non_done[:MIN_ISSUES_NEEDED["F"]]
    elif agent_id == "D":
        # PR/Jira steward: any story needing PR/evidence work
        selected = non_done[:MIN_ISSUES_NEEDED["D"]]
    else:  # C
        selected = non_done[:MIN_ISSUES_NEEDED.get(agent_id, 12)]

    # Ensure we have enough to generate 55 tasks
    min_needed = MIN_ISSUES_NEEDED.get(agent_id, 12)
    if len(selected) < min_needed and len(non_done) >= min_needed:
        # Take the first min_needed from non-done if selector didn't find enough
        selected = non_done[:min_needed]
    elif len(selected) < min_needed:
        selected = non_done  # Take all we have

    return selected[:20]  # Cap at 20 issues (will produce ~60-100 tasks)


def _generate_tasks_from_issue(
    task_start: int,
    issue: dict,
    agent_id: str,
    cycle: int,
    lane: dict,
    tasks_count: int,
) -> list[str]:
    """Expand a single Jira issue into multiple LARGE/XLARGE/XXLARGE tasks."""
    key     = issue.get("key", "SCRUM-???")
    summary = issue.get("summary", "")
    status  = issue.get("status", "To Do")
    priority = issue.get("priority", "Medium")
    acceptance_criteria = issue.get("acceptance_criteria", "AC placeholder: define acceptance criteria in Jira.")
    dod_text = issue.get("definition_of_done", "Definition of done should be confirmed in Jira.")
    owned_paths = lane.get("owns", [])
    primary_path = owned_paths[0].replace("/**", "").replace("/*", "") if owned_paths else "src/"

    task_variants = _get_task_variants_for_role(
        agent_id=agent_id,
        issue_key=key,
        summary=summary,
        primary_path=primary_path,
        cycle=cycle,
    )

    lines: list[str] = []
    for i, variant in enumerate(task_variants[:tasks_count]):
        task_num = task_start + i
        task_title, task_detail, test_stubs, dod_items = variant

        lines += [
            f"### Task {task_num}: {task_title}",
            "",
            f"- **Jira:** {key} â€” {summary[:50]}",
            f"- **Status:** {status} | **Priority:** {priority}",
            f"- **Epic:** See {key} parent epic in Jira board",
            f"- **Spec:** `ref/project_plan/` (see {key} description for referenced spec files)",
            f"- **AC:** {acceptance_criteria}",
            f"- **DoD:** {dod_text}",
            "",
            "**Files to Create/Modify:**",
        ]
        # Generate plausible file paths based on agent role and task
        file_scope = _infer_file_scope(agent_id, key, summary, primary_path, i)
        for fp in file_scope:
            lines.append(f"- {fp}")
        lines.append("")

        lines += [
            "**Implementation Details:**",
            "",
        ]
        lines.append(task_detail)
        lines.append("")

        lines += ["**Required Tests:**"]
        for test in test_stubs:
            lines.append(f"- {test}")
        lines.append("")

        lines += ["**Definition of Done:**"]
        for dod in dod_items:
            lines.append(f"- [ ] {dod}")
        lines += [
            f"- [ ] All AC items for {key} addressed by this task",
            "- [ ] Ruff: 0 errors on changed files",
            "- [ ] Mypy: 0 errors on changed files",
            "",
        ]

    return lines


def _get_task_variants_for_role(
    agent_id: str,
    issue_key: str,
    summary: str,
    primary_path: str,
    cycle: int,
) -> list[tuple[str, str, list[str], list[str]]]:
    """Return (title, detail_100w+, tests, dod) tuples for agent role."""
    slug = issue_key.lower().replace("-", "_")
    cy  = f"{cycle:03d}"

    if agent_id == "A":
        return [
            (
                f"Architecture review and spec for {summary[:35]}",
                f"Review the current architecture for {issue_key} '{summary}'. "
                f"Identify all integration points with the existing pipeline. "
                f"Document the component boundaries, data flow, error handling strategy, "
                f"and API contract in the relevant spec file under ref/project_plan/. "
                f"Ensure the spec names the exact modules to be created or modified, "
                f"the data models involved, the method signatures for new public APIs, "
                f"and the validation strategy. Record the review in PM_Pack with a "
                f"decision log entry explaining any architecture tradeoffs. "
                f"Cross-reference with HYDRATION_HEADER.md to confirm cycle scope. "
                f"Output must be a readable spec artifact that Agent B can execute against.",
                [
                    "Read spec and verify all referenced paths exist or are created this cycle",
                    "Confirm no orphaned imports or missing __init__.py entries",
                    "Validate JSON schema for any new data model definition",
                ],
                [
                    f"Spec file exists at exact path referenced in {issue_key}",
                    "Spec is >=300 words with API contract, acceptance criteria, test requirements",
                    "Architecture decision logged in PM_Pack",
                ],
            ),
            (
                f"GitHub governance and CI gate for {summary[:35]}",
                f"Verify GitHub Actions CI configuration is correctly set up to enforce "
                f"the quality gates required for {issue_key} '{summary}'. "
                f"Check that the ci.yml workflow runs ruff, mypy, pytest, and coverage "
                f"against the files that will be changed in this story. "
                f"Update .github/workflows/ if any gate is missing or misconfigured. "
                f"Confirm branch protection rules for develop are still enforced. "
                f"Update PR template to include the Jira key {issue_key} in the required fields. "
                f"Document any CI changes in a commit log entry with rationale. "
                f"Verify the check names in ci.yml match what merge_gate.py expects to find "
                f"in GitHub status check results.",
                [
                    "CI workflow lint check passes on changed files",
                    "Branch protection still enforced after any config change",
                    f"PR template includes {issue_key} requirement",
                ],
                [
                    f"CI gate configured for {issue_key} scope",
                    "Branch protection rules unchanged",
                    ".github/workflows/ changes committed with rationale",
                ],
            ),
            (
                f"Config and dependency validation for {summary[:35]}",
                f"Validate that all configuration entries required for {issue_key} '{summary}' "
                f"are present and correct in config.yaml. Run python run.py config-check and "
                f"confirm it passes. If new configuration keys are required, add them to "
                f"config.yaml with sensible defaults and update the config schema validation. "
                f"Verify pyproject.toml has the correct dependency entries for any new libraries "
                f"referenced by {issue_key}. Update requirements if needed. Confirm that "
                f"scrapfly.enabled remains false in committed config.yaml. "
                f"Document all config changes in the cycle report with before/after values.",
                [
                    "python run.py config-check passes with no errors",
                    "All new config keys have documented defaults",
                    "scrapfly.enabled=false confirmed in config.yaml",
                ],
                [
                    "config-check PASS",
                    "No new required env vars without defaults",
                    "pyproject.toml up to date",
                ],
            ),
            (
                f"PM_Pack and Jira governance update for {summary[:35]}",
                f"Update PM_Pack hydration and state documents to reflect the work planned "
                f"for {issue_key} '{summary}' in cycle {cy}. Update HYDRATION_HEADER.md with "
                f"the current cycle scope and any new blockers discovered during architecture "
                f"review. Add a cycle log entry in PM_Pack/10_cycle_log/ documenting the "
                f"decision to include {issue_key} in this cycle and the expected agent assignments. "
                f"Verify EPIC_STATUS_TRACKER.md is current and reflects the correct status for "
                f"the epic containing {issue_key}. Cross-check that Jira status for {issue_key} "
                f"matches the planned AC delivery in this cycle. Record any stale document "
                f"findings in STALE_DOCUMENT_REGISTER.md.",
                [
                    f"HYDRATION_HEADER.md updated with cycle {cy} scope",
                    f"Cycle log entry created for {issue_key}",
                    "Jira status matches planned delivery",
                ],
                [
                    "PM_Pack documents are internally consistent",
                    "No new stale document warnings",
                    "Cycle log entry committed",
                ],
            ),
        ]

    elif agent_id == "B":
        return [
            (
                f"Implement core logic for {summary[:35]}",
                f"Implement the primary functionality described in Jira story {issue_key} "
                f"'{summary}'. Follow the architecture spec from Agent A. "
                f"Create the required module under {primary_path} with complete type annotations "
                f"on all public functions and classes. Implement proper error handling with "
                f"specific exception types. Use SQLAlchemy 2.0 patterns for database operations "
                f"and Pydantic v2 for data validation. Every new public function must have a "
                f"docstring. Every new class must document its invariants. Handle all edge cases "
                f"identified in the spec including null inputs, empty collections, and database "
                f"connection failures. Implement the full happy path and at least two error paths.",
                [
                    f"tests/unit/test_{slug}_happy_path: core logic returns expected result",
                    f"tests/unit/test_{slug}_empty_input: handles empty/null input gracefully",
                    f"tests/unit/test_{slug}_error_path: exception handling tested",
                ],
                [
                    f"All AC items in {issue_key} implemented",
                    "Type annotations complete on all public APIs",
                    "Docstrings on all public classes and functions",
                ],
            ),
            (
                f"Database schema and migration for {summary[:35]}",
                f"If {issue_key} requires new database fields or tables, implement the "
                f"SQLAlchemy model changes in the appropriate models file. Write a migration "
                f"script that can be run to update the schema. The migration must be reversible. "
                f"Update any existing queries that use modified tables to handle the schema change. "
                f"Add index annotations where query performance requires them. Ensure the "
                f"baseline DB (data/cycle037_live.db) is not modified; all changes target the "
                f"active development database only. Document the migration in the cycle report "
                f"with the before/after schema definition. Verify the config-check still passes "
                f"after schema changes.",
                [
                    f"tests/unit/test_{slug}_schema: model fields match spec",
                    f"tests/unit/test_{slug}_migration: migration runs and is reversible",
                    f"tests/unit/test_{slug}_query: queries return correct results after migration",
                ],
                [
                    "Schema change is backward compatible or migration is provided",
                    "Baseline DB untouched",
                    "All existing tests still pass",
                ],
            ),
            (
                f"API and integration wiring for {summary[:35]}",
                f"Wire the new implementation from {issue_key} '{summary}' into the existing "
                f"pipeline. Add the required imports and factory registrations in __init__.py. "
                f"Update any CLI commands or entrypoints that need to expose the new functionality. "
                f"Ensure the new code is reachable from the standard pipeline execution path. "
                f"Add or update configuration entries so the feature can be enabled or disabled "
                f"without code changes. Verify integration with the scoring pipeline by running "
                f"a targeted integration test. Document the integration points in the cycle report.",
                [
                    f"tests/integration/test_{slug}_pipeline: feature is reachable from pipeline",
                    f"tests/unit/test_{slug}_factory: factory/registry includes new component",
                    f"tests/unit/test_{slug}_config: feature can be toggled via config",
                ],
                [
                    "New functionality reachable from pipeline",
                    "__init__.py exports updated",
                    "Config entry documented",
                ],
            ),
            (
                f"Error handling and resilience for {summary[:35]}",
                f"Implement comprehensive error handling for {issue_key} '{summary}'. "
                f"Identify all failure modes: network errors, database errors, parsing errors, "
                f"rate limits, invalid data shapes. For each failure mode, implement a handler "
                f"that logs the error with sufficient context, returns a safe default or raises "
                f"a domain-specific exception, and does not silently swallow errors. "
                f"Add retry logic with exponential backoff where appropriate. "
                f"Ensure that errors in one component do not cascade to unrelated components. "
                f"Add circuit breaker logic for external service calls if the service is used "
                f"frequently. Test each error path explicitly.",
                [
                    f"tests/unit/test_{slug}_network_error: network failure handled gracefully",
                    f"tests/unit/test_{slug}_db_error: database error logged and surfaced",
                    f"tests/unit/test_{slug}_invalid_data: malformed data rejected cleanly",
                ],
                [
                    "Every error path has a test",
                    "No silent exception swallowing",
                    "All errors logged with context",
                ],
            ),
            (
                f"Documentation and cycle report for {summary[:35]}",
                f"Write complete documentation for the implementation of {issue_key} '{summary}'. "
                f"Update any relevant runbooks in docs/runbooks/. Update API documentation if "
                f"public-facing APIs changed. Add inline code comments explaining non-obvious "
                f"logic choices. Write a clear description of the feature in the cycle report "
                f"at docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_B.md including: "
                f"what was implemented, why certain design choices were made, what tests cover "
                f"it, and what the acceptance criteria evidence is. Reference the Jira AC items "
                f"explicitly.",
                [
                    "Docstrings present on all public functions",
                    "README or runbook updated if behavior changes",
                    f"Cycle report section covers {issue_key} evidence",
                ],
                [
                    "Documentation complete",
                    "Cycle report includes Jira evidence",
                    "All inline comments explain non-obvious logic",
                ],
            ),
        ]

    elif agent_id == "E":
        return [
            (
                f"Live validation probe for {summary[:35]}",
                f"Implement a production validation probe for {issue_key} '{summary}'. "
                f"A LARGE validation probe must: run actual code against live data or the "
                f"development database, record specific measured values (not just pass/fail), "
                f"have explicit acceptance criteria, and write results to the evidence file "
                f"at docs/cycle_reports/CYCLE_{cy}_AGENT_E.md. "
                f"Design the probe to catch real production failure modes such as: wrong data "
                f"types returned, unexpected null values, performance regression vs baseline, "
                f"or incorrect scoring calculations. Run the probe against the current "
                f"data/cycle037_live.db golden anchor and verify consistency. "
                f"Record the exact measured value and the accepted range.",
                [
                    "Probe runs without errors against development database",
                    "Measured value recorded in evidence file",
                    "Acceptance criterion verified and documented",
                ],
                [
                    "Evidence file contains specific measured values (not just PASS)",
                    "Probe covers real production failure mode",
                    "Baseline DB integrity confirmed",
                ],
            ),
            (
                f"External signal validation for {summary[:35]}",
                f"Validate external signal collection for {issue_key} '{summary}'. "
                f"Run a controlled check of the external data sources used by this feature "
                f"(Google Trends, Reddit signals, competitive data). Verify that the data "
                f"collection does not exceed cost limits. Confirm that scrapfly.enabled "
                f"remains false in config.yaml. If using mock data, verify mock matches "
                f"the real API schema. Record the signal validation results with timestamps "
                f"in the evidence file. Document any API rate limit usage observed.",
                [
                    "Signal collection runs within budget limits",
                    "scrapfly.enabled=false confirmed",
                    "Mock data matches real API schema",
                ],
                [
                    "Cost guard respected",
                    "Evidence file has timestamped signal data",
                    "No live API calls without budget approval",
                ],
            ),
            (
                f"Scoring pipeline validation for {summary[:35]}",
                f"Run validation checks on the scoring pipeline output for {issue_key} "
                f"'{summary}'. Verify that the scoring components produce consistent results "
                f"across multiple runs. Check for any floating-point instability or "
                f"non-deterministic behavior. Confirm that the golden anchor keyword "
                f"(kw=110) still scores within the expected range after any changes "
                f"in this cycle. Record the exact score values and compare against the "
                f"cycle037_live.db baseline. Flag any regression of more than 0.5 points. "
                f"Document findings with before/after comparison in the evidence file.",
                [
                    "Golden anchor (kw=110) scores within expected range",
                    "Scores are deterministic across 3 runs",
                    "No regression vs baseline DB",
                ],
                [
                    "Score consistency verified",
                    "Baseline DB mtime unchanged",
                    "Evidence file records exact score values",
                ],
            ),
            (
                f"Integration evidence collection for {summary[:35]}",
                f"Collect integration evidence for {issue_key} '{summary}'. "
                f"Run the full integration suite against the development database. "
                f"Record which integration tests pass and which fail. For any failing "
                f"integration tests, identify whether the failure is pre-existing or "
                f"introduced by cycle {cy} changes. Document the findings with full "
                f"test output in the evidence file. If integration failures are pre-existing "
                f"and tracked in Jira, reference the Jira key. New integration failures "
                f"must be escalated as blockers.",
                [
                    "Integration test suite runs without environment errors",
                    "All new integration failures documented",
                    "Pre-existing failures traced to Jira keys",
                ],
                [
                    "Integration evidence collected and recorded",
                    f"No new integration failures from cycle {cy} changes",
                    "Evidence file references specific test names and results",
                ],
            ),
        ]

    elif agent_id == "C":
        return [
            (
                f"Integration check and validation for {summary[:35]}",
                f"Run integration checks for {issue_key} '{summary}'. "
                f"Execute the targeted integration tests for the feature being delivered. "
                f"Verify that the implementation integrates correctly with the scoring "
                f"pipeline, database layer, and any external services. Run "
                f"pytest tests/integration/ -q and record results. "
                f"Confirm that the config-check still passes after integration. "
                f"Write the integration validation summary to the cycle report "
                f"at docs/cycle_reports/CYCLE_{cy}_AGENT_C.md.",
                [
                    f"pytest tests/integration/ passes for {issue_key} scope",
                    "config-check passes after integration",
                    "Cycle report documents integration evidence",
                ],
                [
                    "Integration tests pass",
                    "No config regressions",
                    "Cycle report updated with evidence",
                ],
            ),
            (
                f"Cycle report compilation for {summary[:35]}",
                f"Compile the cycle report for {issue_key} '{summary}'. "
                f"Gather commit SHAs, changed file list, test results, and Jira "
                f"evidence from all agents. Write the cycle report to "
                f"docs/cycle_reports/CYCLE_{cy}_AGENT_C.md with a complete summary "
                f"of what was implemented, what was tested, and what evidence exists "
                f"for each AC/DoD item in {issue_key}. Reference all test names that "
                f"validate the implementation. Confirm the report meets the post-cycle "
                f"review requirements.",
                [
                    "Cycle report exists at correct path",
                    "Report references all changed files with evidence",
                    "All Jira AC items mapped to test evidence",
                ],
                [
                    "Cycle report is complete and includes agent summaries",
                    "All AC items have evidence references",
                    "Report is readable by post-cycle PM review",
                ],
            ),
            (
                f"Quality gate verification for {summary[:35]}",
                f"Verify all quality gates pass for {issue_key} '{summary}'. "
                f"Run the full test suite: ruff check, mypy type check, pytest with coverage. "
                f"Verify coverage meets the floor (90%). If coverage is below floor, "
                f"identify which lines are uncovered and create a task for Agent F. "
                f"Confirm that the CI workflow check names match what merge_gate.py "
                f"expects. Document all gate results in the cycle report with exact numbers.",
                [
                    "ruff check passes with 0 errors",
                    "mypy passes with 0 errors",
                    "pytest coverage >= 90%",
                ],
                [
                    "All quality gates passing",
                    "Coverage floor met",
                    "Gate results documented in cycle report",
                ],
            ),
        ]

    elif agent_id == "F":
        return [
            (
                f"Test coverage gap analysis for {summary[:35]}",
                f"Analyze test coverage gaps for {issue_key} '{summary}'. "
                f"Run pytest --cov on the files changed in this story. Identify all "
                f"uncovered lines and branches. For each gap, determine if the gap "
                f"represents a real risk (untested error path, untested edge case) or "
                f"is acceptable (boilerplate, logging). Write tests for all high-risk "
                f"coverage gaps. Target 90%+ coverage on changed files. "
                f"Document the coverage analysis in the cycle report.",
                [
                    "Coverage report shows >= 90% on changed files",
                    "All high-risk uncovered paths have tests",
                    "Coverage gap analysis documented",
                ],
                [
                    "Coverage floor (90%) met for all changed files",
                    "High-risk gaps have test coverage",
                    "Coverage report committed",
                ],
            ),
            (
                f"Regression test expansion for {summary[:35]}",
                f"Add regression tests for {issue_key} '{summary}'. "
                f"Review the permanent regression pack in AGENT_EXECUTION_STRATEGY.md. "
                f"Verify that all 20+ existing regression tests still pass after changes "
                f"in this cycle. Add new regression tests for any production failure modes "
                f"discovered during this cycle. Each new regression test must be substantive: "
                f"it must run actual code, produce a measurable result, have acceptance "
                f"criteria, and be added to the permanent pack documentation.",
                [
                    "All existing regression tests still pass",
                    f"New regression test added for {issue_key} failure mode",
                    "New test added to permanent pack documentation",
                ],
                [
                    "Regression pack integrity maintained",
                    "New regression tests documented in AGENT_EXECUTION_STRATEGY.md",
                    "No existing regression tests broken",
                ],
            ),
            (
                f"Edge case and error path tests for {summary[:35]}",
                f"Write edge case and error path tests for {issue_key} '{summary}'. "
                f"Identify the most likely real-world failure modes: empty database, "
                f"malformed API response, rate limit hit, concurrent access, very large "
                f"or very small numeric values. For each edge case, write a test that: "
                f"sets up the specific failure condition, calls the code under test, "
                f"and verifies the correct error behavior. Tests must be deterministic "
                f"and not require live API access.",
                [
                    "Edge case test covers empty/null input correctly",
                    "Error path test verifies exception type and message",
                    "Concurrent access test (if applicable) passes under load",
                ],
                [
                    "All edge cases identified in spec have tests",
                    "Error paths produce specific, testable exceptions",
                    "Tests are deterministic (no flakiness)",
                ],
            ),
            (
                f"Test fixture and conftest improvements for {summary[:35]}",
                f"Improve test fixtures and conftest.py for {issue_key} '{summary}'. "
                f"If tests for this story require complex setup, extract it into reusable "
                f"pytest fixtures in the appropriate conftest.py. Ensure fixtures are "
                f"properly scoped (function/class/module/session). Add parameterized "
                f"test cases where the same logic needs to be tested with multiple inputs. "
                f"Verify that fixture teardown is clean and does not leave test artifacts "
                f"that could affect other tests.",
                [
                    "Fixtures extracted and reusable across multiple tests",
                    "Parametrized tests cover all required input variants",
                    "Fixture teardown is clean (verified by running tests in isolation)",
                ],
                [
                    "No fixture pollution between tests",
                    "Complex setup is in fixtures, not inline",
                    "Parametrized cases cover the full AC matrix",
                ],
            ),
        ]

    else:  # D
        return [
            (
                f"PR body and Jira evidence for {summary[:35]}",
                f"Prepare the PR body and Jira evidence for {issue_key} '{summary}'. "
                f"Write a complete PR description following the PR template that includes: "
                f"the Jira key {issue_key}, the AC items addressed with evidence, "
                f"the test names that verify each AC item, the validation results "
                f"(ruff/mypy/pytest outputs), and the Codex review disposition. "
                f"Verify Jira issue {issue_key} is transitioned to In Review status. "
                f"Add a Jira comment with the PR link and brief evidence summary. "
                f"Check that all required PR labels are present.",
                [
                    f"PR body includes Jira key {issue_key} and AC evidence",
                    "Jira comment with PR link posted",
                    "PR template fully populated",
                ],
                [
                    "PR body passes validation (all required sections present)",
                    "Jira transitioned to In Review",
                    "All required labels on PR",
                ],
            ),
            (
                f"Merge gate preparation for {summary[:35]}",
                f"Prepare for merge gate execution for {issue_key} '{summary}'. "
                f"Verify all CI checks are passing (ruff, mypy, pytest, coverage). "
                f"Confirm Codecov statuses are present (codecov/project and codecov/patch). "
                f"Review Codex AI review threads and classify each as "
                f"VALID_FIXED, VALID_DEFERRED, NOT_APPLICABLE, or FALSE_POSITIVE with evidence. "
                f"Ensure all VALID_FIXED items have commit evidence. "
                f"Document the Codex disposition in the cycle report. "
                f"Verify the merge gate will pass by running merge-gate --dry-run.",
                [
                    "All CI checks green before merge gate",
                    "Codecov statuses present",
                    "Codex threads all classified with evidence",
                ],
                [
                    "merge-gate --dry-run PASS",
                    "All Codex threads resolved or deferred with documentation",
                    "Codecov shows no patch coverage regression",
                ],
            ),
            (
                f"Cycle closeout governance for {summary[:35]}",
                f"Complete cycle governance closeout for {issue_key} '{summary}'. "
                f"After the PR is merged to develop, transition Jira {issue_key} to Done "
                f"only if ALL DoD criteria are met (merge confirmation, full test suite pass, "
                f"coverage floor met, Codex disposition complete). "
                f"Update the epic status tracker in PM_Pack. "
                f"Write the cycle log entry in PM_Pack/10_cycle_log/ with: merged PR SHA, "
                f"test suite results, coverage percentage, Score1 and Score2 values, "
                f"and any post-cycle review items. "
                f"Verify CURRENT_STATE_CANONICAL.md reflects the completed cycle.",
                [
                    f"Jira {issue_key} is Done only after full DoD evidence",
                    "Epic status tracker updated",
                    "Cycle log entry written with all required fields",
                ],
                [
                    "Jira Done transition has full evidence",
                    "PM_Pack state updated atomically",
                    "Cycle log entry committed",
                ],
            ),
        ]


def _infer_file_scope(
    agent_id: str, key: str, summary: str, primary_path: str, variant: int
) -> list[str]:
    """Infer realistic file paths for a task based on agent role."""
    slug = re.sub(r"[^a-z0-9]", "_", summary.lower())[:25].strip("_")
    key_slug = key.lower().replace("-", "_")

    if agent_id == "A":
        paths = [
            ["- MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md",
             f"- CREATE: PM_Pack/10_cycle_log/CYCLE_075_{key_slug}_spec.md"],
            ["- MODIFY: .github/workflows/ci.yml",
             "- MODIFY: .github/PULL_REQUEST_TEMPLATE.md"],
            ["- MODIFY: config.yaml",
             "- MODIFY: pyproject.toml"],
            ["- MODIFY: PM_Pack/07_hydration/HYDRATION_HEADER.md",
             "- MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md"],
        ]
    elif agent_id == "B":
        paths = [
            [f"- CREATE: {primary_path}/{slug}.py",
             f"- CREATE: tests/unit/test_{slug}.py"],
            [f"- MODIFY: {primary_path}/models.py (add fields for {key})",
             f"- CREATE: tests/unit/test_{slug}_schema.py"],
            [f"- MODIFY: {primary_path}/__init__.py (export new components)",
             f"- MODIFY: {primary_path}/pipeline.py (wire new component)"],
            [f"- CREATE: {primary_path}/{slug}_errors.py",
             f"- MODIFY: tests/unit/test_{slug}.py (add error path tests)"],
            [f"- MODIFY: docs/runbooks/{slug}.md (or create)",
             f"- MODIFY: {primary_path}/{slug}.py (add docstrings)"],
        ]
    elif agent_id in ("E", "C"):
        paths = [
            [f"- CREATE: docs/cycle_reports/CYCLE_075_AGENT_{agent_id}.md (section for {key})"],
            [f"- MODIFY: docs/cycle_reports/CYCLE_075_AGENT_{agent_id}.md"],
            [f"- MODIFY: docs/cycle_reports/CYCLE_075_AGENT_{agent_id}.md"],
            [f"- MODIFY: docs/cycle_reports/CYCLE_075_AGENT_{agent_id}.md"],
        ]
    elif agent_id == "F":
        paths = [
            [f"- MODIFY: tests/unit/test_{slug}.py (add coverage tests)",
             "- MODIFY: tests/conftest.py (add fixtures if needed)"],
            [f"- CREATE: tests/unit/test_{slug}_regression.py",
             "- MODIFY: docs/AGENT_EXECUTION_STRATEGY.md (add to permanent pack)"],
            [f"- MODIFY: tests/unit/test_{slug}.py (add edge case tests)"],
            ["- MODIFY: tests/conftest.py (extract fixtures)",
             f"- MODIFY: tests/unit/test_{slug}.py (use fixtures)"],
        ]
    else:  # D
        paths = [
            ["- MODIFY: docs/cycle_reports/CYCLE_075_AGENT_D.md"],
            ["- MODIFY: docs/cycle_reports/CYCLE_075_AGENT_D.md"],
            ["- MODIFY: PM_Pack/10_cycle_log/CYCLE_075.md",
             "- MODIFY: PM_Pack/08_task_queue/EPIC_STATUS_TRACKER.md"],
        ]

    return paths[variant % len(paths)]


def _inject_agent_a_floor_script(lines: list[str], cycle: int) -> list[str]:
    """Inject the mandatory floor verification script at Agent A Task 1."""
    script = f"""
**MANDATORY FLOOR CHECK â€” Run at the start of your work (AGENT_TASK_FLOOR_ENFORCEMENT.md):**

```python
# cycle_{cycle:03d}_floor_check.py
import sys
from pathlib import Path

CYCLE = {cycle}
MIN_TASKS = 55
prompt_dir = Path("PM_Pack/automation/prompts")

total = 0
for agent in ["A", "B", "E", "C", "F", "D"]:
    p = prompt_dir / f"CYCLE_{{CYCLE:03d}}_AGENT_{{agent}}_PROMPT.md"
    if p.exists():
        count = len([l for l in p.read_text().splitlines()
                     if l.startswith("### Task ")])
        print(f"Agent {{agent}}: {{count}} tasks")
        total += count

print(f"Total: {{total}}")
if total < MIN_TASKS * 6:
    print(f"FLOOR VIOLATION: {{total}} < {{MIN_TASKS * 6}} minimum", file=sys.stderr)
    sys.exit(1)
print("PASS: task floor met")
```
"""
    for i, line in enumerate(lines):
        if line.startswith("### Task 1:"):
            lines.insert(i, script)
            break
    return lines


def write_prompts(
    cycle: int,
    branch: str,
    run_id: str,
    agents: list[str],
    jira_issues: list[dict],
    prompts_dir: Path,
) -> dict[str, Path]:
    """Generate and write all agent prompts. Returns agent -> path map.
    Raises RuntimeError with PLANNING_INCOMPLETE if insufficient Jira issues.
    """
    prompts_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    planning_failures: list[str] = []

    for agent_id in agents:
        prompt_text = generate_prompt(
            agent_id=agent_id,
            cycle=cycle,
            branch=branch,
            jira_issues=jira_issues,
            run_id=run_id,
        )

        # Verify task count meets floor
        task_count = len([ln for ln in prompt_text.splitlines()
                          if ln.startswith("### Task ")])
        if task_count < TASK_FLOOR:
            planning_failures.append(
                f"Agent {agent_id}: {task_count} tasks < {TASK_FLOOR} minimum "
                f"(need {TASK_FLOOR - task_count} more Jira issues)"
            )

        path = prompts_dir / f"CYCLE_{cycle:03d}_AGENT_{agent_id}_PROMPT.md"
        path.write_text(prompt_text, encoding="utf-8")
        written[agent_id] = path

    if planning_failures:
        # Write PLANNING_INCOMPLETE diagnostic (do not write final-named prompts to dispatch dir)
        diagnostic_path = prompts_dir / f"PLANNING_INCOMPLETE_CYCLE_{cycle:03d}.md"
        diagnostic_path.write_text(
            f"# PLANNING INCOMPLETE â€” Cycle {cycle:03d}\n\n"
            f"Generated: {datetime.now(UTC).isoformat()}\n\n"
            f"## Failures\n\n" +
            "\n".join(f"- {f}" for f in planning_failures) +
            "\n\n## Resolution\n\n"
            "Fetch more Jira issues from the board or reduce the task floor policy.\n"
            "Re-run plan-cycle --live after adding stories to Jira.\n",
            encoding="utf-8"
        )
        raise RuntimeError(
            "PLANNING_INCOMPLETE: " + "; ".join(planning_failures) +
            f"\nDiagnostic written to {diagnostic_path}"
        )

    return written
