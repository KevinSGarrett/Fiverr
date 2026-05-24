# CYCLE 037 PREP NOTES

Date: 2026-05-24
Branch Context: `cycle/036/integration`

## Remote Cycle Branch Inventory

- Remote cycle branch count: `3`
- Remote cycle branches:
  - `cycle/009/integration`
  - `cycle/035/integration`
  - `cycle/036/integration`

## Cleanup Candidates

- Candidate rule: cycle branches at least 3 cycles old **and** already merged into `develop`.
- Current candidates: none.
- Notes:
  - `cycle/035/integration` is merged into `develop` but is only one cycle old.
  - `cycle/009/integration` is old enough but is not currently merged into `develop`.

## PXCR Mitigation Status

- ScrapFly infrastructure status: complete in codebase (client, fetcher abstraction, parser, workflow wiring, orchestrator wiring, docs, config templates, tests).
- Operator action required before live bypass usage:
  - add `SCRAPFLY_API_KEY` to local `.env`
  - set `collection.scrapfly.enabled: true` in runtime config

## Recommended Cycle 037 Scope

### Option A: First ScrapFly-Enabled Live Collection Run

- Precondition: `SCRAPFLY_API_KEY` must be present in `.env` before execution.
- Validate that Stage 3 / Stage 4 / Stage 5 collect real data through ScrapFly.
- Validate `data-testid` selector behavior in ScrapFly-fetched HTML payloads.
- Target output threshold:
  - at least 10 keywords
  - at least 5 gigs
  - persisted in live DB

### Option B: Reddit Credentials Configuration

- Configure:
  - `REDDIT_CLIENT_ID`
  - `REDDIT_CLIENT_SECRET`
- Outcome: enables Stage 6b live Reddit signal collection path.

## Explicit Precondition Reminder

- Option A must not be attempted until `SCRAPFLY_API_KEY` exists in `.env`.
