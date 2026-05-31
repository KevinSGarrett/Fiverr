# Handoff A -> E (Live Validation Only)

## Ownership and zone

- You are report-only for this cycle.
- Commit only: `docs/cycle_reports/CYCLE_054_AGENT_E.md`
- Never commit `src/`, `tests/`, or `config.yaml`.

## Objective

Perform a light but real live validation sample for R4 scoring effects, with `kw=110` (`support_kb_readiness`) first.

## Mandatory ScrapFly runbook (verbatim contract)

Committed config.yaml keeps collection.scrapfly.enabled = false (CI stays dry + credit-free). Live validation ONLY (never committed):
1. Copy config.yaml → config.live.yaml (config.live.yaml is gitignored)
2. In config.live.yaml set: collection.scrapfly.enabled: true (keep asp: true, render_js: true)
3. Ensure SCRAPFLY_API_KEY is present in .env (gitignored). Confirm PRESENCE only (length/prefix); never print the value.
4. Run live, e.g.: python run.py collect-only --config-path config.live.yaml --niche support_kb_readiness
5. CONFIRM the log line: "ScrapFly session: requests=… credits=…" (proof the bypass transport ran)
6. If ScrapFly cannot be enabled or the line is absent → mark "[SEED — no live signal]" in the report. Do NOT fabricate numbers. Do NOT silently fall back to Playwright (that yields 403-degraded sweeps).
7. A LARGE live run (significant credit burn) is Tier-D → the operator/user authorizes it first.

## Validation checklist

- [ ] live attempt executed for sample set
- [ ] kw=110 sampled first
- [ ] ScrapFly session line present (or `[SEED - no live signal]` explicitly recorded)
- [ ] cleaned-set movement direction documented
- [ ] whether kw=110 remains CONDITIONAL_GO documented
- [ ] no fabricated values

## Sample set

1. `support_kb_readiness` (required first)
2. Optional small follow-up sample keywords from current cycle data if credits permit

## Report template (`CYCLE_054_AGENT_E.md`)

- run date/time
- command used
- ScrapFly enablement proof (or seed fallback marker)
- sampled keywords/niches
- before/after observations for TRC reliability and price-outlier logic
- kw=110 status check (final score, confidence modifier, tier)
- explicit limits/unknowns

## Exit criteria

- report committed
- staged files include only `docs/cycle_reports/CYCLE_054_AGENT_E.md`

