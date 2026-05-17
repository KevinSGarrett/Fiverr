"""Gig detail workflow — Stage 4 (Story 2.9)."""
from __future__ import annotations

from types import ModuleType
from typing import Any

from src.collection import gig_detail as _mod


class GigDetailWorkflow:
    """Visits each gig page and extracts full detail including packages, FAQ, extras."""

    def run(self, *args: Any, **kwargs: Any) -> ModuleType:
        return _mod
