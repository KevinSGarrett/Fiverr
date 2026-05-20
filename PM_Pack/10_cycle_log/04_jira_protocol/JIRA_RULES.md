# JIRA BOARD MANAGEMENT RULES
# Updated: Cycle 019

---

## Core Principles
1. Jira is the single source of truth for task status
2. Every story in the project must have a Jira ticket — no orphan work
3. Jira is updated EVERY cycle without exception
4. Jira comments are the audit trail for what happened and when
5. GitHub and Jira are connected — use Jira keys in all PR titles, branch names, and commit messages

---

## Board Connection

| Field | Value |
|---|---|
| Board URL | https://kevinsgarrett.atlassian.net/jira/software/projects/SCRUM/boards |
| Cloud ID | eae77257-a572-4e19-b746-8b184ba2d01f |
| Project key | SCRUM |
| GitHub integration | Live — KevinSGarrett/Fiverr backfilled from 2025-11-13 |

Including a Jira key (e.g., SCRUM-136) anywhere in a branch name, commit message, or PR title/body will automatically create a development link visible on the Jira issue's Development panel. Always use exact Jira keys.

---

## Board Structure

### Issue Types
| Type | Maps To | Usage |
|---|---|---|
| Epic | Epic 01-10 | One epic issue per epic (SCRUM-16 through SCRUM-25) |
| Story | Story S{N}.{N} | One story issue per story (105 total) |
| Task | Sub-task or governance task | Sub-tasks under stories, or meta tasks |
| Bug | Discovered bugs | Created during review |
| Spike | Research tasks | Investigation before implementation |

### Statuses
| Status | Meaning |
|---|---|
| Backlog | Not started, not assigned to any sprint |
| To Do | Assigned to current sprint, waiting for agent |
| In Progress | Agent is actively working on it |
| In Review | Agent work complete — PM is reviewing |
| Done | Completed, tested, merged to develop |
| Blocked | Cannot proceed — dependency or issue |

---

## Label System (Cycle 019 — 61 Labels Deployed)

All 61 labels are deployed on GitHub and must be mirrored in Jira label fields.

### Type Labels (use exactly one per issue)
`type:feature` | `type:fix` | `type:test` | `type:chore` | `type:docs` | `type:refactor` | `type:perf` | `type:ci` | `type:security` | `type:spike` | `type:revert`

### Priority Labels (use exactly one)
`priority:P1-critical` | `priority:P2-high` | `priority:P3-medium` | `priority:P4-low`

### Scope Labels (use exactly one — matches epic)
`scope:epic01` through `scope:epic10`

### Agent Labels (use exactly one)
`agent:1-infrastructure` | `agent:2-collection` | `agent:3-analysis` | `agent:4-dashboard` | `agent:pm`

### Size Labels (auto-calculated by PR checks, but set manually on Jira)
`size:XS` (<50 lines) | `size:S` (50-149) | `size:M` (150-299) | `size:L` (300-499) | `size:XL` (500-999) | `size:XXL` (1000+)

### Status Labels
`status:blocked` | `status:needs-review` | `status:in-progress` | `status:ready-to-merge` | `status:wont-fix` | `status:duplicate` | `status:stale`

### Risk Labels
`risk:breaking-change` | `risk:data-migration` | `risk:performance` | `risk:security`

### Override Labels
`override:large-pr` — bypasses the 1000-line PR size gate (use for audit/batch PRs only)
`override:skip-smoke` — bypasses smoke gate
`override:force-merge` — PM-authorized force merge

---

## Sprint Protocol

### Creating a New Sprint
- Name format: `Cycle {NNN}` (e.g., Cycle 019, Cycle 020)
- Duration: Not fixed — use manual start/end based on cycle work
- Stories to assign: All stories planned for the cycle

### Assigning Stories to Sprint
Every story worked in a cycle must be moved to the active sprint in Jira before agent work begins.

### Sprint Closure
At cycle end: all Done stories remain in sprint. Incomplete stories are moved to Backlog or next sprint based on PM decision.

---

## fixVersion

- Current version: `v0.1.0 - Foundation`
- Assigned to: 7 E01 stories (S1.1–S1.7)
- New versions: Create when a new milestone release is planned
- Do NOT assign a fixVersion to stories that are not part of the next planned release

---

## Mandatory Jira Actions Per Cycle

### Planning Phase (before agent work begins)
1. Confirm active sprint exists — create Cycle {NNN} sprint if needed
2. Move selected stories: Backlog → To Do
3. Assign agent labels (agent:1 through agent:4)
4. Assign scope, type, priority, and risk labels
5. Add planning comment with branch name and cycle number
6. Verify sprint assignment

### Review Phase (after agent work)
7. Move completed stories: In Progress → In Review → Done
8. Move incomplete stories: In Progress → To Do (with rework comment)
9. Move blocked stories: → Blocked (with blocker description)
10. Add review comment: [Cycle NNN] Agent X | Branch: cycle/NNN/integration | PR: #N | Evidence: ...
11. Update story progress on parent epic ticket
12. Update epic progress percentage

### Every Cycle (mandatory regardless)
13. Verify no ticket stuck in wrong status from prior cycles
14. Add cycle summary comment on active epic tickets
15. Create Bug tickets for issues found during review
16. Verify GitHub Development panel links appear on updated stories
17. Ensure no ticket left in intermediate state at cycle close

---

## Comment Format (mandatory)

Every Jira comment added by an agent or PM must follow this format:

```
[Cycle 019] Agent A | Branch: cycle/019/integration | PR: #16

Summary: {what was done}

Files changed:
- src/utils/datetime.py (created)
- src/utils/validation.py (created)

AC status:
- AC-1.6.1: PASS — format_duration tests passing
- AC-1.6.2: PASS — parse_fiverr_date tests passing

DoD status: PARTIAL / COMPLETE
Confidence: 92/100
```

---

## Jira-GitHub Link Rules

1. Every branch name must contain the relevant Jira key: `feature/epic01/SCRUM-136-db-init`
2. Every PR title must contain the Jira key in the body (not required in title, but preferred)
3. Every commit that closes a story should include the key: `fix(models): SCRUM-136 add FK constraints`
4. The GitHub Development panel on each Jira story will automatically show linked PRs and commits
5. Do NOT add manual "PR: #N" text to Jira if the Development panel already shows it — avoid duplication

---

## Anti-Patterns (Never Do These)

- Never mark a broad story Done without full DOD satisfied
- Never use "update relevant tickets" — cite exact keys
- Never leave a ticket In Progress at cycle close
- Never create a Jira story for work that is already Done without evidence
- Never skip the sprint assignment step
- Never use old agent labels (agent:A, agent:B, etc.) — use agent:1 through agent:4 format
