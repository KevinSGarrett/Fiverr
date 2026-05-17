"""Dashboard page modules — one page per file, per .cursorrules.

COMPATIBILITY: Re-exports from the legacy pages.py module are preserved here
so that existing imports (e.g. from src.dashboard.pages import build_registered_page_payloads)
continue to work without modification.
"""
from __future__ import annotations

# ── Legacy compatibility re-exports ──────────────────────────────────────────
# The flat pages.py module (now pages/_legacy.py) provided these; preserve them.
from src.dashboard._pages_legacy import (
    build_registered_page_payloads,
    get_dashboard_page_payload_builders,
)

# ── New per-page render functions (Story 9.3–9.16) ───────────────────────────
from src.dashboard.pages.competitors import render_competitors_page
from src.dashboard.pages.discovery import render_discovery_page
from src.dashboard.pages.keywords import render_keywords_page
from src.dashboard.pages.llm_costs import render_llm_costs_page
from src.dashboard.pages.opportunities import render_opportunities_page
from src.dashboard.pages.playbook import render_playbook_page
from src.dashboard.pages.pricing import render_pricing_page
from src.dashboard.pages.recommendations import render_recommendations_page
from src.dashboard.pages.run_history import render_run_history_page

__all__ = [
    # legacy
    "build_registered_page_payloads",
    "get_dashboard_page_payload_builders",
    # new
    "render_competitors_page",
    "render_discovery_page",
    "render_keywords_page",
    "render_llm_costs_page",
    "render_opportunities_page",
    "render_playbook_page",
    "render_pricing_page",
    "render_recommendations_page",
    "render_run_history_page",
]
