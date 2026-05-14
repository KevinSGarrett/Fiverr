"""Dashboard app shell for future Streamlit-based presentation."""

from __future__ import annotations

from typing import Any

from src.dashboard.navigation import (
    DashboardPage,
)
from src.dashboard.navigation import (
    get_available_pages as get_navigation_pages,
)
from src.dashboard.state import build_cycle003_status_state, build_phase2_readiness_state


def build_page_title() -> str:
    """Return a stable dashboard title for the foundation shell."""
    return "Fiverr Research System Dashboard (Foundation Shell)"


def get_available_pages() -> list[DashboardPage]:
    """Expose dashboard page metadata for callers and tests."""
    return get_navigation_pages()


def get_cycle003_status_state() -> dict[str, Any]:
    """Expose import-safe status sections for Foundation/Collection/Analysis dry runs."""
    return build_cycle003_status_state()


def get_phase2_readiness_state() -> dict[str, Any]:
    """Expose import-safe Phase 2 readiness placeholders."""
    return build_phase2_readiness_state()


def main() -> None:
    """Render a minimal Streamlit shell when explicitly invoked."""
    import streamlit as st

    st.title(build_page_title())
    st.caption("Dashboard UX implementation is planned for a later cycle.")

    st.subheader("Available Pages")
    for page in get_available_pages():
        status = "ready" if page.enabled else f"disabled ({page.status})"
        st.write(f"- {page.label}: {status}")

    st.subheader("Cycle 003 Status")
    status_state = get_cycle003_status_state()
    for section in status_state["sections"]:
        st.write(f"### {section['label']}")
        for metric in section["metrics"]:
            st.write(f"- {metric['name']}: {metric['value']}")

    st.subheader("Cycle 004 Phase 2 Readiness (Preview)")
    readiness_state = get_phase2_readiness_state()
    st.write(f"- Collection Dry Run: {readiness_state['collection_dry_run']['status']}")
    st.write(f"- Analysis Dry Run: {readiness_state['analysis_dry_run']['status']}")
    st.write(
        "- Fixture Coverage (gig detail parser): "
        f"{readiness_state['fixture_coverage']['gig_detail_parser']}"
    )

