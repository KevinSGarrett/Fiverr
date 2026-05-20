# Design System
# Fiverr Research System — Wave 12

**Document Status:** Complete
**Wave:** 12 — Dashboard UX Overhaul
**Purpose:** Complete visual design system — color palette, typography, spacing, component library, dark mode, loading states, empty states, and Streamlit CSS injection.

---

## Design Philosophy

The dashboard is used daily by one person making high-stakes decisions about which gigs to create. It needs to be:

1. **Scannable** — Key metrics visible at a glance without scrolling
2. **Decision-oriented** — Every view answers a specific question
3. **Data-dense without clutter** — Show more data, less chrome
4. **Consistent** — Same patterns everywhere, no surprises
5. **Fast-feeling** — Loading states prevent dead screens, progressive rendering

---

## Color Palette

### Core Colors

```css
:root {
    /* Primary — used for navigation, key actions, links */
    --color-primary-50:  #eff6ff;
    --color-primary-100: #dbeafe;
    --color-primary-200: #bfdbfe;
    --color-primary-500: #3b82f6;
    --color-primary-600: #2563eb;
    --color-primary-700: #1d4ed8;

    /* Neutral — text, borders, backgrounds */
    --color-neutral-50:  #f9fafb;
    --color-neutral-100: #f3f4f6;
    --color-neutral-200: #e5e7eb;
    --color-neutral-300: #d1d5db;
    --color-neutral-400: #9ca3af;
    --color-neutral-500: #6b7280;
    --color-neutral-600: #4b5563;
    --color-neutral-700: #374151;
    --color-neutral-800: #1f2937;
    --color-neutral-900: #111827;

    /* Surface — cards, panels, containers */
    --color-surface:        #ffffff;
    --color-surface-raised: #ffffff;
    --color-surface-sunken: #f9fafb;
    --color-border:         #e5e7eb;
    --color-border-strong:  #d1d5db;
}
```

### Semantic Colors

```css
:root {
    /* Tag colors — the GO/PASS system */
    --color-strong-go:      #f59e0b; /* Amber/Gold */
    --color-strong-go-bg:   #fef3c7;
    --color-conditional-go: #6b7280; /* Silver/Gray */
    --color-conditional-go-bg: #f3f4f6;
    --color-monitor:        #3b82f6; /* Blue */
    --color-monitor-bg:     #dbeafe;
    --color-caution:        #ef4444; /* Red */
    --color-caution-bg:     #fee2e2;
    --color-pass:           #9ca3af; /* Muted gray */
    --color-pass-bg:        #f3f4f6;

    /* Status colors */
    --color-success:     #10b981;
    --color-success-bg:  #d1fae5;
    --color-warning:     #f59e0b;
    --color-warning-bg:  #fef3c7;
    --color-error:       #ef4444;
    --color-error-bg:    #fee2e2;
    --color-info:        #3b82f6;
    --color-info-bg:     #dbeafe;

    /* Discovery */
    --color-gold:        #d97706;
    --color-gold-bg:     #fef3c7;

    /* Score gradient (0-100) */
    --color-score-low:    #ef4444;  /* 0-30 */
    --color-score-mid:    #f59e0b;  /* 30-60 */
    --color-score-high:   #10b981;  /* 60-80 */
    --color-score-top:    #059669;  /* 80-100 */
}
```

### Dark Mode Colors

```css
[data-theme="dark"] {
    --color-surface:        #1f2937;
    --color-surface-raised: #374151;
    --color-surface-sunken: #111827;
    --color-border:         #374151;
    --color-border-strong:  #4b5563;
    --color-neutral-900:    #f9fafb;
    --color-neutral-800:    #f3f4f6;
    --color-neutral-700:    #e5e7eb;
    --color-neutral-500:    #9ca3af;
    --color-neutral-400:    #6b7280;
    --color-neutral-100:    #1f2937;
    --color-neutral-50:     #111827;
}
```

---

## Typography

```css
:root {
    /* Font family */
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;

    /* Font sizes — modular scale (1.200 ratio) */
    --text-xs:   0.694rem;  /* 11.1px — captions, metadata */
    --text-sm:   0.833rem;  /* 13.3px — secondary text, labels */
    --text-base: 1rem;      /* 16px — body text */
    --text-md:   1.2rem;    /* 19.2px — subheadings */
    --text-lg:   1.44rem;   /* 23px — section headings */
    --text-xl:   1.728rem;  /* 27.6px — page titles */
    --text-2xl:  2.074rem;  /* 33.2px — hero numbers (KPI values) */

    /* Font weights */
    --font-normal:   400;
    --font-medium:   500;
    --font-semibold: 600;
    --font-bold:     700;

    /* Line heights */
    --leading-tight:  1.25;
    --leading-normal: 1.5;
    --leading-loose:  1.75;
}
```

### Typography Usage Rules

| Element | Size | Weight | Color |
|---|---|---|---|
| Page title | --text-xl | --font-bold | --color-neutral-900 |
| Section heading | --text-lg | --font-semibold | --color-neutral-800 |
| Card heading | --text-md | --font-semibold | --color-neutral-800 |
| Body text | --text-base | --font-normal | --color-neutral-700 |
| Label / caption | --text-sm | --font-medium | --color-neutral-500 |
| Metadata | --text-xs | --font-normal | --color-neutral-400 |
| KPI large number | --text-2xl | --font-bold | --color-neutral-900 |
| KPI label | --text-xs | --font-medium | --color-neutral-500 |
| Code / technical | --text-sm | --font-normal (mono) | --color-neutral-700 |

---

## Spacing System

4px base grid. All spacing uses multiples of 4px:

```css
:root {
    --space-1:  4px;
    --space-2:  8px;
    --space-3:  12px;
    --space-4:  16px;
    --space-5:  20px;
    --space-6:  24px;
    --space-8:  32px;
    --space-10: 40px;
    --space-12: 48px;
    --space-16: 64px;

    /* Component-specific spacing */
    --card-padding:     var(--space-5);    /* 20px */
    --card-gap:         var(--space-4);    /* 16px between cards */
    --section-gap:      var(--space-8);    /* 32px between sections */
    --page-padding:     var(--space-6);    /* 24px page edges */
    --metric-gap:       var(--space-3);    /* 12px between metric boxes */
}
```

---

## Border and Shadow System

```css
:root {
    /* Border radius */
    --radius-sm:  4px;   /* Small elements (badges, chips) */
    --radius-md:  8px;   /* Cards, inputs */
    --radius-lg:  12px;  /* Large cards, modals */
    --radius-xl:  16px;  /* Feature panels */
    --radius-full: 9999px; /* Pills, avatars */

    /* Shadows */
    --shadow-sm:  0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md:  0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
    --shadow-lg:  0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
    --shadow-card: var(--shadow-sm);
    --shadow-card-hover: var(--shadow-md);
}
```

---

## Component Library

### C1 — ScoreCard

Reusable score display with mini-bar, label, and value:

```python
def score_card(label: str, value: float, max_val: float = 100, size: str = "md"):
    """
    Renders a score card with colored progress bar.
    size: "sm" (inline in tables), "md" (cards), "lg" (detail views)
    """
    pct = min(100, max(0, value / max_val * 100))
    color = _score_color(value)

    if size == "sm":
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:var(--text-xs); color:var(--color-neutral-500); width:50px;">{label}</span>
            <div style="flex:1; height:6px; background:var(--color-neutral-100); border-radius:3px; overflow:hidden;">
                <div style="width:{pct}%; height:100%; background:{color}; border-radius:3px;"></div>
            </div>
            <span style="font-size:var(--text-sm); font-weight:600; width:30px; text-align:right;">{value:.0f}</span>
        </div>
        """, unsafe_allow_html=True)
    elif size == "md":
        st.markdown(f"""
        <div style="padding:12px; border:1px solid var(--color-border); border-radius:var(--radius-md); background:var(--color-surface);">
            <div style="font-size:var(--text-xs); color:var(--color-neutral-500); text-transform:uppercase; margin-bottom:4px;">{label}</div>
            <div style="font-size:var(--text-2xl); font-weight:700; color:{color};">{value:.1f}</div>
            <div style="height:4px; background:var(--color-neutral-100); border-radius:2px; margin-top:8px; overflow:hidden;">
                <div style="width:{pct}%; height:100%; background:{color}; border-radius:2px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _score_color(value: float) -> str:
    if value >= 80: return "var(--color-score-top)"
    elif value >= 60: return "var(--color-score-high)"
    elif value >= 40: return "var(--color-score-mid)"
    else: return "var(--color-score-low)"
```

### C2 — TagBadge

```python
def tag_badge(tag: str, size: str = "md"):
    """Color-coded GO/PASS badge."""
    styles = {
        "STRONG GO":      {"bg": "var(--color-strong-go-bg)", "fg": "var(--color-strong-go)", "icon": "⭐"},
        "CONDITIONAL GO": {"bg": "var(--color-conditional-go-bg)", "fg": "var(--color-conditional-go)", "icon": "◐"},
        "MONITOR":        {"bg": "var(--color-monitor-bg)", "fg": "var(--color-monitor)", "icon": "👁"},
        "CAUTION":        {"bg": "var(--color-caution-bg)", "fg": "var(--color-caution)", "icon": "⚠️"},
        "PASS":           {"bg": "var(--color-pass-bg)", "fg": "var(--color-pass)", "icon": "—"},
    }
    s = styles.get(tag, styles["PASS"])
    font_size = "11px" if size == "sm" else "13px"
    padding = "2px 8px" if size == "sm" else "4px 12px"

    st.markdown(f"""
    <span style="display:inline-block; padding:{padding}; border-radius:var(--radius-full);
                 background:{s['bg']}; color:{s['fg']}; font-size:{font_size};
                 font-weight:600; letter-spacing:0.02em;">
        {s['icon']} {tag}
    </span>
    """, unsafe_allow_html=True)
```

### C3 — AlertBanner

```python
def alert_banner(message: str, severity: str, dismissible: bool = True, key: str = ""):
    """Severity-colored dismissible banner."""
    colors = {
        "HIGH":   {"bg": "var(--color-error-bg)", "border": "var(--color-error)", "icon": "🚨"},
        "MEDIUM": {"bg": "var(--color-warning-bg)", "border": "var(--color-warning)", "icon": "⚡"},
        "LOW":    {"bg": "var(--color-info-bg)", "border": "var(--color-info)", "icon": "ℹ️"},
    }
    c = colors.get(severity, colors["LOW"])

    st.markdown(f"""
    <div style="padding:12px 16px; background:{c['bg']}; border-left:4px solid {c['border']};
                border-radius:0 var(--radius-md) var(--radius-md) 0; margin-bottom:12px;
                display:flex; align-items:center; gap:12px;">
        <span style="font-size:18px;">{c['icon']}</span>
        <span style="flex:1; font-size:var(--text-sm); color:var(--color-neutral-800);">{message}</span>
    </div>
    """, unsafe_allow_html=True)
```

### C4 — MetricBox

```python
def metric_box(label: str, value: str, delta: str = None, delta_color: str = None):
    """Single KPI display with optional trend delta."""
    delta_html = ""
    if delta:
        arrow = "↑" if not delta.startswith("-") else "↓"
        color = delta_color or ("var(--color-success)" if arrow == "↑" else "var(--color-error)")
        delta_html = f'<div style="font-size:var(--text-xs); color:{color}; margin-top:2px;">{arrow} {delta}</div>'

    st.markdown(f"""
    <div style="padding:16px; border:1px solid var(--color-border); border-radius:var(--radius-md);
                background:var(--color-surface); text-align:center; min-width:100px;">
        <div style="font-size:var(--text-2xl); font-weight:700; color:var(--color-neutral-900);">{value}</div>
        <div style="font-size:var(--text-xs); color:var(--color-neutral-500); text-transform:uppercase;
                    letter-spacing:0.05em; margin-top:4px;">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)
```

### C5 — DataTable (Enhanced)

```python
def styled_dataframe(df, key: str, height: int = 400,
                     highlight_column: str = None, tag_column: str = None):
    """
    Enhanced dataframe with consistent styling.
    highlight_column: apply score color gradient
    tag_column: render as TagBadge
    """
    # Apply column formatting
    styled = df.style

    if highlight_column and highlight_column in df.columns:
        styled = styled.background_gradient(
            subset=[highlight_column],
            cmap="RdYlGn",
            vmin=0, vmax=100,
        )

    st.dataframe(
        styled,
        use_container_width=True,
        height=height,
        hide_index=True,
        column_config={
            tag_column: st.column_config.TextColumn(width="small") if tag_column else None,
        },
    )
```

### C6 — ChartContainer

```python
def chart_container(title: str, subtitle: str = None, help_text: str = None):
    """
    Consistent chart wrapper. Use as context manager.
    """
    header_html = f'<div style="font-size:var(--text-md); font-weight:600; color:var(--color-neutral-800);">{title}</div>'
    if subtitle:
        header_html += f'<div style="font-size:var(--text-xs); color:var(--color-neutral-400); margin-top:2px;">{subtitle}</div>'

    st.markdown(header_html, unsafe_allow_html=True)
    if help_text:
        st.caption(f"ℹ️ {help_text}")
    # Caller renders chart after this


def chart_config():
    """Standard Plotly layout config applied to all charts."""
    return dict(
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=40, l=50, r=20),
        xaxis=dict(gridcolor="#f3f4f6", zeroline=False),
        yaxis=dict(gridcolor="#f3f4f6", zeroline=False),
        colorway=["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
                   "#06b6d4", "#f97316", "#ec4899"],
    )
```

### C7 — RecommendationCard (Complete Component)

```python
def recommendation_card(rec, db):
    """
    Full recommendation card as a reusable component.
    Includes tag badge, score, tabs for all 14 fields, export buttons.
    """
    st.markdown(f"""
    <div style="border:1px solid var(--color-border); border-radius:var(--radius-lg);
                padding:0; overflow:hidden; margin-bottom:16px;">
        <div style="padding:16px 20px; background:var(--color-surface-sunken);
                    border-bottom:1px solid var(--color-border);
                    display:flex; align-items:center; justify-content:space-between;">
            <div style="display:flex; align-items:center; gap:12px;">
                <!-- Tag + Title -->
            </div>
            <div style="font-size:var(--text-2xl); font-weight:700;">
                {rec.final_score:.1f}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    # Tabs rendered below via st.tabs()
```

### C8 — FilterBar

```python
def filter_bar(filters: list[dict], key_prefix: str):
    """
    Consistent filter row used across all pages.
    filters: [{"label": "Niche", "type": "select", "options": [...], "key": "niche"}]
    """
    cols = st.columns(len(filters))
    values = {}
    for i, f in enumerate(filters):
        with cols[i]:
            if f["type"] == "select":
                values[f["key"]] = st.selectbox(f["label"], f["options"],
                                                  key=f"{key_prefix}_{f['key']}")
            elif f["type"] == "multiselect":
                values[f["key"]] = st.multiselect(f["label"], f["options"],
                                                    default=f.get("default", []),
                                                    key=f"{key_prefix}_{f['key']}")
            elif f["type"] == "search":
                values[f["key"]] = st.text_input(f["label"], key=f"{key_prefix}_{f['key']}")
    return values
```

---

## Streamlit CSS Injection

All custom styles injected via `st.markdown` at app load:

```python
# src/dashboard/styles.py

def inject_custom_css():
    """Injects the complete design system CSS into Streamlit."""
    st.markdown(f"""
    <style>
        /* Import Inter font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Global overrides */
        .stApp {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            background: var(--color-neutral-50);
            border-right: 1px solid var(--color-border);
        }}

        [data-testid="stSidebar"] .stRadio label {{
            padding: 8px 16px;
            border-radius: var(--radius-md);
            transition: background 0.15s;
        }}

        [data-testid="stSidebar"] .stRadio label:hover {{
            background: var(--color-neutral-100);
        }}

        /* Card containers */
        [data-testid="stHorizontalBlock"] > div {{
            border-radius: var(--radius-md);
        }}

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 4px;
            border-bottom: 1px solid var(--color-border);
        }}

        .stTabs [data-baseweb="tab"] {{
            padding: 8px 16px;
            border-radius: var(--radius-md) var(--radius-md) 0 0;
            font-size: var(--text-sm);
            font-weight: 500;
        }}

        /* Metric styling */
        [data-testid="stMetric"] {{
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            padding: 16px;
        }}

        [data-testid="stMetricValue"] {{
            font-size: var(--text-2xl);
            font-weight: 700;
        }}

        [data-testid="stMetricLabel"] {{
            font-size: var(--text-xs);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--color-neutral-500);
        }}

        /* Expander styling */
        .streamlit-expanderHeader {{
            font-size: var(--text-base);
            font-weight: 600;
            color: var(--color-neutral-800);
        }}

        /* DataFrame styling */
        [data-testid="stDataFrame"] {{
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            overflow: hidden;
        }}

        /* Button styling */
        .stButton > button {{
            border-radius: var(--radius-md);
            font-weight: 500;
            font-size: var(--text-sm);
            transition: all 0.15s;
        }}

        .stButton > button:hover {{
            box-shadow: var(--shadow-md);
        }}

        /* Download button */
        .stDownloadButton > button {{
            border-radius: var(--radius-md);
            font-weight: 500;
        }}

        /* Toast notifications */
        [data-testid="stToast"] {{
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
        }}

        /* Hide Streamlit default elements */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        header {{ visibility: hidden; }}
    </style>

    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
    """, unsafe_allow_html=True)
```

---

## Loading States

```python
def skeleton_card(count: int = 3):
    """Renders placeholder skeleton cards while data loads."""
    for _ in range(count):
        st.markdown("""
        <div style="border:1px solid var(--color-border); border-radius:var(--radius-lg);
                    padding:20px; margin-bottom:12px; animation:pulse 1.5s infinite;">
            <div style="height:16px; background:var(--color-neutral-100); border-radius:4px;
                        width:60%; margin-bottom:12px;"></div>
            <div style="height:12px; background:var(--color-neutral-100); border-radius:4px;
                        width:40%; margin-bottom:8px;"></div>
            <div style="height:8px; background:var(--color-neutral-100); border-radius:4px;
                        width:80%;"></div>
        </div>
        """, unsafe_allow_html=True)


def loading_spinner(message: str = "Loading..."):
    """Consistent loading indicator."""
    with st.spinner(message):
        pass  # Caller uses this as context manager
```

---

## Empty States

```python
EMPTY_STATES = {
    "no_data": {
        "icon": "📊",
        "title": "No data yet",
        "message": "Run your first full analysis to populate this view.",
        "action": "Run `python run.py --mode full` to get started.",
    },
    "no_recommendations": {
        "icon": "📝",
        "title": "No recommendations generated",
        "message": "Recommendations are generated for STRONG GO and CONDITIONAL GO keywords.",
        "action": "Score keywords first, then run `--mode recommendations-only`.",
    },
    "no_discoveries": {
        "icon": "🔬",
        "title": "Discovery engine warming up",
        "message": "The discovery engine learns from scored data. After 2-3 full runs, it starts generating hypotheses.",
        "action": "Keep running full analyses — discovery activates automatically.",
    },
    "no_competitors": {
        "icon": "👥",
        "title": "No competitor data",
        "message": "Select a niche to see competitive intelligence.",
        "action": None,
    },
    "filter_empty": {
        "icon": "🔍",
        "title": "No results match your filters",
        "message": "Try broadening your filter criteria.",
        "action": None,
    },
}


def empty_state(state_key: str):
    """Renders a centered empty state message."""
    state = EMPTY_STATES.get(state_key, EMPTY_STATES["no_data"])
    st.markdown(f"""
    <div style="text-align:center; padding:48px 24px; color:var(--color-neutral-400);">
        <div style="font-size:48px; margin-bottom:16px;">{state['icon']}</div>
        <div style="font-size:var(--text-lg); font-weight:600; color:var(--color-neutral-600);
                    margin-bottom:8px;">{state['title']}</div>
        <div style="font-size:var(--text-sm); max-width:400px; margin:0 auto;">{state['message']}</div>
        {"<div style='margin-top:16px; font-size:var(--text-xs); font-family:monospace; color:var(--color-neutral-400);'>" + state['action'] + "</div>" if state.get('action') else ""}
    </div>
    """, unsafe_allow_html=True)
```

---

## Dark Mode Toggle

```python
def render_theme_toggle():
    """Sidebar toggle for dark/light mode."""
    theme = st.sidebar.toggle("🌙 Dark Mode", value=False, key="dark_mode")

    if theme:
        st.markdown("""
        <style>
            .stApp { background-color: #111827; color: #f9fafb; }
            [data-testid="stSidebar"] { background: #1f2937; border-color: #374151; }
            [data-testid="stMetric"] { background: #1f2937; border-color: #374151; }
            /* ... additional dark overrides ... */
        </style>
        """, unsafe_allow_html=True)

    return theme
```
