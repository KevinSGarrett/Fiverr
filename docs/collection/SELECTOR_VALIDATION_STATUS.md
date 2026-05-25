# Selector Validation Status (Cycle 035)

This document tracks selectors that are currently marked `UNVERIFIED` in `src/collection/fiverr_selectors.py` and must be validated against live Fiverr DOM during Cycle 035 collection runs.

## Summary

- Total literal selector constants in `fiverr_selectors.py`: **50**
- `UNVERIFIED` selectors: **15**
- Unverified ratio: **30.0%**
- Current risk concentration: **W2 autocomplete + W5 seller profile**

## W2 Step 2a — Autocomplete / Search Suggestions

| Selector | CSS | Workflow | Current status | Verified? |
| --- | --- | --- | --- | --- |
| `SEARCH_BOX` | `[data-testid='search-bar-input'], input[placeholder*='Find'], input[name='query']` | W2 Step 2a | Pending live DOM validation in browser run | No |
| `AUTOCOMPLETE_DROPDOWN` | `[data-testid='search-suggestion-dropdown'], .search-suggestions, .autocomplete-dropdown` | W2 Step 2a | Pending live DOM validation in browser run | No |
| `AUTOCOMPLETE_ITEM` | `[data-testid='search-suggestion-item'], .search-suggestion-item, .suggestion-item` | W2 Step 2a | Pending live DOM validation in browser run | No |
| `AUTOCOMPLETE_ITEM_TEXT` | `[data-testid='search-suggestion-text'], .suggestion-text` | W2 Step 2a | Pending live DOM validation in browser run | No |

## W3 — Fiverr Search Results

No selectors are currently annotated as `UNVERIFIED` for W3 in `fiverr_selectors.py`. Agent B should still monitor for real-DOM drift and record any selector failures.

## W4 — Gig Detail

No selectors are currently annotated as `UNVERIFIED` for W4 in `fiverr_selectors.py`. Agent B should still monitor for real-DOM drift and record any selector failures.

## W5 — Seller Profile

| Selector | CSS | Workflow | Current status | Verified? |
| --- | --- | --- | --- | --- |
| `SELLER_LEVEL_BADGE` | `[data-testid='seller-level-badge'], [data-testid='seller-level'], .seller-level-badge, .seller-level` | W5 | Pending live DOM validation in browser run | No |
| `SELLER_MEMBER_SINCE` | `[data-testid='seller-member-since'], [data-testid='member-since'], .member-since` | W5 | Pending live DOM validation in browser run | No |
| `SELLER_RESPONSE_TIME` | `[data-testid='seller-response-time'], [data-testid='response-time'], .response-time` | W5 | Pending live DOM validation in browser run | No |
| `SELLER_RESPONSE_RATE` | `[data-testid='seller-response-rate'], [data-testid='response-rate'], .response-rate` | W5 | Pending live DOM validation in browser run | No |
| `SELLER_LANGUAGES` | `[data-testid='seller-language-item'], [data-testid='language-item'], .languages li, .language-list li` | W5 | Pending live DOM validation in browser run | No |
| `SELLER_BIO` | `[data-testid='seller-bio'], [data-testid='seller-description'], .seller-overview p, .seller-bio` | W5 | Pending live DOM validation in browser run | No |
| `SELLER_TOTAL_REVIEWS` | `[data-testid='seller-total-reviews'], [data-testid='seller-review-count'], .total-reviews` | W5 | Pending live DOM validation in browser run | No |
| `SELLER_TOTAL_GIGS` | `[data-testid='seller-total-gigs'], [data-testid='gig-count'], .gigs-count` | W5 | Pending live DOM validation in browser run | No |
| `SELLER_GIG_TITLE` | `[data-testid='seller-gig-title'], [data-testid='gig-title'], .gig-list .title, .gig-title` | W5 | Pending live DOM validation in browser run | No |
| `SELLER_PORTFOLIO_ITEM` | `[data-testid='seller-portfolio-item'], [data-testid='portfolio-item'], .portfolio-item` | W5 | Pending live DOM validation in browser run | No |
| `SELLER_BADGE` | `[data-testid='seller-badge-item'], [data-testid='badge-item'], .badge-card` | W5 | Pending live DOM validation in browser run | No |

## ScrapFly Mode - Impact on Selector Validation

ScrapFly mode changes selector validation priorities because workflows can parse fully rendered HTML without using browser-side Playwright CSS selectors.

- ScrapFly returns rendered page HTML, so parsing runs through `search_result_parser.py` and `gig_detail.py` data-testid extraction paths.
- The 15 currently unverified Playwright CSS selectors (all `AUTOCOMPLETE_*` and `SELLER_*` entries above) are not used when ScrapFly fetcher mode is active.
- In ScrapFly mode, search parsing currently inspects these `data-testid` values:
  - Card containers: `gig-card-layout`, `gig_listing_item`, `gig-card`
  - Card fields: `gig-title`, `seller-name`, `seller-level`, `review-count`, `starting-price`, `price`
  - Sponsored markers: `sponsored-badge`, `promoted-badge`, `ad-badge`
  - Result count: `total-result-count`
- Validation status for ScrapFly HTML parsing markers remains pending against live ScrapFly-fetched pages:
  `gig-card-layout`, `gig-title`, `seller-name`, `seller-level`, `review-count`, `starting-price`, `sponsored-badge`, `total-result-count`.

Conclusion: once operators enable ScrapFly, selector validation focus should shift from Playwright CSS selectors to HTML `data-testid` stability in ScrapFly response payloads.

## Agent B Validation Logging Rule

For every selector failure or empty extraction:

1. Capture the selector constant name.
2. Capture the URL and stage.
3. Capture the exact exception (`SelectorError`, timeout, empty-node path).
4. Propose replacement selector candidates in `fiverr_selectors.py`.

## Cycle 037 ScrapFly Live Run Results

### ScrapFly `data-testid` validation (live HTML)

| Marker | Status in ScrapFly HTML | Notes |
| --- | --- | --- |
| `gig-card-layout` | MISSING | Not present in `data/debug_search_html.html` |
| `gig-title` | MISSING | Not present in ScrapFly-fetched markup |
| `seller-name` | MISSING | Not present in ScrapFly-fetched markup |
| `starting-price` | MISSING | Not present in ScrapFly-fetched markup |
| `total-result-count` | MISSING | Not present in ScrapFly-fetched markup |
| `sponsored-badge` | MISSING | Not present in ScrapFly-fetched markup |

### Playwright CSS selectors in ScrapFly mode

- `SEARCH_BOX`, `AUTOCOMPLETE_DROPDOWN`, `AUTOCOMPLETE_ITEM`, `AUTOCOMPLETE_ITEM_TEXT`: **NOT USED IN SCRAPFLY MODE**
- `SELLER_LEVEL_BADGE`, `SELLER_MEMBER_SINCE`, `SELLER_RESPONSE_TIME`, `SELLER_RESPONSE_RATE`: **NOT USED IN SCRAPFLY MODE**
- `SELLER_LANGUAGES`, `SELLER_BIO`, `SELLER_TOTAL_REVIEWS`, `SELLER_TOTAL_GIGS`: **NOT USED IN SCRAPFLY MODE**
- `SELLER_GIG_TITLE`, `SELLER_PORTFOLIO_ITEM`, `SELLER_BADGE`: **NOT USED IN SCRAPFLY MODE**

### Parser actions taken

- Updated `src/collection/search_result_parser.py` with a href-based fallback when Fiverr SERP no longer exposes expected `data-testid` hooks.
- Fallback now extracts gig URLs from listing-like links (`source=gig_cards`, `referrer_gig_slug`, `context_referrer`, `pckg_id`) and preserves seller username derivation.
- Stage 3 moved from `gig_cards_collected=0` to `gig_cards_collected=20` per keyword (via fallback), with warning retained to indicate missing `data-testid` selectors.

### Codex P1 production validation (Cycle 037 live data)

- Gig detail P1 fix (`tags`/`faq_text`/`video_present` overwrite guard): **NEEDS INVESTIGATION**
  - Stage 4 executed, but DB `gigs` rows remained `0`, so no `detail_collected=True` rows were available for direct field-value confirmation.
- Seller profile P1 fix (parser field mapping to persistence fields): **NEEDS INVESTIGATION**
  - Stage 5 wrote seller rows (`sellers=19`), but sampled rows show `seller_level=NO_LEVEL`, `member_since=None`, `total_reviews=None`, `total_gigs=None`, indicating profile parser/HTML mismatch in live payloads.

## Cycle 038 Parser Fix Results

### Extraction strategy used

- **Gig detail parser:** Strategy A with structured `application/ld+json` as primary source, plus Strategy D fallback for `__NEXT_DATA__` when present.
- **Seller profile parser:** Strategy D variant using `perseus-initial-props` JSON hydration script as primary source (live seller pages did not expose `__NEXT_DATA__`/JSON-LD), plus HTML fallbacks (`data-testid` and review-text regex).

### Live HTML findings

- `data/debug_gig_html.html`: `JSON-LD blocks=3`, `__NEXT_DATA__=0`, `data-testid` sparse and unstable.
- `data/debug_seller_html.html`: `JSON-LD blocks=0`, `__NEXT_DATA__=0`, hydration data present in `script#perseus-initial-props`.
- Seller page `data-testid` keys were minimal (`username`, `response-time`, a few controls) and insufficient alone for full profile extraction.

### Fields extracted in Cycle 038

| Parser | Extracted successfully | Still partially limited |
| --- | --- | --- |
| `parse_gig_detail_from_html` | `title`, `description`, `packages`, `review_count`, `rating`, `warnings` | `starting_price` nullable on many live gigs when no explicit package price is exposed |
| `parse_seller_profile_from_html` | `username`, `display_name`, `level`, `member_since`, `review_count`, `active_gig_count`, `response_time` | Some sellers still omit review totals in hydration payloads; parser now marks warning instead of silent null |

### Production validation verdicts (Cycle 038)

- **Gig detail P1:** `CONFIRMED_FIXED`
  - Live DB: `gigs detail_collected=20`, `title non-null=20`.
- **Seller profile P1:** `CONFIRMED_FIXED`
  - Live DB: `sellers with seller_level != NO_LEVEL = 17` (from `38` total sellers), with `member_since` populated for most live rows.
