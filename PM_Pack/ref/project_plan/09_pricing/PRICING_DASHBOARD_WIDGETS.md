# Pricing Dashboard Widgets
# Fiverr Research System — Wave 9

**Document Status:** Complete
**Wave:** 9 — Pricing Strategy Engine
**Purpose:** All new dashboard widgets for pricing analysis — price distribution histograms, pricing strategy cards, price heatmap, revenue projections, and integration into existing pages.

---

## Widget Integration Map

| Existing Page | New Widget(s) | Location |
|---|---|---|
| Page 1 — Opportunities | Price distribution mini-chart on opportunity cards | Inside W1.3 card |
| Page 2 — Keywords | Price summary column in keyword table | New column in W2.2 |
| Page 4 — Recommendations | Pricing Strategy tab in recommendation cards | New tab in W4.2 |
| Page 5 — Run History | Revenue projection at entry pricing | Inside W5.3 |
| NEW Section | Price Heatmap (cross-keyword price comparison) | New widget on Page 2 |

---

## W-PRICE-1 — Price Distribution Histogram (Page 1 Keyword Detail + Page 2)

When a user clicks into keyword detail, show the price distribution:

```python
def render_price_distribution_chart(keyword_id: int, db):
    """
    Plotly histogram showing competitor price distribution at Basic tier.
    Overlaid with the recommended entry price as a vertical line.
    """
    price_data = db.query(PriceAnalysis).filter(
        PriceAnalysis.keyword_id == keyword_id,
    ).first()

    if not price_data or not price_data.basic_n:
        st.caption("No pricing data available for this keyword")
        return

    # Get raw prices for histogram
    gigs = get_gigs_for_keyword(keyword_id, db)
    basic_prices = extract_tier_prices(gigs, "basic")

    if not basic_prices:
        return

    fig = go.Figure()

    # Histogram of competitor prices
    fig.add_trace(go.Histogram(
        x=basic_prices,
        nbinsx=min(20, len(basic_prices)),
        name="Competitor Prices",
        marker_color="rgba(99, 110, 250, 0.6)",
        hovertemplate="$%{x}<br>%{y} sellers<extra></extra>",
    ))

    # Market median line
    fig.add_vline(
        x=price_data.basic_median,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Median ${price_data.basic_median:.0f}",
        annotation_position="top",
    )

    # Recommended entry price (if available)
    rec = db.query(Recommendation).filter(
        Recommendation.keyword_id == keyword_id,
    ).first()
    if rec and rec.pricing_strategy:
        entry_price = rec.pricing_strategy.get("entry_prices", {}).get("basic")
        if entry_price:
            fig.add_vline(
                x=entry_price,
                line_dash="solid",
                line_color="#10b981",
                line_width=3,
                annotation_text=f"Your Entry ${entry_price}",
                annotation_position="top right",
            )

    # Price gaps (shaded regions)
    if price_data.basic_gaps:
        for gap in price_data.basic_gaps[:2]:
            fig.add_vrect(
                x0=gap["gap_start"],
                x1=gap["gap_end"],
                fillcolor="rgba(255, 193, 7, 0.15)",
                line_width=0,
                annotation_text="Gap",
                annotation_position="top",
            )

    fig.update_layout(
        title=f"Basic Price Distribution ({price_data.basic_n} sellers)",
        xaxis_title="Price ($)",
        yaxis_title="Number of Sellers",
        showlegend=False,
        height=300,
        margin=dict(t=40, b=40, l=40, r=20),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Stats row below chart
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Median", f"${price_data.basic_median:.0f}")
    col2.metric("Range", f"${price_data.basic_p10:.0f}–${price_data.basic_p90:.0f}")
    col3.metric("Moat", price_data.moat_strength or "—")
    col4.metric("Market", price_data.market_type or "—")
```

---

## W-PRICE-2 — Opportunity Card Price Mini-Chart (Page 1)

Added to the existing opportunity card layout from Wave 8:

```python
def render_opportunity_card_with_pricing(ranking, db):
    """Enhanced opportunity card with price position indicator."""

    # ... existing card content (tag badge, score, D/C/O/F bars) ...

    # NEW: Price position indicator
    price_data = db.query(PriceAnalysis).filter(
        PriceAnalysis.keyword_id == ranking.keyword_id,
    ).first()

    if price_data and price_data.basic_median:
        rec = db.query(Recommendation).filter(
            Recommendation.keyword_id == ranking.keyword_id,
        ).first()
        entry_price = None
        if rec and rec.pricing_strategy:
            entry_price = rec.pricing_strategy.get("entry_prices", {}).get("basic")

        price_text = f"💰 Median: ${price_data.basic_median:.0f}"
        if entry_price:
            price_text += f" → Entry: ${entry_price:.0f}"
        st.caption(price_text)
```

---

## W-PRICE-3 — Pricing Strategy Tab (Page 4 Recommendations)

New tab added to each recommendation card:

```python
# Inside the recommendation card's st.tabs(), add "Pricing" tab:

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Titles", "Packages", "Description", "Differentiation",
    "FAQ & Persona", "Risks", "💰 Pricing"  # NEW TAB
])

# ... existing tabs 1-6 unchanged ...

with tab7:
    if rec.pricing_strategy:
        ps = rec.pricing_strategy

        # Entry prices header
        st.markdown("### Entry Pricing (0 Reviews)")
        col1, col2, col3 = st.columns(3)
        lead = ps.get("entry_prices", {}).get("lead_tier", "basic")
        for i, (tier, col) in enumerate(zip(["basic", "standard", "premium"],
                                             [col1, col2, col3])):
            price = ps.get("entry_prices", {}).get(tier, 0)
            label = tier.title()
            if tier == lead:
                label += " ⭐ LEAD"
            col.metric(label, f"${price}")

        # Lead tier explanation
        lead_reason = ps.get("entry_prices", {}).get("lead_tier_reasoning", "")
        if lead_reason:
            st.caption(f"Lead with {lead.title()}: {lead_reason}")

        # Acquisition pricing
        st.markdown("### First 5 Orders (Acquisition Pricing)")
        acq = ps.get("acquisition_prices", {})
        col1, col2, col3 = st.columns(3)
        col1.metric("Basic", f"${acq.get('basic', 0)}")
        col2.metric("Standard", f"${acq.get('standard', 0)}")
        col3.metric("Premium", f"${acq.get('premium', 0)}")
        st.caption(f"Period: {acq.get('acquisition_period', 'First 5 orders')}")

        # Price ladder chart
        st.markdown("### Price Ladder")
        ladder = ps.get("price_ladder", [])
        if ladder:
            fig = go.Figure()
            milestones = [str(step["milestone_reviews"]) for step in ladder]
            for tier in ["basic", "standard", "premium"]:
                fig.add_trace(go.Scatter(
                    x=milestones,
                    y=[step[tier] for step in ladder],
                    name=tier.title(),
                    mode="lines+markers",
                ))
            fig.update_layout(
                xaxis_title="Reviews",
                yaxis_title="Price ($)",
                height=300,
                margin=dict(t=10, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)

        # Strategy narrative
        narrative = ps.get("strategy_narrative", "")
        if narrative:
            st.markdown("### Strategy")
            st.markdown(narrative)

        # Recommended extras
        extras = ps.get("recommended_extras", [])
        if extras:
            st.markdown("### Recommended Extras (Upsells)")
            for extra in extras:
                st.markdown(f"→ **{extra['name']}** — ${extra['price']} — _{extra['rationale']}_")

        # Pricing risks
        risks = ps.get("pricing_risks", [])
        if risks:
            st.markdown("### Pricing Risks")
            for risk in risks:
                sev_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(
                    risk["severity"], "⚪"
                )
                st.markdown(f"{sev_icon} **{risk['risk']}**")
                st.caption(f"Mitigation: {risk['mitigation']}")

        # Projected AOV
        aov = ps.get("projected_aov", {})
        if aov:
            st.markdown("### Projected AOV Growth")
            col1, col2, col3 = st.columns(3)
            col1.metric("At Entry", f"${aov.get('at_entry', 0):.0f}")
            col2.metric("At 50 Reviews", f"${aov.get('at_50_reviews', 0):.0f}")
            col3.metric("Growth", f"+{aov.get('aov_growth_pct', 0):.0f}%")

    else:
        st.info("No pricing strategy generated for this keyword. "
                "Run `--mode recommendations-only` to generate.")
```

---

## W-PRICE-4 — Price Heatmap (Page 2 — Keywords)

Cross-keyword price comparison for a niche:

```python
def render_price_heatmap(niche_id: str, db):
    """
    Heatmap showing price positions across keywords in a niche.
    X-axis: price tiers (Basic, Standard, Premium)
    Y-axis: keywords (sorted by final score)
    Color: price relative to niche median (green=below, yellow=at, red=above)
    """
    keywords = get_scored_keywords_for_niche(niche_id, db, limit=20)
    niche_prices = db.query(NichePriceAnalysis).filter(
        NichePriceAnalysis.niche_id == niche_id,
    ).first()

    if not niche_prices:
        st.caption("No niche price data available")
        return

    data = []
    for kw in keywords:
        pa = db.query(PriceAnalysis).filter(
            PriceAnalysis.keyword_id == kw.id,
        ).first()
        if pa:
            data.append({
                "Keyword": kw.keyword_text[:30],
                "Basic": pa.basic_median,
                "Standard": pa.standard_median,
                "Premium": pa.premium_median,
            })

    if not data:
        return

    df = pd.DataFrame(data).set_index("Keyword")

    # Normalize to niche medians for color coding
    norms = {
        "Basic": niche_prices.basic_median or 1,
        "Standard": niche_prices.standard_median or 1,
        "Premium": niche_prices.premium_median or 1,
    }
    df_normalized = df.copy()
    for col in ["Basic", "Standard", "Premium"]:
        df_normalized[col] = df[col] / norms[col]

    fig = px.imshow(
        df_normalized.values,
        labels=dict(x="Tier", y="Keyword", color="vs Median"),
        x=["Basic", "Standard", "Premium"],
        y=df_normalized.index.tolist(),
        color_continuous_scale="RdYlGn_r",
        zmin=0.5, zmax=1.5,
        aspect="auto",
        text_auto=False,
    )

    # Add actual price values as text annotations
    for i, keyword in enumerate(df.index):
        for j, tier in enumerate(["Basic", "Standard", "Premium"]):
            val = df.loc[keyword, tier]
            if val and not np.isnan(val):
                fig.add_annotation(
                    x=j, y=i,
                    text=f"${val:.0f}",
                    showarrow=False,
                    font=dict(size=10, color="black"),
                )

    fig.update_layout(
        title=f"Price Position Heatmap — {get_niche_name(niche_id)}",
        height=max(300, len(data) * 30),
        margin=dict(l=200),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Niche pricing summary
    st.markdown(f"**Niche Medians:** Basic ${niche_prices.basic_median:.0f} | "
                f"Standard ${niche_prices.standard_median:.0f} | "
                f"Premium ${niche_prices.premium_median:.0f}")
    st.markdown(f"**Review Moat:** {niche_prices.moat_strength or '—'} | "
                f"**Price-Review Correlation:** {niche_prices.avg_price_review_correlation or '—'}")
```

---

## W-PRICE-5 — Revenue Projection at Entry Pricing (Page 5)

Enhanced Revenue Gate Tracker with entry pricing integration:

```python
def render_revenue_projection_with_pricing(db):
    """
    Shows how many orders are needed at RECOMMENDED ENTRY PRICES
    (not at niche config prices) to hit each revenue gate.
    """
    st.markdown("### Revenue Projection at Entry Pricing")

    # Get all pricing strategies
    recs_with_pricing = db.query(Recommendation).filter(
        Recommendation.pricing_strategy.isnot(None),
    ).all()

    if not recs_with_pricing:
        st.info("No pricing strategies generated yet. Run recommendations first.")
        return

    # Calculate weighted average entry AOV across all recommended keywords
    total_aov = 0
    count = 0
    for rec in recs_with_pricing:
        ps = rec.pricing_strategy
        if ps and ps.get("projected_aov", {}).get("at_entry"):
            total_aov += ps["projected_aov"]["at_entry"]
            count += 1

    if count == 0:
        return

    avg_entry_aov = total_aov / count

    REVENUE_GATES = {4: 1720, 6: 4770, 9: 17795, 10: 25045, 12: 37500}

    projection_data = []
    for month, target in REVENUE_GATES.items():
        orders_needed = target / avg_entry_aov if avg_entry_aov > 0 else 0
        orders_per_month = orders_needed / month
        orders_per_week = orders_per_month / 4.33
        feasible = orders_per_week <= 10

        projection_data.append({
            "Gate": f"Month {month}",
            "Target": f"${target:,.0f}",
            "Entry AOV": f"${avg_entry_aov:.0f}",
            "Orders Needed": f"{orders_needed:.0f}",
            "Per Month": f"{orders_per_month:.1f}",
            "Per Week": f"{orders_per_week:.1f}",
            "Feasible": "✅" if feasible else "⚠️",
        })

    st.dataframe(pd.DataFrame(projection_data), use_container_width=True, hide_index=True)

    st.caption(f"Based on average entry AOV of ${avg_entry_aov:.0f} across "
               f"{count} recommended keywords")
```

---

## W-PRICE-6 — Pricing Column in Keyword Table (Page 2)

Add pricing columns to the keyword table:

```python
# Updated keyword table DataFrame construction (W2.2):

df = pd.DataFrame([{
    "Keyword": kw.keyword_text,
    "Niche": get_niche_name(kw.niche_id),
    "Score": get_final_score(kw.id, db) or "—",
    "Tag": get_tag(kw.id, db) or "—",
    # ... existing columns ...
    # NEW pricing columns:
    "Basic $": get_basic_median(kw.id, db) or "—",
    "Entry $": get_entry_price(kw.id, db) or "—",
    "Moat": get_moat_strength(kw.id, db) or "—",
} for kw in keywords])
```

---

## Export Format Updates

### CSV — keywords.csv (new columns)

| New Column | Source | Format |
|---|---|---|
| basic_median | price_analysis.basic_median | float, 0 decimal |
| standard_median | price_analysis.standard_median | float, 0 decimal |
| premium_median | price_analysis.premium_median | float, 0 decimal |
| entry_basic | pricing_strategy.entry_prices.basic | integer |
| entry_standard | pricing_strategy.entry_prices.standard | integer |
| entry_premium | pricing_strategy.entry_prices.premium | integer |
| moat_strength | price_analysis.moat_strength | string |
| market_type | price_analysis.market_type | string |

### Excel — New "Pricing" Sheet

| Column | Content |
|---|---|
| Keyword | keyword_text |
| Niche | niche_name |
| Tag | GO/PASS tag |
| Market Median (Basic) | basic_median |
| Market Median (Standard) | standard_median |
| Market Median (Premium) | premium_median |
| Entry Price (Basic) | from pricing_strategy |
| Entry Price (Standard) | from pricing_strategy |
| Entry Price (Premium) | from pricing_strategy |
| Undercut % | total discount percentage |
| Moat Strength | HIGH/MEDIUM/LOW |
| Lead Tier | basic or standard |
| Projected Entry AOV | at_entry AOV |
| Price Ladder (5 reviews) | basic price at 5 reviews |
| Price Ladder (25 reviews) | basic price at 25 reviews |
| Price Ladder (100 reviews) | basic price at 100 reviews |

Conditional formatting: Entry prices colored green (below median), yellow (at median), red (above median).

### Markdown — recommendations.md (new section)

```markdown
### 💰 Pricing Strategy
Entry: Basic $65 / Standard $145 / Premium $280 (30% below median)
Lead with: Basic (acquisition tier)
First 5 Orders: $55 / $130 / $265

Price Ladder:
| Reviews | Basic | Standard | Premium |
|---|---|---|---|
| 0 | $65 | $145 | $280 |
| 5 | $75 | $160 | $305 |
| 25 | $90 | $183 | $345 |
| 100 | $100 | $200 | $375 |

Extras: Express delivery (+$50), Architecture diagram (+$75)
```
