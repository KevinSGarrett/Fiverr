# Seller Setup Playbook
# Fiverr Research System — Wave 11

**Document Status:** Complete
**Wave:** 11 — Gig Creation Playbook
**Purpose:** End-to-end new seller onboarding guide generated per niche — account setup, gig creation walkthrough, first 5 orders strategy, review acquisition, buyer request strategy, and promotion tactics. Exportable as PDF playbook.

---

## Playbook Architecture

The Seller Setup Playbook is a **generated document** — not static. It's assembled from:
1. Profile optimization data (this wave)
2. Recommendation data (Wave 7)
3. Pricing strategy data (Wave 9)
4. Visual recommendations (this wave)
5. Competitor intelligence (Wave 5)
6. Niche configuration (Wave 1)

Each niche gets its own playbook. The playbook is regenerated when underlying data changes.

---

## Playbook Sections

### Section 1 — Account Setup Checklist

```python
def build_account_setup_section(
    niche_id: str,
    profile_optimization: dict,
    profile_patterns: dict,
) -> dict:
    """Section 1: Everything to do before creating your first gig."""
    return {
        "section": "Account Setup",
        "estimated_time": "2-3 hours",
        "steps": [
            {
                "step": 1,
                "title": "Profile Photo",
                "action": profile_optimization["avatar_recommendation"]["guidance"],
                "priority": "CRITICAL",
                "detail": (
                    f"In {get_niche_name(niche_id)}, "
                    f"{profile_patterns['elements']['avatar']['top_headshot_pct']}% of top sellers "
                    "use professional headshots. This is the first thing buyers see."
                ),
                "time": "10 minutes",
            },
            {
                "step": 2,
                "title": "Professional Bio",
                "action": "Write your profile description using the bio template",
                "priority": "CRITICAL",
                "detail": profile_optimization["bio_template"],
                "time": "30 minutes",
            },
            {
                "step": 3,
                "title": "Skills Tags",
                "action": f"Add these skills to your profile: {', '.join(_get_recommended_skills(niche_id))}",
                "priority": "HIGH",
                "time": "5 minutes",
            },
            {
                "step": 4,
                "title": "Portfolio Items",
                "action": "Create and upload portfolio samples",
                "priority": "HIGH",
                "detail": profile_optimization["portfolio_recommendations"],
                "time": "1-2 hours",
            },
            {
                "step": 5,
                "title": "Skill Tests",
                "action": f"Take these Fiverr skill tests: {', '.join(profile_optimization.get('skill_tests_to_take', ['Python 3']))}",
                "priority": "MEDIUM",
                "time": "1-2 hours",
            },
            {
                "step": 6,
                "title": "Response Time Setup",
                "action": "Enable push notifications on mobile + desktop",
                "priority": "HIGH",
                "detail": profile_optimization.get("response_strategy", "Respond within 1 hour during business hours"),
                "time": "5 minutes",
            },
            {
                "step": 7,
                "title": "Languages",
                "action": "Add all languages you speak with accurate proficiency levels",
                "priority": "LOW",
                "time": "5 minutes",
            },
        ],
    }
```

---

### Section 2 — Gig Creation Walkthrough

```python
def build_gig_creation_section(
    recommendation: dict,
    pricing_strategy: dict,
    visual_recommendations: dict,
) -> dict:
    """Section 2: Step-by-step gig creation using recommendation data."""
    return {
        "section": "Gig Creation",
        "estimated_time": "1-2 hours",
        "prerequisite": "Complete Account Setup first",
        "steps": [
            {
                "step": 1,
                "title": "Choose Your Gig Title",
                "action": "Select from these recommended titles:",
                "options": recommendation.get("gig_titles", []),
                "guidance": ("Pick the title that best matches your actual experience. "
                             "You can change it later — the first title just needs to be "
                             "good enough to start getting impressions."),
            },
            {
                "step": 2,
                "title": "Set Category and Tags",
                "action": f"Category: {recommendation.get('category_path', 'See niche config')}",
                "tags": recommendation.get("tag_sets", [[]])[0] if recommendation.get("tag_sets") else [],
                "guidance": "Use tag set 1 to start. Test tag set 2 after 2 weeks if impressions are low.",
            },
            {
                "step": 3,
                "title": "Set Package Pricing",
                "action": "Use ACQUISITION pricing for your first gig:",
                "pricing": pricing_strategy.get("acquisition_prices", {}),
                "guidance": (
                    f"Start with acquisition prices (first 5 orders). "
                    f"After 5 reviews, raise to entry prices: "
                    f"Basic ${pricing_strategy.get('entry_prices', {}).get('basic', 'N/A')} / "
                    f"Standard ${pricing_strategy.get('entry_prices', {}).get('standard', 'N/A')} / "
                    f"Premium ${pricing_strategy.get('entry_prices', {}).get('premium', 'N/A')}"
                ),
                "package_structure": recommendation.get("package_structure", {}),
            },
            {
                "step": 4,
                "title": "Write Description",
                "action": "Follow this outline:",
                "outline": recommendation.get("description_outline", {}),
                "guidance": ("Write in YOUR voice — the outline provides structure, "
                             "not word-for-word copy. Keep it specific to your actual skills."),
            },
            {
                "step": 5,
                "title": "Add FAQ",
                "action": "Add these FAQ entries:",
                "faqs": recommendation.get("faq_entries", []),
                "guidance": "You can customize the answers based on your actual process.",
            },
            {
                "step": 6,
                "title": "Create Thumbnail and Gallery",
                "action": "Follow these visual guidelines:",
                "visual": visual_recommendations,
                "guidance": ("Create your thumbnail in Canva or Figma. "
                             "Match the recommended style but make it YOUR brand. "
                             "Upload 3-5 gallery images showing your work."),
            },
            {
                "step": 7,
                "title": "Add Gig Extras",
                "action": "Set up these upsells:",
                "extras": (pricing_strategy.get("recommended_extras", [])
                          or recommendation.get("upsell_structure", [])),
            },
            {
                "step": 8,
                "title": "Review and Publish",
                "action": "Final checklist before publishing",
                "checklist": [
                    "Title starts with 'I will' and contains your keyword",
                    "All 3 package tiers filled with specific deliverables",
                    "Description has exclusions section (what you DON'T include)",
                    "At least 3 gallery images uploaded",
                    "FAQ addresses scope boundaries",
                    "Delivery times are realistic (don't over-promise)",
                ],
            },
        ],
    }
```

---

### Section 3 — First 5 Orders Strategy

```python
def build_first_5_orders_section(
    niche_id: str,
    pricing_strategy: dict,
    buyer_persona: dict,
) -> dict:
    """Section 3: How to get and deliver your first 5 orders."""
    return {
        "section": "First 5 Orders",
        "estimated_time": "2-4 weeks",
        "goal": "Get 5 five-star reviews as fast as possible",
        "strategies": [
            {
                "strategy": "Buyer Requests",
                "priority": "PRIMARY",
                "detail": (
                    "Check Fiverr's Buyer Requests section 3x daily (morning, noon, evening). "
                    "Respond to EVERY relevant request within 15 minutes. "
                    "Your response template:"
                ),
                "template": {
                    "opening": "Hi [name]! I'd love to help with [specific thing they asked for].",
                    "proof": "I specialize in [niche] and have [relevant experience/skill].",
                    "differentiator": "What sets me apart: [reference your key differentiator].",
                    "cta": "I can start immediately. Want to discuss the details?",
                },
                "tips": [
                    "Reference something SPECIFIC from their request — shows you read it",
                    "Don't copy-paste generic responses — buyers can tell",
                    "Offer a slightly lower price than your listed Basic for the first 3 orders",
                    "Respond in under 15 minutes — speed wins on Buyer Requests",
                ],
            },
            {
                "strategy": "Search Optimization",
                "priority": "SECONDARY",
                "detail": (
                    "Fiverr's algorithm rewards: "
                    "fast response time, high completion rate, and positive reviews. "
                    "For your first 2 weeks, keep your response time under 30 minutes."
                ),
                "tips": [
                    "Log into Fiverr multiple times per day — 'online' status boosts visibility",
                    "Complete every order on time or early",
                    "Ask buyers to leave a review after delivery (politely, once)",
                    "Don't cancel orders — cancellations hurt your ranking badly",
                ],
            },
            {
                "strategy": "Outside Traffic",
                "priority": "SUPPLEMENTARY",
                "detail": "Drive initial traffic to your gig from outside Fiverr.",
                "channels": [
                    {
                        "channel": "Reddit",
                        "action": f"Post helpful answers in subreddits where your buyer persona ({buyer_persona.get('name', 'your target buyer')}) hangs out",
                        "subreddits": _get_relevant_subreddits(niche_id),
                        "note": "Don't spam your gig link — provide value first, link in profile",
                    },
                    {
                        "channel": "LinkedIn",
                        "action": "Share a post about what you offer with your gig link",
                    },
                    {
                        "channel": "Twitter/X",
                        "action": "Tweet about your specialization with relevant hashtags",
                    },
                ],
            },
            {
                "strategy": "Pricing Leverage",
                "priority": "PRIMARY",
                "detail": (
                    "Use acquisition pricing for the first 5 orders. "
                    "The goal is REVIEWS, not revenue. "
                    f"Acquisition prices: "
                    f"Basic ${pricing_strategy.get('acquisition_prices', {}).get('basic', 'N/A')} / "
                    f"Standard ${pricing_strategy.get('acquisition_prices', {}).get('standard', 'N/A')} / "
                    f"Premium ${pricing_strategy.get('acquisition_prices', {}).get('premium', 'N/A')}"
                ),
            },
        ],
        "delivery_excellence_tips": [
            "Deliver 12-24 hours EARLY when possible — buyers love over-delivery on time",
            "Include a bonus deliverable they didn't ask for (small add-on that takes 10 min)",
            "Write a professional delivery message explaining what you delivered and why",
            "Ask ONE follow-up question after delivery: 'Is there anything you'd like adjusted?'",
            "If a buyer is unhappy, fix it immediately — don't argue, don't defend, just fix",
        ],
    }
```

---

### Section 4 — Review Acquisition Strategy

```python
def build_review_strategy_section(niche_id: str) -> dict:
    """Section 4: How to systematically earn reviews."""
    return {
        "section": "Review Acquisition",
        "goal": "Convert every completed order into a 5-star review",
        "strategies": [
            {
                "strategy": "Delivery Message Template",
                "detail": ("Your delivery message is the last thing buyers read before deciding "
                           "whether to leave a review. Make it count."),
                "template": (
                    "Hi [name]! 🎉\n\n"
                    "Your [deliverable] is complete! Here's what I delivered:\n"
                    "- [Deliverable 1]\n"
                    "- [Deliverable 2]\n"
                    "- [Bonus item — wasn't in the package but I included it]\n\n"
                    "Please review everything and let me know if you'd like any adjustments — "
                    "I want to make sure this is exactly what you need.\n\n"
                    "If you're happy with the work, I'd really appreciate a review — "
                    "it helps me serve more clients like you. Thank you! 🙏"
                ),
            },
            {
                "strategy": "Follow-Up Message (48 hours post-delivery)",
                "detail": "If no review after 48 hours, send one polite follow-up.",
                "template": (
                    "Hi [name], just checking in! Were you able to review the [deliverable]? "
                    "Happy to make any changes if needed. "
                    "If everything looks good, a review would mean a lot — "
                    "it's the main way I grow as a new seller. Thank you!"
                ),
                "rules": [
                    "Only send ONE follow-up — never more",
                    "Don't mention reviews again if they don't respond",
                    "Never offer incentives for reviews (violates Fiverr ToS)",
                ],
            },
            {
                "strategy": "Over-Delivery Pattern",
                "detail": "The #1 driver of 5-star reviews is exceeding expectations.",
                "examples": [
                    "Deliver 1 day early on a 3-day order",
                    "Include a quick-reference summary they didn't ask for",
                    "Format the deliverable more professionally than expected",
                    "Add a brief 'next steps' section at no extra charge",
                ],
            },
        ],
    }
```

---

### Section 5 — Ongoing Optimization

```python
def build_ongoing_optimization_section(
    pricing_strategy: dict,
) -> dict:
    """Section 5: What to do after the first 5 orders."""
    return {
        "section": "Ongoing Optimization",
        "milestones": [
            {
                "milestone": "5 Reviews",
                "actions": [
                    f"Raise prices to entry level: Basic ${pricing_strategy.get('entry_prices', {}).get('basic', 'N/A')}",
                    "Update gig description with proof: '5+ satisfied clients'",
                    "Add a portfolio item from your best completed order",
                    "If a review mentions something specific, add it to your FAQ",
                ],
            },
            {
                "milestone": "10 Reviews",
                "actions": [
                    f"Raise prices to 10-review level from price ladder",
                    "Create a second gig targeting a related keyword",
                    "Update thumbnail with a 'results' screenshot if applicable",
                    "Consider adding a gig video (30-60 seconds)",
                ],
            },
            {
                "milestone": "25 Reviews",
                "actions": [
                    "Raise prices again per price ladder",
                    "Apply for Fiverr's Seller Plus program",
                    "Create a third gig — consider a different niche from your portfolio",
                    "Analyze which package tier sells most — optimize accordingly",
                ],
            },
            {
                "milestone": "50 Reviews — Level 2",
                "actions": [
                    "Raise to near-market-median pricing",
                    "Add Premium package extras",
                    "Consider expanding to adjacent niches identified by Discovery Engine",
                    "Update all gig copy to emphasize your track record",
                ],
            },
        ],
    }
```

---

## Playbook Generation and Export

```python
# src/playbook/generator.py

def generate_playbook(niche_id: str, db, config) -> dict:
    """
    Generates a complete seller setup playbook for a niche.
    Returns structured data that can be rendered as PDF, Markdown, or dashboard view.
    """
    # Get best recommendation for this niche (highest final_score with complete data)
    recommendation = get_best_recommendation_for_niche(niche_id, db)
    pricing = recommendation.pricing_strategy if recommendation else {}
    visual = recommendation.visual_recommendations if recommendation else {}
    buyer_persona = recommendation.buyer_persona if recommendation else {}
    profile_opt = recommendation.profile_optimization if recommendation else {}
    profile_patterns = analyze_profile_patterns(niche_id, db)

    playbook = {
        "niche_id": niche_id,
        "niche_name": get_niche_name(niche_id),
        "generated_at": datetime.utcnow().isoformat(),
        "keyword_used": recommendation.keyword_text if recommendation else None,
        "sections": [
            build_account_setup_section(niche_id, profile_opt, profile_patterns),
            build_gig_creation_section(recommendation, pricing, visual),
            build_first_5_orders_section(niche_id, pricing, buyer_persona),
            build_review_strategy_section(niche_id),
            build_ongoing_optimization_section(pricing),
        ],
    }

    return playbook


def export_playbook_pdf(playbook: dict, output_path: str):
    """Exports the playbook as a PDF using WeasyPrint."""
    env = Environment(loader=FileSystemLoader("src/reports/templates"))
    template = env.get_template("playbook.html")
    html = template.render(playbook=playbook)
    HTML(string=html).write_pdf(output_path)


def export_playbook_markdown(playbook: dict) -> str:
    """Exports the playbook as Markdown for copy-paste."""
    lines = [f"# Seller Setup Playbook — {playbook['niche_name']}\n"]
    lines.append(f"Generated: {playbook['generated_at']}\n")

    for section in playbook["sections"]:
        lines.append(f"\n## {section['section']}\n")
        if section.get("estimated_time"):
            lines.append(f"*Estimated time: {section['estimated_time']}*\n")
        if section.get("steps"):
            for step in section["steps"]:
                lines.append(f"\n### Step {step['step']}: {step['title']}\n")
                lines.append(f"**Action:** {step['action']}\n")
                if step.get("detail"):
                    if isinstance(step["detail"], str):
                        lines.append(f"{step['detail']}\n")
        if section.get("strategies"):
            for strategy in section["strategies"]:
                lines.append(f"\n### {strategy['strategy']} ({strategy.get('priority', '')})\n")
                lines.append(f"{strategy['detail']}\n")
        if section.get("milestones"):
            for milestone in section["milestones"]:
                lines.append(f"\n### At {milestone['milestone']}\n")
                for action in milestone["actions"]:
                    lines.append(f"- {action}\n")

    return "\n".join(lines)
```

---

## Dashboard Integration — Playbook Page

New section on Page 4 (Recommendations) or standalone access:

```python
def render_playbook_section(niche_id: str, db):
    """Renders the playbook for a niche with export buttons."""
    playbook = generate_playbook(niche_id, db, config)

    if not playbook:
        st.info("No playbook available — need at least one recommendation with pricing data")
        return

    st.subheader(f"📋 Seller Setup Playbook — {playbook['niche_name']}")

    for section in playbook["sections"]:
        with st.expander(f"**{section['section']}** ({section.get('estimated_time', '')})"):
            if section.get("steps"):
                for step in section["steps"]:
                    st.markdown(f"**Step {step['step']}: {step['title']}** "
                               f"({'🔴 CRITICAL' if step.get('priority') == 'CRITICAL' else '🟡 ' + step.get('priority', '')})")
                    st.markdown(step["action"])
                    if step.get("time"):
                        st.caption(f"⏱ {step['time']}")

            if section.get("strategies"):
                for strategy in section["strategies"]:
                    st.markdown(f"**{strategy['strategy']}** — {strategy.get('priority', '')}")
                    st.markdown(strategy["detail"])
                    if strategy.get("template"):
                        if isinstance(strategy["template"], str):
                            st.code(strategy["template"], language=None)
                        elif isinstance(strategy["template"], dict):
                            for key, val in strategy["template"].items():
                                st.markdown(f"_{key}_: {val}")

    # Export buttons
    col1, col2 = st.columns(2)
    with col1:
        md_content = export_playbook_markdown(playbook)
        st.download_button("📄 Export Markdown", md_content,
                           file_name=f"playbook_{niche_id}.md")
    with col2:
        pdf_path = f"data/exports/pdf/playbook_{niche_id}.pdf"
        export_playbook_pdf(playbook, pdf_path)
        with open(pdf_path, "rb") as f:
            st.download_button("📕 Export PDF", f.read(),
                               file_name=f"playbook_{niche_id}.pdf",
                               mime="application/pdf")
```

---

## Playbook PDF Template

```html
<!-- src/reports/templates/playbook.html -->
{% extends "base.html" %}
{% block content %}

<h1>Seller Setup Playbook</h1>
<h2>{{ playbook.niche_name }}</h2>
<p style="color: #6b7280;">
    Generated: {{ playbook.generated_at }} |
    Based on: "{{ playbook.keyword_used }}"
</p>

{% for section in playbook.sections %}
<div {% if not loop.first %}class="page-break"{% endif %}>
    <h2>{{ section.section }}</h2>
    {% if section.estimated_time %}
    <p><em>Estimated time: {{ section.estimated_time }}</em></p>
    {% endif %}

    {% if section.steps %}
    {% for step in section.steps %}
    <h3>Step {{ step.step }}: {{ step.title }}
        {% if step.priority == "CRITICAL" %}
        <span style="color: #ef4444; font-size: 12px;">● CRITICAL</span>
        {% endif %}
    </h3>
    <p><strong>{{ step.action }}</strong></p>
    {% if step.detail and step.detail is string %}
    <p>{{ step.detail }}</p>
    {% endif %}
    {% if step.time %}<p style="color: #6b7280; font-size: 10px;">⏱ {{ step.time }}</p>{% endif %}
    {% endfor %}
    {% endif %}

    {% if section.strategies %}
    {% for strategy in section.strategies %}
    <h3>{{ strategy.strategy }} ({{ strategy.priority }})</h3>
    <p>{{ strategy.detail }}</p>
    {% if strategy.template and strategy.template is string %}
    <div style="background: #f3f4f6; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 10px; white-space: pre-wrap;">{{ strategy.template }}</div>
    {% endif %}
    {% endfor %}
    {% endif %}

    {% if section.milestones %}
    {% for milestone in section.milestones %}
    <h3>At {{ milestone.milestone }}</h3>
    <ul>
    {% for action in milestone.actions %}
    <li>{{ action }}</li>
    {% endfor %}
    </ul>
    {% endfor %}
    {% endif %}
</div>
{% endfor %}

{% endblock %}
```
