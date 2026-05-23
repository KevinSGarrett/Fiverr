# Live Collection Preflight (Cycle 035)

Use this checklist before Agent B runs the first live Fiverr collection attempt.

> Login note: most Fiverr scraping targets in this system are public pages. Session auth is a fallback for rate-limit reduction and authenticated-only content.

## Step-by-Step Checklist

1. **Confirm session file exists**
   - `Test-Path "data\sessions\fiverr_session.json"`

2. **Validate session file health**
   - `python run.py session-check`
   - Expected healthy path: no crash, and clear status output.

3. **Validate config**
   - `python run.py config-check`

4. **Run foundation gate**
   - `python run.py foundation-gate --database-url sqlite:///data/fiverr_cycle035_live.db`

5. **Review selector risk list**
   - Read: `docs/collection/SELECTOR_VALIDATION_STATUS.md`
   - Know which selectors are marked `UNVERIFIED`.

6. **Start with low-risk depth and one niche**
   - Prefer `keyword_only` depth.
   - Use one niche only for first pass (recommended: `support_kb_readiness`).
   - Goal is first successful data landing, not completeness.

7. **Run collection**
   - `python run.py collect-only`

8. **Inspect DB immediately after run**
   - `python scripts/collection_debug.py`

9. **Log all failures and partials**
   - Record each `SelectorError`, timeout, and empty-result path.
   - Capture stage + URL + selector constant name + fallback attempt.

## First Live Run Strategy

- **Phase 1 (safest):** `keyword_only` depth, single niche; validate keyword generation and DB writes.
- **Phase 2:** introduce Fiverr search stage and validate W3 selectors on real pages.
- **Phase 3:** attempt deeper stages only after Phase 1 and 2 are stable.

## PXCR Awareness

If Fiverr pages return empty content with no explicit selector exception, inspect rendered content for `PXCR` indicators (PerimeterX bot-block). This is often a browser fingerprint condition, not necessarily an IP ban.
