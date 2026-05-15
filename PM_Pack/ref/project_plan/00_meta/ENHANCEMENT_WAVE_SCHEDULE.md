# Enhancement Wave Schedule — Post-Wave 8
# Fiverr Research System
# Created: 2026-05-12

---

## Gap Analysis: What You Asked vs. What's Already Built

Before creating new waves, here's what the existing Waves 0–8 already cover and what's genuinely new:

### ALREADY FULLY COVERED (No new wave needed)

| Your Request | Where It's Covered |
|---|---|
| Connection lost / save state / resume | Wave 4: RETRY_AND_CHECKPOINT.md — atomic checkpoints every 50 records, `--mode resume`, checkpoint JSON, resume algorithm |
| Start new run while in middle of another | Wave 4: QUEUE_DESIGN.md — run status tracking, CANCELLED status, new run clears queue |
| Unauthenticated scraping before login | Wave 4: PLAYWRIGHT_SESSION_DESIGN.md — SessionManager handles both auth/unauth; search results, gig cards, and many fields are public |
| Files/reports saved incrementally | Wave 4: checkpoints + Wave 8: exports auto-generated after every run |
| LLM model selection optimization | Wave 7: each of 11 tasks assigned gpt-4o or gpt-4o-mini based on complexity; cache layer |
| What new/avg/pro sellers are doing | Wave 5: SELLER_STRENGTH_MODEL (authority_score), COMPETITOR_PROFILING (weakness analysis), GIG_QUALITY_RUBRIC (15 criteria across all seller levels) |

### PARTIALLY COVERED (Needs enhancement, not full new wave)

| Your Request | What Exists | Gap |
|---|---|---|
| Pricing optimization for new sellers | Wave 6: PROFITABILITY_SCORE analyzes competitor pricing tiers and upsells | Missing: optimal entry price calculator, undercut strategy, price-to-first-order model |
| Best gig images/thumbnails/profile setup | Wave 7: THUMBNAIL_DIRECTION task gives creative direction | Missing: image pattern analysis from competitors, profile setup checklist, visual best practices |
| Dashboard design depth | Wave 8: DASHBOARD_PLAN has 6 pages with widgets | Missing: UI/UX design system, mobile responsiveness, interaction patterns, visual styling guide |

### GENUINELY NEW (Requires new waves)

| Your Request | What's Needed |
|---|---|
| Pricing Strategy Engine | Full pricing model: competitor price distribution, price-to-conversion analysis, optimal entry pricing, dynamic pricing recommendations per keyword |
| LLM-Powered Niche Discovery ("Gold Mining") | Autonomous niche/keyword discovery loop: LLM analyzes scored data → generates new search hypotheses → scores results → learns from outcomes → iterates |
| Gig Creation Playbook | Comprehensive best-practice engine: what top sellers do across title, description, images, profile, FAQ, packages — distilled into actionable templates |
| Extended Seller Intelligence | Profile optimization checklist, response templates, portfolio strategy, review solicitation patterns |
| Dashboard UX Overhaul | Full design system, component library, interaction patterns, responsive layout, visual polish |

---

## Enhancement Wave Schedule

| Wave | Name | Documents | Purpose |
|---|---|---|---|
| 9 | Pricing Strategy Engine | 4 docs | Competitor price analysis, optimal entry pricing, undercut strategy, price-to-first-order model |
| 10 | LLM-Powered Niche Discovery | 4 docs | Autonomous discovery loop, hypothesis generation, scoring feedback, gold-level detection |
| 11 | Gig Creation Playbook | 3 docs | Visual/text best practices, profile optimization, seller setup checklist |
| 12 | Dashboard UX Overhaul | 3 docs | Design system, component library, interaction polish, responsive layout |

**Total new documents:** 14
**Estimated planning time:** 4 waves

---

## Wave 9 — Pricing Strategy Engine

### WHY THIS MATTERS
The existing Profitability Score (Wave 6) tells you WHETHER a niche is profitable. It does NOT tell you WHAT PRICE TO SET as a new seller. That's a completely different question. A keyword can score 80 on profitability but the optimal entry price for a brand-new seller with zero reviews is very different from what established sellers charge.

### Documents to Write

**9A. PRICE_DISTRIBUTION_ANALYSIS.md**
- Competitor price distribution curves per keyword (histogram of Basic/Standard/Premium prices)
- Price quartile analysis: what percentage of sellers charge $X–$Y at each tier
- Price clustering: natural price points in the market (e.g., most sellers cluster at $50, $95, $150)
- Price-to-review correlation: do higher-priced sellers have more reviews? (moat analysis)
- Price gap detection: empty price bands where no one is competing
- Median, mean, mode, and IQR per keyword and per niche
- Data source: gigs.packages (already collected in Stage 4)

**9B. NEW_SELLER_PRICING_MODEL.md**
- Optimal entry price calculator for zero-review sellers
- Formula: base_price = f(competitor_median, new_seller_discount, niche_floor, demand_signal)
- Undercut strategy: how far below established sellers to price without triggering race-to-bottom
- Price ladder: recommended price increases at review milestones (5, 10, 25, 50, 100 reviews)
- Tier-specific recommendations: Basic (acquisition price), Standard (margin price), Premium (aspirational price)
- "First 5 orders" pricing vs. "established seller" pricing
- Integration with revenue gate tracker: does entry pricing support the month 4/6/9/10/12 gates?

**9C. PRICING_RECOMMENDATIONS_LLM.md**
- LLM task #12 (new): generates pricing recommendation based on competitor price distribution + new seller position
- Prompt template receives: price histogram, price quartiles, competitor weakness data, niche pricing config
- Output: recommended Basic/Standard/Premium prices with reasoning, plus 3-month price ladder
- Integrates into RecommendationOutput as a new field: `pricing_strategy`

**9D. PRICING_DASHBOARD_WIDGETS.md**
- New widgets for Opportunities page: price distribution histogram per keyword
- New widgets for Recommendations page: pricing strategy card with entry price + ladder
- Price heatmap: keywords × price tiers showing where competition clusters
- Revenue projection: at recommended entry prices, how many orders to hit each revenue gate

---

## Wave 10 — LLM-Powered Niche Discovery ("Gold Mining")

### WHY THIS MATTERS
The current system researches 9 pre-defined niches. But what if the BEST opportunities are in niches you haven't thought of? This wave creates an autonomous discovery loop where the LLM analyzes everything the system has learned and generates hypotheses for new keywords, sub-niches, and adjacent markets — then the system tests those hypotheses automatically.

### Documents to Write

**10A. DISCOVERY_ENGINE_ARCHITECTURE.md**
- Discovery Loop: Score existing data → LLM generates hypotheses → System tests hypotheses → Score results → Feed back to LLM
- Discovery modes:
  - `adjacent_keyword`: LLM suggests keywords related to high-scoring existing keywords
  - `adjacent_niche`: LLM suggests entirely new niche categories based on skill overlap
  - `gap_exploit`: LLM identifies pricing/quality gaps in existing data and suggests keywords targeting those gaps
  - `trend_chase`: LLM analyzes Google Trends + Reddit signals to suggest emerging keywords before they saturate
- Discovery budget: max N new keywords per run, max $X LLM cost per discovery cycle
- Hypothesis scoring: each LLM suggestion gets a `hypothesis_confidence` (0–1) before committing collection resources
- Feedback loop: after collection and scoring, actual scores are compared to hypothesis_confidence → LLM learns which hypothesis types perform best
- Gold-level threshold: configurable "gold score" (default 85+) that triggers immediate notification

**10B. HYPOTHESIS_GENERATION_PROMPTS.md**
- 4 Jinja2 prompt templates (one per discovery mode)
- Each prompt receives: top 10 highest-scoring keywords with full score breakdown, top 5 lowest-competition keywords, demand trend data, niche saturation levels, skill profile from config
- Output: ranked list of 5–10 keyword suggestions with:
  - `suggested_keyword`: the actual search term
  - `rationale`: why this keyword should perform well (must reference specific data)
  - `hypothesis_confidence`: 0–1 estimate
  - `expected_demand`: LOW/MEDIUM/HIGH
  - `expected_competition`: LOW/MEDIUM/HIGH
  - `category_path`: likely Fiverr category
- Temperature: 0.4 (slightly more creative than recommendation tasks)
- Model: gpt-4o (needs strong reasoning for hypothesis quality)

**10C. DISCOVERY_SCORING_AND_FEEDBACK.md**
- After a discovery keyword completes collection + scoring:
  - Compare actual Final Score to hypothesis_confidence
  - Track hit rate: what % of hypotheses scored above the gold threshold
  - Track miss patterns: which hypothesis types consistently underperform
  - Feed summary back to LLM in next cycle: "Your last 10 adjacent_keyword suggestions averaged 52.3 final score — focus on keywords with clearer transactional intent"
- Discovery leaderboard: ranked list of discovered keywords by final score
- Auto-retire: keywords that score below 30 after full analysis are auto-retired (not rescored in future runs)
- Gold alert: any discovered keyword scoring 85+ triggers NEW_GOLD_DISCOVERY alert

**10D. DISCOVERY_DASHBOARD_WIDGETS.md**
- New Page 7 on dashboard: "Discovery" (or tab within Opportunities)
- Hypothesis queue: pending suggestions waiting for collection
- Discovery results: scored keywords with hypothesis_confidence vs. actual_score comparison
- Hit rate trend: line chart of hypothesis accuracy over time
- Gold discoveries: highlighted cards for 85+ scores
- Discovery cost tracker: LLM spend on hypothesis generation vs. value of discoveries found
- Discovery mode performance: which of the 4 modes produces the best results

---

## Wave 11 — Gig Creation Playbook

### WHY THIS MATTERS
The recommendation engine (Wave 7) generates gig CONTENT — titles, descriptions, packages. But it doesn't analyze what makes top sellers' gigs VISUALLY and STRUCTURALLY successful. This wave adds pattern analysis for images, profile setup, and seller presentation — the things that influence buyer decisions beyond text.

### Documents to Write

**11A. GIG_VISUAL_ANALYSIS.md**
- Thumbnail classification: expand the existing thumbnail_class to capture more patterns
  - Image type: mockup, screenshot, text-heavy, photo, illustration, abstract, video thumbnail
  - Color scheme: dark/light/branded/colorful
  - Text presence: none, keyword-overlay, headline, feature-list
  - People: no people, headshot, team, stock photo
  - Quality indicator: professional, amateur, AI-generated, template
- Competitor image audit: for top 10 gigs per keyword, classify all gallery images (not just thumbnail)
- Pattern detection: which visual patterns correlate with high review counts and high conversion
- LLM task (gpt-4o with vision): analyze competitor thumbnail screenshots and extract winning patterns
- Collection: screenshot competitor gig cards during Stage 4 (Playwright screenshot API)
- Storage: image metadata in gig_visual_analysis table (no raw images stored — just classifications)

**11B. SELLER_PROFILE_OPTIMIZATION.md**
- Profile elements to analyze from competitor sellers:
  - Bio structure: length, tone, credentials mentioned, specializations listed
  - Profile image: professional headshot vs. logo vs. avatar vs. none
  - Languages listed and their impact on buyer reach
  - Response time badge: how it correlates with authority_score
  - Portfolio items: count, quality, relevance to gig
  - Skills tests: which Fiverr skill tests top sellers have completed
  - Social proof: external links, certifications, education mentioned
- New seller profile checklist: ordered list of profile setup actions with priority
- LLM task: generate personalized profile optimization recommendations based on competitor analysis
- Integration: new section in RecommendationOutput — `profile_recommendations`

**11C. SELLER_SETUP_PLAYBOOK.md**
- End-to-end new seller onboarding guide (generated per niche):
  - Account setup checklist (profile photo, bio, skills tests, portfolio)
  - First gig creation walkthrough (using recommendation data)
  - First 5 orders strategy (pricing, delivery speed, communication templates)
  - Review acquisition strategy (how top sellers in this niche get reviews)
  - Response time optimization
  - Buyer request strategy (how to use Fiverr's buyer request feature)
  - Promotion strategy: social media, portfolio, outside traffic
- Template-based: Jinja2 templates that pull from recommendation + competitor data
- Export as PDF playbook per niche

---

## Wave 12 — Dashboard UX Overhaul

### WHY THIS MATTERS
The Wave 8 dashboard is FUNCTIONAL but uses default Streamlit styling. For daily use, it needs to feel polished, intuitive, and fast. This wave adds a design system, component patterns, and interaction polish.

### Documents to Write

**12A. DESIGN_SYSTEM.md**
- Color palette: primary, secondary, accent, status colors (GO/PASS/MONITOR/etc.)
- Typography: font family, size scale, weight hierarchy
- Spacing system: 4px base grid, consistent padding/margins
- Component library:
  - ScoreCard: reusable score display with mini-bar + label + value
  - TagBadge: color-coded GO/PASS badge component
  - AlertBanner: severity-colored dismissible banner
  - MetricBox: single KPI display (value + label + trend arrow)
  - DataTable: sortable, filterable table with row actions
  - ChartContainer: consistent chart wrapper with title, subtitle, and export button
  - RecommendationCard: the full card layout as a reusable component
  - FilterBar: consistent filter row across all pages
- Dark mode support: CSS variable-based theming
- Loading states: skeleton screens for data-heavy views
- Empty states: helpful messages when no data exists yet
- Custom Streamlit CSS injection via st.markdown with unsafe_allow_html

**12B. INTERACTION_PATTERNS.md**
- Navigation flow: how users move between pages (breadcrumbs, back links, cross-references)
- Keyboard shortcuts: common actions (R = refresh, N = new run, / = search)
- Notification system: toast notifications for completed actions, run status changes
- Progressive disclosure: summary → detail → raw data drill-down pattern
- Bulk actions: select multiple recommendations for export, select multiple keywords for comparison
- Comparison mode: side-by-side keyword comparison view (2-3 keywords, all scores)
- Quick actions: one-click export, one-click regenerate, one-click run
- Help tooltips: every metric and chart has a "?" tooltip explaining what it means
- Onboarding flow: first-run wizard that guides user through initial niche setup

**12C. RESPONSIVE_AND_PERFORMANCE.md**
- Streamlit layout optimization: column ratios, container widths, expander usage
- Chart performance: lazy-load charts below the fold, limit data points for large datasets
- Query optimization: SQLAlchemy query patterns that avoid N+1 problems
- Caching strategy: st.cache_data for expensive queries with appropriate TTLs
- Session state management: what goes in st.session_state vs. what gets re-queried
- Mobile considerations: Streamlit on mobile browser (column stacking, touch targets)
- Data pagination: tables with 100+ rows use server-side pagination
- Export performance: large Excel files generated asynchronously with progress bar

---

## Implementation Priority

| Priority | Wave | Rationale |
|---|---|---|
| 1st | Wave 9 — Pricing Strategy | Directly answers "what price should I set?" — most immediately actionable for a new seller |
| 2nd | Wave 10 — Discovery Engine | Highest long-term value — system becomes self-improving and finds opportunities you'd never think of |
| 3rd | Wave 11 — Gig Playbook | Turns research into action — bridges the gap between "this keyword is good" and "here's exactly how to create the gig" |
| 4th | Wave 12 — Dashboard UX | Polish layer — makes daily use pleasant but doesn't change analytical capability |

---

## Updated Master Wave Schedule

| Wave | Name | Status |
|---|---|---|
| 0 | Foundation | COMPLETE |
| 1 | Vision and Product Design | COMPLETE |
| 2 | Technical Architecture | COMPLETE |
| 3 | Data Schema and Source Design | COMPLETE |
| 4 | Collection Engine Design | COMPLETE |
| 5 | Analysis and Competitor Model | COMPLETE |
| 6 | Scoring System | COMPLETE |
| 7 | Recommendation Engine | COMPLETE |
| 8 | Reporting and Dashboard | COMPLETE |
| 9 | Pricing Strategy Engine | **NEXT** |
| 10 | LLM-Powered Niche Discovery | PLANNED |
| 11 | Gig Creation Playbook | PLANNED |
| 12 | Dashboard UX Overhaul | PLANNED |
