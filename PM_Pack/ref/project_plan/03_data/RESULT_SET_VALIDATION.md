# Result Set Validation -- Stage 3.5
# Fiverr Research System -- SRDI Initiative Wave C (R2)

**Document Status:** Active
**Source:** WAVE_C_POST_COLLECTION_RELEVANCE_VALIDATION.md
**Epic:** R2 (SCRUM-605 to SCRUM-612)
**Modules:** src/analysis/result_set_validator.py (NEW),
             src/analysis/result_set_validation_workflow.py (NEW)
**Pipeline:** Immediately after Stage 3 (Fiverr Search), before Stage 4 (Gig Detail)
**Tier:** 0 -- must ship before first recommendation

---

## What Stage 3.5 Does

For each keyword collected in a run, Stage 3.5:
  1. Scores each gig title for relevance to the keyword (0.0-1.0)
  2. Aggregates individual scores to a result-set relevance score
  3. Detects ghost markets (<0.20 relevance with >5 results, or 0 cards)
  4. Writes a ResultSetValidation row for each (keyword_id, run_id)
  5. Updates Gig.relevance_flag and Gig.relevance_score on each gig
  6. Updates SearchResult with denormalized ghost/contamination flags
  7. Emits a confidence_deduction that all downstream scorers consume

Stage 3.5 is fail-soft: an error on one keyword does not abort the run.
UPSERT behavior: re-running Stage 3.5 overwrites the existing RSV row.

---

## Result Set Relevance Score Definition

result_set_relevance_score (0.0-1.0): fraction of returned gig titles that are
genuinely about the searched keyword.

Score interpretation:
  1.0: All titles clearly match keyword intent
  0.80: 8/10 match -- minor contamination
  0.60: 6/10 match -- moderate contamination, scores degraded
  0.40: 4/10 match -- significant contamination, strong deduction
  0.20: 2/10 match -- severe contamination, results nearly unusable
  0.00: No titles match -- ghost market or complete semantic broadening

---

## Per-Gig Relevance Scoring: 4 Signals

Implemented in: compute_gig_relevance(gig_title, keyword, niche_id, gig_url) -> GigRelevanceResult

Signal 1 Core term match: +0.30 per core_term found in title (max +0.60)
Signal 2 Keyword overlap:  +0.25 when >= 1 keyword words appear in title
Signal 3 Exclusion terms: -0.25 per non-negated exclusion term hit
Signal 4 Generic penalty:  -0.15 when 3+ generic phrases AND 0 core terms

Generic phrases: "i will do", "professional", "high quality", "best", "expert",
  "top quality", "custom", "quick delivery"

Final score = max(0.0, min(1.0, sum of signals))
relevance_flag = True when score >= 0.35

Special cases:
  Missing title: score=0.0, flag=False, reason="missing_title"
  Non-English title: score=0.50, flag=True (neutral -- include without penalty)
  Negation guard: exclusion term preceded by not/avoid/no/without/unlike
    within 15 chars -> skip that exclusion term

Rejection reasons (when flag=False):
  "exclusion_term_match:TERM" -- exclusion term found (not negated)
  "no_niche_terms"            -- score < 0.35 AND 0 core terms matched
  "low_relevance_score:X.XX"  -- score < 0.35 (other reason)

---

## Result-Set Aggregate Validation

validate_result_set(gig_cards, keyword, niche_id) -> ResultSetValidationResult:

  Score all gig cards via compute_gig_relevance()
  total = len(gig_cards)
  relevant = [r for r in results if r.relevance_flag]
  rsv_score = len(relevant) / max(total, 1)

  Ghost threshold from config (per_niche or 0.20 global default)
  ghost_flag = (total == 0) OR (rsv_score < ghost_threshold AND total > 5)
  contamination_flag = not ghost_flag AND rsv_score < 0.60 AND total >= 5

  Confidence deduction tiers:
    rsv >= 0.80: 0.0
    rsv >= 0.60: -0.05
    rsv >= 0.40: -0.15 (+ contamination_flag)
    rsv >= 0.20: -0.30 (+ contamination_flag)
    rsv <  0.20 (total > 5) OR 0 cards: -0.50 (+ ghost_flag)

---

## Stage 3.5 Orchestrator

run_stage_3_5_validation(run_id, niche_id, db, config) -> dict:

  if not config.relevance.enable_stage_3_5: return {"skipped": True}

  For each keyword in run+niche:
    try:
      Load SearchResult; parse gig_cards JSON
      rsv_result = validate_result_set(gig_cards, kw.keyword, niche_id)
      Write/upsert ResultSetValidation row
      Update SearchResult denormalized flags
      Update Gig.relevance_flag and Gig.relevance_score per URL match
      If ghost: log immediate WARNING with top-5 gig titles
      db.commit()
    except Exception as e:
      log error; stats["skipped"] += 1; db.rollback()

  Returns: {keywords_validated, ghost_markets, contamination_flags, skipped}

The stats dict is emitted to the run summary and used to generate alerts.

---

## Scoring Integration

All scoring calculators check RSV via get_result_set_validation(keyword_id, run_id, db):
  If rsv is None: no penalty, no filter (backward compat -- identical to pre-SRDI)
  If rsv present: apply relevant deductions and filters (see SRDI addenda per file)

Ghost market absolute block: if rsv.ghost_market_flag is True:
  passes_recommendation_gates() returns False unconditionally.
  No score, however high, produces a recommendation for a ghost market keyword.

---

## Permanent Regressions

REG-15: test_ghost_market_blocks_recommendation_generation_absolutely
REG-16: test_trc_qualified_by_result_set_relevance_score_in_demand

See also: 03_data/VALIDATION_RULES.md for NICHE_VALIDATION_CONFIG (all 9 niches)
See also: 03_data/SCHEMA.md for ResultSetValidation model (M1 migration)
