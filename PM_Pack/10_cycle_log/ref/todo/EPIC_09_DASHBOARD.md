# EPIC 09 — Dashboard & Reporting
# Fiverr Research System — Implementation To-Do

**Source Specs:** Wave 8 (07_reporting), Wave 12 (12_dashboard_ux)
**Depends On:** Epics 01-08 (all data layers)
**Priority:** P1
**Estimated Stories:** 16 | **Estimated Tasks:** 78

---

## Story 9.1 — Design System Implementation

| ID | Task | Type | Description |
|---|---|---|---|
| 9.1.1 | Create styles.py | TASK | `src/dashboard/styles.py` — inject_custom_css() with full design system CSS from DESIGN_SYSTEM.md |
| 9.1.2 | Implement color palette CSS variables | TASK | Primary, neutral, semantic (GO/PASS tags), status, score gradient, discovery gold |
| 9.1.3 | Implement typography system | TASK | Inter font import, modular scale, 7 font sizes, weight/line-height tokens |
| 9.1.4 | Implement spacing system | TASK | 4px grid tokens: space-1 through space-16, component-specific spacing |
| 9.1.5 | Implement dark mode toggle | TASK | CSS variable swap via st.sidebar.toggle, persisted in session_state |
| 9.1.6 | Implement Streamlit overrides | TASK | Custom sidebar, tab, metric, button, dataframe, expander, toast styling |
| 9.1.7 | Hide default Streamlit chrome | TASK | MainMenu, footer, header visibility: hidden |

---

## Story 9.2 — Reusable Component Library

| ID | Task | Type | Description |
|---|---|---|---|
| 9.2.1 | Create components.py | TASK | `src/dashboard/components.py` — All 8 reusable components from DESIGN_SYSTEM.md |
| 9.2.2 | Implement ScoreCard component | TASK | Mini-bar with label, value, colored progress. Sizes: sm (inline), md (card), lg (detail) |
| 9.2.3 | Implement TagBadge component | TASK | Color-coded GO/PASS pill with icon. 5 tag styles + 2 sizes |
| 9.2.4 | Implement AlertBanner component | TASK | Severity-colored dismissible banner. HIGH (red), MEDIUM (amber), LOW (blue) |
| 9.2.5 | Implement MetricBox component | TASK | KPI display with value, label, optional trend delta arrow |
| 9.2.6 | Implement styled DataTable | TASK | Enhanced st.dataframe with score gradient, tag column formatting |
| 9.2.7 | Implement ChartContainer | TASK | Consistent chart wrapper with title, subtitle, help text. Standard Plotly layout config |
| 9.2.8 | Implement RecommendationCard | TASK | Full recommendation display: tag + score header, tabbed body for all 14 fields |
| 9.2.9 | Implement FilterBar | TASK | Consistent filter row: select, multiselect, search inputs |
| 9.2.10 | Implement skeleton loading cards | TASK | Pulse-animated placeholder cards for data loading states |
| 9.2.11 | Implement empty state renderer | TASK | 6 named empty states with icons, messages, and action suggestions |

---

## Story 9.3 — Page 1: Opportunities (Landing Page)

| ID | Task | Type | Description |
|---|---|---|---|
| 9.3.1 | Create page_opportunities.py | TASK | `src/dashboard/pages/opportunities.py` — Decision view with KPI metrics + card grid |
| 9.3.2 | Implement KPI metric row | TASK | 5 MetricBoxes: Total Keywords, STRONG GO count, CONDITIONAL GO count, Avg Score, Best Opportunity |
| 9.3.3 | Implement filter bar | TASK | Niche filter, tag multi-select, sort dropdown (Final Score, Demand, Opportunity, Trend) |
| 9.3.4 | Implement opportunity card grid | TASK | 2-column grid of keyword cards: tag badge + score + key metrics + "View Details" expander |
| 9.3.5 | Implement tag distribution chart | TASK | Plotly horizontal bar: count per tag category with tag colors |
| 9.3.6 | Implement alert banner row | TASK | Show active HIGH/MEDIUM alerts from Alert table at top of page |
| 9.3.7 | Create opportunities page tests | TASK | Test data loading, filter behavior, metric calculations |

---

## Story 9.4 — Page 2: Keywords

| ID | Task | Type | Description |
|---|---|---|---|
| 9.4.1 | Create page_keywords.py | TASK | `src/dashboard/pages/keywords.py` — Full keyword database with search + sort + detail view |
| 9.4.2 | Implement keyword search | TASK | Text search across keyword_text with instant filter |
| 9.4.3 | Implement sortable data table | TASK | Columns: keyword, niche, tag, final_score, demand, competition, opportunity, trend, confidence |
| 9.4.4 | Implement keyword detail expander | TASK | Click row → expand: radar chart (6 scores), score breakdown table, competitor summary, pricing |
| 9.4.5 | Implement radar chart | TASK | Plotly Scatterpolar: demand, competition (inverted), opportunity, feasibility, profitability, trend |
| 9.4.6 | Implement "Add to Compare" button | TASK | Adds keyword to compare_keywords session state (max 3) |
| 9.4.7 | Implement comparison mode | TASK | Side-by-side table + overlay radar chart for 2-3 keywords |
| 9.4.8 | Implement paginated table | TASK | 50 rows per page with page controls for 100+ keyword databases |

---

## Story 9.5 — Page 3: Competitors

| ID | Task | Type | Description |
|---|---|---|---|
| 9.5.1 | Create page_competitors.py | TASK | `src/dashboard/pages/competitors.py` — Competitive intelligence per niche |
| 9.5.2 | Implement niche selector | TASK | Dropdown to select niche, loads competitor data for that niche |
| 9.5.3 | Implement cluster cards | TASK | One card per cluster: label, keyword count, avg competition score, top 3 sellers |
| 9.5.4 | Implement synthesis narrative display | TASK | Expandable: who_dominates, why_they_win, the_gap, entry_verdict |
| 9.5.5 | Implement seller detail expander | TASK | Click seller → authority score, review count, level, weakness list, gig count |
| 9.5.6 | Implement weakness heatmap | TASK | Plotly heatmap: weakness types (rows) × clusters (columns), color by frequency |

---

## Story 9.6 — Page 4: Recommendations

| ID | Task | Type | Description |
|---|---|---|---|
| 9.6.1 | Create page_recommendations.py | TASK | `src/dashboard/pages/recommendations.py` — Gig-ready packages |
| 9.6.2 | Implement recommendation card list | TASK | Full-width RecommendationCards, sorted by score descending |
| 9.6.3 | Implement tabbed recommendation detail | TASK | 8 tabs: Titles, Packages, Description, Differentiation, FAQ, Risks, Pricing, Profile |
| 9.6.4 | Implement "Regenerate" button per recommendation | TASK | Triggers per-keyword recommendation regeneration |
| 9.6.5 | Implement bulk selection + export | TASK | Checkbox per recommendation, bulk export to Markdown/Excel/JSON |
| 9.6.6 | Implement playbook download link | TASK | If playbook PDF exists, show download button |

---

## Story 9.7 — Page 5: Run History

| ID | Task | Type | Description |
|---|---|---|---|
| 9.7.1 | Create page_run_history.py | TASK | `src/dashboard/pages/run_history.py` — Operational monitoring |
| 9.7.2 | Implement run list table | TASK | Paginated: run_id, mode, status, duration, keywords_scored, cost, timestamp |
| 9.7.3 | Implement run detail expander | TASK | Stage-by-stage breakdown: stage name, duration, record count, errors |
| 9.7.4 | Implement revenue tracker sidebar | TASK | Revenue gate chart: cumulative revenue vs gate thresholds, ON_TRACK/BEHIND badge |
| 9.7.5 | Implement run comparison | TASK | Select 2 runs → delta view: new keywords, score changes, new recommendations |

---

## Story 9.8 — Page 6: LLM Costs

| ID | Task | Type | Description |
|---|---|---|---|
| 9.8.1 | Create page_llm_costs.py | TASK | `src/dashboard/pages/llm_costs.py` — Budget monitoring |
| 9.8.2 | Implement cost summary metrics | TASK | Total cost, avg cost per run, cache hit rate, cost per keyword |
| 9.8.3 | Implement cost by model chart | TASK | Plotly pie/donut: gpt-4o vs gpt-4o-mini vs embeddings cost split |
| 9.8.4 | Implement cost by stage chart | TASK | Plotly bar: cost per pipeline stage |
| 9.8.5 | Implement cost trend chart | TASK | Plotly line: cost per run over time |
| 9.8.6 | Implement cache hit rate chart | TASK | Plotly gauge or line: cache hit % over time |

---

## Story 9.9 — Page 7: Discovery

| ID | Task | Type | Description |
|---|---|---|---|
| 9.9.1 | Create page_discovery.py | TASK | `src/dashboard/pages/discovery.py` — Autonomous exploration results |
| 9.9.2 | Implement gold discovery banner | TASK | Prominent gold-styled banner for any gold discoveries (score ≥ 85) |
| 9.9.3 | Implement discovery leaderboard | TASK | Ranked table of discovery keywords: keyword, mode, hypothesis_confidence, actual_score, is_gold |
| 9.9.4 | Implement mode hit rate chart | TASK | Plotly bar: hit rate per discovery mode |
| 9.9.5 | Implement cycle history chart | TASK | Plotly line: discoveries per cycle, cost per cycle, gold count over time |
| 9.9.6 | Implement keyword promotion button | TASK | "Promote to Niche" action on discovery keywords |

---

## Story 9.10 — Interaction Patterns

| ID | Task | Type | Description |
|---|---|---|---|
| 9.10.1 | Create interactions.py | TASK | `src/dashboard/interactions.py` — Navigation, shortcuts, notifications, session state |
| 9.10.2 | Implement cross-page navigation | TASK | navigate_to(page, entity_id) via session_state |
| 9.10.3 | Implement breadcrumb trail | TASK | Dynamic breadcrumbs based on current page + entity |
| 9.10.4 | Implement keyboard shortcuts | TASK | JavaScript injection: R, N, /, 1-7, Esc, E, ? |
| 9.10.5 | Implement toast notifications | TASK | notify(message, type) for 8 event types |
| 9.10.6 | Implement quick actions sidebar | TASK | Full Run, Recs Only, Export All, Discover buttons |
| 9.10.7 | Implement session state management | TASK | initialize_session_state() with all defaults |
| 9.10.8 | Implement first-run onboarding wizard | TASK | 4-step wizard for empty database state |
| 9.10.9 | Implement help tooltips | TASK | TOOLTIPS dict + help_tooltip() renderer for every metric |

---

## Story 9.11 — Query Layer

| ID | Task | Type | Description |
|---|---|---|---|
| 9.11.1 | Create queries.py | TASK | `src/dashboard/queries.py` — Pre-built batch queries per page. Source: RESPONSIVE_AND_PERFORMANCE.md |
| 9.11.2 | Implement get_opportunities_page_data() | TASK | Single join query: keywords + scores + rankings + recommendation exists flag |
| 9.11.3 | Implement get_recommendations_page_data() | TASK | Eager-loaded recommendations with keyword data |
| 9.11.4 | Implement get_competitors_page_data() | TASK | Clusters + sellers + gig quality per niche |
| 9.11.5 | Implement get_run_history_data() | TASK | Run logs with stage breakdowns |
| 9.11.6 | Implement get_llm_cost_data() | TASK | Aggregated LLM usage by model, stage, run |
| 9.11.7 | Implement get_discovery_data() | TASK | Discovery keywords + outcomes + cycle logs |
| 9.11.8 | Implement caching decorators | TASK | @st.cache_data with appropriate TTLs per query |

---

## Story 9.12 — Export System

| ID | Task | Type | Description |
|---|---|---|---|
| 9.12.1 | Create export_manager.py | TASK | `src/exports/export_manager.py` — Centralized export handler |
| 9.12.2 | Implement CSV export | TASK | Keywords, recommendations, scores as CSV |
| 9.12.3 | Implement Excel multi-sheet export | TASK | openpyxl: Summary + Keywords + Scores + Recommendations + Pricing + Competitors sheets |
| 9.12.4 | Implement JSON full export | TASK | Complete database snapshot as structured JSON |
| 9.12.5 | Implement Markdown report export | TASK | Per-niche opportunity report with recommendations |
| 9.12.6 | Implement PDF opportunity report | TASK | WeasyPrint: styled opportunity report with charts |
| 9.12.7 | Implement export trigger from dashboard | TASK | Download buttons on each page + "Export All" quick action |
| 9.12.8 | Create export tests | TASK | Test each format: file creation, structure, content correctness |

---

## Story 9.13 — Alert System

| ID | Task | Type | Description |
|---|---|---|---|
| 9.13.1 | Create alert_manager.py | TASK | `src/reports/alert_manager.py` — Generate, store, and manage alerts |
| 9.13.2 | Implement 8 alert types | TASK | NEW_STRONG_GO, SCORE_DROP, COMPETITOR_CHANGE, PRICE_RAISE_DUE, GOLD_DISCOVERY, RUN_FAILED, SELECTOR_BROKEN, DEAD_LETTER_THRESHOLD |
| 9.13.3 | Implement alert severity classification | TASK | HIGH: RUN_FAILED, SELECTOR_BROKEN. MEDIUM: SCORE_DROP, COMPETITOR_CHANGE. LOW: NEW_STRONG_GO, PRICE_RAISE_DUE |
| 9.13.4 | Implement alert resolution | TASK | Mark alert as resolved with resolution_note |
| 9.13.5 | Implement alert display on Opportunities page | TASK | AlertBanner component showing unresolved HIGH/MEDIUM alerts |
| 9.13.6 | Create alert system tests | TASK | Test each alert type creation, severity, resolution |

---

## Story 9.14 — App Entry Point

| ID | Task | Type | Description |
|---|---|---|---|
| 9.14.1 | Create app.py | TASK | `src/dashboard/app.py` — Main Streamlit app with sidebar navigation, page routing, all initializations |
| 9.14.2 | Implement page routing | TASK | st.sidebar.radio → page function mapping |
| 9.14.3 | Implement sidebar footer | TASK | Last run time, niche count, keyword count |
| 9.14.4 | Implement performance measurement | TASK | measure_page_load() wrapper with debug logging |
| 9.14.5 | Wire `python run.py dashboard` | TASK | Launches `streamlit run src/dashboard/app.py` |

---

## Story 9.15 — Mobile Optimization

| ID | Task | Type | Description |
|---|---|---|---|
| 9.15.1 | Implement responsive CSS | TASK | Column stacking at 768px, reduced padding, larger touch targets |
| 9.15.2 | Implement responsive metric row | TASK | Auto-stacking metrics on narrow viewports |
| 9.15.3 | Test on mobile viewport | TASK | Verify all pages render correctly at 375px width |

---

## Story 9.16 — Pricing Dashboard Widgets

| ID | Task | Type | Description |
|---|---|---|---|
| 9.16.1 | Implement price distribution chart | TASK | Plotly histogram + KDE overlay on Keywords page detail expander |
| 9.16.2 | Implement price gap visualization | TASK | Highlighted gaps on price distribution chart |
| 9.16.3 | Implement price ladder step chart | TASK | Current position + future milestones on Recommendations page |
| 9.16.4 | Implement revenue gate chart | TASK | Dual-axis: cumulative revenue (bar) + gate thresholds (line) on Run History page |

---

## Epic 09 Summary: 16 Stories, 78 Tasks
