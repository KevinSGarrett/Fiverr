# EPIC 07 — Discovery Engine
# Fiverr Research System — Implementation To-Do

**Source Specs:** Wave 10 (10_discovery)
**Depends On:** Epic 04 (Scoring — discovery learns from scored keywords)
**Priority:** P2 — Enhances system but not required for core pipeline
**Estimated Stories:** 9 | **Estimated Tasks:** 46

---

## Story 7.1 — Discovery Engine Core Loop

| ID | Task | Type | Description |
|---|---|---|---|
| 7.1.1 | Create DiscoveryEngine class | TASK | `src/discovery/engine.py` — Main loop: generate hypotheses → collect data → score → evaluate → learn. Source: DISCOVERY_ENGINE_ARCHITECTURE.md |
| 7.1.2 | Implement run_discovery_cycle() | TASK | Single cycle: select mode → generate hypotheses → filter by budget → collect → score → record outcomes |
| 7.1.3 | Implement budget gate | TASK | Track cumulative LLM cost per cycle. Abort if exceeds max_cost_per_run from config |
| 7.1.4 | Implement cycle logging | TASK | Create DiscoveryCycleLog entry per cycle: mode, hypotheses_generated, keywords_added, gold_found, cost |
| 7.1.5 | Implement mode selection logic | TASK | Round-robin across enabled modes, with preference for historically highest-hit-rate mode |
| 7.1.6 | Create discovery engine tests | TASK | Test cycle execution, budget gate, mode rotation |

---

## Story 7.2 — Hypothesis Mode: Adjacent Keyword

| ID | Task | Type | Description |
|---|---|---|---|
| 7.2.1 | Create AdjacentKeywordGenerator | TASK | `src/discovery/modes/adjacent_keyword.py` — LLM generates nearby keyword variations from high-scoring seeds |
| 7.2.2 | Create adjacent_keyword.j2 prompt | TASK | Input: top 5 keywords per niche. Output: 10-15 adjacent keyword suggestions with confidence 0-1 |
| 7.2.3 | Implement deduplication against existing | TASK | Jaccard similarity 0.65 threshold against all known keywords |
| 7.2.4 | Create adjacent keyword tests | TASK | Test dedup, output format, confidence range |

---

## Story 7.3 — Hypothesis Mode: Adjacent Niche

| ID | Task | Type | Description |
|---|---|---|---|
| 7.3.1 | Create AdjacentNicheGenerator | TASK | `src/discovery/modes/adjacent_niche.py` — LLM proposes new niches related to existing portfolio |
| 7.3.2 | Create adjacent_niche.j2 prompt | TASK | Input: 9 current niches + skill profile. Output: 3-5 niche suggestions with seed keywords |
| 7.3.3 | Implement niche validation | TASK | LLM-generated niches get 2-3 seed keywords automatically collected for feasibility check |
| 7.3.4 | Create adjacent niche tests | TASK | Test output format, seed keyword generation |

---

## Story 7.4 — Hypothesis Mode: Gap Exploit

| ID | Task | Type | Description |
|---|---|---|---|
| 7.4.1 | Create GapExploitGenerator | TASK | `src/discovery/modes/gap_exploit.py` — Finds positioning gaps in existing niches |
| 7.4.2 | Create gap_exploit.j2 prompt | TASK | Input: competitor weaknesses + pricing gaps per niche. Output: keyword + positioning angle suggestions |
| 7.4.3 | Implement gap-to-keyword mapping | TASK | Convert positioning gaps to searchable keywords |
| 7.4.4 | Create gap exploit tests | TASK | Test gap detection, keyword conversion |

---

## Story 7.5 — Hypothesis Mode: Trend Chase

| ID | Task | Type | Description |
|---|---|---|---|
| 7.5.1 | Create TrendChaseGenerator | TASK | `src/discovery/modes/trend_chase.py` — LLM identifies emerging trends in tech/AI that could become Fiverr niches |
| 7.5.2 | Create trend_chase.j2 prompt | TASK | Input: current date context + skill profile + recent trend data. Output: 5-10 trending keywords with confidence |
| 7.5.3 | Implement trend validation | TASK | Cross-reference LLM suggestions with Google Trends to filter noise |
| 7.5.4 | Create trend chase tests | TASK | Test output format, trend validation logic |

---

## Story 7.6 — Discovery Scoring and Feedback

| ID | Task | Type | Description |
|---|---|---|---|
| 7.6.1 | Create DiscoveryScorer | TASK | `src/discovery/scorer.py` — Score discovery hypotheses after collection + analysis |
| 7.6.2 | Implement gold detection | TASK | Gold threshold: discovery keyword scores ≥ 85. Generate GOLD_DISCOVERY alert |
| 7.6.3 | Implement outcome recording | TASK | Store DiscoveryOutcome: keyword_id, hypothesis_confidence, actual_score, is_gold, mode |
| 7.6.4 | Implement feedback loop | TASK | Track hit rate per mode (% keywords scoring ≥ 60). Weight future mode selection by hit rate |
| 7.6.5 | Implement discovery leaderboard data | TASK | Rank all discovery keywords by score, highlight golds |
| 7.6.6 | Create scoring and feedback tests | TASK | Test gold detection, hit rate calculation, feedback weighting |

---

## Story 7.7 — Discovery Keyword Integration

| ID | Task | Type | Description |
|---|---|---|---|
| 7.7.1 | Mark discovery keywords | TASK | Set Keyword.is_discovery=True, Keyword.discovery_mode, Keyword.hypothesis_confidence |
| 7.7.2 | Integrate into collection pipeline | TASK | Discovery keywords enter the same collection + analysis pipeline as seed keywords |
| 7.7.3 | Prevent discovery pollution | TASK | Discovery keywords don't contaminate niche averages until manually promoted |
| 7.7.4 | Implement keyword promotion | TASK | Dashboard action: promote discovery keyword to permanent niche keyword (sets is_discovery=False) |

---

## Story 7.8 — Stage 16 Orchestration

| ID | Task | Type | Description |
|---|---|---|---|
| 7.8.1 | Wire Stage 16 (Discovery) | TASK | Runs after all other stages in `--mode full`. Optional skip via config.discovery.enabled=false |
| 7.8.2 | Implement `--mode discovery-only` | TASK | Run only the discovery cycle using existing scored data |
| 7.8.3 | Implement `--mode discovery-collect` | TASK | Run discovery cycle + collect data for new hypotheses + score them |
| 7.8.4 | Create Stage 16 integration test | TASK | Pre-seed scored data → run discovery → verify hypotheses generated, collected, scored |

---

## Story 7.9 — Discovery Dashboard Widgets (Data Layer)

| ID | Task | Type | Description |
|---|---|---|---|
| 7.9.1 | Create get_discovery_leaderboard_data() | TASK | Returns ranked discovery keywords with scores, tags, modes, gold flags |
| 7.9.2 | Create get_mode_hit_rate_data() | TASK | Returns hit rate per mode for bar chart |
| 7.9.3 | Create get_discovery_cycle_history_data() | TASK | Returns cycle logs for trend chart |
| 7.9.4 | Create get_gold_discoveries_data() | TASK | Returns all gold discoveries with details |

---

## Epic 07 Summary: 9 Stories, 46 Tasks
