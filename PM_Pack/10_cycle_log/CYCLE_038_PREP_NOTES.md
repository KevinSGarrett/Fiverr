# CYCLE 038 PREP NOTES

Date: 2026-05-24  
Source cycle: 037

## Remote Cycle Branch Inventory (Post-Cycle 037 Cleanup State)

- `origin/cycle/037/integration` (active branch for PR #44)
- `origin/cycle/009/integration` (legacy branch retained per prior investigation)
- `origin/cycle/035/integration` removed
- `origin/cycle/036/integration` removed

## Live Collection Status

- Pipeline verdict from Cycle 037 Agent C: `MINIMAL`
- Live DB snapshot (`sqlite:///data/cycle037_live.db`): `keywords=2`, `search_results=4`, `gigs=0`, `sellers=19`
- ScrapFly gate status: `OPEN`

## Codex P1 Status

- `test_seller_profile_fetcher_maps_parser_fields_for_persistence`: passing in regression suite
- `test_gig_detail_fetcher_does_not_overwrite_existing_optional_fields`: passing in regression suite
- Independent live-data interpretation from Agent C:
  - gig_detail: `INSUFFICIENT_DATA` (`gigs=0`)
  - seller_profile: `STILL_BROKEN` (live sparse/null profile fields)

## data-testid Parsing Status

- Cycle 037 live validation recorded `MISSING` for target `data-testid` selectors.
- `src/collection/search_result_parser.py` fallback extraction path is active and recovers Stage 3 links/cards.
- Status: parser fallback works for partial recovery, but canonical `data-testid` extraction still needs tuning/validation.

## Recommended Cycle 038 Scope (Pipeline = MINIMAL)

Priority: parser testid fix validation.

1. Validate expected `data-testid` attributes against fresh live ScrapFly HTML captures.
2. If testids are fixed/confirmed, rerun Stage 3 immediately and re-check Stage 4 persistence.
3. If testids still absent/unreliable, escalate to alternative parsing strategy with explicit selectors/fallback hierarchy and regression coverage.
4. Preserve Codex P1 regression tests while collecting new live evidence for seller profile field extraction.

## Live Run Preconditions

- `SCRAPFLY_API_KEY` present in `.env`
- `collection.scrapfly.enabled: true` in configuration
