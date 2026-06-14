# CYCLE 078 PM_Pack Translation Evidence

## Manual PM Action: Read PM_Pack/ref before deciding what to build

- Automation equivalent: `automation/ref_catalog_builder.py` + generated catalogs.
- Evidence:
  - `project_plan_catalog.json` entries: 95
  - `dod_catalog.json` entries: 10
  - `todo_epic_catalog.json` entries: 11
  - `brain-check` confirms catalogs are present and fresh.

## Manual PM Action: Check Jira AC/DoD before writing prompts

- Automation equivalent: `automation/jira_client.board_inventory()`.
- Evidence:
  - `jira-inventory --dry-run` output shows AC and DoD preview fields.
  - Multiple stories include DoD references to `PM_Pack/ref/dod/DOD_EPIC_XX.md`.

## Manual PM Action: Write agent prompts using PROMPT_TEMPLATE.md

- Automation equivalent: `automation/prompt_contract_builder.py` + `automation/prompt_promotion.py`.
- Evidence:
  - Validated prompt package exists under `PM_Pack/automation/prompts/validated/`.
  - `validate-prompts --cycle 078` returns 6/6 PASS.

## Manual PM Action: Use POST_CYCLE_PM_REVIEW_v4.md after every cycle

- Automation equivalent: `automation/post_cycle_review.py`.
- Evidence:
  - `SOURCE_PROMPT = PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md`
  - file read via `SOURCE_PROMPT.read_text(...)`
  - Claude adapter invocation path present (`claude_post_cycle_adapter.submit_for_review(...)`).

## Manual PM Action: Update PM_Pack state documents

- Automation equivalent: state writer + policy compilation flow.
- Evidence:
  - `HYDRATION_HEADER.md`, `CURRENT_STATE_CANONICAL.md`, `STATE_SNAPSHOT.md` all align to cycle 078 context.
  - `pm-pack-audit` currently PASS.

## Manual PM Action: Run pm-pack-audit to verify state agreement

- Automation equivalent: `python automation/ai_cycle_controller.py pm-pack-audit`.
- Evidence:
  - Command executed and returned PASS with consistent cycle/status sources.

## Full Automation Chain (Cycle loop)

`compile-policy` -> `brain-check` -> `jira-inventory` -> `plan-cycle --live` -> prompt mapping/build/promotion -> `run-agent` from validated prompts -> `post-cycle-review` -> state updates.

## Remaining Gaps (Honest)

- Real PR lifecycle is blocked in this environment by `gh` authentication failure (HTTP 401).
- Full combined coverage gate command still fails/interrupted in long runs (`KeyboardInterrupt`, aggregate ~68%).
- Official post-merge review flow with real merged PR still pending.
