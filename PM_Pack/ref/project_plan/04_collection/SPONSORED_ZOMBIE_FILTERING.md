# Sponsored and Zombie Gig Filtering
# Fiverr Research System -- SRDI Initiative Wave D (R3)

**Document Status:** Active
**Source:** WAVE_D_SPONSORED_AND_ZOMBIE_GIG_FILTERING.md
**Epic:** R3 (SCRUM-598 to SCRUM-604)
**Modules:** src/collection/gig_detail.py (updated), src/analysis/zombie_gig_detector.py (NEW)
**Tier:** 0 -- ships with R1

---

## Problem Statement

Sponsored gigs are paid placements -- not organic competition. Including them in
competition top-10 inflates difficulty. Counting their TRC inflates demand.

Zombie gigs are indexed-but-abandoned -- they have few/no recent reviews and are
unlikely to be active competition. They suppress the review barrier and level ratio.

"10k+" review counts were returning 0 due to a parsing bug.

---

## R3.1: Sponsored Flag Propagation

Stage 3 (search collection) parses gig_cards JSON which includes sponsored_flag per card.
Stage 4 (gig_detail.py) propagates this flag to the Gig model.

_urls_match(url_a, url_b) -> bool:
  Normalize both: lowercase, strip scheme (https://), strip query string (?...),
  strip trailing slash. Then compare normalized strings.
  Handles: http vs https, ?ref=xxx, path case differences.

_propagate_sponsored_flag(gig, gig_cards):
  For each card in gig_cards:
    if _urls_match(card.url, gig.gig_url):
      gig.is_sponsored = card.sponsored_flag
      break
  If no match: gig.is_sponsored = None (treat as organic per backward compat)

SearchResult columns populated:
  sponsored_gig_count = sum(1 for c in gig_cards if c.sponsored_flag)
  organic_gig_count = len(gig_cards) - sponsored_gig_count

---

## R3.2: Sponsored Exclusion in Scoring

competition.py: sponsored gigs excluded from top-10 window
  organic_gigs = [g for g in top_gigs if g.is_sponsored is not True][:10]

feasibility.py: sponsored gigs excluded from level ratio and review barrier

demand.py: TRC sponsored-fraction adjustment (active until R4.1 ships):
  sponsored_fraction = sponsored_gig_count / max(total, 1)
  sponsored_fraction <= 10%: multiplier = 1.00
  sponsored_fraction <= 20%: multiplier = 0.90
  sponsored_fraction <= 35%: multiplier = 0.80
  sponsored_fraction >  35%: multiplier = 0.70
  NOTE: once R4.1 ships, this is superseded by the single TRC reliability multiplier.
  Never stack both (Decision DL-209).

---

## R3.3: Review Count Parsing Fix

parse_review_count(s) -> int | None:
  regex r"([0-9.]+)[kK]\+?" -> multiply by 1000
  "10k+"  -> 10000
  "2.5k"  -> 2500
  "1,234" -> 1234
  "42"    -> 42
  None/empty -> None

---

## R3.3: Zombie Detection Algorithm

New module: src/analysis/zombie_gig_detector.py

ZOMBIE_THRESHOLD = 0.50
MIN_ACCOUNT_AGE_DAYS = 180

compute_zombie_score(gig, seller, reference_date=None) -> (float, dict):

  CRITICAL GUARD (run first):
  if seller.member_since and (ref - seller.member_since).days < MIN_ACCOUNT_AGE_DAYS:
    return 0.0, {"new_seller": True, "account_age_days": N}
  (This prevents Dec 2025 new sellers with 2 reviews being misclassified as zombies)

  score = 0.0; signals = {}

  Signal 1: review_count < 10 -> +0.30
  Signal 2: last_reviewed_at > 365 days ago (or no reviews ever) -> +0.25/+0.20
  Signal 3: response_rate < 30% -> +0.15
  Signal 4: orders_in_queue = 0 AND review_count < 5 -> +0.10

  return min(score, 1.0), signals

is_zombie_gig(gig, seller) -> bool:
  score, _ = compute_zombie_score(gig, seller)
  return score >= ZOMBIE_THRESHOLD

---

## R3.4: Stage 4.5 Wiring

Called as sub-step of Stage 4 (gig_detail.py), per gig:

  if config.relevance.enable_zombie_filter:
    zombie_score, zombie_signals = compute_zombie_score(gig, seller)
    gig.is_zombie = zombie_score >= ZOMBIE_THRESHOLD
    gig.zombie_score = zombie_score
    gig.zombie_signals = zombie_signals

  gig.last_reviewed_at = _extract_last_review_date(gig.review_snippets)

_extract_last_review_date(snippets) -> datetime | None:
  Parses date formats: "Jan 2022", "2022-01-15", "3 months ago", etc.
  Returns None for unparseable input without raising.

---

## R3.5: Zombie Exclusion in Scoring

competition.py:  zombie gigs excluded from top-10 (never set competition pressure)
feasibility.py:  zombie gigs excluded from level ratio (never distort difficulty)
feasibility.py:  zombie gigs excluded from review barrier (never set artificially low)
profitability.py: zombie gig prices excluded from price distribution

Confidence deduction:
  zombie_fraction = zombie_count / max(total_organic_gigs, 1)
  zombie_fraction >= 0.50: confidence_breakdown["zombie_concentration_high"]    = -0.10
  zombie_fraction >= 0.25: confidence_breakdown["zombie_concentration_moderate"] = -0.05

---

## R3.6: Pagination Normalization

TOP_N_FOR_SCORING = 10 (hard cap regardless of pages collected)
pages_collected stored on SearchResult for audit trail.
All scoring uses only top 10 gigs regardless of collection depth.

---

## Permanent Regressions

REG-17: test_sponsored_gigs_never_included_in_competition_top10
REG-18: test_zombie_gigs_never_used_in_feasibility_review_barrier
REG-19: test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20_percent

Critical test (NOT a permanent REG but must pass):
  test_zombie_score_low_reviews_new_account:
  new seller Dec 2025 + 2 reviews -> score = 0.0, is_zombie = False
