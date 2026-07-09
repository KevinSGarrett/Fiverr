"""Stage 16: Discovery Engine orchestration.

Wires the complete S7.1-S7.7 discovery loop into a single callable function:

  1. evaluate_discovery_results()  - classify previously scored discoveries (S7.6)
  2. build_feedback_summary()      - aggregate feedback context (S7.6)
  3. _select_modes()               - which hypothesis modes this cycle
  4. generate_*_hypotheses()       - produce candidates (S7.2-S7.5)
  5. Budget gate                   - filter by confidence, cap at max
  6. process_accepted_hypotheses() - insert to keyword table (S7.7)
  7. DiscoveryCycleLog             - persist cycle record

The 4 rule-based modes (adjacent_keyword/adjacent_niche/gap_exploit/trend_chase) do
pure data analysis with no LLM calls. An optional 5th mode, llm_niche_expansion, calls
generate_niche_hypotheses() when a caller supplies llm_client (SCRUM-1106); it is a
no-op when llm_client is None, matching the codebase-wide LLM-optional convention.
No new migration required (DiscoveryCycleLog from migration_14 / C070).
Does NOT modify src/discovery/orchestrator.py (SRDI legacy, untouched).
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime
from inspect import isawaitable
from typing import Any

from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG
from src.discovery.feedback import build_feedback_summary, evaluate_discovery_results
from src.discovery.hypothesis import (
    HypothesisContract,
    generate_adjacent_keyword_hypotheses,
    generate_adjacent_niche_hypotheses,
    generate_gap_exploit_hypotheses,
    generate_niche_hypotheses,
    generate_trend_chase_hypotheses,
)
from src.discovery.integration import get_pending_discovery_keywords, process_accepted_hypotheses
from src.models import DiscoveryCycleLog, Keyword, KeywordScore, Niche

log = logging.getLogger(__name__)

DEFAULT_MIN_CONFIDENCE: float = 0.50
DEFAULT_MAX_HYPOTHESES: int = 15

_BASE_MODES = ["adjacent_keyword", "gap_exploit", "trend_chase", "llm_niche_expansion"]
_PERIODIC_MODES: dict[int, str] = {3: "adjacent_niche"}


def _select_modes(
    config: dict[str, Any] | None = None,
    run_number: int | None = None,
) -> list[str]:
    """Select which hypothesis modes to run this discovery cycle."""
    modes = list(_BASE_MODES)
    if run_number is not None:
        for period, mode in _PERIODIC_MODES.items():
            if run_number % period == 0:
                modes.append(mode)

    enabled = (config or {}).get("discovery", {}).get("enabled_modes")
    if enabled and isinstance(enabled, list):
        modes = [mode for mode in modes if mode in enabled]
    return list(dict.fromkeys(modes))


def _resolve_niche_pk(db: Any, niche_id: str) -> int | None:
    """Resolve niche slug to integer primary key used by Keyword rows."""
    row = db.query(Niche).filter(Niche.slug == niche_id).first()
    return int(row.id) if row is not None else None


def _normalize_0_100_to_unit(raw: Any, default: float = 0.5) -> float:
    """KeywordScore's demand/competition/trend/opportunity scores are 0-100 (see
    src/scoring/demand.py:709, competition.py:518, trend.py:140), but hypothesis.py's
    gap/trend filters and thresholds (GAP_DEMAND_THRESHOLD, TREND_VELOCITY_THRESHOLD,
    etc.) are written for a 0-1 scale. Missing values default directly to 0.5 on the
    0-1 scale (not divided), matching a neutral "unknown" prior."""
    if raw is None:
        return default
    try:
        return max(0.0, min(1.0, float(raw) / 100.0))
    except (TypeError, ValueError):
        return default


def _build_seed_data(
    niche_id: str,
    db: Any,
    modes: list[str],
) -> dict[str, Any]:
    """Query DB for the data each hypothesis mode needs as input."""
    existing_kw_texts: list[str] = []
    seed_keywords: list[str] = []
    gap_signals: list[dict[str, Any]] = []
    trend_signals: list[dict[str, Any]] = []

    try:
        niche_pk = _resolve_niche_pk(db, niche_id)
        if niche_pk is None:
            return {
                "seed_keywords": [],
                "gap_signals": [],
                "trend_signals": [],
                "existing_kw_texts": [],
            }

        existing_rows = (
            db.query(Keyword)
            .filter(
                Keyword.niche_id == niche_pk,
                Keyword.is_discovery.is_(False),
            )
            .limit(50)
            .all()
        )
        existing_kw_texts = [row.keyword for row in existing_rows if getattr(row, "keyword", None)]
        seed_keywords = existing_kw_texts[:20]

        if "gap_exploit" in modes:
            score_rows = (
                db.query(Keyword, KeywordScore)
                .join(KeywordScore, Keyword.id == KeywordScore.keyword_id)
                .filter(Keyword.niche_id == niche_pk)
                .limit(30)
                .all()
            )
            gap_signals = [
                {
                    "keyword": keyword.keyword,
                    "demand_score": _normalize_0_100_to_unit(getattr(score, "demand_score", None)),
                    "competition_score": _normalize_0_100_to_unit(getattr(score, "competition_score", None)),
                    "opportunity_score": _normalize_0_100_to_unit(getattr(score, "opportunity_score", None)),
                }
                for keyword, score in score_rows
                if getattr(keyword, "keyword", None)
            ]

        if "trend_chase" in modes:
            score_rows = (
                db.query(Keyword, KeywordScore)
                .join(KeywordScore, Keyword.id == KeywordScore.keyword_id)
                .filter(Keyword.niche_id == niche_pk)
                .limit(20)
                .all()
            )
            trend_signals = [
                {
                    "keyword": keyword.keyword,
                    "trend_score": _normalize_0_100_to_unit(getattr(score, "trend_score", None)),
                    # KeywordScore.score_components (see calculate_weighted_composite in
                    # src/scoring/pipeline.py) only preserves the FINAL 0-100 composite
                    # value per metric, not TrendScoreCalculator's raw google_trends_slope
                    # sub-signal - that breakdown never reaches the persisted row. There is
                    # no separately-persisted velocity signal, so trend_score is the best
                    # real proxy available; a "trend_velocity" key here was previously read
                    # from a location that never existed, silently defaulting to 0.3 and
                    # failing the >= 0.40 threshold on every real row (SCRUM-1104).
                    "trend_velocity": _normalize_0_100_to_unit(getattr(score, "trend_score", None)),
                    "opportunity_score": _normalize_0_100_to_unit(getattr(score, "opportunity_score", None)),
                }
                for keyword, score in score_rows
                if getattr(keyword, "keyword", None)
            ]
    except Exception as exc:
        log.debug("seed-data query failure for niche=%s: %s", niche_id, exc)

    return {
        "seed_keywords": seed_keywords,
        "gap_signals": gap_signals,
        "trend_signals": trend_signals,
        "existing_kw_texts": existing_kw_texts,
    }


class _CostTrackingLLMClient:
    """Proxies a real LLMClient's complete() call to record estimated_cost_usd
    without changing generate_niche_hypotheses' widely-tested return contract
    (Codex P2 finding on PR #181): llm_niche_expansion made real paid calls but
    never accounted for or gated on discovery.max_cost_per_run, and always
    persisted DiscoveryCycleLog.total_cost_usd=0.0 regardless."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.cost_usd = 0.0

    def complete(self, *args: Any, **kwargs: Any) -> Any:
        result = self._inner.complete(*args, **kwargs)
        # generate_niche_hypotheses explicitly supports async-capable clients
        # (`if isawaitable(response): response = await response`); mirror that
        # contract here too, or an async client's real cost would never be
        # recorded (Codex P2, PR #181 round 5) - reading .metadata off the raw
        # coroutine before it's awaited always yields None.
        if isawaitable(result):
            return self._await_and_record(result)
        self._record_cost(result)
        return result

    async def _await_and_record(self, awaitable: Any) -> Any:
        result = await awaitable
        self._record_cost(result)
        return result

    def _record_cost(self, result: Any) -> None:
        metadata = getattr(result, "metadata", None) or {}
        self.cost_usd += float(metadata.get("estimated_cost_usd", 0.0) or 0.0)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def _adapt_llm_hypotheses(raw: list[dict[str, Any]], niche_id: str) -> list[HypothesisContract]:
    """Convert generate_niche_hypotheses' gated dict output into HypothesisContract
    rows so LLM-driven hypotheses flow through the same accept/gate/persist pipeline
    as the rule-based generators. Called with enable_relevance_gates=True, so every
    dict already passed hypothesis.py's own GATE1_SPECIFICITY_THRESHOLD filter.
    Stamps discovery_mode="llm_niche_expansion" so insert_discovery_keyword()
    (src/discovery/integration.py) attributes these keywords correctly instead of
    falling back to "unknown" (Codex P2 finding on PR #181)."""
    contracts: list[HypothesisContract] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        hypothesis_text = str(item.get("hypothesis_text") or "").strip()
        if not hypothesis_text:
            continue
        contracts.append(
            HypothesisContract(
                hypothesis_text=hypothesis_text,
                niche_id=niche_id,
                buyer=item.get("buyer"),
                deliverable=item.get("deliverable"),
                specificity_score=float(item.get("specificity_score") or 0.0),
                accepted=True,
                reason=str(item.get("gate_reason") or "llm gate1 accepted"),
                discovery_mode="llm_niche_expansion",
            )
        )
    return contracts


def _generate_all_hypotheses(
    niche_id: str,
    modes: list[str],
    seed_data: dict[str, Any],
    min_confidence: float,
    llm_client: Any | None = None,
    cost_tracker: list[float] | None = None,
) -> tuple[list[Any], int]:
    """Generate hypotheses from all active modes for one niche."""
    all_hypotheses: list[Any] = []

    if "adjacent_keyword" in modes:
        try:
            batch = generate_adjacent_keyword_hypotheses(
                niche_id,
                seed_data["seed_keywords"],
                seed_data["existing_kw_texts"],
            )
            all_hypotheses.extend(batch)
        except Exception as exc:
            log.warning("adjacent_keyword generation failed for %s: %s", niche_id, exc)

    if "adjacent_niche" in modes:
        try:
            batch = generate_adjacent_niche_hypotheses(
                niche_id,
                seed_data["seed_keywords"],
                list(NICHE_VALIDATION_CONFIG.keys()),
            )
            all_hypotheses.extend(batch)
        except Exception as exc:
            log.warning("adjacent_niche generation failed for %s: %s", niche_id, exc)

    if "gap_exploit" in modes:
        try:
            batch = generate_gap_exploit_hypotheses(
                niche_id,
                seed_data["gap_signals"],
                seed_data["existing_kw_texts"],
            )
            all_hypotheses.extend(batch)
        except Exception as exc:
            log.warning("gap_exploit generation failed for %s: %s", niche_id, exc)

    if "trend_chase" in modes:
        try:
            batch = generate_trend_chase_hypotheses(
                niche_id,
                seed_data["trend_signals"],
                seed_data["existing_kw_texts"],
            )
            all_hypotheses.extend(batch)
        except Exception as exc:
            log.warning("trend_chase generation failed for %s: %s", niche_id, exc)

    if "llm_niche_expansion" in modes and llm_client is not None:
        tracked_client = _CostTrackingLLMClient(llm_client)
        try:
            # enable_relevance_gates=True is required here (not tied to the separate
            # discovery.enable_relevance_gates config key, which only gates the unwired
            # DiscoveryOrchestrator legacy path): the ungated dict shape has no
            # specificity_score/buyer/deliverable at all, which _adapt_llm_hypotheses
            # needs to build a usable HypothesisContract.
            raw = asyncio.run(
                generate_niche_hypotheses(
                    niche_id,
                    seed_data["existing_kw_texts"],
                    tracked_client,
                    None,
                    enable_relevance_gates=True,
                )
            )
            all_hypotheses.extend(_adapt_llm_hypotheses(raw, niche_id))
        except Exception as exc:
            log.warning("llm_niche_expansion generation failed for %s: %s", niche_id, exc)
        finally:
            # Codex P2 (PR #181): the provider call may have already incurred real
            # cost even if parsing/adapting the response raises afterward - always
            # record what the proxy actually observed, not just on the happy path,
            # so max_cost_per_run gating and DiscoveryCycleLog.total_cost_usd stay
            # accurate for malformed-response cases too.
            if cost_tracker is not None:
                cost_tracker.append(tracked_client.cost_usd)

    passing = [
        hypothesis
        for hypothesis in all_hypotheses
        if getattr(hypothesis, "accepted", False)
        and (getattr(hypothesis, "specificity_score", 0.0) or 0.0) >= min_confidence
    ]
    gated = len(all_hypotheses) - len(passing)
    return all_hypotheses, gated


def run_discovery_cycle(
    db: Any,
    run_id: str | None = None,
    config: dict[str, Any] | None = None,
    llm_client: Any | None = None,
) -> Any:
    """Execute one complete autonomous discovery cycle."""
    if run_id is None:
        run_id = f"discovery-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"

    discovery_config = (config or {}).get("discovery", {})
    min_confidence = discovery_config.get("min_hypothesis_confidence", DEFAULT_MIN_CONFIDENCE)
    max_hypotheses = discovery_config.get("max_hypotheses_per_run", DEFAULT_MAX_HYPOTHESES)
    run_number = discovery_config.get("run_number")
    max_cost_per_run = discovery_config.get("max_cost_per_run")

    try:
        evaluate_discovery_results(run_id, db)
    except Exception as exc:
        log.warning("evaluate_discovery_results failed (non-fatal): %s", exc)

    try:
        feedback_dict = build_feedback_summary(db)
    except Exception as exc:
        log.warning("build_feedback_summary failed (non-fatal): %s", exc)
        feedback_dict = {"total_hypotheses": 0, "note": "feedback unavailable"}

    pending_count = len(get_pending_discovery_keywords(db))
    modes = _select_modes(config=config, run_number=run_number)
    all_hypotheses: list[Any] = []
    total_gated = 0
    total_llm_cost_usd = 0.0

    if pending_count <= (max_hypotheses * 3):
        for niche_id in NICHE_VALIDATION_CONFIG.keys():
            seed_data = _build_seed_data(niche_id, db, modes)
            # Codex P2 (PR #181): every generator (rule-based and llm_niche_expansion
            # alike) stamps the validation slug (e.g. "python_automation") onto
            # HypothesisContract.niche_id, but Keyword.niche_id is an integer FK to
            # niches.id - insert_discovery_keyword() would pass the slug straight
            # into the Keyword constructor and fail at flush. Resolve the real PK
            # once per niche up front and overwrite it on every hypothesis from that
            # niche before it reaches process_accepted_hypotheses(); leave it as the
            # slug (existing behavior) when the niche row can't be resolved, e.g. in
            # tests against a mocked/empty DB.
            niche_pk = _resolve_niche_pk(db, niche_id)
            niche_llm_client = llm_client
            if niche_llm_client is not None and niche_pk is None:
                # Round 6: any llm_niche_expansion candidate for a niche that can't
                # be resolved to a real row would carry the unresolvable slug and
                # could never be persisted - skip the paid call entirely rather than
                # spend on output that gets silently dropped.
                niche_llm_client = None
            # Budget gate (Codex P2, PR #181): stop spending on llm_niche_expansion
            # once the accumulated cost reaches discovery.max_cost_per_run, but keep
            # running the free rule-based generators for the remaining niches.
            if (
                niche_llm_client is not None
                and max_cost_per_run is not None
                and total_llm_cost_usd >= float(max_cost_per_run)
            ):
                niche_llm_client = None
            cost_tracker: list[float] = []
            niche_hypotheses, niche_gated = _generate_all_hypotheses(
                niche_id=niche_id,
                modes=modes,
                seed_data=seed_data,
                min_confidence=min_confidence,
                llm_client=niche_llm_client,
                cost_tracker=cost_tracker,
            )
            total_llm_cost_usd += sum(cost_tracker)
            if niche_pk is not None:
                for hypothesis in niche_hypotheses:
                    hypothesis.niche_id = niche_pk
            all_hypotheses.extend(niche_hypotheses)
            total_gated += niche_gated
    else:
        log.info(
            "Skipping generation due to pending backlog: pending=%s max=%s",
            pending_count,
            max_hypotheses,
        )

    total_generated = len(all_hypotheses)
    accepted = [
        hypothesis
        for hypothesis in all_hypotheses
        if getattr(hypothesis, "accepted", False)
        and (getattr(hypothesis, "specificity_score", 0.0) or 0.0) >= min_confidence
    ][:max_hypotheses]
    total_gated = total_generated - len(accepted)

    try:
        insert_result = process_accepted_hypotheses(accepted, run_id, db)
    except Exception as exc:
        log.error("process_accepted_hypotheses failed: %s", exc)
        insert_result = {"inserted": 0, "skipped": 0, "run_id": run_id, "keyword_ids": []}

    cycle_log = DiscoveryCycleLog(
        run_id=run_id,
        modes_run=json.dumps(modes),
        hypotheses_generated=total_generated,
        hypotheses_gated=total_gated,
        hypotheses_accepted=insert_result["inserted"],
        total_cost_usd=round(total_llm_cost_usd, 6),
        feedback_summary=json.dumps(feedback_dict),
        cycle_at=datetime.utcnow(),
    )
    db.add(cycle_log)
    db.commit()
    return cycle_log


__all__ = [
    "DEFAULT_MAX_HYPOTHESES",
    "DEFAULT_MIN_CONFIDENCE",
    "_BASE_MODES",
    "_CostTrackingLLMClient",
    "_adapt_llm_hypotheses",
    "_build_seed_data",
    "_generate_all_hypotheses",
    "_select_modes",
    "run_discovery_cycle",
]
