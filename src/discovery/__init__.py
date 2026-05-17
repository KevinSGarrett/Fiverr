"""Discovery engine — E07 implementation module.

Provides the discovery core loop, hypothesis mode generation
(adjacent keyword, adjacent niche, gap opportunity, trend chase),
scoring/feedback, keyword integration, and Stage 16 orchestration.

Status: Scaffolded (SCRUM-273). Full implementation in SCRUM-195 through SCRUM-204.
"""

from __future__ import annotations

from src.discovery.contracts import (
    DiscoveryHypothesisResult,
    DiscoveryInput,
    DiscoveryOutput,
    HypothesisMode,
    HypothesisStatus,
)
from src.discovery.orchestrator import DiscoveryOrchestrator

__all__ = [
    "DiscoveryHypothesisResult",
    "DiscoveryInput",
    "DiscoveryOrchestrator",
    "DiscoveryOutput",
    "HypothesisMode",
    "HypothesisStatus",
]
