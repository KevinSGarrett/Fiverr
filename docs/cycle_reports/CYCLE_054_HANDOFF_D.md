# Handoff A -> D (Merge Gate + Release Control)

## Ownership and zone

- You own final merge gate after A/B/E/C/F complete.
- Report + prep notes only; no no-op attribution edits.

## Merge checklist (D1-D8)

### D1) Deliverables table

- verify all six-agent deliverables exist and match claimed scope

### D2) Zone checks

- Agent E commit zone: `git show E_SHA` contains zero `src/` + `tests/`
- Agent F commit zone: `git show F_SHA` contains zero `src/`

### D3) Attribution invariant

- `base=$(git merge-base develop cycle/054/integration)`
- `git log "$base..HEAD" --name-only`
- all `src/` files in cycle range authored only by Agent B commits

### D4) Config gate re-verify

- committed `collection.scrapfly.enabled` remains false
- only documented R4 toggles changed in config
- `reddit` devvit bridge settings unchanged

### D5) Coverage gate

- run exactly one comprehensive `--cov=src` command for cycle gate
- record final coverage result

### D6) Codex thread gate

- run review threads GraphQL query twice (pre and post resolution)
- unresolved threads must be zero with real fixes (no no-op commits)

### D7) Parity + regression gate

- OFF parity equals legacy baseline
- ON mode still keeps `kw=110` as CONDITIONAL_GO
- all 23 named regressions pass by name

### D8) Final merge + Jira transitions

- only merge after all checklist items PASS/YES
- then execute post-merge Jira transitions (Done id `41`) only where DoD is met

## Post-merge Jira transition plan

- SCRUM-613 -> Done when R4.1 AC and parity conditions met
- SCRUM-614 -> Done when R4.2 AC and parity conditions met
- SCRUM-615 -> Done when R4.3 AC and profile source persistence met
- SCRUM-813 -> Done when contamination exclusion + REG-20 met
- SCRUM-616 -> Done when IQR exclusion + REG-22 met
- SCRUM-617 -> Done when clean-gig feasibility + REG-18 continuity met
- SCRUM-618 -> Done when opportunity qualifier/integrity cols + REG-21 met
- SCRUM-619 -> Done when 8+12 + REG-20/21/22 + patch coverage gate met
- SCRUM-1008 -> Done when PR merges and all gates are green

Each transition comment must include merge SHA + PR link.

## Exit rule

`Ready to merge ONLY when ALL items PASS/YES.`

