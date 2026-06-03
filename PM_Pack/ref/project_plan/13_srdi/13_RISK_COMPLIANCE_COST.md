# 13 Risk Compliance Cost

## Platform and Compliance Risk

- Fiverr ToS/platform-policy risk remains active for automated collection paths (tracked in SCRUM-74).
- Collection strategy must continue respecting pacing, authentication, and anti-abuse boundaries.
- Compliance evidence must remain attached to each live run decision record.

## Cost Governance

- ScrapFly credit consumption remains a user-governed cost decision (TierD-2).
- Full live collection across all niches should not be initiated without explicit budget approval.
- LLM cost posture remains conservative: `gpt-4o-mini` default for most tasks with daily alert threshold at `$5`.

## Data Hygiene and Security Controls

- No scraped raw marketplace payloads are to be committed to source control.
- No API keys, tokens, or credentials may be committed in any prompt/report/config artifact.
- Throwaway DB usage is mandatory for live validation experiments when requested by execution agents.

## Known Risks and Operational Watchlist

- **SEED-band uncertainty:** live collection is still required for full confidence in RSV behavior beyond fixture-backed paths.
- **Stale stash inventory (TierD-1):** unresolved historical stashes can create accidental drift and should be user-confirmed before cleanup.
- **Wave coupling risk:** Waves 9-12 sequencing dependencies increase NO-GO probability if stage boundaries are violated.

## Mitigation Ownership Model

- Agent A: governance packaging and evidence readiness.
- Agent B: implementation quality and schema parity.
- Agent C: independent gate validation and GO/NO-GO evidence.
- Agent D: final merge governance, codex thread closure, and Jira completion.
- User/owner: budget decisions (ScrapFly/LLM) and final risk acceptance.
