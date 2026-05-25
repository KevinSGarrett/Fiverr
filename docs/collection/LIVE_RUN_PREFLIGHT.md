# Live Collection Preflight (Cycle 035)

Use this checklist before Agent B runs the first live Fiverr collection attempt.

> Login note: most Fiverr scraping targets in this system are public pages. Session auth is a fallback for rate-limit reduction and authenticated-only content.

## Step-by-Step Checklist

1. **Confirm session file exists**
   - `Test-Path "data\sessions\fiverr_session.json"`

2. **Validate session file health**
   - `python run.py session-check`
   - Expected output: `Session is VALID. Ready for collection.`
   - If not valid, run `python run.py relogin` and re-run `session-check`.

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

## ScrapFly Mode (Recommended for PXCR environments)

- **Prerequisites**
  - Set `SCRAPFLY_API_KEY` in `.env`.
  - Set `collection.scrapfly.enabled: true` in `config.yaml`.
- **Verify ScrapFly is active**
  - Run `python run.py config-check` and confirm `collection.scrapfly.enabled` resolves to `true`.
- **Expected behavior**
  - ScrapFly performs JS rendering and handles PerimeterX bypass on collection pages.
- **Credit monitoring**
  - Watch logs for `ScrapFly session: requests=N credits=N`.
- **Fallback**
  - Set `collection.scrapfly.enabled: false` to return to Playwright transport.

## Cycle 037 ScrapFly Live Run Strategy

### Phase 1 — Keyword expansion only (no Playwright/ScrapFly required)

- Run W2 via `collect-only` using `keyword_only` depth.
- This phase uses OpenAI + Google Suggest inputs; no Fiverr pages are fetched yet.
- Target outcome: `>= 10` keywords across target niches.
- Purpose: validate LLM/API connectivity before any page-fetching stages.

### Phase 2 — ScrapFly search (Stage 3) with `data-testid` validation

- If `SCRAPFLY_API_KEY` is present, Stage 3 should fetch search pages through ScrapFly.
- If the key is absent, fallback is Playwright (which can still hit PXCR).
- Capture and log the first raw HTML returned in ScrapFly mode to validate test IDs.
- Validate these key selectors in fetched HTML: `gig-card-layout`, `gig-title`, `seller-name`, `seller-level`, `review-count`, `starting-price`, `sponsored-badge`, `total-result-count`.
- If `gig_cards_collected == 0`, inspect `parse_warnings` from the stage return payload.
- Target outcome: `>= 5` gig cards collected per search query.

### Phase 3 — ScrapFly gig detail (Stage 4)

- Execute only when `gig_urls_queued > 0`.
- Each gig URL should be fetched via ScrapFly and parsed by `parse_gig_detail_from_html`.
- Codex P1 validation: `tags`, `faq_text`, and `video_present` must not be forced empty/false when present in HTML.
- Log these fields for every collected gig to preserve evidence.
- Target outcome: `>= 5` gigs with `detail_collected=True`.

### Phase 4 — ScrapFly seller profile (Stage 5)

- Execute only when sellers are queued from prior stages.
- Codex P1 validation: `seller_level`, `member_since`, and `total_reviews` should be populated (not `None`) when present in HTML.
- Target outcome: `>= 3` seller profiles with non-`None` key profile fields.

### Data quality checks after each phase

- Run: `python scripts/collection_debug.py` with `DATABASE_URL=sqlite:///data/cycle037_live.db`.
- Log row counts for `keywords`, `search_results`, `gigs`, `sellers`, and `external_signals`.
