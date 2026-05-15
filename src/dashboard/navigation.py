"""Navigation contracts for the dashboard shell."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DashboardPage:
    """Metadata describing one dashboard page entry."""

    page_id: str
    label: str
    enabled: bool
    status: str


def get_available_pages() -> list[DashboardPage]:
    """Return foundation page metadata without launching any UI runtime."""
    return [
        DashboardPage(page_id="overview", label="Overview", enabled=True, status="foundation_shell"),
        DashboardPage(
            page_id="foundation_status",
            label="Foundation Status",
            enabled=True,
            status="cycle003_shell",
        ),
        DashboardPage(
            page_id="collection_dry_run",
            label="Collection Dry Run",
            enabled=True,
            status="cycle003_shell",
        ),
        DashboardPage(
            page_id="analysis_dry_run",
            label="Analysis Dry Run",
            enabled=True,
            status="cycle003_shell",
        ),
        DashboardPage(
            page_id="phase2_readiness",
            label="Phase 2 Readiness",
            enabled=False,
            status="preview_cycle004",
        ),
        DashboardPage(
            page_id="phase2_reports",
            label="Phase 2 Reports",
            enabled=False,
            status="preview_cycle004",
        ),
        DashboardPage(
            page_id="phase2_exports",
            label="Phase 2 Exports",
            enabled=False,
            status="preview_cycle004",
        ),
        DashboardPage(
            page_id="opportunities",
            label="Opportunities",
            enabled=True,
            status="cycle014_payload_ready",
        ),
        DashboardPage(
            page_id="keywords",
            label="Keywords",
            enabled=True,
            status="cycle014_payload_ready",
        ),
        DashboardPage(
            page_id="run_history",
            label="Run History",
            enabled=True,
            status="cycle014_payload_ready",
        ),
        DashboardPage(page_id="niches", label="Niches", enabled=False, status="not_implemented"),
        DashboardPage(page_id="scores", label="Scores", enabled=False, status="not_implemented"),
        DashboardPage(
            page_id="recommendations",
            label="Recommendations",
            enabled=False,
            status="not_implemented",
        ),
        DashboardPage(page_id="reports", label="Reports", enabled=False, status="not_implemented"),
        DashboardPage(page_id="settings", label="Settings", enabled=False, status="not_implemented"),
    ]
