# DOD — EPIC 09: Dashboard & Reporting
# Fiverr Research System — Definitions of Done & Acceptance Criteria

---

## Story 9.1 — Design System Implementation

### Definition of Done
- [ ] Design tokens defined (colours, typography, spacing)
- [ ] Streamlit theme configured consistently across all pages
- [ ] Design system documented in src/dashboard/design.py

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-9.1.1 | inject_custom_css() adds CSS to Streamlit without errors | Page load test |
| AC-9.1.2 | Inter font loads from Google Fonts CDN | Network request check |
| AC-9.1.3 | Dark mode toggle swaps all CSS variable values | Visual test: backgrounds, text, borders change |
| AC-9.1.4 | Default Streamlit MainMenu, footer, header are hidden | DOM inspection |

---

## Story 9.2 — Reusable Component Library

### Definition of Done
- [ ] Reusable component library covers: score badge, tag chip, gig card, opportunity row
- [ ] All components tested with sample data
- [ ] Components available via src/dashboard/components.py

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-9.2.1 | ScoreCard renders at all 3 sizes (sm/md/lg) with correct color for score value | Visual test at values 20, 50, 80 |
| AC-9.2.2 | TagBadge renders all 5 tag types with correct colors and icons | Visual test for each tag |
| AC-9.2.3 | AlertBanner renders HIGH (red), MEDIUM (amber), LOW (blue) with correct icons | Visual test per severity |
| AC-9.2.4 | MetricBox shows delta arrow (↑ green / ↓ red) when delta provided | Visual test |
| AC-9.2.5 | DataTable applies score gradient to highlight_column | Visual test |
| AC-9.2.6 | ChartContainer wraps Plotly chart with title + subtitle | Visual test |
| AC-9.2.7 | Skeleton loading cards show pulse animation | Visual test |
| AC-9.2.8 | Empty state renderer shows correct icon + message for all 6 named states | Test each state key |

---

## Story 9.3 — Page 1: Opportunities

### Definition of Done
- [ ] Page 1 renders opportunities ranked by final_score
- [ ] GO/CAUTION/PASS tags displayed with correct colour
- [ ] Filters: niche, tag, min_score working

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-9.3.1 | Page loads in < 2 seconds with 500 keywords in database | Performance measurement |
| AC-9.3.2 | KPI metrics show correct counts: Total Keywords, STRONG GO count, etc. | Count verification against DB |
| AC-9.3.3 | Niche filter reduces displayed keywords to selected niche only | Filter test |
| AC-9.3.4 | Tag filter shows only keywords matching selected tags | Filter test |
| AC-9.3.5 | Sort by "Demand Score" reorders cards by demand_score descending | Order test |
| AC-9.3.6 | Alert banner shows unresolved HIGH alerts when present | Alert display test |
| AC-9.3.7 | Empty database shows "No data yet" empty state with setup instructions | Empty state test |

---

## Story 9.4 — Page 2: Keywords

### Definition of Done
- [ ] Page 2 renders all keywords with scores and cluster labels
- [ ] Sortable by each score dimension
- [ ] Search/filter by keyword text working

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-9.4.1 | Search for "python" filters to keywords containing "python" | Search test |
| AC-9.4.2 | Keyword detail expander shows radar chart with 6 correct axes | Chart test |
| AC-9.4.3 | "Add to Compare" adds keyword to compare list (max 3) | Session state test |
| AC-9.4.4 | Comparison mode shows side-by-side table + overlay radar | Visual test with 2 keywords |
| AC-9.4.5 | Pagination shows 50 rows per page with correct page controls | Row count + navigation test |

---

## Story 9.5 — Page 3: Competitors

### Definition of Done
- [ ] Page 3 renders competitor profiles per cluster
- [ ] Competitor strength score displayed
- [ ] synthesis_narrative displayed per cluster

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-9.5.1 | Niche selector loads all 9 niches | Option count test |
| AC-9.5.2 | Cluster cards show correct keyword count and avg score per cluster | Count verification |
| AC-9.5.3 | Synthesis narrative displays 4 sections (who/why/gap/verdict) | Section count test |
| AC-9.5.4 | Weakness heatmap renders with correct dimensions and color scale | Visual test |

---

## Story 9.6 — Page 4: Recommendations

### Definition of Done
- [ ] Page 4 renders full recommendation for selected keyword
- [ ] All 14 recommendation fields displayed
- [ ] Regenerate button triggers per-keyword regeneration

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-9.6.1 | Recommendation cards display in score-descending order | Sort order test |
| AC-9.6.2 | Tabbed detail shows all 8 tab labels | Tab count test |
| AC-9.6.3 | "Regenerate" triggers recommendation regeneration and shows toast notification | Action + notification test |
| AC-9.6.4 | Bulk export creates downloadable Markdown file with selected recommendations | File creation + download test |

---

## Stories 9.7–9.9 — Pages 5-7 (Run History, LLM Costs, Discovery)

### Acceptance Criteria
| AC ID | Page | Criteria | Validation Method |
|---|---|---|---|
| AC-9.7.1 | Run History | Run list shows all runs with correct status colors | Visual + count test |
| AC-9.7.2 | Run History | Revenue tracker shows ON_TRACK/BEHIND badge | Status calculation test |
| AC-9.8.1 | LLM Costs | Cost by model pie shows correct proportions | Data verification |
| AC-9.8.2 | LLM Costs | Cache hit rate gauge shows correct percentage | Calculation test |
| AC-9.9.1 | Discovery | Gold discoveries show gold-styled banner | Visual test |
| AC-9.9.2 | Discovery | "Promote to Niche" sets is_discovery=False and refreshes page | Action + DB test |

---

## Story 9.10 — Interaction Patterns

### Definition of Done
- [ ] Tab navigation between all 9 pages works
- [ ] State preserved across tab switches
- [ ] Mobile-responsive layout implemented

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-9.10.1 | Clicking keyword on Opportunities page navigates to Keywords page with that keyword expanded | Cross-page navigation test |
| AC-9.10.2 | Pressing "R" key refreshes page data | Keyboard shortcut test |
| AC-9.10.3 | Pressing "1" through "7" navigates to corresponding page | Keyboard shortcut test |
| AC-9.10.4 | Toast notification appears for run completion | Event trigger test |
| AC-9.10.5 | First-run onboarding wizard appears on empty database | Empty DB test |
| AC-9.10.6 | After completing onboarding step 4, wizard does not reappear | onboarding_complete flag test |

---

## Story 9.11 — Query Layer

### Definition of Done
- [ ] All DB queries use DashboardQueryLayer
- [ ] No raw SQL in dashboard pages
- [ ] Query results cached appropriately

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-9.11.1 | get_opportunities_page_data() executes exactly 1 SQL query (no N+1) | SQL query count test |
| AC-9.11.2 | Cached query returns same result without hitting DB on second call within TTL | Cache test with mock |
| AC-9.11.3 | invalidate_caches() clears all cached data | Post-invalidation fresh data test |

---

## Story 9.12 — Export System

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-9.12.1 | CSV export: valid CSV with correct headers and row count | File parse test |
| AC-9.12.2 | Excel export: 6 worksheets with correct sheet names | openpyxl sheet count test |
| AC-9.12.3 | JSON export: valid JSON matching Pydantic schema | Schema validation test |
| AC-9.12.4 | Markdown report: valid Markdown with section headers | Structure test |
| AC-9.12.5 | PDF report: generates without error, file size 200KB-2MB | File existence + size test |
| AC-9.12.6 | All export files written to data/exports/{format}/ with timestamped filenames | Path + filename test |

---

## Story 9.13 — Alert System

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-9.13.1 | Each of 8 alert types creates Alert row with correct severity | Per-type creation test |
| AC-9.13.2 | Resolving an alert sets resolved_at timestamp and resolution_note | Resolution test |
| AC-9.13.3 | Only unresolved alerts appear on Opportunities page banner | Filter test |

---

## Story 9.14 — App Entry Point

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-9.14.1 | `python run.py dashboard` launches Streamlit on localhost:8501 | Process launch test |
| AC-9.14.2 | All 7 pages are accessible via sidebar navigation | Navigation test |
| AC-9.14.3 | Page load times logged when debug_mode=True | Log capture test |
| AC-9.14.4 | Performance budget: all pages load in < 3 seconds | Timing test |

---

## Epic 09 — Overall Definition of Done

1. ✅ All 7 dashboard pages render correctly with real data
2. ✅ Design system applies consistently (colors, fonts, spacing, dark mode)
3. ✅ All 8 components render correctly across all pages
4. ✅ Cross-page navigation works (click entity → navigate to detail)
5. ✅ Keyboard shortcuts work
6. ✅ Exports produce valid files in all 5 formats
7. ✅ Alert system generates and displays alerts correctly
8. ✅ Performance budget met: all pages < 3 seconds
9. ✅ Empty state + onboarding wizard work for fresh installs
10. ✅ All dashboard tests pass
