"""Seller profile workflow — Stage 5 (Story 2.10)."""
from __future__ import annotations

from types import ModuleType
from typing import Any

from src.collection import seller_profile as _mod


class SellerProfileWorkflow:
    """Visits seller profile pages and extracts bio, stats, portfolio, skills."""

    def run(self, *args: Any, **kwargs: Any) -> ModuleType:
        return _mod
