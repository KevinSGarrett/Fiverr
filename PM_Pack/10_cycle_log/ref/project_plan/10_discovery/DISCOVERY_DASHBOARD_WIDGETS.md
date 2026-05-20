# Discovery Dashboard Widgets
# Fiverr Research System — Wave 10

**Document Status:** Complete
**Wave:** 10 — LLM-Powered Niche Discovery
**Purpose:** New Dashboard Page 7 (Discovery) with all widgets — hypothesis queue, discovery results, hit rate trends, gold highlights, cost tracking, and mode performance comparison.

---

## Page 7 — Discovery (New Dashboard Page)

### Purpose
The intelligence command center. Shows what the discovery engine has found, how accurate its predictions are, which modes work best, and gold opportunities that need immediate attention.

### Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  🔍 Discovery Engine                      [Run Discovery ▼]    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │
│  │  42    │ │ 35.2%  │ │  3 🏆  │ │ 22.4   │ │ $1.84  │       │
│  │ Total  │ │Hit Rate│ │ Golds  │ │Avg Err │ │ Cost   │       │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘       │
│                                                                 │
│  ─── 🏆 GOLD DISCOVERIES ────────────────────────────────────  │
│  [Gold discovery cards — highest priority, always visible]      │
│                                                                 │
│  ─── TABS ────────────────────────────────────────────────────  │
│  [Leaderboard] [Hypothesis Queue] [Mode Performance] [Trends]  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### W7.1 — Discovery Summary Metrics

```python
def render_discovery_metrics(db):
    """Top-level KPI row for the discovery page."""
    feedback = build_feedback_summary(db)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Hypotheses", feedback.get("total_hypotheses", 0))
    col2.metric("Hit Rate", f"{feedback.get('hit_rate_pct', 0):.1f}%",
                delta=_get_hit_rate_delta(db))
    col3.metric("🏆 Golds", feedback.get("gold_hits", 0))
    col4.metric("Avg Error", f"{feedback.get('avg_prediction_error', 0):.1f} pts")
    col5.metric("Discovery Cost", f"${get_total_discovery_cost(db):.2f}")
```

---

### W7.2 — Gold Discovery Cards

Always-visible section showing the highest-value discoveries:

```python
def render_gold_discoveries(db):
    """Highlighted cards for 85+ score discoveries."""
    golds = db.query(Keyword).filter(
        Keyword.is_discovery == True,
    ).join(KeywordScore).filter(
        KeywordScore.final_score >= 85,
    ).order_by(KeywordScore.final_score.desc()).all()

    if not golds:
        st.info("No gold discoveries yet. The engine is learning — "
                "gold discoveries typically appear after 3-5 cycles.")
        return

    st.subheader(f"🏆 Gold Discoveries ({len(golds)})")

    for kw in golds:
        score = get_final_score(kw.id, db)
        tag = get_tag(kw.id, db)

        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"### 🏆 \"{kw.keyword_text}\"")
                st.caption(f"Discovered via **{kw.discovery_mode}** | "
                          f"Predicted: {kw.hypothesis_confidence:.0%} → "
                          f"Actual: **{score:.1f}** | "
                          f"Niche: {get_niche_name(kw.niche_id)}")
                if kw.hypothesis_rationale:
                    st.markdown(f"_Rationale: {kw.hypothesis_rationale[:200]}_")
            with col2:
                st.metric("Score", f"{score:.1f}")
            with col3:
                st.metric("Tag", tag)

            # Check if recommendation exists
            rec = db.query(Recommendation).filter(
                Recommendation.keyword_id == kw.id,
            ).first()
            if rec:
                st.success("📝 Recommendation available — view in Recommendations page")
            else:
                st.warning("No recommendation yet — run `--mode recommendations-only`")
```

---

### W7.3 — Discovery Leaderboard Tab

```python
def render_discovery_leaderboard(db):
    """Ranked table of all discovery keywords by actual score."""
    leaderboard = get_discovery_leaderboard(db, limit=50)

    if not leaderboard:
        st.info("No scored discovery keywords yet.")
        return

    df = pd.DataFrame(leaderboard)

    # Color-code the result column
    def color_result(val):
        colors = {
            "gold": "background-color: #fef3c7",
            "hit": "background-color: #d1fae5",
            "monitor": "background-color: #dbeafe",
            "miss": "background-color: #fee2e2",
            "retire": "background-color: #f3f4f6; color: #9ca3af",
            "pending": "background-color: #f9fafb",
        }
        return colors.get(val, "")

    st.dataframe(
        df[["keyword_text", "niche", "discovery_mode", "hypothesis_confidence",
            "actual_score", "tag", "result", "prediction_error"]].rename(columns={
            "keyword_text": "Keyword",
            "niche": "Niche",
            "discovery_mode": "Mode",
            "hypothesis_confidence": "Predicted",
            "actual_score": "Actual",
            "tag": "Tag",
            "result": "Result",
            "prediction_error": "Error",
        }),
        use_container_width=True,
        hide_index=True,
        height=500,
    )
```

---

### W7.4 — Hypothesis Queue Tab

Shows hypotheses waiting for collection:

```python
def render_hypothesis_queue(db):
    """Pending discovery keywords that haven't been collected/scored yet."""
    pending = db.query(Keyword).filter(
        Keyword.is_discovery == True,
        Keyword.discovery_evaluated == False,
    ).outerjoin(KeywordScore).filter(
        KeywordScore.final_score.is_(None),
    ).order_by(Keyword.hypothesis_confidence.desc()).all()

    if not pending:
        st.success("All discovery hypotheses have been scored.")
        return

    st.subheader(f"Pending Hypotheses ({len(pending)})")

    for kw in pending:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.markdown(f"**{kw.keyword_text}**")
            st.caption(f"{kw.discovery_mode} | {kw.hypothesis_rationale[:100] if kw.hypothesis_rationale else ''}...")
        with col2:
            st.metric("Confidence", f"{kw.hypothesis_confidence:.0%}")
        with col3:
            st.caption(f"Niche: {get_niche_name(kw.niche_id)}")
        with col4:
            if st.button("🗑️ Remove", key=f"remove_disc_{kw.id}"):
                kw.is_retired = True
                db.commit()
                st.rerun()
```

---

### W7.5 — Mode Performance Tab

Compare discovery modes side-by-side:

```python
def render_mode_performance(db):
    """Bar chart + stats comparing discovery mode effectiveness."""
    feedback = build_feedback_summary(db)
    mode_stats = feedback.get("mode_stats", {})

    if not mode_stats:
        st.info("No discovery data yet.")
        return

    # Hit rate comparison bar chart
    fig = go.Figure()
    modes = list(mode_stats.keys())
    hit_rates = [mode_stats[m]["hit_rate"] for m in modes]
    counts = [mode_stats[m]["count"] for m in modes]
    avg_scores = [mode_stats[m]["avg_score"] for m in modes]

    fig.add_trace(go.Bar(
        x=modes, y=hit_rates,
        name="Hit Rate (%)",
        marker_color=["#10b981" if r >= 30 else "#f59e0b" if r >= 15 else "#ef4444"
                       for r in hit_rates],
        text=[f"{r:.0f}%" for r in hit_rates],
        textposition="auto",
    ))

    fig.update_layout(
        title="Discovery Mode Hit Rates",
        yaxis_title="Hit Rate (%)",
        yaxis_range=[0, 100],
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Detailed stats table
    stats_df = pd.DataFrame([{
        "Mode": mode.replace("_", " ").title(),
        "Hypotheses": stats["count"],
        "Hit Rate": f"{stats['hit_rate']:.1f}%",
        "Avg Score": f"{stats['avg_score']:.1f}",
        "Golds": stats["gold_count"],
        "Avg Confidence": f"{stats['avg_confidence']:.0%}",
        "Avg Error": f"{stats['avg_error']:.1f}",
    } for mode, stats in mode_stats.items()])

    st.dataframe(stats_df, use_container_width=True, hide_index=True)

    # Calibration insights
    calibration = feedback.get("calibration", {})
    if calibration.get("guidance"):
        st.subheader("Calibration Insights")
        for note in calibration["guidance"]:
            st.warning(f"📊 {note}")
```

---

### W7.6 — Discovery Trends Tab

Track how discovery performance improves over time:

```python
def render_discovery_trends(db):
    """Line charts showing discovery metrics over cycles."""
    cycles = db.query(DiscoveryCycleLog).order_by(
        DiscoveryCycleLog.cycle_at
    ).all()

    if len(cycles) < 2:
        st.info("Need at least 2 discovery cycles for trend analysis.")
        return

    # Cumulative hit rate over time
    cumulative_data = []
    running_total = 0
    running_hits = 0

    for cycle in cycles:
        # Get outcomes for hypotheses generated in this cycle's run
        cycle_outcomes = db.query(DiscoveryOutcome).filter(
            DiscoveryOutcome.keyword_id.in_(
                db.query(Keyword.id).filter(
                    Keyword.discovered_in_run == cycle.run_id,
                    Keyword.is_discovery == True,
                )
            )
        ).all()

        running_total += len(cycle_outcomes)
        running_hits += sum(1 for o in cycle_outcomes if o.is_hit)
        hit_rate = (running_hits / running_total * 100) if running_total > 0 else 0

        cumulative_data.append({
            "Cycle": cycle.cycle_at.strftime("%Y-%m-%d"),
            "Cumulative Hit Rate": hit_rate,
            "Hypotheses This Cycle": cycle.hypotheses_accepted,
            "Cost": cycle.total_cost_usd,
        })

    df_trends = pd.DataFrame(cumulative_data)

    # Hit rate trend
    fig1 = px.line(df_trends, x="Cycle", y="Cumulative Hit Rate",
                   title="Discovery Hit Rate Over Time",
                   markers=True)
    fig1.add_hline(y=30, line_dash="dash", line_color="green",
                   annotation_text="Target: 30%")
    fig1.update_layout(yaxis_range=[0, 100], height=300)
    st.plotly_chart(fig1, use_container_width=True)

    # Cost per cycle
    fig2 = px.bar(df_trends, x="Cycle", y="Cost",
                  title="Discovery Cost per Cycle", text_auto=".3f")
    fig2.update_layout(height=250)
    st.plotly_chart(fig2, use_container_width=True)

    # Prediction accuracy trend (if enough data)
    prediction_data = []
    for cycle in cycles:
        cycle_outcomes = db.query(DiscoveryOutcome).filter(
            DiscoveryOutcome.keyword_id.in_(
                db.query(Keyword.id).filter(
                    Keyword.discovered_in_run == cycle.run_id,
                )
            )
        ).all()

        if cycle_outcomes:
            avg_error = sum(
                abs(o.actual_final_score - o.hypothesis_confidence * 100)
                for o in cycle_outcomes
            ) / len(cycle_outcomes)
            prediction_data.append({
                "Cycle": cycle.cycle_at.strftime("%Y-%m-%d"),
                "Avg Prediction Error": avg_error,
            })

    if len(prediction_data) >= 2:
        fig3 = px.line(pd.DataFrame(prediction_data), x="Cycle", y="Avg Prediction Error",
                       title="Prediction Accuracy Over Time (lower = better)",
                       markers=True)
        fig3.update_layout(height=250)
        st.plotly_chart(fig3, use_container_width=True)
```

---

### W7.7 — Discovery Cost Tracker

```python
def render_discovery_cost(db):
    """Cost breakdown specific to discovery operations."""
    total_cost = get_total_discovery_cost(db)
    total_hits = get_total_discovery_hits(db)
    total_golds = get_total_discovery_golds(db)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Discovery Spend", f"${total_cost:.2f}")
    col2.metric("Cost per Hit", f"${total_cost / max(1, total_hits):.2f}")
    col3.metric("Cost per Gold", f"${total_cost / max(1, total_golds):.2f}" if total_golds > 0 else "N/A")
```

---

## Streamlit App Update — Navigation

```python
# Updated sidebar navigation (src/dashboard/app.py)

pages = {
    "🎯 Opportunities": page_opportunities,
    "🔑 Keywords": page_keywords,
    "👥 Competitors": page_competitors,
    "📝 Recommendations": page_recommendations,
    "📊 Run History": page_run_history,
    "💰 LLM Costs": page_llm_costs,
    "🔬 Discovery": page_discovery,  # NEW — Page 7
}
```

---

## Alert Integration

New alert type added to ALERT_SYSTEM.md:

```python
# Alert Type 9: NEW_GOLD_DISCOVERY
# Trigger: Discovery keyword scores 85+ after evaluation
# Severity: HIGH
# Display: Page 1 banner + Page 7 gold card
# Auto-resolve: After user views Discovery page
```

---

## Export Format Updates

### CSV — discovery_keywords.csv (new export file)

| Column | Source | Format |
|---|---|---|
| keyword_text | keywords.keyword_text | string |
| niche | niche name (joined) | string |
| discovery_mode | keywords.discovery_mode | string |
| hypothesis_confidence | keywords.hypothesis_confidence | float, 2 decimal |
| actual_score | keyword_scores.final_score | float, 1 decimal |
| tag | opportunity_rankings.tag | string |
| result | gold/hit/monitor/miss/retire/pending | string |
| prediction_error | |actual - predicted| | float, 1 decimal |
| discovered_in_run | keywords.discovered_in_run | string |
| is_retired | keywords.is_retired | boolean |

### Excel — New "Discovery" Sheet

Added as Sheet 5 in the export workbook with the same columns as the CSV above, plus conditional formatting: gold rows highlighted yellow, retired rows grayed out.

### JSON — discovery section in full_export.json

```json
{
  "discovery": {
    "total_hypotheses": 42,
    "hit_rate_pct": 35.2,
    "gold_count": 3,
    "avg_prediction_error": 22.4,
    "leaderboard": [...],
    "mode_stats": {...},
    "cost_total_usd": 1.84
  }
}
```
