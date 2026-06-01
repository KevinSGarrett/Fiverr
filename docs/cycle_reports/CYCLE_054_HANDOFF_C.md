# Handoff A -> C (Integration Verify, Zero `src/`)

## Ownership and zone

- You perform integration verification after B and E both complete.
- Zero `src/` edits.
- Report-only output for your cycle artifact.

## Entry gate

- B complete (implementation + tests in scope)
- E complete (live validation report committed)

## Checklist C1-C5

### C1) Local verification stack

- file-scoped/local suite runs (no comprehensive `--cov=src`)
- import checks
- `python run.py config-check`
- `python run.py phase2-smoke`

### C2) Toggle-OFF parity verification

Run and verify each equals legacy baseline:

- `python run.py score --golden --config-override scoring.demand.use_trc_reliability=false`
- `python run.py score --golden --config-override scoring.demand.use_signal_qualifiers=false`
- `python run.py score --golden --config-override scoring.competition.use_per_keyword_profile=false`
- `python run.py score --golden --config-override scoring.competition.exclude_contaminated=false`
- `python run.py score --golden --config-override scoring.exclude_price_outliers=false`
- `python run.py score --golden --config-override scoring.feasibility.use_clean_gig_set=false`
- `python run.py score --golden --config-override scoring.opportunity.qualify_by_relevance=false`

### C3) Code-vs-config drift check

- verify scoring constants and niche IDs remain aligned with `config.yaml`
- verify exact canonical 9 niche IDs are present and unchanged

### C4) Config safety re-check

- committed `collection.scrapfly.enabled` remains false
- ensure no `config.live.yaml` committed

### C5) Integration report

- summarize results and blockers
- any gap -> explicit BLOCKER callout

## Report template

- entry criteria met (Y/N)
- command run log
- parity results by toggle
- drift check results
- config guard results
- blocker list (or none)

## Exit criteria

- all checks complete
- report committed
- staged diff excludes `src/`

