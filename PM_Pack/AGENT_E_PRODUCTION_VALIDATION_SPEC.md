# AGENT_E_PRODUCTION_VALIDATION_SPEC

## Zone
Agent E commits only `docs/cycle_reports/CYCLE_074_AGENT_E.md`.

## Probe Format
Each of 55 probes must include:
- `probe_id`
- `code_run`
- `expected_value`
- `actual_value` (measured at runtime)
- `pass_fail`

No probe can be marked pass without concrete measured output.

## Probes E-01 through E-20 (exact)
- E-01: `PilotLogger(tmp).log_request` x20 => JSONL has exactly 20 lines.
- E-02: 15/20 blocked => `block_rate=0.75`, `stop_conditions_triggered=True`.
- E-03: `write_evidence_bundle(extra={'niche_id':'x'})` includes `niche_id`.
- E-04: live pilot with session error => `stop_reason='session_expired'`.
- E-05: `DEFAULT_BUDGET_CREDITS == 500`.
- E-06: `collect-live` string present in `run.py`.
- E-07: `live-validate` string present in `run.py`.
- E-08: `live_mode` support present in `run.py`.
- E-09: `config.yaml` keeps `scrapfly.enabled == False`.
- E-10: requirements include scrapfly dependency.
- E-11: `.gitignore` includes live pilot pattern.
- E-12: `generator.py` contains exactly 9 target functions.
- E-13: `generate_playbook(empty db)` => 5 sections and `has_full_data=False`.
- E-14: account setup builder => 7 steps.
- E-15: gig creation builder => 8 steps + checklist in step 8.
- E-16: first 5 orders builder => 4 strategies and >=4 tips.
- E-17: review builder first template length >20.
- E-18: optimization builder => 4 milestones.
- E-19: `RecommendationOutput` has `profile_optimization`.
- E-20: `RecommendationOutput` has `visual_recommendations`.

## Probes E-21 through E-55
Cover remaining C074 deliverables across:
- live pilot stop modes
- evidence schema integrity
- CLI option/default integrity
- Wave 9/10 non-regression checks
- baseline DB untouched verification
- test inventory and gate presence

## Required Artifact
`CYCLE_074_AGENT_E.md` must include a 55-row table with expected/actual/pass columns.
