# Full-Board Jira AC/DoD-First Protocol

Version: Cycle 012

## Purpose

This protocol corrects the remaining Jira-process gap: the project must not merely update Jira after code changes. Jira must lead cycle planning.

## Binding rule

Every cycle must begin with a Jira board review before code work is assigned.

## Required Board Inventory (Before Any Code Planning)

Before agent prompts are generated, the PM or assigned Cursor agent must inspect:

1. active Sprint/board state where available;
2. all non-Done SCRUM issues or a documented paginated subset;
3. relevant Epics for the planned work;
4. product stories with acceptance criteria and DoD;
5. governance/process tickets;
6. stale In Progress tickets;
7. To Do tickets that should become active;
8. Done tickets that may have been prematurely closed;
9. duplicate/legacy/import issues;
10. unresolved cycle-specific tickets.

Inventory output must include: issue type counts, status counts, selected backlog slice criteria, and why any slice was used instead of full-board sweep.

## Required issue selection method

Work must be selected in this order:

1. Identify blocking PR/Codex/CI items.
2. Identify active Jira stories with matching AC/DoD.
3. Select product stories from Jira before implementation.
4. Select governance tasks only for process/governance work.
5. Map each planned file group to exact Jira keys.
6. Copy AC/DoD bullets into agent prompts.
7. Assign Jira update duty to PM or named Cursor agent.
8. Confirm no prompt starts from Git diff/PR-first planning.

## Required AC/DoD progress ledger

Every active story touched by a cycle must maintain a progress note containing:

- Jira key;
- story summary;
- parent epic;
- branch;
- PR number;
- files changed;
- AC bullets advanced;
- AC bullets not yet done;
- DoD bullets advanced;
- DoD bullets not yet done;
- tests/evidence;
- Codex status;
- CI/Codecov status;
- recommended Jira status;
- reason if not Done.

Ledger notes are mandatory for both product stories and governance tickets. Governance-only updates are never sufficient when product artifacts changed.

## Status rules

- To Do -> In Progress: work started or partial implementation exists.
- In Progress -> In Review: PR open, mapped, validated, and awaiting review/merge.
- In Review -> Done: only after merge and full source DoD satisfied.
- Done is prohibited for partial scaffolding, fixture-only, placeholder-only, dry-run-only, or governance-only progress on a product story.

## PR rules

Every PR body must include:

1. Jira AC/DoD table.
2. Changed file group table.
3. Product-story progress table.
4. Governance-ticket progress table.
5. Codex disposition table.
6. CI/Codecov table.
7. Uncommitted/local-discrepancy check.
8. Explicit "no-main" confirmation.

## Failure condition

A cycle fails governance if product code changes but Jira updates only governance/cycle tickets.

## Enforcement Notes

1. Cursor agents assigned Jira work may execute Jira updates directly.
2. Jira updates must cite exact issue keys and AC/DoD progress status.
3. Broad stories remain `In Progress` or `In Review` unless full source DoD is met.
