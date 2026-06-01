# Handoff A -> F (Coverage + Regression Pack, Tests-Only)

## Ownership and zone

- You own test expansion/coverage for Cycle 054 after C completes.
- Do not edit `src/`.
- Commit tests + your report only.

## Required outcomes

### F1) Seat permanent regressions

Add and validate:

- REG-20 `test_niche_profile_excludes_contaminated_keywords`
- REG-21 `test_opportunity_qualified_by_relevance`
- REG-22 `test_price_outlier_excluded_from_competition_and_profitability`

### F2) R4 test backfill

- complete 8 + 12 unit coverage for SCRUM-619 intents
- ensure patch coverage >= 90% on new B lines

### F3) Regression ledger handoff

- provide REG-20/21/22 names explicitly to D merge gate
- provide same names for strategy section 7 update tracking

### F4) Zone compliance

- commit only tests + `CYCLE_054_AGENT_F.md`

## Test matrix handoff (intent mapping)

- R4.1 TRC reliability: bounds, None handling, consolidated factor behavior
- R4.2 signal qualifiers: emerging/absent + trends qualifier path
- R4.3 profile source choice behavior
- R4.4 contamination exclusion behavior
- R4.5 IQR filtering for both competition and profitability
- R4.6 clean-gig feasibility calculations
- R4.7 opportunity qualifier + integrity fields
- R4.8 parity/test gate assertions

## Validation commands (example)

- run targeted test files for changed areas
- run regression selectors for REG-20/21/22
- run coverage command(s) scoped to changed tests/new lines as needed

## Exit checklist

- [ ] REG-20/21/22 present and green
- [ ] patch coverage >= 90
- [ ] 8 + 12 matrix satisfied
- [ ] staged files include no `src/`
- [ ] report committed

