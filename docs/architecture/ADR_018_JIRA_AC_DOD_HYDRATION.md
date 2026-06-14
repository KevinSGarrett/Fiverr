# ADR 018: Jira AC/DoD Hydration

## Status
Accepted

## Context
Cycle 078 required prompt planning to use real Jira acceptance criteria (AC) and definition of done (DoD) data instead of placeholders. The planning layer also needed a deterministic bridge from Jira stories into PM_Pack reference artifacts.

## Decision
- Extend `automation.jira_client.board_inventory()` to return:
  - `description`
  - `acceptance_criteria`
  - `definition_of_done`
- Add `JiraClient.hydrate_ac_dod(issue_key)` for per-story AC/DoD retrieval.
- Add `automation.jira_spec_mapper.map_jira_to_project_plan()` to map Jira story context to PM_Pack reference paths.
- Update `automation.prompt_generator.write_prompts()` to:
  - enrich incoming Jira stories via `jira_spec_mapper`
  - raise `PlanningIncompleteError` with `PLANNING_INCOMPLETE` diagnostics when a story has no AC, no DoD, and no DoD reference path.

## Consequences
- Prompt generation is blocked early when planning data is incomplete.
- Agent prompts embed real AC/DoD values where available.
- Agent E can later plug in a richer catalog without changing Agent B APIs because mapper already accepts optional catalogs.
