# Cycle 013 Execution Protocol (Cycle 079 Baseline)

## Purpose

Define the execution and governance protocol used to generate cycle prompts and
drive cross-agent handoffs. For Cycle 079, this file is the canonical project
plan reference for all prompt contracts and lineage records.

## Scope

- Applies to cycle prompt generation and PM-pack governance updates.
- Covers agent ordering, handoff requirements, and validation expectations.
- Complements lane ownership in `PM_Pack/automation/agent_lanes.yml`.

## Execution Order

Default handoff chain for Cycle 079:

1. Agent A (Planning / PM Pack Integration)
2. Agent B (Primary Implementation)
3. Agent E (Live Validation; waits for B first commit in standard flow)
4. Agent C (Integration Validation)
5. Agent F (Test Coverage / Regression)
6. Agent D (PR Steward / Merge Gate)

## Governance Requirements

- Planning artifacts must be refreshed for the active cycle.
- Cross-agent dependencies must be explicit in PM governance docs.
- Validation commands defined per-agent prompt must be executed and reported.
- Cycle report must include `AGENT_COMPLETE` as completion evidence.

## Cycle 079 Governance Refresh

- Refresh target: `SCRUM-263` (Cycle 079 planning and PM Pack integration governance).
- Agent A ownership: planning, architecture docs, governance consistency, and quality-gate evidence capture.
- Dependency chain for this cycle:
  - Agent A publishes governance artifacts and acceptance mapping.
  - Agent B consumes routing/control notes and implementation constraints.
  - Agent E/C/F execute validation and regression evidence tied to Agent A acceptance coverage.
  - Agent D finalizes merge-gate stewardship after all upstream evidence lands.
- Required evidence files:
  - `docs/cycle_reports/CYCLE_079_AGENT_A.md`
  - `docs/cycle_reports/CYCLE_082_AGENT_A.md`
  - `PM_Pack/automation/post_cycle_reviews/current_run/github_verification.json`
  - `PM_Pack/automation/post_cycle_reviews/current_run/jira_verification.json`

## Required Handoff Artifacts

- Updated cycle report in `docs/cycle_reports/`.
- Refreshed PM governance files under `PM_Pack/`.
- Validation evidence captured in the cycle report.
- Any referenced spec paths must resolve to real files in-repo.

## Stop Conditions

- Attempted edits outside allowed ownership for the active agent.
- Validation failures caused by newly introduced import regressions.
- Any action that would perform controller-owned git operations.
