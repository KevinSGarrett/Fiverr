"""State container for dashboard shell interactions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DashboardState:
    """Serializable state holder for dashboard shell defaults."""

    selected_page: str = "overview"
    filters: dict[str, Any] = field(default_factory=dict)
    active_run_id: str | None = None
