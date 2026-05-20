# Dashboard Plan
# Fiverr Research System — Wave 8

**Document Status:** Complete
**Wave:** 8 — Reporting and Dashboard (FINAL planning wave)
**Purpose:** Complete specification for all 6 Streamlit dashboard pages — every widget, data source query, chart type, and interactive behavior.

**OQ-008 Resolved:** Dashboard is SOLO (single user). No authentication, no multi-user. Streamlit v1 runs on localhost:8501. React+FastAPI v2 is a future upgrade path.

---

## Technology Stack

```
Dashboard v1:
  Framework:   Streamlit 1.35+
  Charts:      Plotly (via st.plotly_chart)
  Data:        SQLAlchemy queries → Pandas DataFrames → Streamlit widgets
  State:       st.session_state for filters, selections, and view toggles
  Hosting:     localhost:8501 (single user, no auth)
  Refresh:     Manual refresh button + auto-refresh toggle (60s interval via st.rerun)
```

---

## Global Layout

```
┌─────────────────────────────────────────────────────────────┐
│  🔍 Fiverr Research System        [Run Now ▼]  [⟳ Refresh] │
├────┬────────────────────────────────────────────────────────┤
│    │                                                        │
│ N  │   [Page Content Area]                                  │
│ A  │                                                        │
│ V  │                                                        │
│    │                                                        │
│ 1  │                                                        │
│ 2  │                                                        │
│ 3  │                                                        │
│ 4  │                                                        │
│ 5  │                                                        │
│ 6  │                                                        │
│    │                                                        │
├────┴────────────────────────────────────────────────────────┤
│  Last run: 2026-05-12 03:14  │  9 niches  │  LLM: $1.42   │
└─────────────────────────────────────────────────────────────┘
```

Global elements:
- **Sidebar navigation:** 6 page links with icons
- **Run Now dropdown:** --mode full | score-only | recommendations-only | collect-only
- **Refresh button:** triggers st.rerun
- **Footer bar:** last run timestamp, niche count, last run LLM cost

---

## Page 1 — Opportunities (Default Landing Page)

### Purpose
The primary decision-making view. Shows all scored keywords ranked by opportunity, with visual indicators for tag, confidence, and recommendation availability.

### Widgets

#### W1.1 — Alert Banners (top of page)

```python
# Data source
alerts = db.query(Alert).filter(
    Alert.resolved == False,
    Alert.alert_type.in_([
        "STALE_DATA", "AUTO_PROMOTION", "RUN_FAILURE",
        "NEW_STRONG_GO", "DATA_QUALITY_LOW"
    ])
).order_by(Alert.severity.desc(), Alert.created_at.desc()).all()

# Display
for alert in alerts:
    if alert.severity == "HIGH":
        st.error(f"⚠️ {alert.message}", icon="🚨")
    elif alert.severity == "MEDIUM":
        st.warning(f"⚡ {alert.message}")
    else:
        st.info(f"ℹ️ {alert.message}")
```

**Alert types shown here:**
- `STALE_DATA`: "PRD keyword data is 3 days past TTL — consider running collection"
- `AUTO_PROMOTION`: "Python Automation promoted from standard → full depth after Run 3"
- `RUN_FAILURE`: "Last run failed at Stage 5 — click to view error details"
- `NEW_STRONG_GO`: "2 new STRONG GO keywords detected this run"
- `DATA_QUALITY_LOW`: "AI Agent niche data quality below 50% — missing Google Trends"

#### W1.2 — Filter Controls (row below banners)

```python
col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

with col1:
    niche_filter = st.selectbox(
        "Niche",
        ["All Niches"] + get_niche_names(db),
        key="opp_niche_filter"
    )

with col2:
    tag_filter = st.multiselect(
        "Tag",
        ["STRONG GO", "CONDITIONAL GO", "MONITOR", "CAUTION", "PASS"],
        default=["STRONG GO", "CONDITIONAL GO"],
        key="opp_tag_filter"
    )

with col3:
    sort_by = st.selectbox(
        "Sort by",
        ["Final Score", "Demand Score", "Opportunity Score", "Trend Score", "Feasibility Score"],
        key="opp_sort"
    )

with col4:
    intent_filter = st.selectbox(
        "Intent Class",
        ["All", "TRANSACTIONAL", "HIGH_INTENT", "CONSIDERATION", "INFORMATIONAL"],
        key="opp_intent"
    )
```

#### W1.3 — Opportunity Cards Grid

```python
# Data source
query = db.query(OpportunityRanking).join(Keyword).join(KeywordScore)
if niche_filter != "All Niches":
    query = query.filter(Keyword.niche_id == niche_id_from_name(niche_filter))
if tag_filter:
    query = query.filter(OpportunityRanking.tag.in_(tag_filter))
if intent_filter != "All":
    query = query.filter(Keyword.intent_class == intent_filter)

sort_map = {
    "Final Score": OpportunityRanking.final_score.desc(),
    "Demand Score": KeywordScore.demand_score.desc(),
    "Opportunity Score": KeywordScore.opportunity_score.desc(),
    "Trend Score": KeywordScore.trend_score.desc(),
    "Feasibility Score": KeywordScore.feasibility_score.desc(),
}
query = query.order_by(sort_map[sort_by])
rankings = query.limit(50).all()

# Display as 2-column card grid
for i in range(0, len(rankings), 2):
    cols = st.columns(2)
    for j, col in enumerate(cols):
        if i + j < len(rankings):
            ranking = rankings[i + j]
            with col:
                render_opportunity_card(ranking, db)
```

**Opportunity Card Content:**
```
┌──────────────────────────────────────────┐
│ [STRONG GO]  Score: 82.3  📊 Conf: 0.91 │
│ "AI SaaS PRD"                            │
│ Niche: PRD / AI SaaS MVP Roadmap         │
│                                          │
│ D: ████████░░ 75   C: ██████░░░░ 66     │
│ O: ██░░░░░░░░ 26   F: ██████░░░░ 64     │
│                                          │
│ 📝 Recommendation available              │
│ [View Details]                           │
└──────────────────────────────────────────┘
```

Mini-bar chart for D(emand), C(ompetition), O(pportunity), F(easibility) using st.progress or plotly horizontal bars. Tag badge color: gold=STRONG GO, silver=CONDITIONAL GO, blue=MONITOR, orange=CAUTION, grey=PASS.

#### W1.4 — Keyword Detail Expander (on card click)

When user clicks "View Details", an `st.expander` opens showing:

```python
def render_keyword_detail(keyword_id: int, db):
    scores = db.query(KeywordScore).filter(KeywordScore.keyword_id == keyword_id).first()
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()

    # Radar chart of all 9 scores
    fig = go.Figure(data=go.Scatterpolar(
        r=[scores.demand_score, 100 - scores.competition_score,
           scores.opportunity_score, scores.feasibility_score or 0,
           scores.profitability_score or 0, scores.intent_score or 0,
           100 - (scores.saturation_score or 50), scores.weakness_score or 0,
           scores.trend_score or 0],
        theta=["Demand", "Competition (inv)", "Opportunity", "Feasibility",
               "Profitability", "Intent", "Saturation (inv)", "Weakness", "Trend"],
        fill="toself",
    ))
    st.plotly_chart(fig, use_container_width=True)

    # Score breakdown table
    st.dataframe(build_score_breakdown_df(scores))

    # Explanation text (LLM-generated)
    if scores.explanation_text:
        st.markdown(f"**Analysis:** {scores.explanation_text}")

    # Red flags
    if scores.red_flags:
        for flag in scores.red_flags:
            st.warning(f"⚠️ {flag['description']}")

    # Link to recommendation if available
    rec = db.query(Recommendation).filter(
        Recommendation.keyword_id == keyword_id
    ).first()
    if rec:
        st.success("📝 Recommendation available — go to Recommendations page")
```

**Chart type:** Plotly Scatterpolar (radar chart)
**Interactive behavior:** Hover shows exact score value per axis

---

## Page 2 — Keywords

### Purpose
Full keyword database browser with cluster grouping, search, and detailed views.

### Widgets

#### W2.1 — Keyword Search and Filters

```python
col1, col2, col3 = st.columns([3, 2, 2])
with col1:
    search_text = st.text_input("Search keywords", key="kw_search")
with col2:
    niche_filter = st.selectbox("Niche", ["All"] + get_niche_names(db), key="kw_niche")
with col3:
    view_mode = st.radio("View", ["Table", "Cluster View"], horizontal=True, key="kw_view")
```

#### W2.2 — Keyword Table (Table View)

```python
# Data source
query = db.query(Keyword).join(KeywordScore, isouter=True)
if search_text:
    query = query.filter(Keyword.keyword_text.ilike(f"%{search_text}%"))
if niche_filter != "All":
    query = query.filter(Keyword.niche_id == niche_id_from_name(niche_filter))

keywords = query.order_by(KeywordScore.final_score.desc().nullslast()).all()

df = pd.DataFrame([{
    "Keyword": kw.keyword_text,
    "Niche": get_niche_name(kw.niche_id),
    "Cluster": get_cluster_label(kw.cluster_id) or "—",
    "Intent": kw.intent_class or "—",
    "Final Score": get_final_score(kw.id, db) or "—",
    "Tag": get_tag(kw.id, db) or "—",
    "Demand": get_demand_score(kw.id, db) or "—",
    "Competition": get_competition_score(kw.id, db) or "—",
} for kw in keywords])

st.dataframe(df, use_container_width=True, height=600)
```

**Interactive behavior:** Clickable rows → open keyword detail expander (same as W1.4)

#### W2.3 — Cluster View

```python
# Group keywords by cluster
if view_mode == "Cluster View":
    clusters = db.query(ClusterAnalysis).filter(
        ClusterAnalysis.niche_id == niche_id
    ).order_by(ClusterAnalysis.cluster_label).all()

    for cluster in clusters:
        with st.expander(f"📁 {cluster.cluster_label} ({cluster.keyword_count} keywords)"):
            st.markdown(f"**Opportunity Narrative:** {cluster.opportunity_narrative}")
            cluster_keywords = get_keywords_for_cluster(cluster.cluster_id, db)
            df = build_keyword_df(cluster_keywords, db)
            st.dataframe(df, use_container_width=True)
```

---

## Page 3 — Competitors

### Purpose
Competitive intelligence view. Shows cluster synthesis, top sellers, weakness analysis, and change alerts.

### Widgets

#### W3.1 — Niche Selector

```python
niche = st.selectbox("Select Niche", get_niche_names(db), key="comp_niche")
```

#### W3.2 — Competitor Change Alerts

```python
# Data source
changes = db.query(Alert).filter(
    Alert.alert_type == "COMPETITOR_CHANGE",
    Alert.niche_id == niche_id,
    Alert.resolved == False,
).order_by(Alert.created_at.desc()).all()

if changes:
    st.subheader("Recent Changes")
    for change in changes:
        icon = {"REVIEW_SURGE": "📈", "LEVEL_UPGRADE": "⬆️", "NEW_TOP_ENTRANT": "🆕"}.get(
            change.metadata.get("change_type", ""), "📌"
        )
        st.info(f"{icon} {change.message}")
```

#### W3.3 — Cluster Synthesis Cards

```python
clusters = get_clusters_for_niche(niche_id, db)
for cluster in clusters:
    comp_analysis = get_competitor_analysis_for_cluster(cluster.cluster_id, db)
    if not comp_analysis:
        continue

    with st.container(border=True):
        st.subheader(f"📁 {cluster.cluster_label}")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**Who Dominates:** {comp_analysis.who_dominates}")
            st.markdown(f"**Why They Win:** {comp_analysis.why_they_win}")
            st.markdown(f"**The Gap:** {comp_analysis.the_gap}")
            st.markdown(f"**Entry Verdict:** {comp_analysis.entry_verdict}")
        with col2:
            # Feasibility gauge
            st.metric("Entry Feasibility", f"{comp_analysis.entry_feasibility_rating}/10")
```

#### W3.4 — Top Sellers Table

```python
sellers = get_top_sellers_for_niche(niche_id, db, limit=20)
df = pd.DataFrame([{
    "Username": s.seller_username,
    "Level": s.seller_level,
    "Reviews": s.total_reviews,
    "Authority": get_authority_score(s, db),
    "Response Rate": f"{s.response_rate}%",
    "Top Weakness": get_top_weakness(s, db),
    "New Seller?": "✅" if is_new_seller(s) else "",
} for s in sellers])

st.dataframe(df, use_container_width=True)
```

**Interactive behavior:** Click seller row → expander with full authority_signals list, all weaknesses, and bio parse results.

---

## Page 4 — Recommendations

### Purpose
The action page. Shows all generated recommendation packages with copy-paste-ready content and export buttons.

### Widgets

#### W4.1 — Recommendation Filters

```python
col1, col2, col3 = st.columns(3)
with col1:
    rec_niche = st.selectbox("Niche", ["All"] + get_niche_names(db), key="rec_niche")
with col2:
    rec_tag = st.multiselect("Tag", ["STRONG GO", "CONDITIONAL GO"], default=["STRONG GO", "CONDITIONAL GO"], key="rec_tag")
with col3:
    rec_complete = st.selectbox("Status", ["All", "Complete", "Partial"], key="rec_status")
```

#### W4.2 — Recommendation Cards

Each card follows the layout from RECOMMENDATION_OUTPUT_FORMAT.md:

```python
recommendations = get_filtered_recommendations(rec_niche, rec_tag, rec_complete, db)

for rec in recommendations:
    with st.container(border=True):
        # Header
        tag_color = {"STRONG GO": "🟡", "CONDITIONAL GO": "⚪"}.get(rec.tag, "⚫")
        complete_badge = "✅" if rec.generation_complete else "⚠️ Partial"
        st.markdown(f"### {tag_color} {rec.tag} — \"{get_keyword_text(rec.keyword_id, db)}\" "
                    f"  Score: {rec.final_score}  {complete_badge}")
        st.caption(f"Niche: {get_niche_name(rec.niche_id)} | Generated: {rec.generated_at.strftime('%Y-%m-%d %H:%M')} | Cost: ${rec.llm_cost_usd:.3f}")

        # Viability assessment
        if rec.niche_viability_assessment:
            via = rec.niche_viability_assessment
            st.markdown(f"**Viability:** {via.get('viability_assessment', '')}")
            st.markdown(f"**Timing:** {via.get('timing_assessment', '')}")
            st.markdown(f"**⚡ Recommendation:** {via.get('blunt_recommendation', '')}")

        # Tabbed sections
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Titles", "Packages", "Description", "Differentiation", "FAQ & Persona", "Risks"
        ])

        with tab1:
            if rec.gig_titles:
                for i, title in enumerate(rec.gig_titles, 1):
                    col_t, col_b = st.columns([5, 1])
                    with col_t:
                        st.markdown(f"**{i}.** {title['title']}  _{title['positioning_angle']}_")
                    with col_b:
                        st.button("📋", key=f"copy_title_{rec.keyword_id}_{i}",
                                  help="Copy to clipboard")

        with tab2:
            if rec.package_structure:
                pkg = rec.package_structure
                df_pkg = pd.DataFrame([
                    {"Tier": "Basic", "Name": pkg["basic"]["name"],
                     "Price": f"${pkg['basic']['price']}", "Delivery": f"{pkg['basic']['delivery_days']}d",
                     "Revisions": pkg["basic"]["revisions"],
                     "Deliverables": ", ".join(pkg["basic"]["deliverables"])},
                    {"Tier": "Standard", "Name": pkg["standard"]["name"],
                     "Price": f"${pkg['standard']['price']}", "Delivery": f"{pkg['standard']['delivery_days']}d",
                     "Revisions": pkg["standard"]["revisions"],
                     "Deliverables": ", ".join(pkg["standard"]["deliverables"])},
                    {"Tier": "Premium", "Name": pkg["premium"]["name"],
                     "Price": f"${pkg['premium']['price']}", "Delivery": f"{pkg['premium']['delivery_days']}d",
                     "Revisions": pkg["premium"]["revisions"],
                     "Deliverables": ", ".join(pkg["premium"]["deliverables"])},
                ])
                st.dataframe(df_pkg, use_container_width=True, hide_index=True)

        with tab3:
            if rec.description_outline:
                for section in rec.description_outline.get("sections", []):
                    st.markdown(f"**{section['heading']}** (~{section['estimated_words']} words)")
                    st.caption(section["copy_direction"])
                    if section.get("proof_elements"):
                        st.markdown(f"Proof elements: {', '.join(section['proof_elements'])}")

        with tab4:
            if rec.differentiation_angle:
                da = rec.differentiation_angle
                st.markdown(f"**Positioning:** {da.get('positioning_statement', '')}")
                st.markdown(f"**One-liner:** _{da.get('one_sentence_pitch', '')}_")
                for diff in da.get("differentiators", []):
                    st.markdown(f"→ **{diff['action']}** — exploits _{diff['competitor_weakness_exploited']}_, addresses _{diff['buyer_pain_addressed']}_")

        with tab5:
            if rec.faq_entries:
                for faq in rec.faq_entries:
                    st.markdown(f"**Q: {faq['question']}**")
                    st.markdown(f"A: {faq['answer']}")
            if rec.buyer_persona:
                bp = rec.buyer_persona
                st.divider()
                st.markdown(f"**Buyer Persona: {bp.get('name', 'Buyer')}** — {bp.get('role', '')}")
                st.markdown(f"Stage: {bp.get('company_stage', '')} | Budget: {bp.get('budget_range', '')}")
                st.markdown(f"Trigger: {bp.get('decision_trigger', '')}")

        with tab6:
            if rec.red_flags:
                rf = rec.red_flags
                risk_color = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(rf.get("overall_risk_level", ""), "⚪")
                st.markdown(f"**Overall Risk: {risk_color} {rf.get('overall_risk_level', 'Unknown')}**")
                st.markdown(f"_{rf.get('proceed_recommendation', '')}_")
                for flag in rf.get("red_flags", []):
                    sev_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(flag["severity"], "⚪")
                    st.markdown(f"{sev_icon} **{flag['flag_type']}:** {flag['description']}")
                    st.caption(f"Mitigation: {flag['mitigation']}")

        # Export and action buttons
        col_e1, col_e2, col_e3, col_e4 = st.columns(4)
        with col_e1:
            st.download_button("📄 Export Markdown", export_recommendation_markdown(rec),
                               file_name=f"rec_{rec.keyword_id}.md", key=f"md_{rec.keyword_id}")
        with col_e2:
            st.download_button("📊 Export JSON", export_recommendation_json(rec),
                               file_name=f"rec_{rec.keyword_id}.json", key=f"json_{rec.keyword_id}")
        with col_e3:
            if not rec.generation_complete:
                st.button("🔄 Regenerate", key=f"regen_{rec.keyword_id}",
                          on_click=trigger_regeneration, args=(rec.keyword_id,))
        with col_e4:
            st.button("📋 Copy All", key=f"copyall_{rec.keyword_id}")
```

#### W4.3 — Bulk Export

```python
st.divider()
col1, col2 = st.columns(2)
with col1:
    st.download_button("📦 Export All (Markdown)", bulk_export_markdown(recommendations),
                       file_name="all_recommendations.md")
with col2:
    st.download_button("📦 Export All (JSON)", bulk_export_json(recommendations),
                       file_name="all_recommendations.json")
```

---

## Page 5 — Run History

### Purpose
Operational view. Shows run logs, revenue gate tracking, data quality scores, and dead letter review.

### Widgets

#### W5.1 — Run List

```python
runs = db.query(RunLog).order_by(RunLog.started_at.desc()).limit(20).all()

df_runs = pd.DataFrame([{
    "Run": r.run_id[:8],
    "Date": r.started_at.strftime("%Y-%m-%d %H:%M"),
    "Mode": r.mode,
    "Duration": format_duration(r.duration_seconds),
    "Keywords": r.keywords_expanded,
    "Gigs": r.gigs_collected,
    "LLM Cost": f"${r.llm_cost_usd:.2f}",
    "Errors": r.error_count,
    "Status": r.status,
} for r in runs])

selected_run = st.dataframe(df_runs, use_container_width=True, on_select="rerun",
                             selection_mode="single-row")
```

#### W5.2 — Run Detail (on row selection)

```python
if selected_run:
    run = get_run_by_id(selected_run_id, db)

    st.subheader(f"Run {run.run_id[:8]} — {run.status}")
    st.markdown(run.summary_text or "_No summary available_")

    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Duration", format_duration(run.duration_seconds))
    col2.metric("LLM Cost", f"${run.llm_cost_usd:.2f}")
    col3.metric("Keywords Expanded", run.keywords_expanded)
    col4.metric("Gigs Collected", run.gigs_collected)

    # Auto-promotion changes
    if run.auto_promotion_changes:
        st.subheader("Depth Changes")
        for change in run.auto_promotion_changes:
            st.info(f"📊 {change['niche']}: {change['from_depth']} → {change['to_depth']}")

    # Dead letter jobs
    dead_letters = get_dead_letters_for_run(run.run_id, db)
    if dead_letters:
        st.subheader(f"Dead Letter Jobs ({len(dead_letters)})")
        for dl in dead_letters:
            with st.expander(f"❌ {dl.job_type} — {dl.error_message[:60]}"):
                st.code(dl.error_traceback)
                st.button("🔄 Retry", key=f"retry_{dl.id}",
                          on_click=retry_dead_letter, args=(dl.id,))
```

#### W5.3 — Revenue Gate Tracker

```python
st.subheader("💰 Revenue Gate Tracker")

# Order entry form
with st.form("order_entry"):
    col1, col2, col3 = st.columns(3)
    with col1:
        order_date = st.date_input("Date")
    with col2:
        order_niche = st.selectbox("Niche", get_niche_names(db))
    with col3:
        order_gross = st.number_input("Gross Amount ($)", min_value=0.0, step=5.0)
    submitted = st.form_submit_button("Add Order")
    if submitted and order_gross > 0:
        add_order(order_date, order_niche, order_gross, db)
        st.success(f"Order added: ${order_gross:.2f} for {order_niche}")

# Revenue gates
REVENUE_GATES = {
    4: 1720, 6: 4770, 9: 17795, 10: 25045, 12: 37500,
}

cumulative_gross = get_cumulative_gross(db)
current_month = get_months_since_start(db)

# Gate status bars
for month, target in REVENUE_GATES.items():
    progress = min(1.0, cumulative_gross / target) if target > 0 else 0
    if current_month >= month:
        status = "🟢" if cumulative_gross >= target else "🔴"
    elif current_month >= month - 1:
        status = "🟡"
    else:
        status = "⚪"
    st.progress(progress, text=f"{status} Month {month}: ${cumulative_gross:,.0f} / ${target:,.0f}")

# Cumulative vs target line chart
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(1, 13)), y=[get_target_at_month(m) for m in range(1, 13)],
                          name="Target", line=dict(dash="dash")))
fig.add_trace(go.Scatter(x=get_order_months(db), y=get_cumulative_by_month(db),
                          name="Actual"))
fig.update_layout(title="Cumulative Gross Revenue vs Target", xaxis_title="Month",
                  yaxis_title="Gross Revenue ($)")
st.plotly_chart(fig, use_container_width=True)
```

#### W5.4 — Data Quality Score

```python
st.subheader("📊 Data Quality")

quality_data = []
for niche_id in get_all_niche_ids(db):
    quality = calculate_niche_data_quality(niche_id, db)
    quality_data.append({
        "Niche": get_niche_name(niche_id),
        "Score": quality["score"],
        "Label": quality["label"],
        "Missing Fields": quality["missing_count"],
        "Stale Records": quality["stale_count"],
    })

df_quality = pd.DataFrame(quality_data)

# Horizontal bar chart
fig = px.bar(df_quality, x="Score", y="Niche", orientation="h",
             color="Label", color_discrete_map={
                 "GOOD": "#2ecc71", "FAIR": "#f39c12", "POOR": "#e74c3c"
             })
fig.update_layout(xaxis_range=[0, 100])
st.plotly_chart(fig, use_container_width=True)
```

---

## Page 6 — LLM Costs

### Purpose
Budget monitoring and cost optimization view.

### Widgets

#### W6.1 — Cost Summary Metrics

```python
col1, col2, col3, col4 = st.columns(4)
col1.metric("Today", f"${get_llm_cost_today(db):.2f}")
col2.metric("This Week", f"${get_llm_cost_week(db):.2f}")
col3.metric("This Month", f"${get_llm_cost_month(db):.2f}")
col4.metric("All Time", f"${get_llm_cost_total(db):.2f}")
```

#### W6.2 — Cost by Model (Donut Chart)

```python
model_costs = get_cost_by_model(db)
# Returns: [{"model": "gpt-4o", "cost": 12.50}, {"model": "gpt-4o-mini", "cost": 1.20}, ...]

fig = px.pie(model_costs, values="cost", names="model", hole=0.4,
             title="Cost by Model")
st.plotly_chart(fig, use_container_width=True)
```

#### W6.3 — Cost by Stage (Bar Chart)

```python
stage_costs = get_cost_by_stage(db)
# Returns costs grouped by pipeline stage (Stage 2, Stage 7, Stage 8, Stage 9, Stage 13, Stage 14)

fig = px.bar(stage_costs, x="stage", y="cost", title="Cost by Pipeline Stage",
             text_auto=".2f")
st.plotly_chart(fig, use_container_width=True)
```

#### W6.4 — Cost by Niche (Bar Chart)

```python
niche_costs = get_cost_by_niche(db)
fig = px.bar(niche_costs, x="niche", y="cost", title="Cost by Niche",
             text_auto=".2f")
st.plotly_chart(fig, use_container_width=True)
```

#### W6.5 — Cost per Run (Line Chart)

```python
run_costs = get_cost_per_run(db)
fig = px.line(run_costs, x="run_date", y="cost", title="LLM Cost per Run",
              markers=True)
st.plotly_chart(fig, use_container_width=True)
```

#### W6.6 — Cache Efficiency

```python
cache_stats = get_cache_stats(db)
# {"total_calls": 480, "cache_hits": 312, "cache_misses": 168, "hit_rate": 0.65,
#  "estimated_savings": 8.40}

col1, col2, col3 = st.columns(3)
col1.metric("Cache Hit Rate", f"{cache_stats['hit_rate']:.0%}")
col2.metric("Estimated Savings", f"${cache_stats['estimated_savings']:.2f}")
col3.metric("Total LLM Calls", cache_stats["total_calls"])

# Hit rate trend
hit_rate_trend = get_cache_hit_rate_by_run(db)
fig = px.line(hit_rate_trend, x="run_date", y="hit_rate", title="Cache Hit Rate Over Time",
              range_y=[0, 1])
st.plotly_chart(fig, use_container_width=True)
```

---

## Streamlit App Entry Point

```python
# src/dashboard/app.py

import streamlit as st

st.set_page_config(
    page_title="Fiverr Research System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar navigation
pages = {
    "🎯 Opportunities": page_opportunities,
    "🔑 Keywords": page_keywords,
    "👥 Competitors": page_competitors,
    "📝 Recommendations": page_recommendations,
    "📊 Run History": page_run_history,
    "💰 LLM Costs": page_llm_costs,
}

selected = st.sidebar.radio("Navigation", list(pages.keys()))

# Global header
st.sidebar.divider()
st.sidebar.markdown(f"**Last run:** {get_last_run_time(db)}")
st.sidebar.markdown(f"**Niches:** {get_active_niche_count(db)}")
st.sidebar.markdown(f"**Last LLM cost:** ${get_last_run_cost(db):.2f}")

# Run controls
with st.sidebar:
    run_mode = st.selectbox("Run Mode", ["full", "score-only", "recommendations-only", "collect-only"])
    if st.button("▶️ Run Now"):
        trigger_run(run_mode)
        st.toast(f"Run started: --mode {run_mode}")

# Render selected page
pages[selected]()
```
