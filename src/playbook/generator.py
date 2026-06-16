"""Wave 11 S8.3 seller setup playbook generator."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

NICHE_NAME_MAP: dict[str, str] = {
    "prd_ai_saas": "PRD AI SaaS",
    "support_kb_readiness": "Support KB Readiness",
    "gumloop_lindy_workflow": "Gumloop Lindy Workflow",
    "mcp_ai_agent": "MCP AI Agent",
    "python_automation": "Python Automation",
    "ai_tool_llm_integration": "AI Tool LLM Integration",
    "ai_agent_development": "AI Agent Development",
    "workflow_automation": "Workflow Automation",
    "python_web_scraping": "Python Web Scraping",
}


def get_niche_name(niche_id: str) -> str:
    """Return display name for known niche ids with safe fallback."""
    if niche_id in NICHE_NAME_MAP:
        return NICHE_NAME_MAP[niche_id]
    cleaned = niche_id.replace("_", " ").strip()
    return cleaned.title() if cleaned else "General Services"


def generate_playbook(niche_id: str, db: Any, config: Any) -> dict[str, Any]:
    """Build a 5-section playbook payload; always returns a valid structure."""
    recommendation: Any | None = None
    keyword_used = ""
    has_full_data = False
    pricing: dict[str, Any] = {}
    visual: dict[str, Any] = {}
    profile_optimization: dict[str, Any] = {}
    buyer_persona: dict[str, Any] = {}

    try:
        from src.models import Recommendation

        recommendation = (
            db.query(Recommendation)
            .filter(Recommendation.niche_id == niche_id)
            .filter(Recommendation.generation_complete.is_(True))
            .order_by(Recommendation.created_at.desc())
            .first()
        )
        has_full_data = recommendation is not None
    except Exception:
        recommendation = None
        has_full_data = False

    if recommendation is not None:
        try:
            keyword_used = _safe_extract_keyword(recommendation, db)
            raw_payload = getattr(recommendation, "raw_json", {}) or {}
            if isinstance(raw_payload, dict):
                pricing = raw_payload.get("pricing_strategy", {}) or {}
                visual = raw_payload.get("visual_recommendations", {}) or {}
                profile_optimization = raw_payload.get("profile_optimization", {}) or {}
                buyer_persona = raw_payload.get("buyer_persona", {}) or {}
        except Exception:
            keyword_used = ""

    account_setup = build_account_setup_section(niche_id, profile_optimization, config or {})
    gig_creation = build_gig_creation_section(recommendation, pricing, visual)
    first_orders = build_first_5_orders_section(niche_id, pricing, buyer_persona)
    review = build_review_strategy_section(niche_id)
    optimization = build_ongoing_optimization_section(pricing)

    return {
        "niche_id": niche_id,
        "niche_name": get_niche_name(niche_id),
        "generated_at": datetime.now(UTC).isoformat(),
        "keyword_used": keyword_used or "No live recommendation keyword available yet",
        "has_full_data": has_full_data,
        "sections": [
            account_setup,
            gig_creation,
            first_orders,
            review,
            optimization,
        ],
    }


def export_playbook_markdown(playbook: dict[str, Any]) -> str:
    """Render playbook payload as markdown with steps/strategies/milestones."""
    lines: list[str] = [
        f"# {playbook.get('niche_name', 'Playbook')} Seller Setup Playbook",
        "",
        f"- Generated: {playbook.get('generated_at', '')}",
        f"- Keyword: {playbook.get('keyword_used', 'N/A')}",
        f"- Full live data: {playbook.get('has_full_data', False)}",
        "",
    ]

    for section in playbook.get("sections", []):
        title = section.get("section", "Section")
        lines.append(f"## {title}")
        lines.append(f"_Estimated time: {section.get('estimated_time', 'N/A')}_")
        lines.append("")

        for step in section.get("steps", []):
            lines.append(f"### {step.get('title', 'Step')}")
            lines.append(f"- Action: {step.get('action', '')}")
            lines.append(f"- Detail: {step.get('detail', '')}")
            if step.get("priority"):
                lines.append(f"- Priority: {step['priority']}")
            if step.get("guidance"):
                lines.append(f"- Guidance: {step['guidance']}")
            checklist = step.get("checklist", [])
            if isinstance(checklist, list) and checklist:
                lines.append("- Checklist:")
                for item in checklist:
                    lines.append(f"  - [ ] {item}")
            lines.append("")

        for strategy in section.get("strategies", []):
            lines.append(f"### {strategy.get('strategy', 'Strategy')}")
            lines.append(f"- Type: {strategy.get('type', 'GENERAL')}")
            lines.append(f"- Detail: {strategy.get('detail', '')}")
            if strategy.get("template"):
                lines.append(f"- Template: {strategy['template']}")
            tips = strategy.get("tips", [])
            if isinstance(tips, list) and tips:
                lines.append("- Tips:")
                for tip in tips:
                    lines.append(f"  - {tip}")
            lines.append("")

        for milestone in section.get("milestones", []):
            lines.append(f"### Milestone: {milestone.get('milestone', 'Milestone')}")
            for action in milestone.get("actions", []):
                lines.append(f"- {action}")
            lines.append("")

        for tip in section.get("delivery_excellence_tips", []):
            lines.append(f"- {tip}")
        lines.append("")

    return "\n".join(lines)


def export_playbook_pdf(playbook: dict[str, Any], output_path: str) -> None:
    """Render playbook HTML template and write PDF via WeasyPrint."""
    try:
        from jinja2 import Environment, FileSystemLoader
        from weasyprint import HTML  # type: ignore[import-untyped]
    except (ImportError, OSError) as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "PDF export requires WeasyPrint + Jinja2. Install with: pip install weasyprint jinja2"
        ) from exc

    template_dir = Path("src/reports/templates")
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("playbook.html")
    html = template.render(playbook=playbook)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html).write_pdf(str(out))


def render_playbook_section(niche_id: str, db: Any) -> None:
    """Render playbook content into Streamlit with graceful empty/data states."""
    import streamlit as st

    from src.dashboard.db_helpers import get_db_session

    if db is None:
        with get_db_session() as session:
            playbook = generate_playbook(niche_id, session, {})
    else:
        playbook = generate_playbook(niche_id, db, {})

    st.subheader(f"{playbook.get('niche_name', niche_id)} Playbook")
    if not playbook.get("has_full_data", False):
        st.info("Live recommendation data not found yet. Showing actionable starter playbook.")
    for section in playbook.get("sections", []):
        st.markdown(f"### {section.get('section', 'Section')}")
        for step in section.get("steps", []):
            st.markdown(f"- **{step.get('title', 'Step')}**: {step.get('detail', '')}")
        for strategy in section.get("strategies", []):
            st.markdown(f"- **{strategy.get('strategy', 'Strategy')}** ({strategy.get('type', 'GENERAL')})")
        for milestone in section.get("milestones", []):
            st.markdown(f"- **{milestone.get('milestone', 'Milestone')}**")


def build_account_setup_section(
    niche_id: str,
    profile_opt: dict[str, Any] | None,
    profile_patterns: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build 7-step account setup checklist."""
    _ = profile_opt or {}
    _patterns = profile_patterns or {}
    display_name = get_niche_name(niche_id)
    return {
        "section": "Account Setup",
        "estimated_time": "1-2 weeks",
        "steps": [
            {
                "title": "Professional profile photo",
                "action": "Upload a high-trust headshot",
                "detail": "Use consistent lighting/background and direct eye contact to improve clicks.",
                "priority": "CRITICAL",
                "guidance": "Natural expression, no heavy filters, clear face crop.",
            },
            {
                "title": "Bio optimization",
                "action": "Rewrite bio for buyer outcomes",
                "detail": f"Frame your {display_name} service around concrete business results and turnaround.",
            },
            {
                "title": "Portfolio setup",
                "action": "Add 3-5 relevant portfolio samples",
                "detail": "Use short before/after context and include measurable outcomes.",
            },
            {
                "title": "Gig category alignment",
                "action": "Set category/subcategory precisely",
                "detail": "Keep category aligned with your niche to improve ranking relevance.",
            },
            {
                "title": "Skill tags",
                "action": "Select conversion-oriented skill tags",
                "detail": "Prioritize buyer search phrases and remove vague tags.",
            },
            {
                "title": "Profile URL customization",
                "action": "Set clean, brand-consistent profile slug",
                "detail": "Use a short URL that matches your brand identity.",
            },
            {
                "title": "Response-rate operations",
                "action": "Set notifications and response workflow",
                "detail": "Use mobile + desktop alerts and canned reply templates for under-1h responses.",
            },
        ],
    }


def build_gig_creation_section(
    recommendation: Any,
    pricing: dict[str, Any] | None,
    visual: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build 8-step gig setup with launch checklist."""
    pricing = pricing or {}
    visual = visual or {}
    title_hint = "I will deliver high-conversion freelance services"
    if recommendation is not None:
        raw_titles = getattr(recommendation, "gig_titles", None)
        if isinstance(raw_titles, list) and raw_titles:
            maybe = raw_titles[0]
            if isinstance(maybe, str) and maybe.strip():
                title_hint = maybe.strip()
            elif isinstance(maybe, dict) and isinstance(maybe.get("title"), str):
                title_hint = str(maybe["title"]).strip() or title_hint

    acquisition_prices = pricing.get("acquisition_prices", {})
    entry_price = acquisition_prices.get("basic") if isinstance(acquisition_prices, dict) else None
    pricing_note = f"Use entry package around ${entry_price}." if entry_price else "Set an accessible entry package."

    return {
        "section": "Gig Creation",
        "estimated_time": "3-5 days",
        "steps": [
            {"title": "Gig title drafting", "action": "Create title options", "detail": f"Primary title seed: {title_hint}"},
            {"title": "Package architecture", "action": "Define 3-tier packages", "detail": "Differentiate by scope, speed, and deliverable depth."},
            {"title": "Pricing setup", "action": "Apply acquisition pricing", "detail": pricing_note},
            {"title": "Description copy", "action": "Write conversion-focused description", "detail": "Lead with problem -> solution -> outcomes -> trust proof."},
            {"title": "FAQ coverage", "action": "Publish objection-handling FAQ", "detail": "Answer revisions, delivery timeline, and scope boundaries."},
            {"title": "Requirements form", "action": "Set structured order intake questions", "detail": "Collect goals, assets, deadlines, and constraints up front."},
            {"title": "Visual assets", "action": "Prepare thumbnail/gallery media", "detail": str(visual.get("direction", "Use clean, niche-specific visuals with bold value text."))},
            {
                "title": "Launch checklist",
                "action": "Validate listing before publish",
                "detail": "Run final quality checks and publish when all checks pass.",
                "checklist": [
                    "No spelling errors in title/description",
                    "Packages align with scope boundaries",
                    "FAQ covers revisions and timelines",
                    "Thumbnail readable on mobile",
                ],
            },
        ],
    }


def build_first_5_orders_section(
    niche_id: str,
    pricing: dict[str, Any] | None,
    buyer_persona: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build first-orders acquisition strategy bundle."""
    pricing = pricing or {}
    _persona = buyer_persona or {}
    ladder = pricing.get("price_ladder", []) if isinstance(pricing, dict) else []
    ladder_note = f"Anchor upsell path across {len(ladder)} ladder levels." if isinstance(ladder, list) and ladder else "Use gradual price steps as demand increases."

    return {
        "section": "First 5 Orders",
        "estimated_time": "2-4 weeks",
        "strategies": [
            {
                "strategy": f"Buyer Request Sprint for {get_niche_name(niche_id)}",
                "type": "PRIMARY",
                "detail": "Submit tailored buyer-request responses daily with clear outcomes and delivery certainty.",
            },
            {
                "strategy": "Search Optimization Cadence",
                "type": "SECONDARY",
                "detail": "Iterate title tags and thumbnail weekly based on impression/click movement.",
            },
            {
                "strategy": "Outside Traffic Activation",
                "type": "SUPPLEMENTARY",
                "detail": "Drive warm traffic from portfolio channels, social proof posts, and niche communities.",
            },
            {
                "strategy": "Pricing Leverage Loop",
                "type": "PRIMARY",
                "detail": ladder_note,
            },
        ],
        "delivery_excellence_tips": [
            "Confirm scope and assumptions in first buyer message.",
            "Deliver milestone preview before full handoff.",
            "Include one over-delivery element per order.",
            "Use concise delivery summary with next-step guidance.",
        ],
    }


def build_review_strategy_section(niche_id: str) -> dict[str, Any]:
    """Build 3-part review acquisition strategy."""
    display_name = get_niche_name(niche_id)
    return {
        "section": "Review Acquisition",
        "estimated_time": "1-2 months",
        "strategies": [
            {
                "strategy": "Delivery Message Template",
                "detail": "Send a structured final delivery message that confirms outcomes and invites feedback.",
                "template": (
                    f"Thanks for trusting me with your {display_name} project. "
                    "I delivered everything requested plus a bonus optimization note. "
                    "If this helped your goals, I would truly appreciate your honest review."
                ),
            },
            {
                "strategy": "Follow-Up (48hr)",
                "detail": "If no review is left after delivery, send one polite follow-up after 48 hours.",
                "tips": ["Keep message short", "Reference delivered outcome", "Avoid pressure language"],
            },
            {
                "strategy": "Over-Delivery Framework",
                "detail": "Create repeatable micro-upgrades that surprise buyers and increase review likelihood.",
                "tips": ["Bonus checklist", "Extra QA pass", "Actionable next-step recommendations"],
            },
        ],
    }


def build_ongoing_optimization_section(pricing: dict[str, Any] | None) -> dict[str, Any]:
    """Build 4 milestone growth plan with graceful pricing fallbacks."""
    pricing = pricing or {}
    ladder = pricing.get("price_ladder", [])
    ladder_values: list[str] = []
    if isinstance(ladder, list):
        for level in ladder:
            if isinstance(level, dict) and "price" in level:
                ladder_values.append(f"${level['price']}")
    ladder_hint = ", ".join(ladder_values) if ladder_values else "incremental price ladder"

    return {
        "section": "Ongoing Optimization",
        "estimated_time": "3-6 months",
        "milestones": [
            {"milestone": "5 Reviews", "actions": ["Refresh thumbnails using buyer language", "Document 3 high-converting proof points"]},
            {"milestone": "10 Reviews", "actions": [f"Raise entry package using {ladder_hint}", "Split-test title variants"]},
            {"milestone": "25 Reviews", "actions": ["Add premium package differentiators", "Expand FAQ with objection data from messages"]},
            {"milestone": "50 Reviews", "actions": ["Productize repeatable upsells", "Shift positioning toward authority niche outcomes"]},
        ],
    }


def _safe_extract_keyword(recommendation: Any, db: Any) -> str:
    keyword_id = getattr(recommendation, "keyword_id", None)
    if keyword_id is None:
        return ""
    try:
        from src.models.market import Keyword

        row = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if row is not None:
            return str(getattr(row, "keyword", "") or "")
    except Exception:
        return ""
    return ""
