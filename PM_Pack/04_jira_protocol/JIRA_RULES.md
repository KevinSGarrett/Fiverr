# JIRA BOARD MANAGEMENT RULES

---

## Core Principles
1. Jira is the single source of truth for task status
2. Every task in TASK_BACKLOG.md must have a Jira ticket
3. Jira is updated EVERY cycle without exception
4. Jira comments are the audit trail for what happened and when

## Board Structure

### Issue Types
| Type | Maps To | Usage |
|---|---|---|
| Epic | Epic 01-10 | One epic issue per epic |
| Story | Story S{N}.{N} | One story issue per story |
| Task | Task {N}.{N}.{N} | One task per item |
| Bug | Discovered bugs | Created during review |
| Spike | Research tasks | Investigation before implementation |

### Statuses
| Status | Meaning |
|---|---|
| Backlog | Not started, not assigned to a cycle |
| To Do | Assigned to a cycle, waiting for agent |
| In Progress | Agent is working on it (current cycle) |
| In Review | PM is reviewing agent's work |
| Done | Completed, tested, merged |
| Blocked | Cannot proceed — dependency or issue |

## Mandatory Jira Actions Per Cycle

### Planning Phase (before agent work)
1. Move selected tasks: Backlog -> To Do
2. Assign agent labels (agent:A/B/C/D)
3. Set Cycle field to current cycle number
4. Add planning comment with branch info

### Review Phase (after agent work)
5. Move completed tasks: In Progress -> In Review -> Done
6. Move failed tasks: In Progress -> To Do (with rework comment)
7. Move blocked tasks: -> Blocked (with description)
8. Add review comment with cycle results and confidence score
9. Update Story progress (X of Y tasks done)
10. Update Epic progress percentage

### Every Cycle (regardless)
11. Verify no ticket stuck in wrong status from prior cycles
12. Add cycle summary on active epic tickets
13. Create Bug tickets for issues found during review
14. Create Task tickets for rework
15. Ensure no ticket in intermediate state
