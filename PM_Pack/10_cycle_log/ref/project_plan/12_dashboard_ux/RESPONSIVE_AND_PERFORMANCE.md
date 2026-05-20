# Responsive and Performance
# Fiverr Research System — Wave 12

**Document Status:** Complete
**Wave:** 12 — Dashboard UX Overhaul
**Purpose:** Streamlit layout optimization, chart performance, query optimization, caching strategy, session state management, mobile considerations, data pagination, and export performance.

---

## Streamlit Layout Optimization

### Column Ratios by Page

Each page uses specific column ratios optimized for its content type:

```python
# Page-specific layout configurations

PAGE_LAYOUTS = {
    "opportunities": {
        "filter_cols": [2, 2, 2, 2],           # Equal 4-column filter bar
        "card_grid": 2,                          # 2-column card grid
        "detail_cols": [3, 1],                   # Detail expander: content + sidebar
    },
    "keywords": {
        "filter_cols": [3, 2, 2],               # Search wider, filters narrower
        "table_height": 600,                     # Taller table for data browsing
    },
    "competitors": {
        "main_cols": [3, 1],                     # Synthesis narrative + metrics sidebar
        "table_height": 500,
    },
    "recommendations": {
        "card_width": "full",                    # Full-width cards (lots of content)
        "tab_count": 8,                          # Titles, Packages, Description, Differentiation, FAQ, Risks, Pricing, Profile
    },
    "run_history": {
        "main_cols": [2, 1],                     # Run list + revenue tracker sidebar
        "detail_cols": [1, 1, 1, 1, 1],          # 5-column metric row
    },
    "llm_costs": {
        "chart_cols": [1, 1],                    # 2-column chart grid
    },
    "discovery": {
        "gold_cols": [3, 1, 1],                  # Gold card: content + score + tag
    },
}
```

### Container Usage Patterns

```python
# Pattern 1: Card with header and body
def card(title: str, tag_html: str = ""):
    """Reusable card container with header."""
    with st.container(border=True):
        # Header row
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{title}**")
        with col2:
            if tag_html:
                st.markdown(tag_html, unsafe_allow_html=True)
        # Body content rendered by caller after this

# Pattern 2: Sidebar metrics panel
def sidebar_metrics(metrics: list[dict]):
    """Vertical stack of metrics on the right side."""
    for m in metrics:
        st.metric(m["label"], m["value"], delta=m.get("delta"))

# Pattern 3: Section with divider
def section(title: str, help_text: str = None):
    """Section heading with optional help."""
    st.divider()
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader(title)
    if help_text:
        with col2:
            st.caption(f"ℹ️ {help_text}")
```

---

## Chart Performance

### Lazy Loading

Charts below the viewport shouldn't render until the user scrolls to them:

```python
def lazy_chart(chart_fn, key: str, **kwargs):
    """
    Renders a chart only when the user scrolls to it.
    Uses st.empty() as placeholder, renders on visibility.

    In Streamlit v1, true lazy loading isn't native.
    Workaround: use st.expander for non-critical charts.
    """
    # For critical charts (top of page): render immediately
    if kwargs.get("critical", False):
        chart_fn(**kwargs)
        return

    # For secondary charts: wrap in collapsed expander
    with st.expander(kwargs.get("title", "Chart"), expanded=False):
        chart_fn(**kwargs)
```

### Data Point Limits

```python
# Maximum data points per chart type to prevent slow rendering

CHART_LIMITS = {
    "line_chart": 500,      # Max points per trace
    "bar_chart": 100,       # Max bars
    "scatter": 1000,        # Max scatter points
    "heatmap_rows": 50,     # Max rows in heatmap
    "radar": 12,            # Max axes on radar chart
    "pie_slices": 10,       # Max slices (group remainder as "Other")
}


def limit_chart_data(df, chart_type: str, sort_by: str = None) -> pd.DataFrame:
    """Reduces dataframe to chart-appropriate size."""
    limit = CHART_LIMITS.get(chart_type, 100)
    if len(df) <= limit:
        return df

    if sort_by and sort_by in df.columns:
        return df.nlargest(limit, sort_by)
    return df.head(limit)
```

### Plotly Configuration for Performance

```python
def fast_plotly_config():
    """Plotly config optimized for rendering speed."""
    return {
        "displayModeBar": False,      # Hide toolbar for cleaner look
        "staticPlot": False,          # Keep interactivity
        "responsive": True,
        "scrollZoom": False,          # Prevent accidental zoom
    }


def render_plotly(fig, key: str, height: int = 350):
    """Standardized Plotly rendering with performance defaults."""
    fig.update_layout(
        **chart_config(),
        height=height,
        autosize=True,
    )
    st.plotly_chart(
        fig,
        use_container_width=True,
        config=fast_plotly_config(),
        key=key,
    )
```

---

## Query Optimization

### Avoiding N+1 Queries

The biggest performance pitfall: querying the database in a loop.

```python
# ❌ BAD: N+1 query pattern (1 query per keyword)
for keyword in keywords:
    score = db.query(KeywordScore).filter(KeywordScore.keyword_id == keyword.id).first()
    tag = db.query(OpportunityRanking).filter(OpportunityRanking.keyword_id == keyword.id).first()


# ✅ GOOD: Batch query with joins
results = db.query(
    Keyword,
    KeywordScore,
    OpportunityRanking,
).outerjoin(
    KeywordScore, Keyword.id == KeywordScore.keyword_id,
).outerjoin(
    OpportunityRanking, Keyword.id == OpportunityRanking.keyword_id,
).filter(
    Keyword.niche_id == niche_id,
).order_by(
    KeywordScore.final_score.desc().nullslast(),
).all()

# Convert to DataFrame in one step
df = pd.DataFrame([{
    "keyword": r.Keyword.keyword_text,
    "score": r.KeywordScore.final_score if r.KeywordScore else None,
    "tag": r.OpportunityRanking.tag if r.OpportunityRanking else None,
} for r in results])
```

### Pre-Built Query Functions

```python
# src/dashboard/queries.py

def get_opportunities_page_data(niche_id: str | None, tag_filter: list, sort_by: str,
                                  db, limit: int = 50) -> pd.DataFrame:
    """
    Single query that returns all data needed for the Opportunities page.
    Eliminates all N+1 patterns.
    """
    query = db.query(
        Keyword.id,
        Keyword.keyword_text,
        Keyword.niche_id,
        Keyword.intent_class,
        KeywordScore.final_score,
        KeywordScore.demand_score,
        KeywordScore.competition_score,
        KeywordScore.opportunity_score,
        KeywordScore.feasibility_score,
        KeywordScore.confidence_modifier,
        OpportunityRanking.tag,
        OpportunityRanking.rank,
        # Check if recommendation exists
        func.count(Recommendation.id).label("has_recommendation"),
    ).outerjoin(
        KeywordScore, Keyword.id == KeywordScore.keyword_id,
    ).outerjoin(
        OpportunityRanking, Keyword.id == OpportunityRanking.keyword_id,
    ).outerjoin(
        Recommendation, Keyword.id == Recommendation.keyword_id,
    ).group_by(Keyword.id)

    if niche_id:
        query = query.filter(Keyword.niche_id == niche_id)
    if tag_filter:
        query = query.filter(OpportunityRanking.tag.in_(tag_filter))

    sort_map = {
        "Final Score": KeywordScore.final_score.desc().nullslast(),
        "Demand Score": KeywordScore.demand_score.desc().nullslast(),
        "Opportunity Score": KeywordScore.opportunity_score.desc().nullslast(),
        "Trend Score": KeywordScore.trend_score.desc().nullslast(),
    }
    query = query.order_by(sort_map.get(sort_by, KeywordScore.final_score.desc().nullslast()))
    query = query.limit(limit)

    return pd.read_sql(query.statement, db.bind)


def get_recommendations_page_data(niche_id: str | None, tag_filter: list,
                                    db) -> list:
    """
    Returns recommendation objects with all related data pre-loaded.
    Uses SQLAlchemy eager loading to avoid N+1.
    """
    from sqlalchemy.orm import joinedload

    query = db.query(Recommendation).options(
        joinedload(Recommendation.keyword),
    )

    if niche_id:
        query = query.filter(Recommendation.niche_id == niche_id)
    if tag_filter:
        query = query.filter(Recommendation.tag.in_(tag_filter))

    return query.order_by(Recommendation.final_score.desc()).all()
```

---

## Caching Strategy

### Streamlit Cache Decorators

```python
# Cache expensive computations that don't change during a session

@st.cache_data(ttl=300)  # 5-minute TTL
def get_niche_names_cached(db_url: str) -> list[str]:
    """Cached niche names — rarely changes."""
    db = get_db(db_url)
    return [n.name for n in db.query(NicheConfig).order_by(NicheConfig.name).all()]


@st.cache_data(ttl=60)  # 1-minute TTL
def get_opportunities_cached(niche_id, tag_filter, sort_by, db_url) -> pd.DataFrame:
    """Cached opportunities page data — refreshes every minute."""
    db = get_db(db_url)
    return get_opportunities_page_data(niche_id, tag_filter, sort_by, db)


@st.cache_data(ttl=3600)  # 1-hour TTL
def get_price_analysis_cached(keyword_id: int, db_url: str) -> dict:
    """Cached price analysis — expensive to compute, rarely changes."""
    db = get_db(db_url)
    return get_price_analysis(keyword_id, db)


# DO NOT cache:
# - Anything that depends on user interaction (selections, form inputs)
# - Real-time data (run status, active alerts)
# - Data that changes during a run
```

### Cache Invalidation

```python
def invalidate_caches():
    """Called after a run completes or user triggers refresh."""
    st.cache_data.clear()
    notify("Data refreshed", "success")
```

---

## Data Pagination

### Server-Side Pagination for Large Tables

```python
def paginated_table(query_fn, page_size: int = 50, key: str = "table"):
    """
    Renders a paginated dataframe for tables with 100+ rows.
    """
    # Get total count (cached)
    total = query_fn(count_only=True)
    total_pages = max(1, (total + page_size - 1) // page_size)

    # Page selector
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.markdown(f"**{total} records**")
    with col2:
        page = st.number_input("Page", min_value=1, max_value=total_pages,
                                value=1, key=f"{key}_page")
    with col3:
        st.markdown(f"of {total_pages} pages")

    # Fetch current page data
    offset = (page - 1) * page_size
    df = query_fn(offset=offset, limit=page_size)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Quick navigation
    col1, col2, col3 = st.columns(3)
    with col1:
        if page > 1:
            if st.button("← Previous", key=f"{key}_prev"):
                st.session_state[f"{key}_page"] = page - 1
                st.rerun()
    with col3:
        if page < total_pages:
            if st.button("Next →", key=f"{key}_next"):
                st.session_state[f"{key}_page"] = page + 1
                st.rerun()
```

---

## Mobile Considerations

Streamlit renders on mobile browsers with automatic column stacking. Additional mobile optimizations:

```python
def detect_mobile() -> bool:
    """
    Heuristic mobile detection via CSS media query.
    Streamlit doesn't expose viewport width directly.
    """
    # Inject CSS that only applies to narrow viewports
    st.markdown("""
    <style>
        @media (max-width: 768px) {
            /* Stack columns vertically */
            [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
            }

            /* Reduce padding */
            .main .block-container {
                padding: 12px !important;
            }

            /* Smaller metrics */
            [data-testid="stMetricValue"] {
                font-size: 1.5rem !important;
            }

            /* Full-width tables */
            [data-testid="stDataFrame"] {
                min-width: 100% !important;
            }

            /* Hide secondary columns in tables */
            .mobile-hide {
                display: none !important;
            }

            /* Larger touch targets */
            .stButton > button {
                min-height: 44px !important;
                min-width: 44px !important;
            }

            /* Stack tabs vertically on very small screens */
            @media (max-width: 480px) {
                .stTabs [data-baseweb="tab-list"] {
                    flex-wrap: wrap;
                }
            }
        }
    </style>
    """, unsafe_allow_html=True)
```

### Mobile-Friendly Component Variants

```python
def responsive_metric_row(metrics: list[dict]):
    """
    Renders metrics in a row that stacks on mobile.
    Desktop: horizontal row of 4-5 metrics
    Mobile: 2-column grid
    """
    # Use Streamlit columns (auto-stack on mobile)
    cols = st.columns(len(metrics))
    for i, metric in enumerate(metrics):
        with cols[i]:
            st.metric(
                metric["label"],
                metric["value"],
                delta=metric.get("delta"),
            )
```

---

## Export Performance

### Asynchronous Export for Large Datasets

```python
import threading

def async_export(export_fn, *args, **kwargs):
    """
    Runs export in background thread with progress indicator.
    Used for large Excel/PDF exports.
    """
    progress_bar = st.progress(0, text="Preparing export...")

    def run_export():
        try:
            result = export_fn(*args, progress_callback=update_progress, **kwargs)
            st.session_state["export_result"] = result
            st.session_state["export_complete"] = True
        except Exception as e:
            st.session_state["export_error"] = str(e)

    def update_progress(pct: float, message: str = ""):
        progress_bar.progress(pct, text=message)

    thread = threading.Thread(target=run_export)
    thread.start()

    # Poll for completion
    while thread.is_alive():
        import time
        time.sleep(0.5)

    if st.session_state.get("export_complete"):
        progress_bar.progress(1.0, text="Export complete!")
        result = st.session_state.pop("export_result")
        notify(f"Export saved: {result}", "success")
        return result
    elif st.session_state.get("export_error"):
        error = st.session_state.pop("export_error")
        notify(f"Export failed: {error}", "error")
        return None
```

### Export File Size Estimates

| Export Type | Typical Size | Generation Time |
|---|---|---|
| CSV (keywords) | 50–200 KB | < 1 second |
| CSV (recommendations) | 100–500 KB | < 1 second |
| Excel (multi-sheet) | 500 KB – 2 MB | 2–5 seconds |
| PDF (opportunity report) | 200 KB – 1 MB | 3–8 seconds |
| PDF (playbook) | 300 KB – 1.5 MB | 5–10 seconds |
| JSON (full export) | 1–5 MB | 2–5 seconds |
| Markdown (recommendations) | 50–200 KB | < 1 second |

---

## Performance Budget

Target load times per page:

| Page | Target | Strategy |
|---|---|---|
| Opportunities | < 2 seconds | Single batch query + cached niche names |
| Keywords | < 2 seconds | Paginated table (50 rows default) |
| Competitors | < 3 seconds | Lazy-load synthesis narratives in expanders |
| Recommendations | < 3 seconds | Lazy-load tab content (only render active tab) |
| Run History | < 1 second | Paginated run list (20 rows) |
| LLM Costs | < 2 seconds | Cached aggregate queries |
| Discovery | < 2 seconds | Paginated leaderboard + cached mode stats |

### Monitoring

```python
import time

def measure_page_load(page_fn, page_name: str):
    """Wraps a page function to measure and log load time."""
    start = time.time()
    page_fn()
    elapsed = time.time() - start

    if elapsed > 3.0:
        log.warning(f"Page '{page_name}' took {elapsed:.2f}s to load (target: <3s)")

    # Show load time in footer (debug mode only)
    if st.session_state.get("debug_mode"):
        st.caption(f"⏱ Page loaded in {elapsed:.2f}s")
```

---

## App Entry Point (Updated)

```python
# src/dashboard/app.py — Final version with all Wave 12 enhancements

import streamlit as st
from styles import inject_custom_css
from interactions import (initialize_session_state, inject_keyboard_shortcuts,
                          render_quick_actions, render_shortcut_help, render_theme_toggle,
                          check_first_run, render_onboarding_wizard)

st.set_page_config(
    page_title="Fiverr Research System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize
initialize_session_state()
inject_custom_css()
inject_keyboard_shortcuts()

# Theme
render_theme_toggle()

# Check first run
if check_first_run(db):
    render_onboarding_wizard(config)
else:
    # Navigation
    pages = {
        "🎯 Opportunities": page_opportunities,
        "🔑 Keywords": page_keywords,
        "👥 Competitors": page_competitors,
        "📝 Recommendations": page_recommendations,
        "📊 Run History": page_run_history,
        "💰 LLM Costs": page_llm_costs,
        "🔬 Discovery": page_discovery,
    }

    selected = st.sidebar.radio("Navigation", list(pages.keys()),
                                  key="current_page")

    # Quick actions and shortcuts
    render_quick_actions()
    render_shortcut_help()

    # Sidebar footer
    st.sidebar.divider()
    st.sidebar.caption(f"Last run: {get_last_run_time(db)}")
    st.sidebar.caption(f"Niches: {get_active_niche_count(db)} | "
                       f"Keywords: {get_total_keyword_count(db)}")

    # Render page with performance measurement
    measure_page_load(pages[selected], selected)
```
