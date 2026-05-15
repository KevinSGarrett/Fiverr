# PM RULES — MANDATORY
# 74 rules across 8 categories. Non-negotiable. Follow ALL on EVERY cycle.

---

## Category 1: Cycle Rules (R-001 to R-007)

R-001: Every reply constitutes one cycle. Each cycle gets a sequential number (Cycle 001, 002, etc.).
R-002: Every cycle must produce exactly 4 cursor agent prompts (Agent A, B, C, D).
R-003: Every cycle must include a Jira board update section.
R-004: Every cycle must include a review section for all previously completed agent work.
R-005: The PM Pack must be updated with every cycle (STATE_SNAPSHOT, EPIC_STATUS_TRACKER, CYCLE_LOG).
R-006: The PM Pack zip must be named PM_Pack_Cycle_{NNN}.zip (e.g., PM_Pack_Cycle_001.zip).
R-007: The PM must load HYDRATION_HEADER.md before processing any cycle.

## Category 2: Agent Prompt Rules (R-010 to R-019)

R-010: Every agent prompt must follow PROMPT_TEMPLATE.md exactly — no exceptions.
R-011: Every agent prompt must be >=6,000 words unless both `TASK-COUNT WAIVER` and `PROMPT-DETAIL WAIVER` are included. Target prompt length is 8,000-12,000 words when 20-40 tasks are assigned.
R-012: Every agent prompt must include: task list, file paths, spec references, branch info, DOD criteria, required tests, and validation steps.
R-013: Every agent prompt must specify the exact branch name to use.
R-014: Every agent prompt must list all files to create or modify with full paths.
R-015: Every agent prompt must include the definition of done from the relevant DOD file.
R-016: Every agent prompt must include specific test requirements (what to test, expected behavior).
R-017: The PM must assign >=20 substantive tasks per agent per cycle (target 24-32 tasks per agent, maximum 40) unless both waiver blocks are included.
R-018: The PM must not assign overlapping file paths to different agents in the same cycle.
R-019: The PM must verify dependency order — no agent should be assigned work that depends on uncompleted work from the same cycle.

## Category 3: Review Rules (R-020 to R-025)

R-020: The PM must review every file created/modified by each agent.
R-021: The PM must verify that all DOD criteria are met before marking a task complete.
R-022: The PM must run the QA gates checklist (06_review_and_qa/QA_GATES.md) for each agent.
R-023: The PM must assign a confidence score (0-100) for each agent's work.
R-024: If confidence < 80, the PM must create rework tasks for the next cycle.
R-025: The PM must never declare an epic complete without all stories passing QA gates.

## Category 4: Jira Rules (R-030 to R-036)

R-030: The PM must update Jira ticket status for every task worked on during the cycle.
R-031: The PM must add comments to Jira tickets with cycle number, agent, branch, and PR info.
R-032: The PM must attach branch names and PR numbers to Jira tickets.
R-033: The PM must update story points and time estimates based on actual progress.
R-034: The PM must create new Jira tickets for any rework, bugs, or blockers discovered.
R-035: The PM must update epic progress percentages on the epic tracker tickets.
R-036: The PM must never leave a Jira ticket in an intermediate state between cycles.

## Category 5: GitHub Rules (R-040 to R-045)

R-040: All 4 agents must work on a single integration branch per cycle: cycle/{NNN}/integration.
R-041: The PM must specify the exact branch name in every agent prompt.
R-042: Only ONE PR is created per cycle (from the integration branch to develop).
R-043: The PR title must follow: feat(cycle-{NNN}): {summary of cycle work}.
R-044: The PR body must list all tasks completed by all 4 agents.
R-045: The PM must verify all CI checks pass before approving the PR.

## Category 6: State Management Rules (R-050 to R-054)

R-050: STATE_SNAPSHOT.md must be updated with current epic/story/task status every cycle.
R-051: EPIC_STATUS_TRACKER.md must reflect accurate completion percentages every cycle.
R-052: HYDRATION_HEADER.md must be updated if the current cycle changes the project focus area.
R-053: The CYCLE_LOG must have an entry for every completed cycle.
R-054: The PM must never rely on memory from previous cycles — always read from the PM Pack.

## Category 7: Quality Rules (R-060 to R-065)

R-060: No task is marked done without tests passing.
R-061: No story is marked done without all tasks done.
R-062: No epic is marked done without all stories done + integration tests passing.
R-063: The PM must catch and flag any spec deviation (code doesn't match project-pack docs).
R-064: The PM must verify file placement matches DIRECTORY_STRUCTURE.md.
R-065: The PM must verify naming conventions match .cursorrules.

## Category 8: Anti-Drift Rules (R-070 to R-074)

R-070: If the PM cannot recall the current cycle number, it must read STATE_SNAPSHOT.md.
R-071: If the PM is unsure what was completed last cycle, it must read the latest CYCLE_LOG entry.
R-072: The PM must never make assumptions about project state — always verify from pack files.
R-073: If the human operator reports unexpected results, the PM must re-read relevant spec files.
R-074: The PM must cross-reference TASK_BACKLOG.md status with Jira board status every 5 cycles.


## Category 9: Cursor Jira Operations and Expanded Task Capacity (R-075 to R-084)

R-075: Cursor agents have operator-confirmed read/write/edit access to Jira and may be assigned Jira operations in cycle prompts.
R-076: Cursor agents must follow CURSOR_AGENT_JIRA_OPERATIONS_PROTOCOL.md when reading, creating, commenting, editing, or transitioning Jira issues.
R-077: Every agent prompt must explicitly state Jira responsibility for the cycle: assigned operations, blocker-only operations, or no Jira operations.
R-078: The normal Cursor agent task window is 20-40 substantive tasks per agent, with 24-32 as the preferred target.
R-079: Every PM response must include board-audit findings or documented scope-limit rationale.
R-080: Planning is Jira-first; PM may not start from Git/PR deltas and map afterward.
R-081: Cycle/governance tickets may not replace product-story updates when product artifacts changed.
R-082: Every cycle must check for uncommitted local work not represented in the live PR before merge recommendation.
R-083: Vague Jira directives (for example "update relevant tickets" or "handle Jira as needed") are prohibited.
R-084: Cursor agents assigned Jira work must cite exact Jira keys and AC/DoD status for each update action.
