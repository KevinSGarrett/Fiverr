"""Discovery engine — E07 implementation module.

Provides the discovery core loop, hypothesis mode generation
(adjacent keyword, adjacent niche, gap opportunity, trend chase),
scoring/feedback, keyword integration, and Stage 16 orchestration.

Status: Scaffolded (SCRUM-273). Full implementation in SCRUM-195 through SCRUM-204.
"""

from __future__ import annotations

from src.discovery.candidates import (
    create_discovery_candidate,
    get_pending_candidates,
    is_valid_candidate,
    update_candidate_status,
)
from src.discovery.contracts import (
    DiscoveryHypothesisResult,
    DiscoveryInput,
    DiscoveryOutput,
    HypothesisMode,
    HypothesisStatus,
)
from src.discovery.hypothesis import generate_niche_hypotheses, score_hypothesis_signals
from src.discovery.orchestrator import DiscoveryOrchestrator
from src.models.discovery import DiscoveryCandidate

__all__ = [
    "DiscoveryCandidate",
    "DiscoveryHypothesisResult",
    "DiscoveryInput",
    "DiscoveryOrchestrator",
    "DiscoveryOutput",
    "HypothesisMode",
    "HypothesisStatus",
    "create_discovery_candidate",
    "generate_niche_hypotheses",
    "get_pending_candidates",
    "is_valid_candidate",
    "score_hypothesis_signals",
    "update_candidate_status",
]
