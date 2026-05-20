# Report Templates
# Fiverr Research System — Wave 8

**Document Status:** Complete
**Wave:** 8 — Reporting and Dashboard
**Purpose:** Jinja2 HTML templates for PDF report generation via WeasyPrint. Four report types with base template, chart SVG generation, and styling.

---

## Report Types

| Report | Trigger | Content | Typical Length |
|---|---|---|---|
| Opportunity Report | After every run (auto) or on-demand | Per-niche or cross-niche keyword rankings with scores | 3–10 pages |
| Recommendation Report | On-demand from dashboard | All STRONG GO + CONDITIONAL GO recommendations | 5–20 pages |
| Competitor Report | On-demand from dashboard | Per-niche competitive landscape | 3–8 pages |
| Run Summary Report | After every run (auto) | Single-run stats, LLM-generated summary, alerts | 1–3 pages |

---

## Base Template Structure

```
src/reports/templates/
├── base.html            # Shared layout, CSS, header/footer
├── opportunity.html     # Opportunity Report
├── recommendation.html  # Recommendation Report
├── competitor.html      # Competitor Report
├── run_summary.html     # Run Summary Report
└── components/
    ├── score_radar.svg.j2      # Radar chart SVG for 9 scores
    ├── score_bar.svg.j2        # Horizontal bar chart for individual score
    ├── tag_badge.html.j2       # GO/PASS tag badge
    ├── package_table.html.j2   # 3-tier package comparison table
    └── revenue_chart.svg.j2    # Revenue gate progress chart
```

---

## base.html

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {
        size: A4;
        margin: 2cm 1.5cm;
        @bottom-center {
            content: "Fiverr Research System — {{ report_title }} — Page " counter(page);
            font-size: 9px;
            color: #888;
        }
    }
    body {
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 11px;
        line-height: 1.5;
        color: #333;
    }
    h1 { font-size: 22px; color: #1a1a2e; border-bottom: 2px solid #16213e; padding-bottom: 8px; }
    h2 { font-size: 16px; color: #16213e; margin-top: 20px; }
    h3 { font-size: 13px; color: #0f3460; }
    .tag-badge {
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: 10px; font-weight: bold; color: white;
    }
    .tag-strong-go { background: #f59e0b; }
    .tag-conditional-go { background: #6b7280; }
    .tag-monitor { background: #3b82f6; }
    .tag-caution { background: #ef4444; }
    .tag-pass { background: #d1d5db; color: #374151; }
    .score-cell { text-align: center; font-weight: bold; }
    .metric-box {
        display: inline-block; border: 1px solid #e5e7eb; border-radius: 8px;
        padding: 12px 20px; margin: 4px; text-align: center; min-width: 100px;
    }
    .metric-value { font-size: 20px; font-weight: bold; color: #1a1a2e; }
    .metric-label { font-size: 9px; color: #6b7280; text-transform: uppercase; }
    table { width: 100%; border-collapse: collapse; margin: 10px 0; }
    th { background: #f3f4f6; padding: 8px; text-align: left; font-size: 10px; }
    td { padding: 6px 8px; border-bottom: 1px solid #e5e7eb; font-size: 10px; }
    .page-break { page-break-before: always; }
    .red-flag { background: #fef2f2; border-left: 3px solid #ef4444; padding: 8px; margin: 8px 0; }
    .insight-box { background: #f0f9ff; border-left: 3px solid #3b82f6; padding: 8px; margin: 8px 0; }
</style>
</head>
<body>
    <h1>{{ report_title }}</h1>
    <p style="color: #6b7280; font-size: 10px;">
        Generated: {{ generated_at }} | Run: {{ run_id[:8] if run_id else "Manual" }}
        {% if niche_name %} | Niche: {{ niche_name }}{% endif %}
    </p>

    {% block content %}{% endblock %}
</body>
</html>
```

---

## opportunity.html

```html
{% extends "base.html" %}
{% block content %}

<!-- Summary metrics -->
<div style="margin: 20px 0;">
    {% for metric in summary_metrics %}
    <div class="metric-box">
        <div class="metric-value">{{ metric.value }}</div>
        <div class="metric-label">{{ metric.label }}</div>
    </div>
    {% endfor %}
</div>

<!-- Per-niche sections -->
{% for niche in niches %}
<h2>{{ niche.name }}</h2>
<p>Depth: {{ niche.depth }} | Keywords: {{ niche.keyword_count }} |
   Data Quality: {{ niche.data_quality_label }}</p>

<table>
    <thead>
        <tr>
            <th>Rank</th><th>Keyword</th><th>Tag</th><th>Score</th>
            <th>Demand</th><th>Comp</th><th>Opp</th><th>Feas</th>
            <th>Trend</th><th>Conf</th>
        </tr>
    </thead>
    <tbody>
    {% for kw in niche.keywords %}
        <tr>
            <td>{{ loop.index }}</td>
            <td>{{ kw.keyword_text }}</td>
            <td><span class="tag-badge tag-{{ kw.tag | lower | replace(' ', '-') }}">{{ kw.tag }}</span></td>
            <td class="score-cell">{{ kw.final_score | round(1) }}</td>
            <td class="score-cell">{{ kw.demand | round(0) if kw.demand else "—" }}</td>
            <td class="score-cell">{{ kw.competition | round(0) if kw.competition else "—" }}</td>
            <td class="score-cell">{{ kw.opportunity | round(0) if kw.opportunity else "—" }}</td>
            <td class="score-cell">{{ kw.feasibility | round(0) if kw.feasibility else "—" }}</td>
            <td class="score-cell">{{ kw.trend | round(0) if kw.trend else "—" }}</td>
            <td class="score-cell">{{ kw.confidence | round(2) }}</td>
        </tr>
    {% endfor %}
    </tbody>
</table>

{% if not loop.last %}<div class="page-break"></div>{% endif %}
{% endfor %}

{% endblock %}
```

---

## recommendation.html

```html
{% extends "base.html" %}
{% block content %}

{% for rec in recommendations %}
<div {% if not loop.first %}class="page-break"{% endif %}>
    <h2>
        <span class="tag-badge tag-{{ rec.tag | lower | replace(' ', '-') }}">{{ rec.tag }}</span>
        {{ rec.keyword_text }} — Score: {{ rec.final_score | round(1) }}
    </h2>
    <p style="color: #6b7280;">Niche: {{ rec.niche_name }} | Generated: {{ rec.generated_at }}</p>

    {% if rec.viability %}
    <div class="insight-box">
        <strong>Viability:</strong> {{ rec.viability.viability_assessment }}<br>
        <strong>Timing:</strong> {{ rec.viability.timing_assessment }}<br>
        <strong>Recommendation:</strong> {{ rec.viability.blunt_recommendation }}
    </div>
    {% endif %}

    {% if rec.gig_titles %}
    <h3>Gig Titles</h3>
    <ol>
    {% for title in rec.gig_titles %}
        <li>{{ title.title }} <em>({{ title.positioning_angle }})</em></li>
    {% endfor %}
    </ol>
    {% endif %}

    {% if rec.package_structure %}
    <h3>Packages</h3>
    {% include "components/package_table.html.j2" %}
    {% endif %}

    {% if rec.differentiation %}
    <h3>Differentiation Angle</h3>
    <p>{{ rec.differentiation.positioning_statement }}</p>
    <p><strong>Pitch:</strong> <em>{{ rec.differentiation.one_sentence_pitch }}</em></p>
    {% for d in rec.differentiation.differentiators %}
    <p>→ {{ d.action }}</p>
    {% endfor %}
    {% endif %}

    {% if rec.faq_entries %}
    <h3>FAQ</h3>
    {% for faq in rec.faq_entries %}
    <p><strong>Q: {{ faq.question }}</strong><br>A: {{ faq.answer }}</p>
    {% endfor %}
    {% endif %}

    {% if rec.red_flags %}
    <h3>Red Flags (Risk: {{ rec.red_flags.overall_risk_level }})</h3>
    {% for flag in rec.red_flags.red_flags %}
    <div class="red-flag">
        <strong>{{ flag.severity }} — {{ flag.flag_type }}:</strong> {{ flag.description }}<br>
        <em>Mitigation: {{ flag.mitigation }}</em>
    </div>
    {% endfor %}
    {% endif %}
</div>
{% endfor %}

{% endblock %}
```

---

## competitor.html

```html
{% extends "base.html" %}
{% block content %}

<h2>Competitive Landscape: {{ niche_name }}</h2>

{% for cluster in clusters %}
<h3>{{ cluster.label }} ({{ cluster.keyword_count }} keywords)</h3>

{% if cluster.synthesis %}
<div class="insight-box">
    <strong>Who Dominates:</strong> {{ cluster.synthesis.who_dominates }}<br>
    <strong>Why They Win:</strong> {{ cluster.synthesis.why_they_win }}<br>
    <strong>The Gap:</strong> {{ cluster.synthesis.the_gap }}<br>
    <strong>Entry Verdict:</strong> {{ cluster.synthesis.entry_verdict }}
    (Feasibility: {{ cluster.synthesis.entry_feasibility_rating }}/10)
</div>
{% endif %}

<h3>Top Sellers</h3>
<table>
    <thead>
        <tr><th>Seller</th><th>Level</th><th>Reviews</th><th>Authority</th><th>Top Weakness</th></tr>
    </thead>
    <tbody>
    {% for seller in cluster.top_sellers %}
        <tr>
            <td>{{ seller.username }}</td>
            <td>{{ seller.level }}</td>
            <td>{{ seller.reviews }}</td>
            <td class="score-cell">{{ seller.authority | round(1) }}</td>
            <td>{{ seller.top_weakness or "—" }}</td>
        </tr>
    {% endfor %}
    </tbody>
</table>

{% if not loop.last %}<div class="page-break"></div>{% endif %}
{% endfor %}

{% endblock %}
```

---

## run_summary.html

```html
{% extends "base.html" %}
{% block content %}

<div style="margin: 20px 0;">
    <div class="metric-box"><div class="metric-value">{{ run.duration }}</div><div class="metric-label">Duration</div></div>
    <div class="metric-box"><div class="metric-value">${{ run.llm_cost | round(2) }}</div><div class="metric-label">LLM Cost</div></div>
    <div class="metric-box"><div class="metric-value">{{ run.keywords_expanded }}</div><div class="metric-label">Keywords</div></div>
    <div class="metric-box"><div class="metric-value">{{ run.gigs_collected }}</div><div class="metric-label">Gigs</div></div>
    <div class="metric-box"><div class="metric-value">{{ run.error_count }}</div><div class="metric-label">Errors</div></div>
</div>

{% if run.summary_text %}
<div class="insight-box">{{ run.summary_text }}</div>
{% endif %}

{% if run.auto_promotions %}
<h3>Depth Changes</h3>
{% for promo in run.auto_promotions %}
<p>📊 {{ promo.niche }}: {{ promo.from_depth }} → {{ promo.to_depth }}</p>
{% endfor %}
{% endif %}

{% if run.new_strong_go %}
<h3>New STRONG GO Keywords</h3>
<ul>
{% for kw in run.new_strong_go %}
<li>{{ kw.keyword_text }} ({{ kw.niche_name }}) — Score: {{ kw.final_score | round(1) }}</li>
{% endfor %}
</ul>
{% endif %}

{% if run.dead_letters %}
<h3>Failed Jobs ({{ run.dead_letters | length }})</h3>
<table>
    <thead><tr><th>Job Type</th><th>Error</th></tr></thead>
    <tbody>
    {% for dl in run.dead_letters %}
    <tr><td>{{ dl.job_type }}</td><td>{{ dl.error_message[:80] }}</td></tr>
    {% endfor %}
    </tbody>
</table>
{% endif %}

{% endblock %}
```

---

## PDF Generation Engine

```python
# src/reports/generator.py

from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

def generate_report(
    report_type: str,
    data: dict,
    output_path: str,
    niche_id: str = None,
) -> str:
    """
    Generates a PDF report using WeasyPrint.
    Returns the output file path.
    """
    env = Environment(loader=FileSystemLoader("src/reports/templates"))
    template = env.get_template(f"{report_type}.html")

    html_content = template.render(
        report_title=REPORT_TITLES[report_type],
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        niche_name=get_niche_name(niche_id) if niche_id else None,
        **data,
    )

    HTML(string=html_content).write_pdf(output_path)
    return output_path

REPORT_TITLES = {
    "opportunity": "Opportunity Report",
    "recommendation": "Recommendation Report",
    "competitor": "Competitor Report",
    "run_summary": "Run Summary Report",
}
```

Reports are auto-generated after every run and saved to `data/exports/reports/`. They can also be generated on-demand from the dashboard.
