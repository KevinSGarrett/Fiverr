# Run Log Design
# Fiverr Research System — Wave 8

**Document Status:** Complete
**Wave:** 8 — Reporting and Dashboard
**Purpose:** Run log dashboard view, run detail page layout, LLM usage history, data quality trend, and dead letter job review panel.

---

## Run Log Table — Dashboard Display (Page 5)

The run_logs table is defined in Wave 3 SCHEMA.md. This document specifies how it is displayed in the dashboard.

### Main Run List View

```python
# Columns displayed in the run list table
RUN_LIST_COLUMNS = {
    "Run":       "run_id[:8]",           # Truncated for display
    "Date":      "started_at",           # Format: YYYY-MM-DD HH:MM
    "Mode":      "mode",                 # full | score-only | recommendations-only | etc.
    "Duration":  "duration_seconds",      # Formatted: "2h 14m" or "45m"
    "Stage":     "completed_stages",      # "15/15" or "12/15 ⚠️"
    "Keywords":  "keywords_expanded",     # Count of keywords processed
    "Gigs":      "gigs_collected",        # Count of gigs collected
    "LLM Cost":  "llm_cost_usd",         # Format: "$1.42"
    "Errors":    "error_count",           # 0 = green, 1-5 = yellow, 5+ = red
    "Status":    "status",               # COMPLETED ✅ | FAILED ❌ | RUNNING ⏳
}
```

**Sorting:** Most recent first (by `started_at DESC`)
**Row limit:** Last 20 runs (pagination available)
**Interactive:** Click row → opens Run Detail expander

### Status Color Coding

```python
STATUS_COLORS = {
    "COMPLETED": "🟢",
    "COMPLETED_WITH_ERRORS": "🟡",
    "FAILED": "🔴",
    "RUNNING": "🔵",
    "CANCELLED": "⚪",
}
```

---

## Run Detail Page Layout

When a run is selected from the list, the detail view opens:

```
┌─────────────────────────────────────────────────────────────────┐
│ Run: abc12345  │  Status: COMPLETED ✅  │  Mode: full           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐             │
│  │ 2h14m│  │$1.42 │  │  312 │  │  187 │  │   2  │             │
│  │ Time │  │ Cost │  │ KWs  │  │ Gigs │  │ Errs │             │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘             │
│                                                                 │
│  ─── LLM Summary ────────────────────────────────────────────  │
│  "This run scored 312 keywords across 9 niches. 5 keywords     │
│   achieved STRONG GO status, up from 3 in the previous run.    │
│   Python Automation was promoted to full depth after its 3rd    │
│   consecutive run. Google Trends collection hit 2 rate limits   │
│   but recovered via adaptive pacing."                           │
│                                                                 │
│  ─── Stage Completion ───────────────────────────────────────  │
│  Stage 1: Config Load           ✅  0.2s                       │
│  Stage 2: Keyword Expansion     ✅  45s   (+12 new keywords)   │
│  Stage 3: Fiverr Search         ✅  8m    (312 queries)        │
│  Stage 4: Gig Detail Scrape     ✅  32m   (187 gigs)           │
│  Stage 5: Seller Profile        ✅  18m   (142 sellers)        │
│  Stage 6: Reddit Collection     ✅  3m    (9 niche queries)    │
│  Stage 7: Gig Quality Analysis  ✅  5m    ($0.42 LLM)          │
│  Stage 8: Competitor Analysis   ✅  4m    ($0.31 LLM)          │
│  Stage 9: Keyword Clustering    ✅  2m    ($0.08 LLM)          │
│  Stage 10: Scoring              ✅  1m                         │
│  Stage 11: Opportunity Ranking  ✅  0.5s                       │
│  Stage 12: Tag Assignment       ✅  0.3s                       │
│  Stage 13: Recommendations      ✅  6m    ($0.48 LLM, 18 recs) │
│  Stage 14: Reporting            ✅  2m    ($0.13 LLM)          │
│  Stage 15: Export               ✅  1m                         │
│                                                                 │
│  ─── Depth Changes ──────────────────────────────────────────  │
│  📊 Python Automation: standard → full (auto-promoted)          │
│                                                                 │
│  ─── Dead Letter Jobs (2) ───────────────────────────────────  │
│  ❌ google_trends_fetch — "429 Too Many Requests" (3 retries)  │
│     [🔄 Retry]                                                  │
│  ❌ seller_profile_scrape — "Timeout after 30s"                │
│     [🔄 Retry]                                                  │
│                                                                 │
│  ─── Tag Distribution ───────────────────────────────────────  │
│  STRONG GO:      ████░░░░░░░░░░░░  5  (1.6%)                  │
│  CONDITIONAL GO: ██████░░░░░░░░░░  13 (4.2%)                  │
│  MONITOR:        ████████████░░░░  89 (28.5%)                  │
│  CAUTION:        ██████████████░░  142 (45.5%)                 │
│  PASS:           ██████░░░░░░░░░░  63 (20.2%)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Stage Completion Display

```python
def render_stage_completion(run: RunLog, db):
    """Renders the stage-by-stage completion timeline."""
    stages = get_stage_completion_data(run.run_id, db)

    for stage in stages:
        icon = "✅" if stage["status"] == "completed" else "❌" if stage["status"] == "failed" else "⏭️"
        cost_str = f"  (${stage['llm_cost']:.2f} LLM)" if stage.get("llm_cost", 0) > 0 else ""
        detail_str = f"  ({stage['detail']})" if stage.get("detail") else ""

        st.markdown(
            f"**Stage {stage['number']}:** {stage['name']}  "
            f"{icon}  {format_duration(stage['duration_seconds'])}"
            f"{cost_str}{detail_str}"
        )
```

---

## LLM Usage History View

### Per-Run Token Usage Table

```python
def render_llm_usage_for_run(run_id: str, db):
    """Shows detailed LLM usage breakdown for a single run."""
    usage = db.query(LLMUsageLog).filter(
        LLMUsageLog.run_id == run_id,
    ).all()

    # Group by model
    by_model = {}
    for entry in usage:
        model = entry.model
        if model not in by_model:
            by_model[model] = {"calls": 0, "input_tokens": 0, "output_tokens": 0,
                                "cost": 0.0, "cache_hits": 0}
        by_model[model]["calls"] += 1
        by_model[model]["input_tokens"] += entry.input_tokens
        by_model[model]["output_tokens"] += entry.output_tokens
        by_model[model]["cost"] += entry.cost_usd
        if entry.cache_hit:
            by_model[model]["cache_hits"] += 1

    df = pd.DataFrame([
        {
            "Model": model,
            "Calls": data["calls"],
            "Input Tokens": f"{data['input_tokens']:,}",
            "Output Tokens": f"{data['output_tokens']:,}",
            "Cost": f"${data['cost']:.3f}",
            "Cache Hits": f"{data['cache_hits']}/{data['calls']}",
        }
        for model, data in by_model.items()
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
```

### Cost Breakdown by Stage

```python
def render_cost_by_stage(run_id: str, db):
    """Horizontal bar chart of LLM cost by pipeline stage."""
    stage_costs = db.query(
        LLMUsageLog.stage,
        func.sum(LLMUsageLog.cost_usd).label("cost"),
    ).filter(
        LLMUsageLog.run_id == run_id,
    ).group_by(LLMUsageLog.stage).all()

    fig = px.bar(
        [{"Stage": s.stage, "Cost ($)": s.cost} for s in stage_costs],
        x="Cost ($)", y="Stage", orientation="h",
        title="LLM Cost by Pipeline Stage",
    )
    st.plotly_chart(fig, use_container_width=True)
```

### Cache Hit Rate Trend

```python
def render_cache_trend(db):
    """Line chart of cache hit rate over runs."""
    runs = db.query(RunLog).order_by(RunLog.started_at).limit(30).all()

    data = []
    for run in runs:
        total = db.query(LLMUsageLog).filter(LLMUsageLog.run_id == run.run_id).count()
        hits = db.query(LLMUsageLog).filter(
            LLMUsageLog.run_id == run.run_id,
            LLMUsageLog.cache_hit == True,
        ).count()
        rate = hits / max(1, total)
        data.append({
            "Run Date": run.started_at.strftime("%Y-%m-%d"),
            "Hit Rate": rate,
        })

    fig = px.line(data, x="Run Date", y="Hit Rate", title="Cache Hit Rate Over Time",
                  range_y=[0, 1])
    st.plotly_chart(fig, use_container_width=True)
```

---

## Data Quality Score Trend

```python
def render_data_quality_trend(db):
    """Per-niche data quality score over time (line chart)."""
    niches = get_active_niche_ids(db)
    runs = db.query(RunLog).order_by(RunLog.started_at).limit(20).all()

    data = []
    for run in runs:
        for niche_id in niches:
            quality = get_niche_data_quality_at_run(niche_id, run.run_id, db)
            if quality:
                data.append({
                    "Run Date": run.started_at.strftime("%Y-%m-%d"),
                    "Niche": get_niche_name(niche_id),
                    "Quality Score": quality["score"],
                })

    fig = px.line(data, x="Run Date", y="Quality Score", color="Niche",
                  title="Data Quality Score by Niche Over Time", range_y=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
```

Quality score thresholds:
- 80–100: GOOD (green) — all core data fresh and complete
- 50–79: FAIR (yellow) — some gaps or staleness
- 0–49: POOR (red) — significant data issues, triggers DATA_QUALITY_LOW alert

---

## Dead Letter Job Review Panel

```python
def render_dead_letter_panel(run_id: str, db):
    """
    Table of permanently failed jobs with retry buttons.
    Only shows for runs with dead letter entries.
    """
    dead_letters = db.query(Job).filter(
        Job.run_id == run_id,
        Job.status == "DEAD_LETTER",
    ).order_by(Job.priority.desc()).all()

    if not dead_letters:
        st.success("No dead letter jobs for this run.")
        return

    st.warning(f"⚠️ {len(dead_letters)} jobs permanently failed")

    for dl in dead_letters:
        with st.expander(f"❌ {dl.job_type} — {dl.error_message[:60]}..."):
            st.markdown(f"**Job type:** {dl.job_type}")
            st.markdown(f"**Niche:** {get_niche_name(dl.niche_id)}")
            st.markdown(f"**Keyword:** {dl.keyword_text or 'N/A'}")
            st.markdown(f"**Attempts:** {dl.attempt_count}")
            st.markdown(f"**Last error:**")
            st.code(dl.error_traceback or dl.error_message, language="text")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Retry This Job", key=f"retry_{dl.id}"):
                    retry_dead_letter_job(dl.id, db)
                    st.toast(f"Retrying {dl.job_type}...")
                    st.rerun()
            with col2:
                if st.button("🗑️ Dismiss", key=f"dismiss_{dl.id}"):
                    dismiss_dead_letter(dl.id, db)
                    st.rerun()
```

### Retry Logic

```python
def retry_dead_letter_job(job_id: int, db):
    """
    Resets a dead letter job to PENDING status for retry.
    Clears error fields and resets attempt count.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if job:
        job.status = "PENDING"
        job.attempt_count = 0
        job.error_message = None
        job.error_traceback = None
        job.last_error_at = None
        db.commit()
        log.info(f"Dead letter job {job_id} ({job.job_type}) reset to PENDING for retry")
```

After retry, the job is picked up by the next run or by `--mode resume`.

---

## Run Log Summary Text Generation (LLM)

After each run completes, a gpt-4o-mini call generates a natural-language summary:

```python
async def generate_run_summary(run_id: str, db, llm_client) -> str:
    """
    Generates a 3–5 sentence summary of the run using gpt-4o-mini.
    Stored in run_logs.summary_text.
    """
    run = db.query(RunLog).filter(RunLog.run_id == run_id).first()
    stats = get_run_stats(run_id, db)

    prompt = f"""Summarize this automated Fiverr research system run in 3-5 sentences.

Run mode: {run.mode}
Duration: {format_duration(run.duration_seconds)}
Keywords processed: {stats['keywords_scored']}
Gigs collected: {stats['gigs_collected']}
LLM cost: ${stats['llm_cost']:.2f}
STRONG GO keywords: {stats['strong_go_count']}
CONDITIONAL GO keywords: {stats['conditional_go_count']}
New STRONG GO this run: {stats['new_strong_go_count']}
Errors: {stats['error_count']}
Dead letter jobs: {stats['dead_letter_count']}
Auto-promotions: {stats['auto_promotion_changes']}
Cache hit rate: {stats['cache_hit_rate']:.0%}

Focus on: what changed since the last run, any notable new opportunities,
any issues encountered. Be concise and specific."""

    result = await llm_client.complete(prompt, model="gpt-4o-mini", temperature=0.3)
    return result
```

This summary is displayed at the top of the Run Detail view and included in the Run Summary PDF report.
