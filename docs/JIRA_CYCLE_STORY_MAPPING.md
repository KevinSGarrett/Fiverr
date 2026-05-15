# Jira Cycle Story Mapping Protocol

## Purpose

Every cycle must map changed files and executed agent tasks to Jira product stories, not only governance tickets. This protocol is mandatory for all cycle reports and PR bodies targeting `develop`.

## Mandatory Rule

- If any product path changes, the PR/cycle report must include at least one product Jira story key for each affected path family.
- Governance-only keys (for example PM/Jira/admin tasks) are not sufficient when product files changed.
- A PR is not merge-ready if mapping includes only governance keys while product paths changed.

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
|---|---|---|---|---|
| `src/<area>/...` | `Task X` | `Epic NN - <name>` | `SCRUM-###` | `test/doc/command link` |
| `docs/...` or `.github/...` | `Task Y` | `Governance` | `SCRUM-###` | `policy/report update` |

## Pre-PR Readiness Check

Before marking a cycle PR merge-ready, Integration/GitHub Steward must confirm:

- PR body has a Jira mapping section.
- Mapping covers both governance keys and product-story keys when product paths changed.
- Mapping table evidence aligns with changed-file list from `git diff --name-only origin/develop...HEAD`.
