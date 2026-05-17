# DOD — EPIC 07: Discovery Engine
# Fiverr Research System — Definitions of Done & Acceptance Criteria

---

## Story 7.1 — Discovery Engine Core Loop

### Definition of Done
- [ ] Discovery cycle loop runs without error for all enabled modes
- [ ] Hypothesis budget respected (max_cost_per_run)
- [ ] DiscoveryCycleLog entry created per cycle

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-7.1.1 | run_discovery_cycle() completes one full cycle: generate → collect → score → record | Integration test |
| AC-7.1.2 | Budget gate aborts cycle when cumulative cost exceeds max_cost_per_run | Cost injection test: set max=0.01, verify abort |
| AC-7.1.3 | DiscoveryCycleLog created with correct fields: mode, hypotheses_generated, cost | DB assertion |
| AC-7.1.4 | Mode selection rotates across enabled modes, weighted by hit rate | Mode history tracking test |

---

## Story 7.2–7.5 — Hypothesis Modes (All 4)

### Definition of Done
- [ ] All 4 hypothesis modes (adjacent_keyword, adjacent_niche, gap_exploit, trend_chase) generate valid hypotheses
- [ ] Each mode respects the min_confidence threshold
- [ ] Hypotheses stored in discovery_hypotheses table

### Acceptance Criteria
| AC ID | Mode | Criteria | Validation Method |
|---|---|---|---|
| AC-7.2.1 | Adjacent Keyword | Generates 10-15 suggestions from top-scoring seed keywords | Count range test |
| AC-7.2.2 | Adjacent Keyword | Duplicates (Jaccard > 0.65) are filtered out before insertion | Dedup test |
| AC-7.2.3 | Adjacent Keyword | Each suggestion has hypothesis_confidence between 0.0 and 1.0 | Range test |
| AC-7.3.1 | Adjacent Niche | Generates 3-5 niche suggestions with 2-3 seed keywords each | Count + structure test |
| AC-7.3.2 | Adjacent Niche | Generated niches don't duplicate existing 9 niches | Name similarity check |
| AC-7.4.1 | Gap Exploit | Produces keyword suggestions based on competitor pricing/quality gaps | Non-empty output test |
| AC-7.4.2 | Gap Exploit | Each suggestion references a specific gap type (price_gap, quality_gap, specialization_gap) | Enum test |
| AC-7.5.1 | Trend Chase | Produces 5-10 trending keyword suggestions | Count range test |
| AC-7.5.2 | Trend Chase | Cross-validation with Google Trends filters out keywords with DECLINING trend | Filter test |

---

## Story 7.6 — Discovery Scoring and Feedback

### Definition of Done
- [ ] Discovery outcomes scored and fed back into hypothesis confidence
- [ ] Promoted keywords get is_discovery=True on Keyword model
- [ ] gold_threshold promotion logic works correctly

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-7.6.1 | Discovery keyword scoring ≥ 85 → is_gold=True and GOLD_DISCOVERY alert created | Threshold + alert test |
| AC-7.6.2 | DiscoveryOutcome records: hypothesis_confidence vs actual_score for every discovery keyword | Completeness test |
| AC-7.6.3 | Hit rate = count(actual_score ≥ 60) / total_outcomes, per mode | Calculation test |
| AC-7.6.4 | Mode with 40% hit rate gets selected 2× more often than mode with 20% | Weighted selection test |

---

## Story 7.7 — Discovery Keyword Integration

### Definition of Done
- [ ] Promoted discovery keywords enter the main keyword collection pipeline
- [ ] Keyword.discovery_mode set correctly for all promoted keywords

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-7.7.1 | Discovery keywords have is_discovery=True, discovery_mode set, hypothesis_confidence set | Field test |
| AC-7.7.2 | Discovery keywords pass through the full collection + analysis pipeline | Pipeline integration test |
| AC-7.7.3 | Niche averages exclude discovery keywords (is_discovery=True filtered out) | Aggregate query test |
| AC-7.7.4 | Promoting a discovery keyword sets is_discovery=False | Promotion action test |

---

## Story 7.8 — Stage 16 Orchestration

### Definition of Done
- [ ] `--mode discovery-only` runs Stage 16 only
- [ ] `--mode discovery-collect` runs collection then discovery
- [ ] Stage 16 wired in full pipeline orchestrator

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-7.8.1 | `--mode full` with discovery.enabled=true runs Stage 16 after Stage 15 | Stage order test |
| AC-7.8.2 | `--mode full` with discovery.enabled=false skips Stage 16 | Skip test |
| AC-7.8.3 | `--mode discovery-only` runs only Stage 16 | Stage count = 1 test |
| AC-7.8.4 | `--mode discovery-collect` runs discovery + collection for new hypotheses | Multi-stage test |

---

## Epic 07 — Overall Definition of Done

1. ✅ Discovery cycle generates hypotheses from all 4 modes
2. ✅ Budget gate prevents cost overruns
3. ✅ Gold discoveries are detected and alerted
4. ✅ Feedback loop adjusts mode selection based on hit rates
5. ✅ Discovery keywords integrate cleanly into the main pipeline without polluting niche averages
6. ✅ All discovery tests pass
