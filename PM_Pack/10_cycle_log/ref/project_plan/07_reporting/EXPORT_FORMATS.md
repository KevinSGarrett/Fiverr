# Export Formats
# Fiverr Research System — Wave 8

**Document Status:** Complete
**Wave:** 8 — Reporting and Dashboard
**Purpose:** Field-level specifications for all 5 export formats — CSV, Excel, JSON, PDF, Markdown.

**OQ-009 Resolved:** Export formats are CSV, Excel (.xlsx), PDF, JSON, and Markdown. All generated after every run into `data/exports/`. Also triggerable from dashboard.

---

## Export Directory Structure

```
data/exports/
├── csv/
│   ├── keywords_2026-05-12.csv
│   ├── recommendations_2026-05-12.csv
│   └── competitors_2026-05-12.csv
├── excel/
│   └── fiverr_research_2026-05-12.xlsx   (multi-sheet workbook)
├── json/
│   ├── keywords_2026-05-12.json
│   ├── recommendations_2026-05-12.json
│   └── full_export_2026-05-12.json
├── pdf/
│   ├── opportunity_report_2026-05-12.pdf
│   ├── recommendation_report_2026-05-12.pdf
│   └── run_summary_2026-05-12.pdf
└── markdown/
    ├── recommendations_2026-05-12.md
    └── opportunity_summary_2026-05-12.md
```

---

## CSV Export

### keywords.csv

| Column | Source | Format | Null Display |
|---|---|---|---|
| keyword_text | keywords.keyword_text | string | — |
| niche | niche_configs.name (joined) | string | — |
| cluster_label | cluster_analysis.cluster_label (joined) | string | "Unclustered" |
| intent_class | keywords.intent_class | string | "UNKNOWN" |
| final_score | keyword_scores.final_score | float, 2 decimal | "" |
| tag | opportunity_rankings.tag | string | "" |
| demand_score | keyword_scores.demand_score | float, 1 decimal | "" |
| competition_score | keyword_scores.competition_score | float, 1 decimal | "" |
| opportunity_score | keyword_scores.opportunity_score | float, 1 decimal | "" |
| feasibility_score | keyword_scores.feasibility_score | float, 1 decimal | "" |
| profitability_score | keyword_scores.profitability_score | float, 1 decimal | "" |
| intent_score | keyword_scores.intent_score | float, 1 decimal | "" |
| saturation_score | keyword_scores.saturation_score | float, 1 decimal | "" |
| weakness_score | keyword_scores.weakness_score | float, 1 decimal | "" |
| trend_score | keyword_scores.trend_score | float, 1 decimal | "" |
| confidence_modifier | keyword_scores.confidence_modifier | float, 3 decimal | "" |
| total_result_count | search_results.total_result_count | integer | "" |
| trends_slope | external_signals.trends_slope | string | "" |
| autocomplete_position | keywords.autocomplete_position | integer | "" |
| rank_in_niche | opportunity_rankings.rank | integer | "" |
| scored_at | keyword_scores.scored_at | ISO 8601 date | "" |

**Date format:** `2026-05-12T03:14:00Z`
**Delimiter:** Comma
**Encoding:** UTF-8 with BOM (for Excel compatibility)
**Header row:** Yes (first row)

### recommendations.csv

| Column | Source | Format |
|---|---|---|
| keyword_text | keywords.keyword_text | string |
| niche | niche_configs.name | string |
| tag | recommendations.tag | string |
| final_score | recommendations.final_score | float, 1 decimal |
| title_1 through title_5 | recommendations.gig_titles[0-4].title | string |
| basic_price | recommendations.package_structure.basic.price | integer |
| standard_price | recommendations.package_structure.standard.price | integer |
| premium_price | recommendations.package_structure.premium.price | integer |
| basic_deliverables | recommendations.package_structure.basic.deliverables | semicolon-separated |
| standard_deliverables | recommendations.package_structure.standard.deliverables | semicolon-separated |
| premium_deliverables | recommendations.package_structure.premium.deliverables | semicolon-separated |
| one_sentence_pitch | recommendations.differentiation_angle.one_sentence_pitch | string |
| overall_risk_level | recommendations.red_flags.overall_risk_level | string |
| blunt_recommendation | recommendations.niche_viability_assessment.blunt_recommendation | string |
| generation_complete | recommendations.generation_complete | boolean |
| generated_at | recommendations.generated_at | ISO 8601 |

### competitors.csv

| Column | Source | Format |
|---|---|---|
| seller_username | sellers.seller_username | string |
| niche | niche_configs.name | string |
| seller_level | sellers.seller_level | string |
| total_reviews | sellers.total_reviews | integer |
| authority_score | seller_scores.authority_score | float, 1 decimal |
| response_rate | sellers.response_rate | integer |
| portfolio_count | sellers.portfolio_count | integer |
| is_new_seller | computed | boolean |
| top_weakness | seller_scores.top_weakness | string |
| review_velocity_30d | computed | float, 1 decimal |

---

## Excel Export (.xlsx)

Single workbook with 4 sheets:

### Sheet 1: "Keywords"
Same columns as keywords.csv. Additional formatting:
- Header row: bold, frozen
- Tag column: conditional formatting (gold fill for STRONG GO, silver for CONDITIONAL GO)
- Score columns: number format 0.0, color scale (red→yellow→green) from 0 to 100
- Column widths: keyword_text 30, niche 25, scores 10 each

### Sheet 2: "Recommendations"
Same columns as recommendations.csv. Additional formatting:
- Title columns: text wrap
- Price columns: currency format ($#,##0)
- Tag column: conditional formatting matching Sheet 1

### Sheet 3: "Competitors"
Same columns as competitors.csv. Additional formatting:
- Authority score: color scale 0–10
- is_new_seller: checkbox-style (TRUE/FALSE)

### Sheet 4: "Run Summary"
| Row | Content |
|---|---|
| 1 | "Fiverr Research System — Export" (merged across A1:F1, bold) |
| 2 | "Generated: [date]" |
| 3 | blank |
| 4 | "Run ID:", [run_id] |
| 5 | "Mode:", [mode] |
| 6 | "Duration:", [duration] |
| 7 | "LLM Cost:", [$cost] |
| 8 | "Keywords Scored:", [count] |
| 9 | "Recommendations Generated:", [count] |
| 10 | "STRONG GO Keywords:", [count] |
| 11 | "CONDITIONAL GO Keywords:", [count] |

```python
# src/exports/excel_exporter.py

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, numbers

def export_excel(run_id: str, db) -> str:
    wb = openpyxl.Workbook()

    # Sheet 1: Keywords
    ws_kw = wb.active
    ws_kw.title = "Keywords"
    write_keyword_sheet(ws_kw, run_id, db)
    apply_keyword_formatting(ws_kw)

    # Sheet 2: Recommendations
    ws_rec = wb.create_sheet("Recommendations")
    write_recommendation_sheet(ws_rec, run_id, db)

    # Sheet 3: Competitors
    ws_comp = wb.create_sheet("Competitors")
    write_competitor_sheet(ws_comp, run_id, db)

    # Sheet 4: Run Summary
    ws_sum = wb.create_sheet("Run Summary")
    write_summary_sheet(ws_sum, run_id, db)

    output_path = f"data/exports/excel/fiverr_research_{date_stamp()}.xlsx"
    wb.save(output_path)
    return output_path
```

---

## JSON Export

### full_export.json

Complete export of all scored data from a run:

```json
{
  "export_version": "1.0",
  "generated_at": "2026-05-12T03:14:00Z",
  "run_id": "run_20260512_031400",
  "run_mode": "full",
  "niches": [
    {
      "niche_id": "prd_ai_saas",
      "niche_name": "PRD / AI SaaS MVP Roadmap",
      "depth": "full",
      "keyword_count": 45,
      "data_quality_score": 87,
      "keywords": [
        {
          "keyword_id": 1,
          "keyword_text": "AI SaaS PRD",
          "cluster_label": "PRD — MVP Scoping",
          "intent_class": "HIGH_INTENT",
          "scores": {
            "demand": 75.29,
            "competition": 65.55,
            "opportunity": 25.94,
            "feasibility": 63.80,
            "profitability": 80.03,
            "intent": 77.60,
            "saturation": 35.95,
            "weakness": 68.91,
            "trend": 70.20
          },
          "final_score": 52.53,
          "confidence_modifier": 0.913,
          "tag": "MONITOR",
          "rank_in_niche": 1
        }
      ],
      "recommendations": [
        {
          "keyword_id": 1,
          "keyword_text": "AI SaaS PRD",
          "tag": "STRONG GO",
          "final_score": 82.3,
          "gig_titles": ["..."],
          "package_structure": {},
          "differentiation_angle": {},
          "faq_entries": [],
          "buyer_persona": {},
          "red_flags": {},
          "niche_viability": {},
          "generation_complete": true,
          "llm_cost_usd": 0.11
        }
      ]
    }
  ],
  "run_summary": {
    "duration_seconds": 14520,
    "llm_cost_usd": 1.42,
    "keywords_scored": 312,
    "recommendations_generated": 18,
    "strong_go_count": 5,
    "conditional_go_count": 13,
    "error_count": 2
  }
}
```

---

## PDF Export

Uses the WeasyPrint report templates from REPORT_TEMPLATES.md:

| Export Type | Template | Content |
|---|---|---|
| Opportunity PDF | opportunity.html | Per-niche keyword tables with scores |
| Recommendation PDF | recommendation.html | Full recommendation cards |
| Run Summary PDF | run_summary.html | Run stats + alerts |

Page layout: A4 portrait, 2cm margins, header with report title, footer with page number.

---

## Markdown Export

### recommendations.md

Per-recommendation markdown cards concatenated:

```markdown
# Fiverr Research Recommendations
Generated: 2026-05-12 03:14 UTC | Run: run_2026...

---

## ⭐ STRONG GO — "AI SaaS PRD" (Score: 82.3)
**Niche:** PRD / AI SaaS MVP Roadmap

### Viability
This keyword scores 82 driven by strong demand (75)...

### Gig Titles
1. I will write a developer-ready AI SaaS MVP PRD and technical roadmap
2. I will create a complete AI product requirements document...
...

### Packages
| Tier | Price | Deliverables | Delivery | Revisions |
|---|---|---|---|---|
| Basic | $95 | Scope audit, feature matrix | 3 days | 1 |
| Standard | $225 | Complete PRD, user stories | 5 days | 2 |
| Premium | $395 | PRD + roadmap + diagrams | 7 days | 3 |

### Differentiation
Top 10 gigs have generic descriptions with no proof elements...

### FAQ
**Q: What do I need to provide?**
A: A structured intake questionnaire...

### Red Flags (Risk: MEDIUM)
- 🟡 MEDIUM — high_competition_no_weak_spots: Top 3 sellers...

---
```

### opportunity_summary.md

```markdown
# Opportunity Summary — 2026-05-12

## Strong GO Keywords (5)
| Keyword | Niche | Score | Demand | Competition |
|---|---|---|---|---|
| AI SaaS PRD | PRD | 82.3 | 75 | 66 |
...

## Conditional GO Keywords (13)
...

## Key Alerts
- ⚠️ Python Automation promoted to full depth
- ℹ️ 2 new STRONG GO keywords this run
```

---

## Export Orchestration

```python
# src/exports/orchestrator.py

def run_all_exports(run_id: str, db):
    """Called automatically at end of every run."""
    export_csv_keywords(run_id, db)
    export_csv_recommendations(run_id, db)
    export_csv_competitors(run_id, db)
    export_excel(run_id, db)
    export_json_full(run_id, db)
    export_markdown_recommendations(run_id, db)
    export_markdown_opportunity_summary(run_id, db)
    generate_report("opportunity", build_opportunity_data(run_id, db),
                    f"data/exports/pdf/opportunity_report_{date_stamp()}.pdf")
    generate_report("run_summary", build_run_summary_data(run_id, db),
                    f"data/exports/pdf/run_summary_{date_stamp()}.pdf")
    log.info(f"All exports complete for run {run_id[:8]}")
```
