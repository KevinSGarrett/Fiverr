# DOD — EPIC 03: Analysis Engine
# Fiverr Research System — Definitions of Done & Acceptance Criteria

---

## Story 3.1 — Keyword Clustering

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-3.1.1 | Embeddings are L2-normalized (norm ≈ 1.0 for each vector) | `np.linalg.norm()` test |
| AC-3.1.2 | K selection: 20 keywords → k=ceil(sqrt(10))=4 clusters | Formula test |
| AC-3.1.3 | K capped at 2 (minimum) and 20 (maximum) | Boundary test |
| AC-3.1.4 | Silhouette score logged and warning emitted when < 0.3 | Log capture test |
| AC-3.1.5 | Cluster labels are 3-5 words, unique per cluster | Length + uniqueness test |
| AC-3.1.6 | Re-cluster triggers when > 15% new keywords added | Threshold calculation test |
| AC-3.1.7 | Every keyword has a non-null cluster_id after clustering | DB null check |

---

## Story 3.2 — Gig Quality Analysis

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-3.2.1 | Each gig analyzed produces 15 criterion scores (0-10 each) | Count + range test |
| AC-3.2.2 | A gig with no description, no FAQ, generic title → weakness_score ≥ 7.0 | Known-bad gig test |
| AC-3.2.3 | A gig with proof elements, specific deliverables, clear scope → weakness_score ≤ 3.0 | Known-good gig test |
| AC-3.2.4 | At least 3 weakness types detected per analyzed gig (most gigs have some weaknesses) | Minimum detection test |
| AC-3.2.5 | overall_weakness_score is inverted (higher = more exploitable) | Direction test |

---

## Story 3.3 — Competitor Profiling

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-3.3.1 | competitor_strength in range 0-10 for every scored seller | Range test |
| AC-3.3.2 | Cluster synthesis has exactly 4 sections (who_dominates, why_they_win, the_gap, entry_verdict) | Structure test |
| AC-3.3.3 | entry_feasibility_rating is 0-10 float | Range test |
| AC-3.3.4 | Positioning gaps list contains ≥ 1 gap per cluster with non-empty evidence | Non-empty test |

---

## Story 3.4 — Seller Strength Model

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-3.4.1 | authority_score in range 0-10 for every analyzed seller | Range test |
| AC-3.4.2 | Seller with 500 reviews, Level 2, 100% response rate → authority_score ≥ 7.0 | High-authority test |
| AC-3.4.3 | Seller with 2 reviews, New Seller, no portfolio → authority_score ≤ 3.0 | Low-authority test |
| AC-3.4.4 | is_new_seller correctly identifies sellers with < 5 reviews | Threshold test |

---

## Story 3.5 — Saturation Model

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-3.5.1 | saturation_score in range 0-100 | Range test |
| AC-3.5.2 | Jaccard similarity correctly flags "AI PRD writing" vs "AI PRD writer" as similar (> 0.65) | Known-pair test |
| AC-3.5.3 | Keyword with 95% duplicate gig titles → saturation_score ≥ 80 | High-saturation test |
| AC-3.5.4 | Keyword with diverse unique titles → saturation_score ≤ 40 | Low-saturation test |

---

## Story 3.6 — Review Analysis

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-3.6.1 | Review text "delivered 2 weeks late" triggers LATE_DELIVERY red flag | Pattern match test |
| AC-3.6.2 | Review text "amazing work, exactly what I needed" does NOT trigger any red flag | False positive test |
| AC-3.6.3 | top_buyer_complaints returns ≤ 5 items sorted by frequency | Count + order test |

---

## Story 3.7 — Intent Classification

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-3.7.1 | "hire python developer for automation" → TRANSACTIONAL or HIGH_INTENT | Classification test |
| AC-3.7.2 | "what is python automation" → INFORMATIONAL | Classification test |
| AC-3.7.3 | All keywords have non-null intent_class after classification | DB null check |

---

## Epic 03 — Overall Definition of Done

1. ✅ `--mode analyze-only` runs Stages 7-9 on existing collected data without errors
2. ✅ All gigs have quality scores, all sellers have authority scores
3. ✅ Keywords are clustered with labels and silhouette scores logged
4. ✅ Competitor synthesis exists for every cluster with ≥ 3 gigs
5. ✅ All analysis tests pass (pytest)
