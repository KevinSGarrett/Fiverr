# C074_PREFLIGHT_MEASURED_STATE

## Measured Baseline Values
- Golden anchor: `run.py score --golden` => kw=110 `62.7/1.0/CONDITIONAL_GO`.
- Priority regression subset: `8 passed, 5263 deselected`.
- Baseline DB mtime: `1780553758`.
- Config: `scrapfly.enabled=False`.
- Config: `analysis.external_signals_enabled=True`.
- Discovery page length: `162` lines.
- Stage16 length: `301` lines.
- Niche config count: `9`.
- Dashboard page count: `9`.
- Recent migrations (last 6h): `[]`.

## Track Snapshot at C074 Base
- Track 03 Collection: 55% baseline (pre-C074 build uplift target to 60%).
- Track 10 Playbook: 8% baseline (target to 15% with S8.3 scaffold).

## Governance State
- TierD-2: approved controlled pilot (conditions A-J defined).
- G-D: open pending post-build validation.
- TierD-1 stale stash issue: open (user decision required).

These values are measured from actual commands and current repository state.
