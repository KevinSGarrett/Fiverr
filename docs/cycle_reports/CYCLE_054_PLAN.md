# Cycle 054 Plan (R4) - One Page

## Scope

R4 extends existing scoring calculators (no new modules) to improve data-integrity handling across five themes:

- T1 Demand TRC reliability (single consolidated factor, no compounding)
- T2 Signal qualifiers (autocomplete emerging vs absent + trends qualifier)
- T3 Clean competitor set (profile source selection + contamination exclusion + IQR outlier filtering)
- T4 Clean feasibility (clean-gig set for level ratio/review barrier)
- T5 Opportunity/intent integrity (relevance-qualified opportunity + intent alignment + integrity columns)

## Stage sequence

1. A (planner/setup) -> complete baseline, Jira setup, handoffs, docs commit
2. B + E in parallel
   - B: all `src/` implementation + unit tests
   - E: live validation report only
3. C after B and E both complete (integration verify, zero src changes)
4. F after C (coverage + REG-20/21/22 + tests-only zone)
5. D final merge gate and one comprehensive `--cov=src` run

## Hard gates

- G-001 `codecov/patch >= 90%`
- G-002 review threads GraphQL check twice, unresolved = 0 with real fixes
- G-003 D checklist all PASS/YES before merge
- G-004 exactly one comprehensive `--cov=src` run by D only
- Config gate: only documented R4 additive toggles; committed `scrapfly.enabled=false`; devvit bridge intact
- Parity gate: toggles OFF == legacy; ON maintains `kw=110` as `CONDITIONAL_GO`

## Anchors and parity

- Legacy anchor baseline:
  - `kw=110`: `62.70 / CM 1.0 / CONDITIONAL_GO` (must hold)
  - `kw=96`: `35.80 / CAUTION`
  - `kw=3`: `56.66 / MONITOR`
- OFF parity is non-negotiable.
- ON-mode rollout safety rail:
  - expected targeted metric movement only
  - anchor drift <= `2.0`

## Toggle inventory reference

All defaults false (committed):

- `scoring.demand.use_trc_reliability`
- `scoring.demand.use_signal_qualifiers`
- `scoring.competition.use_per_keyword_profile`
- `scoring.competition.exclude_contaminated`
- `scoring.exclude_price_outliers`
- `scoring.feasibility.use_clean_gig_set`
- `scoring.opportunity.qualify_by_relevance`

## File-impact reference

- `src/scoring/demand_score.py`
- `src/scoring/competition_score.py`
- `src/scoring/profitability.py`
- `src/scoring/feasibility.py`
- `src/scoring/intent.py` + opportunity computation
- `src/models` (`KeywordScore` additive nullable integrity columns)
- `tests/unit/*` (B + F split ownership)

## Regression pack delta

- Carry-forward: 20 named permanent regressions
- New this cycle: REG-20/REG-21/REG-22
- Post-F merge-gate expectation: 23 named regressions all green by name

## Agent A completion declaration criteria

- branch pushed
- Jira stories in progress + control task active
- all handoff docs committed
- baseline/parity captured
- B + E explicitly cleared to start in parallel; C waits for both

