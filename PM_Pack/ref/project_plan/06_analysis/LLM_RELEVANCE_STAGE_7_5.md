# LLM Relevance Classification -- Stage 7.5
# Fiverr Research System -- SRDI Initiative Wave F (R5)

**Document Status:** Active
**Source:** WAVE_F_LLM_RELEVANCE_CLASSIFICATION.md
**Epic:** R5 (SCRUM-624/625 + SCRUM-816/823/830/835/841)
**Module:** src/analysis/llm_relevance_classifier.py (NEW)
**Pipeline:** After Stage 7 (Gig Quality LLM), before Stage 8 (Competitor Profiling)
**Tier:** 2 -- requires R2 (RSV) running first
**Budget:** max 50 calls/run at gpt-4o-mini (~$0.06/run)

---

## Purpose: Cost-Proportional Defense

Stage 3.5 (rule-based) clears the clearly clean and clearly contaminated keywords.
Stage 7.5 handles the AMBIGUOUS MIDDLE BAND (RSV 0.35-0.75) where rules cannot decide.

Architecture principle (Decision DL-200):
  Stage 3.5: rule-based (fast, cheap, scales to all keywords)
  Stage 7.5: LLM only (conditional on ambiguity + budget cap)
  Never apply LLM to keywords that rules already resolved.

---

## Trigger Gate (_should_run_llm)

Fires Stage 7.5 when ALL of the following are true:
  1. RSV 0.35-0.75 (ambiguous band)
  2. final_score >= 45 (high enough to matter)
  3. rsv.llm_validated is False (idempotent guard -- never re-process)

ALWAYS fires (regardless of score) when:
  keyword.source == "discovery" AND RSV in 0.35-0.75 (high stakes)
  keyword.keyword in config.relevance.ghost_market_watch_list

NEVER fires when:
  RSV is None (no validation yet)
  rsv.llm_validated = True (already processed this run)
  RSV < 0.35 or RSV > 0.75 (rules have decided -- IRRELEVANT or CLEAN)

---

## Call Budget and Caching

Cap: MAX_LLM_RELEVANCE_CALLS_PER_RUN = 50
Ordering: process keywords by descending final_score (highest value first)
When budget exhausted: log "LLM relevance budget exhausted: N/50 calls used for [niche]"
Keywords that exceed budget: keep rule-based RSV score unchanged

Cache key: "relevance_v1:" + sha256(prompt.encode())[:16].hex()
On cache hit: return cached verdict, do NOT count toward budget
On LLM error: return None, keep rule-based RSV (fail-soft, never crash run)

---

## LLM Prompt Template

Model: gpt-4o-mini (pinned in config; fallback to None on deprecation)
max_tokens: 600

NICHE_EXPECTED_SERVICE_DESCRIPTIONS provides niche-specific service context:
  python_automation:  "Python automation scripts and workflow automation services"
  ai_agent_development: "AI agent development and LLM integration services"
  mcp_ai_agent:  "Model Context Protocol (MCP) tool integration services for Claude"
  n8n_automation: "n8n workflow automation and no-code integration services"
  (etc. for all 9 niches; fallback: "services related to {keyword}")

Prompt instructs LLM to:
  1. Classify each top-10 gig as RELEVANT, IRRELEVANT, or BORDERLINE
  2. Give overall verdict: CLEAN / MIXED / CONTAMINATED / GHOST_MARKET
  3. Respond ONLY in JSON (no markdown fences, no preamble)
  4. Include contamination_explanation and dominant_competing_service if contaminated

JSON parse hardening:
  Strip ```json...``` fences before parsing
  On JSONDecodeError: log warning, return None, keep rule-based RSV

---

## Verdict to Action Mapping

CLEAN:
  llm_validated = True, llm_verdict = "CLEAN"
  No changes to per-gig flags or RSV score

MIXED:
  llm_validated = True, llm_verdict = "MIXED"
  No changes to RSV score (ambiguous but within acceptable range)

CONTAMINATED:
  llm_validated = True, llm_verdict = "CONTAMINATED"
  rsv.result_set_relevance_score = llm_relevant_count / len(gigs)
  rsv.category_contamination_flag = True
  rsv.contamination_explanation = result.contamination_explanation (if present)
  rsv.dominant_competing_service = result.dominant_competing_service (if present)

GHOST_MARKET:
  llm_validated = True, llm_verdict = "GHOST_MARKET"
  rsv.ghost_market_flag = True (OVERRIDE -- even if rule-based was clean)
  rsv.confidence_deduction = min(-0.50, existing_deduction)
  Trigger GHOST_MARKET_DETECTED alert row

Per-gig overrides:
  RELEVANT:    Gig.relevance_flag = True,  Gig.relevance_score = max(existing, 0.85)
  IRRELEVANT:  Gig.relevance_flag = False, Gig.relevance_score = min(existing, 0.15)
  BORDERLINE:  No change (rule-based score preserved -- non-destructive)

Idempotent guard: rsv.llm_validated = True -> return None immediately (no API call)

---

## Stage 7.5 Orchestrator

run_stage_7_5_llm_relevance(run_id, niche_id, db, config, llm_client, cache) -> dict:

  if not config.relevance.enable_llm_relevance: return {"skipped": True}

  Query ambiguous keywords: RSV 0.35-0.75, llm_validated=False, final_score >= 45
  Sort by descending final_score
  Loop up to 50 calls:
    classify_keyword_relevance(kw.id, db, config) -- handles trigger gate + LLM call
    Track: keywords_processed, ghost_markets_detected, contaminated_detected

  Emit stats to run summary:
    keywords_classified, ghost_markets_detected_by_llm,
    contaminated_detected_by_llm, calls_used/budget

Pipeline position: after Stage 7 (gig quality rubric), before Stage 8 (competitor profiling)
Config toggle: config.relevance.enable_llm_relevance (default True)

---

## Competitor Synthesis Relevance Pre-Filter (R5.6)

In run_cluster_synthesis() in competitor_profiler.py:

  relevant_gigs = [g for g in cluster_gigs if g.relevance_flag is not False]
  relevance_fraction = len(relevant_gigs) / max(len(cluster_gigs), 1)

  if relevance_fraction < 0.40:
    return {"status": "skipped_low_relevance",
            "message": "Re-collect with constrained URL."}

  elif relevance_fraction < 0.80:
    synthesis_gigs = relevant_gigs  (relevant-only)

  else:
    synthesis_gigs = cluster_gigs   (full set)

See COMPETITOR_PROFILING.md SRDI ADDENDUM for full detail.

---

## Gig Quality Rubric Pre-Check (R5.3/R5.5)

In score_gig_quality():
  if gig.relevance_flag is False: return score=0, skip_reason="irrelevant_gig"
  if gig.relevance_score < 0.35: return score=0, skip_reason="low_relevance_score"
  Otherwise: proceed with full rubric

See GIG_QUALITY_RUBRIC.md SRDI ADDENDUM.

---

## LLM RSV Columns (written by Stage 7.5)

ResultSetValidation model (R8 M1):
  llm_validated BOOL DEFAULT FALSE
  llm_relevant_count INT
  llm_verdict VARCHAR(20)       -- CLEAN/MIXED/CONTAMINATED/GHOST_MARKET
  contamination_explanation VARCHAR(500)
  dominant_competing_service VARCHAR(200)

---

## Permanent Regressions

REG-23: test_llm_ghost_market_verdict_propagates_to_recommendation_block
  LLM GHOST_MARKET verdict -> rsv.ghost_market_flag=True -> recommendation blocked

REG-24: test_competitor_synthesis_skipped_when_relevance_fraction_below_40_percent
  synthesis skipped when < 40% relevant gigs in cluster
