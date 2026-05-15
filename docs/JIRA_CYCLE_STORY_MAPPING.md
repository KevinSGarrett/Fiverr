# Jira Cycle Story Mapping Protocol

## Purpose

Every cycle must map changed files and executed agent tasks to Jira product stories, not only governance tickets. This protocol is mandatory for all cycle reports and PR bodies targeting `develop`.

## Mandatory Rule

- If any product path changes, the PR/cycle report must include at least one product Jira story key for each affected path family.
- Governance-only keys (for example PM/Jira/admin tasks) are not sufficient when product files changed.
- A PR is not merge-ready if mapping includes only governance keys while product paths changed.

## Cursor-agent Jira authority and evidence rule

- Cursor-agent Jira access is read/write/edit when the active cycle prompt explicitly assigns Jira duties.
- Allowed Jira operations include:
  - reading issue descriptions/status and transition options,
  - posting cycle evidence comments,
  - moving issues to `In Progress` or `In Review` when prompt scope and validation evidence justify it,
  - creating bug tickets from Codex findings,
  - maintaining changed-file-to-Jira mapping tables in reports and PR bodies.
- Disallowed Jira operations include:
  - marking broad product stories `Done` for partial scaffold or governance-only work,
  - closing governance tasks before implementation merges into `develop`,
  - posting ambiguous updates without cycle, branch, changed-file, and validation evidence.
- Every Jira cycle comment must include:
  - cycle id,
  - agent name,
  - branch,
  - changed files,
  - validation evidence,
  - partial/full Definition of Done status.

## Path-to-Epic Mapping Rules

Use these path rules to determine the product Epic/story mapping:

- `src/collection/**`, `tests/**` that validate collection behavior, and collection-specific docs -> Epic 02
- `src/analysis/**` and `tests/**` that validate analysis behavior -> Epic 03
- `src/scoring/**` -> Epic 04
- `src/recommendations/**` -> Epic 05
- `src/pricing/**` -> Epic 06
- `src/discovery/**` -> Epic 07
- `src/playbook/**` -> Epic 08
- `src/dashboard/**`, `src/reports/**`, `src/exports/**` -> Epic 09
- `src/orchestrator/run.py` integration changes -> Epic 10
- `.github/**` and `docs/**` governance/process changes -> PM/GitHub/Jira governance tasks

## Agent Mapping Table (Required)

Every cycle report and PR body must include this completed table:

| Changed file/path | Agent task reference | Epic/story mapping | Jira keys | Evidence note |
| --- | --- | --- | --- | --- |
| `src/<area>/...` | `Task X` | `Epic NN - <name>` | `SCRUM-###` | `test/doc/command link` |
| `docs/...` or `.github/...` | `Task Y` | `Governance` | `SCRUM-###` | `policy/report update` |

## Pre-PR Readiness Check

Before marking a cycle PR merge-ready, Integration/GitHub Steward must confirm:

- PR body has a Jira mapping section.
- Mapping covers both governance keys and product-story keys when product paths changed.
- Mapping table evidence aligns with changed-file list from `git diff --name-only origin/develop...HEAD`.

## Cycle 009 Addendum - Handoff Timing and Report Contract

This addendum is mandatory beginning in Cycle 009:

- Jira story mapping must be completed before final PR handoff, not after a user follow-up.
- Every agent cycle report must explicitly include:
  - changed files list,
  - Jira keys linked to those changed files,
  - Definition of Done status per task, and
  - ticket progression recommendation (`To Do`, `In Progress`, `In Review`, or `Done`).
- Integration/GitHub Steward must block merge-readiness claims if any of the required report fields above are missing.
