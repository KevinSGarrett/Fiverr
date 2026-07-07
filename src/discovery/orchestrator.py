"""Discovery orchestrator — SRDI-legacy, NOT the production discovery path.

`run_cycle()` below implements a real pre-insertion relevance gate (ghost-market /
contamination checks via `DiscoveryPreValidator`, requiring a live `provisional_result_set`
per candidate), but no production entrypoint calls it — the wired path is
`src/discovery/stage16.py::run_discovery_cycle`, which uses a different, POST-hoc
evaluation design instead (`evaluate_discovery_results()` in `src/discovery/feedback.py`
scores discovery keywords once they have real collected/scored data, rather than
requiring a synchronous provisional search at hypothesis-generation time — stage16.py's
rule-based generators derive candidates purely from existing DB data and have no live
search results available to gate against here).

Kept for its dedicated test coverage (tests/unit/test_discovery_relevance_gates.py) and
as a reference implementation of the pre-insertion gating pattern, but do not assume this
class runs in production, and do not add new production wiring to it without first
reconciling it with stage16.py's design (see SCRUM-1105).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from src.analysis.pre_validator import DiscoveryPreValidator, DiscoveryVerdict
from src.discovery.contracts import (
    DiscoveryHypothesisResult,
    DiscoveryInput,
    DiscoveryOutput,
    HypothesisMode,
)
from src.discovery.hypothesis import _gate_hypotheses, parse_hypothesis_contracts
from src.models.discovery_outcome import DiscoveryOutcome
from src.models.market import Keyword
from src.models.niche import Niche

logger = logging.getLogger(__name__)

DISCOVERY_STATUS_INVALID = "INVALID"
DISCOVERY_STATUS_MISS = "MISS"


class DiscoveryOrchestrator:
    """Pre-insertion relevance-gate reference implementation - NOT wired into production.

    See the module docstring: the live discovery cycle is
    `src/discovery/stage16.py::run_discovery_cycle`, which does not use this class.
    `generate_hypotheses()`/`score_and_filter()`/`promote_keywords()` below remain stubs;
    `run_cycle()` is a real, tested implementation but has no production caller.
    """

    def __init__(
        self,
        *,
        config: Any | None = None,
        session: Session | None = None,
        pre_validator: DiscoveryPreValidator | None = None,
    ) -> None:
        self._config = config
        self._session = session
        self._pre_validator = pre_validator or DiscoveryPreValidator()

    def run_cycle(self, discovery_input: DiscoveryInput) -> DiscoveryOutput:
        """Execute a complete discovery cycle for a niche.

        R6 relevance gates are enforced only when discovery.enable_relevance_gates is true.
        """
        niche_id = str(discovery_input.niche_id or "")
        run_id = str(discovery_input.run_id or "")
        hypotheses_payload = discovery_input.llm_context.get("hypotheses", [])
        if not isinstance(hypotheses_payload, list):
            hypotheses_payload = []
        gates_enabled = self._relevance_gates_enabled(discovery_input)
        session = self._resolve_session(discovery_input)

        accepted_contracts = parse_hypothesis_contracts(
            [item for item in hypotheses_payload if isinstance(item, dict)],
            source_niche_id=niche_id,
        )
        total_candidates = len(accepted_contracts)
        if gates_enabled:
            accepted_contracts = _gate_hypotheses(accepted_contracts)

        provisional_result_sets = discovery_input.llm_context.get("provisional_result_sets", {})
        if not isinstance(provisional_result_sets, dict):
            provisional_result_sets = {}

        promoted_keywords: list[str] = []
        rejected_count = total_candidates - len(accepted_contracts)
        for contract in accepted_contracts:
            keyword = contract.hypothesis_text
            provisional = provisional_result_sets.get(keyword, [])
            if not isinstance(provisional, list):
                provisional = []

            if gates_enabled:
                pre_result = self._pre_validator.evaluate(
                    candidate=keyword,
                    niche_id=niche_id,
                    provisional_result_set=provisional,
                )
                if pre_result.verdict is DiscoveryVerdict.VALID:
                    if session is not None:
                        self._insert_keyword(
                            session=session,
                            niche_id=niche_id,
                            keyword_text=keyword,
                            specificity_score=contract.specificity_score,
                            pre_verdict=pre_result.verdict,
                        )
                        self._record_outcome(
                            session=session,
                            run_id=run_id,
                            niche_id=niche_id,
                            keyword_text=keyword,
                            status=DISCOVERY_STATUS_MISS,
                            reason="legacy_miss",
                            rsv=pre_result.rsv,
                            is_contaminated=False,
                        )
                    promoted_keywords.append(keyword)
                else:
                    rejected_count += 1
                    if session is not None:
                        self._record_outcome(
                            session=session,
                            run_id=run_id,
                            niche_id=niche_id,
                            keyword_text=keyword,
                            status=DISCOVERY_STATUS_INVALID,
                            reason=pre_result.reason,
                            rsv=pre_result.rsv,
                            is_contaminated=pre_result.verdict is DiscoveryVerdict.CONTAMINATED,
                        )
                continue

            if session is not None:
                self._insert_keyword(
                    session=session,
                    niche_id=niche_id,
                    keyword_text=keyword,
                    specificity_score=contract.specificity_score,
                    pre_verdict=DiscoveryVerdict.VALID,
                )
                self._record_outcome(
                    session=session,
                    run_id=run_id,
                    niche_id=niche_id,
                    keyword_text=keyword,
                    status=DISCOVERY_STATUS_MISS,
                    reason="legacy_miss",
                    rsv=None,
                    is_contaminated=False,
                )
            promoted_keywords.append(keyword)

        feedback = (
            self.aggregate_feedback(
                run_id=run_id,
                session=session,
                enable_relevance_gates=gates_enabled,
            )
            if session is not None and run_id
            else {"counted_valid": 0, "counted_invalid": 0, "counted_total": 0}
        )

        return DiscoveryOutput(
            run_id=discovery_input.run_id,
            niche_id=discovery_input.niche_id,
            modes_run=list(discovery_input.enabled_modes),
            promoted_keywords=promoted_keywords,
            raw_json={
                "relevance_gates_enabled": gates_enabled,
                "total_candidates": total_candidates,
                "rejected_candidates": rejected_count,
                "rejection_rate": (rejected_count / total_candidates) if total_candidates else 0.0,
                "feedback": feedback,
            },
        )

    def generate_hypotheses(
        self,
        discovery_input: DiscoveryInput,
        mode: HypothesisMode,
    ) -> list[DiscoveryHypothesisResult]:
        """Generate hypotheses for a single mode.

        Stub: returns empty list. Full implementations:
        - SCRUM-197 (S7.2): adjacent_keyword
        - SCRUM-198 (S7.3): adjacent_niche
        - SCRUM-199 (S7.4): gap_opportunity
        - SCRUM-200 (S7.5): trend_chase
        """
        logger.debug("generate_hypotheses called for mode=%s — stub", mode.value)
        return []

    def score_and_filter(
        self,
        hypotheses: list[DiscoveryHypothesisResult],
        min_confidence: float = 0.60,
        gold_threshold: float = 0.82,
    ) -> list[DiscoveryHypothesisResult]:
        """Score hypotheses and filter below minimum confidence.

        Stub: returns all hypotheses unchanged. Full implementation in SCRUM-201 (S7.6).
        """
        return hypotheses

    def promote_keywords(
        self,
        hypotheses: list[DiscoveryHypothesisResult],
        gold_threshold: float = 0.82,
    ) -> list[str]:
        """Promote high-confidence hypotheses to the keyword table.

        Stub: returns empty list. Full implementation in SCRUM-202 (S7.7).
        """
        del hypotheses
        del gold_threshold
        return []

    def aggregate_feedback(
        self,
        *,
        run_id: str,
        session: Session,
        enable_relevance_gates: bool,
    ) -> dict[str, int]:
        query = session.query(DiscoveryOutcome).filter(DiscoveryOutcome.run_id == run_id)
        all_rows = query.all()
        if enable_relevance_gates:
            query = query.filter(
                DiscoveryOutcome.is_invalid.is_(False),
                DiscoveryOutcome.is_contaminated.is_(False),
            )
        counted_rows = query.all()
        return {
            "counted_valid": len(counted_rows),
            "counted_invalid": len([row for row in all_rows if row.is_invalid or row.is_contaminated]),
            "counted_total": len(all_rows),
        }

    def _insert_keyword(
        self,
        *,
        session: Session,
        niche_id: str,
        keyword_text: str,
        specificity_score: float,
        pre_verdict: DiscoveryVerdict,
    ) -> None:
        niche_pk = self._resolve_or_create_niche(session, niche_id)
        keyword = Keyword(
            niche_id=niche_pk,
            keyword=keyword_text,
            normalized_keyword=keyword_text.lower().strip(),
            is_discovery=True,
            discovery_mode="relevance_gated" if self._relevance_gates_enabled_from_config() else "legacy",
            hypothesis_confidence=specificity_score,
            ghost_market_flag=pre_verdict is DiscoveryVerdict.GHOST,
            discovery_needs_recollection=False,
            last_relevance_validated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        session.add(keyword)
        session.flush()

    def _record_outcome(
        self,
        *,
        session: Session,
        run_id: str,
        niche_id: str,
        keyword_text: str,
        status: str,
        reason: str,
        rsv: float | None,
        is_contaminated: bool,
    ) -> None:
        outcome = DiscoveryOutcome(
            run_id=run_id,
            niche_id=niche_id,
            keyword_text=keyword_text,
            is_invalid=status == DISCOVERY_STATUS_INVALID,
            is_contaminated=is_contaminated,
            relevance_score=rsv,
            contamination_reason=reason,
        )
        session.add(outcome)
        session.flush()

    def _resolve_or_create_niche(self, session: Session, niche_slug: str) -> int:
        niche = session.query(Niche).filter(Niche.slug == niche_slug).one_or_none()
        if niche is None:
            niche = Niche(slug=niche_slug, name=niche_slug.replace("_", " ").title(), category_path="discovery")
            session.add(niche)
            session.flush()
        return int(niche.id)

    def _resolve_session(self, discovery_input: DiscoveryInput) -> Session | None:
        context_session = discovery_input.llm_context.get("session")
        if isinstance(context_session, Session):
            return context_session
        return self._session

    def _relevance_gates_enabled(self, discovery_input: DiscoveryInput) -> bool:
        config = discovery_input.llm_context.get("config") or self._config
        return bool(getattr(getattr(config, "discovery", None), "enable_relevance_gates", False))

    def _relevance_gates_enabled_from_config(self) -> bool:
        return bool(getattr(getattr(self._config, "discovery", None), "enable_relevance_gates", False))
