# EPIC 08 — Playbook Engine
# Fiverr Research System — Implementation To-Do

**Source Specs:** Wave 11 (11_playbook)
**Depends On:** Epic 02 (Collection — gig/seller data), Epic 03 (Analysis — quality data)
**Priority:** P2
**Estimated Stories:** 7 | **Estimated Tasks:** 38

---

## Story 8.1 — Gig Visual Analysis

| ID | Task | Type | Description |
|---|---|---|---|
| 8.1.1 | Create GigVisualAnalyzer | TASK | `src/playbook/visual_analysis.py` — Classify gig thumbnails using gpt-4o vision. Source: GIG_VISUAL_ANALYSIS.md |
| 8.1.2 | Implement thumbnail screenshot capture | TASK | During gig detail collection (Stage 4), save thumbnail to data/screenshots/{gig_id}.png |
| 8.1.3 | Implement 6-dimension classification | TASK | image_type (photo/illustration/screenshot/text_heavy/mockup/abstract), color_scheme (warm/cool/neutral/brand_colors/high_contrast), text_presence (none/minimal/moderate/heavy), people (none/headshot/full/team), quality (low/medium/high/professional), brand_consistency (none/partial/full) |
| 8.1.4 | Create visual classification LLM prompt | TASK | gpt-4o with image input: classify thumbnail against 6 dimensions + generate quality_notes |
| 8.1.5 | Implement pattern correlation | TASK | Correlate visual dimensions with gig performance (reviews, score). Identify winning visual patterns per niche |
| 8.1.6 | Implement visual best practices extraction | TASK | Per-niche: top 3 visual styles, color schemes, text approaches used by top sellers |
| 8.1.7 | Store GigVisualAnalysis entries | TASK | Per-gig: all 6 dimensions + quality_notes + is_top_performer flag |
| 8.1.8 | Create visual analysis tests | TASK | Test classification output format, pattern correlation, best practices extraction |

---

## Story 8.2 — Seller Profile Optimization (LLM Task 13)

| ID | Task | Type | Description |
|---|---|---|---|
| 8.2.1 | Create ProfileOptimizer | TASK | `src/playbook/profile_optimizer.py` — Analyze top seller profiles, generate optimization recommendations. Source: SELLER_PROFILE_OPTIMIZATION.md |
| 8.2.2 | Implement profile pattern extraction | TASK | Analyze top 10 sellers per niche: bio structure, credential mentions, specialization keywords, social proof elements |
| 8.2.3 | Implement profile checklist generation | TASK | Generate a 12-item checklist: avatar type, bio length, credentials, portfolio count, skill tests, languages, etc. |
| 8.2.4 | Create profile_optimization.j2 prompt | TASK | Input: top seller profiles + niche context. Output: bio_template, headline, specialization_tags, improvement_actions |
| 8.2.5 | Create ProfileOptimization output schema | TASK | bio_template, headline, specialization_tags, credential_suggestions, portfolio_recommendations |
| 8.2.6 | Create profile optimizer tests | TASK | Test pattern extraction, checklist generation, LLM output format |

---

## Story 8.3 — Seller Setup Playbook Generator

| ID | Task | Type | Description |
|---|---|---|---|
| 8.3.1 | Create PlaybookGenerator | TASK | `src/playbook/playbook_generator.py` — Generate complete seller setup playbook per niche. Source: SELLER_SETUP_PLAYBOOK.md |
| 8.3.2 | Implement 5-section playbook structure | TASK | Sections: 1) Niche Overview & Opportunity, 2) Gig Creation Guide, 3) Profile Setup, 4) First 5 Orders Strategy, 5) Growth Roadmap |
| 8.3.3 | Implement Section 1: Niche Overview | TASK | Pulls from: scores, competitor analysis, market type, demand signals |
| 8.3.4 | Implement Section 2: Gig Creation Guide | TASK | Pulls from: recommendation output (titles, packages, description, FAQ, tags, thumbnail direction) |
| 8.3.5 | Implement Section 3: Profile Setup | TASK | Pulls from: profile optimization output (bio, headline, credentials) |
| 8.3.6 | Implement Section 4: First 5 Orders Strategy | TASK | Pulls from: pricing analysis (entry pricing, acquisition pricing, first-order discount strategy) |
| 8.3.7 | Implement Section 5: Growth Roadmap | TASK | Pulls from: price ladder milestones, review velocity targets, revenue gates |
| 8.3.8 | Implement playbook Markdown renderer | TASK | Render complete playbook as structured Markdown with headers, tables, checklists |
| 8.3.9 | Create playbook tests | TASK | Test each section generation, markdown rendering |

---

## Story 8.4 — Playbook PDF Export

| ID | Task | Type | Description |
|---|---|---|---|
| 8.4.1 | Create playbook PDF renderer | TASK | `src/playbook/pdf_export.py` — Convert Markdown playbook to styled PDF using WeasyPrint |
| 8.4.2 | Implement PDF styling | TASK | Professional styling: cover page, table of contents, section headers, page numbers, brand colors |
| 8.4.3 | Implement chart embedding | TASK | Embed price distribution chart and radar chart as inline SVGs in PDF |
| 8.4.4 | Create PDF export tests | TASK | Test PDF generation, page count, file size |

---

## Story 8.5 — Visual Recommendations (Task 14)

| ID | Task | Type | Description |
|---|---|---|---|
| 8.5.1 | Create generate_visual_recommendations() | TASK | Non-LLM task: uses visual pattern analysis to recommend thumbnail style, color scheme, text approach |
| 8.5.2 | Implement pattern-based recommendation | TASK | Top performing patterns in niche → recommended visual strategy |
| 8.5.3 | Implement gallery recommendation | TASK | Recommended gallery item count, types (screenshot, mockup, video), based on top performer analysis |
| 8.5.4 | Create visual recommendation tests | TASK | Test pattern matching, recommendation output |

---

## Story 8.6 — Playbook Stage Wiring

| ID | Task | Type | Description |
|---|---|---|---|
| 8.6.1 | Wire visual analysis into Stage 4 | TASK | Screenshot + classify during gig detail collection |
| 8.6.2 | Wire profile analysis into Stage 13 | TASK | Task 13 runs as part of recommendation generation |
| 8.6.3 | Wire visual recommendations into Stage 13 | TASK | Task 14 runs after visual analysis data is available |
| 8.6.4 | Wire playbook generation post-Stage 13 | TASK | Playbook generates after recommendations for STRONG GO keywords |

---

## Story 8.7 — Playbook Dashboard Data Layer

| ID | Task | Type | Description |
|---|---|---|---|
| 8.7.1 | Create get_visual_pattern_data() | TASK | Returns visual dimension distributions per niche for charts |
| 8.7.2 | Create get_profile_checklist_data() | TASK | Returns profile checklist with current status per item |
| 8.7.3 | Create get_playbook_list_data() | TASK | Returns list of generated playbooks with niche, date, download link |

---

## Epic 08 Summary: 7 Stories, 38 Tasks
