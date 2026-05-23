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

## Agent B Validation Logging Rule

For every selector failure or empty extraction:

1. Capture the selector constant name.
2. Capture the URL and stage.
3. Capture the exact exception (`SelectorError`, timeout, empty-node path).
4. Propose replacement selector candidates in `fiverr_selectors.py`.
