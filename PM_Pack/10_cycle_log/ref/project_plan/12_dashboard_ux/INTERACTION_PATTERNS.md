# Interaction Patterns
# Fiverr Research System — Wave 12

**Document Status:** Complete
**Wave:** 12 — Dashboard UX Overhaul
**Purpose:** Navigation flows, keyboard shortcuts, notification system, progressive disclosure, bulk actions, comparison mode, quick actions, help tooltips, and first-run onboarding.

---

## Navigation Architecture

### Page Hierarchy

```
Sidebar Navigation (always visible)
├── 🎯 Opportunities      (landing page — decision view)
├── 🔑 Keywords            (full keyword database)
├── 👥 Competitors          (competitive intelligence)
├── 📝 Recommendations      (gig-ready packages)
├── 📊 Run History          (operational + revenue)
├── 💰 LLM Costs            (budget monitoring)
└── 🔬 Discovery            (autonomous exploration)
```

### Cross-Page Navigation Links

Every entity in the system is clickable and navigates to its detail view on the appropriate page:

```python
ENTITY_LINKS = {
    "keyword": {
        "from_pages": ["Opportunities", "Keywords", "Competitors", "Discovery"],
        "target_page": "Keywords",
        "action": "Opens keyword detail expander with full score breakdown",
    },
    "recommendation": {
        "from_pages": ["Opportunities", "Keywords"],
        "target_page": "Recommendations",
        "action": "Scrolls to recommendation card for that keyword",
    },
    "seller": {
        "from_pages": ["Competitors", "Recommendations"],
        "target_page": "Competitors",
        "action": "Opens seller detail expander",
    },
    "run": {
        "from_pages": ["Opportunities (alert banners)", "LLM Costs"],
        "target_page": "Run History",
        "action": "Selects that run in the run list",
    },
    "discovery_keyword": {
        "from_pages": ["Discovery"],
        "target_page": "Keywords",
        "action": "Opens keyword detail with discovery metadata visible",
    },
}
```

Implementation via `st.session_state`:

```python
def navigate_to(page: str, entity_id: int = None, entity_type: str = None):
    """Sets navigation target in session state. App reads this on rerun."""
    st.session_state["nav_target_page"] = page
    st.session_state["nav_target_entity_id"] = entity_id
    st.session_state["nav_target_entity_type"] = entity_type
    st.rerun()


def check_navigation_target():
    """Called at top of each page to handle incoming navigation."""
    target = st.session_state.get("nav_target_entity_id")
    if target:
        entity_type = st.session_state.get("nav_target_entity_type")
        # Clear the target so it doesn't re-trigger
        st.session_state["nav_target_entity_id"] = None
        return target, entity_type
    return None, None
```

### Breadcrumb Trail

```python
def render_breadcrumbs(crumbs: list[dict]):
    """
    Shows navigation path: Dashboard > Keywords > "AI SaaS PRD"
    crumbs: [{"label": "Dashboard", "page": None}, {"label": "Keywords", "page": "Keywords"}, ...]
    """
    parts = []
    for i, crumb in enumerate(crumbs):
        if i == len(crumbs) - 1:
            # Current page — not a link
            parts.append(f'<span style="color:var(--color-neutral-800); font-weight:600;">{crumb["label"]}</span>')
        else:
            parts.append(f'<span style="color:var(--color-neutral-400); cursor:pointer;">{crumb["label"]}</span>')

    separator = ' <span style="color:var(--color-neutral-300); margin:0 8px;">›</span> '
    st.markdown(f"""
    <div style="font-size:var(--text-sm); margin-bottom:16px;">
        {separator.join(parts)}
    </div>
    """, unsafe_allow_html=True)
```

---

## Keyboard Shortcuts

Implemented via JavaScript injection:

```python
def inject_keyboard_shortcuts():
    """Injects keyboard event listeners for common actions."""
    st.markdown("""
    <script>
    document.addEventListener('keydown', function(e) {
        // Don't capture when typing in inputs
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        const shortcuts = {
            'r': 'refresh',      // R = Refresh data
            'n': 'new_run',      // N = Start new run
            '/': 'search',       // / = Focus search
            '1': 'page_1',      // 1-7 = Navigate to page
            '2': 'page_2',
            '3': 'page_3',
            '4': 'page_4',
            '5': 'page_5',
            '6': 'page_6',
            '7': 'page_7',
            'Escape': 'close',   // Esc = Close expander/modal
        };

        const action = shortcuts[e.key];
        if (action) {
            // Send action to Streamlit via custom component or hidden button
            const hiddenBtn = document.querySelector(`[data-shortcut="${action}"]`);
            if (hiddenBtn) hiddenBtn.click();
        }
    });
    </script>
    """, unsafe_allow_html=True)
```

### Shortcut Reference

| Key | Action | Context |
|---|---|---|
| R | Refresh current page data | Any page |
| N | Open "Run Now" dropdown | Any page |
| / | Focus search input | Keywords page |
| 1–7 | Navigate to page 1–7 | Any page |
| Esc | Close open expander or dismiss alert | Any page |
| E | Export current view | Recommendations, Keywords |
| ? | Toggle help tooltips | Any page |

### Shortcut Help Overlay

```python
def render_shortcut_help():
    """Shows keyboard shortcut reference in sidebar footer."""
    with st.sidebar.expander("⌨️ Keyboard Shortcuts"):
        st.markdown("""
        | Key | Action |
        |---|---|
        | `R` | Refresh |
        | `N` | New run |
        | `/` | Search |
        | `1`–`7` | Navigate pages |
        | `Esc` | Close panel |
        | `E` | Export |
        | `?` | Toggle help |
        """)
```

---

## Notification System

### Toast Notifications

```python
def notify(message: str, type: str = "info", duration: int = 3):
    """
    Shows a toast notification.
    type: "success" | "info" | "warning" | "error"
    """
    icons = {"success": "✅", "info": "ℹ️", "warning": "⚠️", "error": "❌"}
    st.toast(f"{icons.get(type, 'ℹ️')} {message}")
```

### Notification Triggers

| Event | Notification | Type |
|---|---|---|
| Run started | "Run started: --mode full" | info |
| Run completed | "Run complete: 312 keywords scored, $1.42 LLM cost" | success |
| Run failed | "Run failed at Stage 5 — see Run History" | error |
| Export complete | "Exported to data/exports/excel/..." | success |
| Recommendation regenerated | "Recommendation updated for 'AI SaaS PRD'" | success |
| Gold discovery | "🏆 Gold discovery: 'keyword' scored 87.2!" | success |
| Dead letter retry | "Retrying google_trends_fetch..." | info |
| Price ladder update | "Prices updated to 10-review level" | info |

---

## Progressive Disclosure Pattern

The dashboard uses a 3-level depth model. Users see the summary first, drill into details on demand:

### Level 1 — Summary (Visible by Default)

Opportunity cards, KPI metrics, tag distribution. Answers: "What are my best opportunities right now?"

### Level 2 — Detail (Click to Expand)

Score breakdown, competitor analysis, pricing data. Answers: "Why is this keyword scoring well?"

### Level 3 — Raw Data (On Demand)

Full score component values, raw competitor data, LLM prompt/response logs. Answers: "How exactly was this calculated?"

```python
def progressive_detail(keyword_id: int, db):
    """
    Level 1: Score card with tag badge (always visible)
    Level 2: Expander with radar chart + score breakdown
    Level 3: Second expander with raw component values
    """
    score = get_keyword_score(keyword_id, db)
    tag = get_tag(keyword_id, db)

    # Level 1 — Summary line
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"**{get_keyword_text(keyword_id, db)}**")
    with col2:
        tag_badge(tag, size="sm")
    with col3:
        score_card("Score", score.final_score, size="sm")

    # Level 2 — Detail (click to expand)
    with st.expander("Score breakdown"):
        render_radar_chart(score)
        render_score_table(score)

        # Level 3 — Raw data (nested expander)
        with st.expander("Raw score components"):
            st.json(score.score_components)
            if score.explanation_text:
                st.markdown(f"**LLM Explanation:** {score.explanation_text}")
```

---

## Bulk Actions

### Multi-Select for Keywords/Recommendations

```python
def render_bulk_action_bar(selected_ids: list[int], entity_type: str):
    """
    Appears when user selects multiple items.
    entity_type: "keyword" | "recommendation" | "discovery"
    """
    if not selected_ids:
        return

    count = len(selected_ids)
    st.markdown(f"""
    <div style="position:sticky; top:0; z-index:100; padding:12px 20px;
                background:var(--color-primary-600); color:white;
                border-radius:var(--radius-md); margin-bottom:16px;
                display:flex; align-items:center; justify-content:space-between;">
        <span style="font-weight:600;">{count} {entity_type}(s) selected</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button(f"📄 Export {count} as Markdown"):
            bulk_export_markdown(selected_ids, entity_type)
    with col2:
        if st.button(f"📊 Export {count} as Excel"):
            bulk_export_excel(selected_ids, entity_type)
    with col3:
        if entity_type == "recommendation":
            if st.button(f"🔄 Regenerate {count}"):
                bulk_regenerate(selected_ids)
    with col4:
        if st.button("✖️ Clear Selection"):
            st.session_state["selected_ids"] = []
            st.rerun()
```

---

## Comparison Mode

Side-by-side keyword comparison (2–3 keywords, all scores):

```python
def render_comparison_mode(db):
    """
    Compare 2-3 keywords side by side.
    Accessible via "Compare" button on keyword rows.
    """
    compare_ids = st.session_state.get("compare_keywords", [])

    if len(compare_ids) < 2:
        st.info("Select 2-3 keywords to compare. Click 'Add to Compare' on keyword rows.")
        return

    st.subheader("Keyword Comparison")

    keywords = [db.query(Keyword).filter(Keyword.id == kid).first() for kid in compare_ids]
    scores = [db.query(KeywordScore).filter(KeywordScore.keyword_id == kid).first() for kid in compare_ids]

    # Header row
    cols = st.columns(len(keywords) + 1)
    cols[0].markdown("**Metric**")
    for i, kw in enumerate(keywords):
        cols[i + 1].markdown(f"**{kw.keyword_text}**")

    # Score rows
    score_fields = [
        ("Final Score", "final_score"),
        ("Tag", "tag"),
        ("Demand", "demand_score"),
        ("Competition", "competition_score"),
        ("Opportunity", "opportunity_score"),
        ("Feasibility", "feasibility_score"),
        ("Profitability", "profitability_score"),
        ("Intent", "intent_score"),
        ("Saturation", "saturation_score"),
        ("Weakness", "weakness_score"),
        ("Trend", "trend_score"),
        ("Confidence", "confidence_modifier"),
    ]

    for label, field in score_fields:
        cols = st.columns(len(keywords) + 1)
        cols[0].markdown(f"**{label}**")
        values = []
        for i, score in enumerate(scores):
            val = getattr(score, field, None) if score else None
            values.append(val)
            if val is not None:
                if field == "tag":
                    tag_badge(str(val), size="sm")
                elif isinstance(val, float):
                    cols[i + 1].markdown(f"`{val:.1f}`")
                else:
                    cols[i + 1].markdown(f"`{val}`")
            else:
                cols[i + 1].markdown("—")

        # Highlight winner (highest value for positive metrics)
        if values and all(isinstance(v, (int, float)) for v in values if v is not None):
            numeric_vals = [(v, i) for i, v in enumerate(values) if v is not None]
            if numeric_vals:
                if field != "competition_score" and field != "saturation_score":
                    best_idx = max(numeric_vals, key=lambda x: x[0])[1]
                else:
                    best_idx = min(numeric_vals, key=lambda x: x[0])[1]
                # Winner gets green highlight (applied via CSS)

    # Overlay radar chart
    fig = go.Figure()
    for kw, score in zip(keywords, scores):
        if not score:
            continue
        fig.add_trace(go.Scatterpolar(
            r=[score.demand_score or 0, 100 - (score.competition_score or 50),
               score.opportunity_score or 0, score.feasibility_score or 0,
               score.profitability_score or 0, score.trend_score or 0],
            theta=["Demand", "Competition (inv)", "Opportunity",
                   "Feasibility", "Profitability", "Trend"],
            fill="toself",
            name=kw.keyword_text[:20],
            opacity=0.6,
        ))
    fig.update_layout(**chart_config(), height=400, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    # Clear comparison button
    if st.button("✖️ Clear Comparison"):
        st.session_state["compare_keywords"] = []
        st.rerun()
```

---

## Quick Actions

One-click actions available on every page:

```python
def render_quick_actions():
    """Quick action buttons in sidebar."""
    st.sidebar.divider()
    st.sidebar.markdown("**Quick Actions**")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("▶️ Full Run", key="qa_full"):
            trigger_run("full")
            notify("Full run started", "info")

    with col2:
        if st.button("📝 Recs Only", key="qa_recs"):
            trigger_run("recommendations-only")
            notify("Recommendation generation started", "info")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("📦 Export All", key="qa_export"):
            trigger_export_all()
            notify("Export started", "info")

    with col2:
        if st.button("🔬 Discover", key="qa_discover"):
            trigger_run("discovery-only")
            notify("Discovery cycle started", "info")
```

---

## Help Tooltips

Every metric and chart has an explanatory tooltip:

```python
TOOLTIPS = {
    "final_score": "Weighted composite of all 11 scores × confidence modifier. Higher = better opportunity.",
    "demand_score": "How much buyer demand exists: Fiverr result count (50%), autocomplete position (20%), Google Trends (20%), Reddit signals (10%).",
    "competition_score": "How strong the existing competition is. LOWER = weaker competition = better for you.",
    "opportunity_score": "Non-linear interaction of demand and competition. Highest when demand is high AND competition is low.",
    "confidence_modifier": "How reliable the scores are (0-1). Based on data completeness, freshness, source diversity, and LLM analysis coverage.",
    "moat_strength": "How much extra established sellers can charge due to reviews. HIGH = big review advantage, you need to undercut more.",
    "market_type": "COMMODITY = tight pricing. WIDE_SPREAD = room for differentiation. FRAGMENTED = unclear buyer expectations.",
    "discovery_hit_rate": "% of discovery hypotheses that scored CONDITIONAL GO (60+) or better.",
    "cache_hit_rate": "% of LLM calls served from cache instead of API. Higher = lower cost.",
}


def help_tooltip(metric_key: str):
    """Renders a small help icon with tooltip text."""
    text = TOOLTIPS.get(metric_key, "")
    if text:
        st.markdown(f'<span title="{text}" style="cursor:help; color:var(--color-neutral-400); font-size:14px;">ℹ️</span>',
                    unsafe_allow_html=True)
```

---

## First-Run Onboarding

When the database is empty (first run), show a guided setup wizard:

```python
def check_first_run(db) -> bool:
    """Returns True if no runs have been executed yet."""
    return db.query(RunLog).count() == 0


def render_onboarding_wizard(config):
    """
    Step-by-step wizard for first-time setup.
    Guides the user through: config review → first run → understanding results.
    """
    st.markdown("""
    <div style="text-align:center; padding:40px 20px;">
        <div style="font-size:48px; margin-bottom:16px;">🚀</div>
        <h1 style="font-size:var(--text-xl); margin-bottom:8px;">Welcome to Fiverr Research System</h1>
        <p style="color:var(--color-neutral-500); max-width:500px; margin:0 auto;">
            Let's get your first analysis running. This wizard will guide you through setup.
        </p>
    </div>
    """, unsafe_allow_html=True)

    step = st.session_state.get("onboarding_step", 1)

    if step == 1:
        st.subheader("Step 1: Review Your Niches")
        st.markdown("These are the niches configured for research:")
        for niche in config.get("niches", []):
            st.markdown(f"- **{niche['name']}** ({niche['depth']}) — "
                       f"${niche.get('starter_price_basic', 'N/A')}/"
                       f"${niche.get('starter_price_standard', 'N/A')}/"
                       f"${niche.get('starter_price_premium', 'N/A')}")

        if st.button("Niches look good → Next"):
            st.session_state["onboarding_step"] = 2
            st.rerun()

    elif step == 2:
        st.subheader("Step 2: Start Your First Run")
        st.markdown("Click below to start a full analysis. This will take 3-6 hours "
                    "and cost approximately $2-5 in LLM fees.")
        st.markdown("The system will: collect Fiverr data → analyze competitors → "
                    "score keywords → generate recommendations → export reports.")

        if st.button("▶️ Start First Full Run"):
            trigger_run("full")
            st.session_state["onboarding_step"] = 3
            st.rerun()

    elif step == 3:
        st.subheader("Step 3: Run In Progress")
        st.markdown("Your first analysis is running. You can close this browser — "
                    "the run continues in the background.")
        st.markdown("Come back in a few hours to see your results.")
        st.progress(get_run_progress())

        if is_run_complete():
            st.session_state["onboarding_step"] = 4
            st.rerun()

    elif step == 4:
        st.subheader("🎉 First Run Complete!")
        st.markdown("Your data is ready. Here's what to look at first:")
        st.markdown("1. **Opportunities page** — see your highest-scoring keywords")
        st.markdown("2. **Recommendations page** — get gig-ready content for top keywords")
        st.markdown("3. **Discovery page** — see what the AI found beyond your seed list")

        if st.button("Let's Go →"):
            st.session_state["onboarding_complete"] = True
            st.rerun()
```

---

## Session State Management

```python
# All UI state lives in st.session_state

SESSION_STATE_KEYS = {
    # Navigation
    "current_page": str,
    "nav_target_page": str | None,
    "nav_target_entity_id": int | None,
    "nav_target_entity_type": str | None,

    # Filters (persist across page switches)
    "opp_niche_filter": str,
    "opp_tag_filter": list,
    "opp_sort": str,
    "kw_search": str,
    "kw_niche": str,
    "comp_niche": str,
    "rec_niche": str,
    "rec_tag": list,

    # Comparison mode
    "compare_keywords": list[int],

    # Bulk selection
    "selected_ids": list[int],

    # Onboarding
    "onboarding_step": int,
    "onboarding_complete": bool,

    # Theme
    "dark_mode": bool,

    # Help
    "show_tooltips": bool,
}


def initialize_session_state():
    """Sets defaults for all session state keys."""
    defaults = {
        "current_page": "Opportunities",
        "compare_keywords": [],
        "selected_ids": [],
        "onboarding_step": 1,
        "onboarding_complete": False,
        "dark_mode": False,
        "show_tooltips": True,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default
```
