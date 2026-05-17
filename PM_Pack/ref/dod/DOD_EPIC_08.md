# DOD — EPIC 08: Playbook Engine
# Fiverr Research System — Definitions of Done & Acceptance Criteria

---

## Story 8.1 — Gig Visual Analysis

### Definition of Done
- [ ] GigVisualAnalysis model populated for all scraped gig thumbnails
- [ ] thumbnail_type classified (branded/stock/illustration/text_only/screenshot)
- [ ] visual_strength_score computed and stored

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-8.1.1 | Thumbnail screenshot saved as PNG at data/screenshots/{gig_id}.png | File existence test |
| AC-8.1.2 | Classification returns all 6 dimensions with valid enum values | Enum validation test |
| AC-8.1.3 | image_type correctly classifies a known screenshot-style thumbnail as "screenshot" | Known-image test |
| AC-8.1.4 | Pattern correlation identifies top 3 visual styles per niche from ≥ 10 classified gigs | Coverage + count test |
| AC-8.1.5 | GigVisualAnalysis row created for every classified gig | DB count test |

---

## Story 8.2 — Seller Profile Optimization

### Definition of Done
- [ ] generate_profile_optimization() returns valid ProfileOptimization schema
- [ ] Bio template includes [PLACEHOLDER] markers for personalisation
- [ ] Output stored in Recommendation profile_optimization field

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-8.2.1 | Profile pattern extraction analyzes top 10 sellers per niche | Seller count test |
| AC-8.2.2 | Profile checklist has exactly 12 items | Count test |
| AC-8.2.3 | bio_template is 100-300 words with placeholder tokens for personalization | Word count + placeholder test |
| AC-8.2.4 | specialization_tags list contains 3-5 tags | Count range test |
| AC-8.2.5 | Task 13 integrates into recommendation async gather without errors | Integration test |

---

## Story 8.3 — Seller Setup Playbook Generator

### Definition of Done
- [ ] Full seller setup playbook generated as structured document
- [ ] Playbook covers: gig setup, profile, pricing, thumbnail, FAQ
- [ ] All required recommendation fields populated before playbook generation

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-8.3.1 | Playbook has exactly 5 sections with correct headers | Section count + header test |
| AC-8.3.2 | Section 1 references actual score data (demand, competition, opportunity) | Content presence test |
| AC-8.3.3 | Section 2 includes at least 3 gig title suggestions from recommendations | Count test |
| AC-8.3.4 | Section 4 includes entry pricing with specific dollar amounts | Dollar format regex test |
| AC-8.3.5 | Section 5 includes price ladder milestones with review thresholds | Milestone presence test |
| AC-8.3.6 | Rendered Markdown is valid with proper heading hierarchy (H1 > H2 > H3) | Markdown lint test |

---

## Story 8.4 — Playbook PDF Export

### Definition of Done
- [ ] Playbook exported as PDF using WeasyPrint
- [ ] PDF includes all playbook sections with correct formatting
- [ ] Export path follows data/exports/playbook/ convention

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-8.4.1 | PDF file generated at data/exports/playbooks/{niche_id}_{date}.pdf | File existence test |
| AC-8.4.2 | PDF has cover page + table of contents + ≥ 5 content pages | Page count ≥ 7 test |
| AC-8.4.3 | PDF file size between 200KB and 2MB (reasonable for styled doc with charts) | File size range test |
| AC-8.4.4 | Embedded charts render as visible graphics (not broken images) | Visual inspection / PDF parser test |

---

## Story 8.5 — Visual Recommendations

### Definition of Done
- [ ] generate_visual_recommendations() uses GigVisualAnalysis patterns
- [ ] Visual recommendations stored in Recommendation visual_recommendations field
- [ ] Recommendations are specific (not generic placeholder text)

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-8.5.1 | thumbnail_style recommendation references actual top-performing patterns in niche | Pattern match test |
| AC-8.5.2 | gallery_recommendations includes item count (3-5) and types | Count + type test |
| AC-8.5.3 | Task 14 does not make an LLM call (uses pre-computed visual analysis data) | Cost tracking: $0 for task 14 |

---

## Epic 08 — Overall Definition of Done

1. ✅ Visual analysis classifies thumbnails for all gigs with screenshots
2. ✅ Profile optimization produces actionable recommendations per niche
3. ✅ Playbook generator creates 5-section guides for every STRONG GO keyword
4. ✅ PDF export produces professional, styled documents with embedded charts
5. ✅ All playbook tests pass
