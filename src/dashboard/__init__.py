"""Dashboard package exports."""

from src.dashboard.app import build_page_title, get_available_pages, main
from src.dashboard.navigation import DashboardPage
from src.dashboard.state import DashboardState

__all__ = [
    "DashboardPage",
    "DashboardState",
    "build_page_title",
    "get_available_pages",
    "main",
]

