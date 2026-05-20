# CYCLE NAMING CONVENTIONS

---

## Cycle Numbers
- Format: 3-digit zero-padded (001, 002, ..., 999)
- Sequential, never skip numbers
- Cycle 000 = initialization (no agent work)

## PM Pack Zip
- Format: PM_Pack_Cycle_{NNN}.zip
- Examples: PM_Pack_Cycle_001.zip, PM_Pack_Cycle_042.zip

## Git Branches Per Cycle
- Integration branch: cycle/{NNN}/integration
- Created from: develop
- Merges to: develop via single PR

## PR Per Cycle
- Title: feat(cycle-{NNN}): {summary}
- Example: feat(cycle-001): epic 01 scaffolding, config, and base models

## Jira Comments
- Prefix: [Cycle {NNN}]
- Example: [Cycle 001] Agent A completed S1.1 scaffolding. Branch: cycle/001/integration

## Cycle Log Files
- Format: CYCLE_{NNN}.md
- Location: 10_cycle_log/
