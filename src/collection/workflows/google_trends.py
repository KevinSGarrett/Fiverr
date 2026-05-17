"""Google Trends workflow — Stage 6a (Story 2.11)."""
from __future__ import annotations

from types import ModuleType
from typing import Any

from src.collection import external_signals as _mod


class GoogleTrendsWorkflow:
    """Fetches Google Trends interest-over-time data for each keyword."""

    def run(self, *args: Any, **kwargs: Any) -> ModuleType:
        return _mod
