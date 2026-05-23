# Cycle 035 Prep Notes

## Context

- Prepared during Cycle 034 Agent D closure work.
- Purpose: provide Agent A (Cycle 035) with branch-cleanup execution inputs.

## Remote Cycle Branch Inventory

- Remote branch count (`git branch -r | Select-String "cycle/"`): **3**
- Observed remote cycle branches:
  - `origin/cycle/009/integration`
  - `origin/cycle/027/integration`
  - `origin/cycle/034/integration`

## Cleanup Candidate Set (Cycle 029 and older)

- Candidate branches (by cycle number <= 029):
  - `origin/cycle/009/integration` (unmerged vs `origin/develop` at prep time)
  - `origin/cycle/027/integration` (merged vs `origin/develop` at prep time)

## Required Cycle 035 Agent A Cleanup Procedure

- For each remote `cycle/*` branch older than 3 cycles:
  - Verify merged state against `origin/develop`.
  - If merged, delete remote branch.
  - If unmerged, do **not** delete; document blocker/owner and keep branch.
- Record exact commands, branch list before/after, and resulting branch count.

## Branches That Should Not Be Deleted

- `origin/cycle/034/integration` (current active cycle branch during this prep snapshot).
- Any branch that is unmerged at execution time (currently `origin/cycle/009/integration`).
