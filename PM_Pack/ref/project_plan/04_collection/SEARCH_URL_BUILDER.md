# Search URL Builder -- Category-Constrained Search
# Fiverr Research System -- SRDI Initiative Wave B (R1)

**Document Status:** Active
**Source:** WAVE_B_CATEGORY_FILTER_SEARCH_URL_HARDENING.md
**Epic:** R1 (SCRUM-591 to SCRUM-597)
**Module:** src/collection/search_url_builder.py (NEW)
**Tier:** 0 -- must ship before first recommendation

---

## Purpose

Without a category filter, Fiverr search returns results from all categories for any
keyword. "Python automation" can return SEO writers, logo designers, and voiceover
artists alongside actual automation gigs. Category-constrained URLs fix this at source.

---

## SearchStrictness Enum

SUBCATEGORY -- category_id + sub_category param (most specific)
CATEGORY    -- category_id only (broader fallback)
NONE        -- no category filter (unconstrained; last resort)

---

## NICHE_CATEGORY_MAP (All 9 Production Niches)

prd_ai_saas:
  fiverr_category_id: "10"        (Writing and Translation)
  fiverr_subcategory_id: "10_7"   (Technical Writing)
  search_url_param: "category_id=10&sub_category=technical_writing"
  fallback_category_id: "10"

support_kb_readiness:
  fiverr_category_id: "10"
  fiverr_subcategory_id: "10_7"
  search_url_param: "category_id=10&sub_category=technical_writing"
  fallback_category_id: "10"

python_automation:
  fiverr_category_id: "6"         (Programming and Tech)
  fiverr_subcategory_id: "6_2"    (Desktop Applications)
  search_url_param: "category_id=6&sub_category=desktop_applications"
  fallback_category_id: "6"

ai_agent_development:
  fiverr_category_id: "6"
  fiverr_subcategory_id: "6_11"   (Chatbots)
  search_url_param: "category_id=6&sub_category=chatbots"
  fallback_category_id: "6"

mcp_ai_agent:
  fiverr_category_id: "6"
  fiverr_subcategory_id: "6_11"
  search_url_param: "category_id=6&sub_category=chatbots"
  fallback_category_id: "6"

n8n_automation:
  fiverr_category_id: "6"
  fiverr_subcategory_id: "6_2"
  search_url_param: "category_id=6&sub_category=desktop_applications"
  fallback_category_id: "6"

gumloop_automation:
  fiverr_category_id: "6"
  fiverr_subcategory_id: "6_2"
  search_url_param: "category_id=6&sub_category=desktop_applications"
  fallback_category_id: "6"

workflow_automation:
  fiverr_category_id: "6"
  fiverr_subcategory_id: "6_2"
  search_url_param: "category_id=6&sub_category=desktop_applications"
  fallback_category_id: "6"

python_web_scraping:
  fiverr_category_id: "6"
  fiverr_subcategory_id: "6_2"
  search_url_param: "category_id=6&sub_category=desktop_applications"
  fallback_category_id: "6"

NICHE_CATEGORY_MAP_VERSION = "1.0"
NICHE_CATEGORY_MAP_NEXT_VALIDATION = "2026-08-29"

---

## Core Functions

build_search_url(keyword, niche_id, strictness, page=1) -> str
  Returns Fiverr search URL with category constraint.
  Unknown niche: returns NONE-strictness URL + logs WARNING (never raises).
  Page offset: (page - 1) * 16
  Special chars: URL-encoded with urllib.parse.quote(keyword, safe="")

search_with_fallback(keyword, niche_id, config, collect_fn) -> (results, strictness)
  Tries SUBCATEGORY -> CATEGORY -> NONE until len(results) >= min_threshold (default 5).
  Returns (results, strictness_used). Never raises. Always returns something.

check_category_mapping_freshness() -> bool
  Returns True when today >= NICHE_CATEGORY_MAP_NEXT_VALIDATION.
  Called at pipeline start to warn when quarterly re-validation is due.

---

## Demand Confidence Deduction for NONE Strictness

When search_strictness_used = "NONE" on a post-R1 SearchResult:
  confidence_breakdown["unconstrained_search"] = -0.08
  score_components note: "Demand from unconstrained search. Re-collect recommended."

Legacy rows (collected before R1 was active) are never retroactively penalized.

---

## Category Validation Sweep (R1.6.2)

Run before activating in production to verify category IDs match live Fiverr:
  python src/collection/search_url_builder.py --sweep --niches all
  Compares constrained vs unconstrained result counts per niche
  Outputs recommendation: SUBCATEGORY / CATEGORY / NONE per niche
  Lock decision DL-207 (URL param shape) after sweep

---

## Permanent Regressions

REG-13: test_fiverr_search_url_always_includes_category_filter_for_production_niches
  all 9 production niches emit category_id param with SUBCATEGORY strictness

REG-14: test_unconstrained_search_result_applies_demand_confidence_deduction
  NONE-strictness SearchResult (post-R1) triggers -0.08 demand confidence deduction
