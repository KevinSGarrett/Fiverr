"""Discovery engine — E07 implementation module.

Provides the discovery core loop, hypothesis mode generation
(adjacent keyword, adjacent niche, gap opportunity, trend chase),
scoring/feedback, keyword integration, and Stage 16 orchestration.

The PRODUCTION entrypoint is `src.discovery.stage16.run_discovery_cycle` (also reachable
via `python run.py discover` and `src.orchestrator.run_pipeline(mode="discovery-only")`).
`DiscoveryOrchestrator` exported below is an SRDI-legacy reference implementation with no
production caller — see its module docstring in `orchestrator.py` before relying on it.
`generate_niche_hypotheses` (LLM-driven hypothesis generation) is wired into
`run_discovery_cycle` as the optional `llm_niche_expansion` mode: it runs alongside the
rule-based adjacent_keyword/adjacent_niche/gap_exploit/trend_chase generators whenever a
caller supplies `llm_client`, and is a no-op otherwise (SCRUM-1106).
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
from src.discovery.stage16 import run_discovery_cycle
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
    "run_discovery_cycle",
    "score_hypothesis_signals",
    "update_candidate_status",
]
