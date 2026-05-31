# ScrapFly Collection Policy & Runbook

**Canonical rule lives in `AGENT_EXECUTION_STRATEGY.md` §10.** This file is the quick operator
runbook. Read it before any live Fiverr collection or live validation work.

## TL;DR

- ScrapFly is the **PerimeterX bypass** transport for **live** Fiverr fetches. **No ScrapFly →
  Playwright fallback → 403 → no live data.** This is why Agent E's live sweeps were 403-degraded.
- The `SCRAPFLY_API_KEY` is already in `.env` (a real `scp-` key, gitignored). The key is NOT the
  blocker — the disabled toggle is.
- Committed `config.yaml` keeps `collection.scrapfly.enabled: false` **on purpose** (CI/tests run
  dry → zero live calls, zero credits). That is correct and the config gate enforces it.
- **Live work turns ScrapFly on at runtime via a LOCAL, UNCOMMITTED config — never by committing
  `enabled: true`.**

## When ScrapFly matters

| Run type | `dry_run` | Fetcher built? | ScrapFly needed? |
| --- | --- | --- | --- |
| Unit/integration tests, CI | True | No | No (mock or dry) |
| `*-dry-run` CLI modes | True | No | No |
| Live collection / live validation / DL-207 capture | False | Yes | **YES** |

## How it is wired (so you can verify, not guess)

- `src/collection/orchestrator.py` builds a fetcher only when `dry_run=False`, reading
  `collection.scrapfly.enabled`:
  - `true` → opens `ScrapFlyClient` (key from `SCRAPFLY_API_KEY`) + `build_fetcher(prefer_scrapfly=True)`.
  - `false` → `build_fetcher(prefer_scrapfly=False)` → Playwright/session → **403**.
- There is **no CLI flag** to enable ScrapFly. It is config-file driven (`--config-path`).

## Runbook — enabling ScrapFly for a live run (operator or Agent E)

1. Confirm the key is present (do NOT print it):
   ```powershell
   (Get-Content .env | Select-String '^SCRAPFLY_API_KEY=') -ne $null
   ```
2. Make a local, uncommitted live config:
   ```powershell
   Copy-Item config.yaml config.live.yaml
   # edit config.live.yaml -> collection.scrapfly.enabled: true   (leave asp:true, render_js:true)
   ```
   `config.live.yaml` is gitignored (see §10.6) — never commit a config with `enabled: true`.
3. Run a LIVE (non-dry-run) mode against it, e.g.:
   ```powershell
   python run.py collect-only --config-path config.live.yaml --database-url sqlite:///data/<run>.db
   ```
4. Confirm the bypass transport was actually used — look for the session log line:
   ```text
   ScrapFly session: requests=<n> credits=<n>
   ```
   If you do not see it, ScrapFly did NOT run (you were on the Playwright path).
5. Mind credits. `cost_budget_credits` can cap spend. A **large** live run is a Tier-D action
   (ask the user first — see §9). A small validation sample is normal.

## Rules (do / don't)

- DO keep committed `config.yaml` `scrapfly.enabled: false`.
- DO enable ScrapFly only via a local/uncommitted config for live runs.
- DO mock the fetcher / ScrapFly client in all automated tests (no live calls in CI).
- DON'T commit `enabled: true` (config-gate violation).
- DON'T interpret "committed-off" as "never use ScrapFly" — that is the exact mistake that caused
  the 403-degraded live sweeps.
- If ScrapFly is unavailable during validation, Agent E marks the niche **"[SEED — no live signal]"**
  and does NOT fabricate counts.

## For prompt authors (PM)

Every Agent E (and any live-collection) prompt MUST embed §10.5 step 4 verbatim: enable ScrapFly via
a local config + `SCRAPFLY_API_KEY`, run live, confirm the `ScrapFly session:` log line, and use the
`[SEED — no live signal]` fallback if it cannot be enabled. The post-cycle review prompt verifies the
committed config still has `scrapfly.enabled: false`.
