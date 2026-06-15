# ADR-019: PM_Pack/ref Catalog Architecture

- Status: Accepted
- Date: 2026-06-13
- Owner: Cycle 078 Agent E

## Context

The autonomous runner needs machine-readable project planning context equivalent to the manual PM workflow. The reference corpus under `PM_Pack/ref` contains 172 files across project plans, DoD definitions, epic TODO breakdowns, and governance rules. Before this decision, these were available only as markdown documents and were not consistently freshness-validated.

## Decision

1. Build four generated catalogs in `PM_Pack/automation/`:
   - `project_plan_catalog.json`
   - `dod_catalog.json`
   - `todo_epic_catalog.json`
   - `github_governance_catalog.json`
2. Implement `automation/ref_catalog_builder.py` to index and regenerate all four catalogs.
3. Add `generated_catalogs` metadata to `PM_Pack/automation/BRAIN_REGISTRY.yml` with freshness SLAs.
4. Extend `automation.pm_pack_loader.brain_check()` to fail required stale/missing catalogs with `CATALOG_STALE`.
5. Hook catalog rebuild into `automation.policy_compiler.compile_policy()` so `compile-policy` keeps catalogs fresh.
6. Keep `jira_spec_mapper` compatible by using `project_plan_catalog` as a direct input object from JSON.

## Consequences

- PM planning context is queryable and auditable by automation components.
- `brain-check` now validates required catalog freshness, reducing stale-ref risk.
- `compile-policy` enforces regular regeneration automatically.
- Prompt construction and Jira mapping layers can consume consistent project-plan metadata.
