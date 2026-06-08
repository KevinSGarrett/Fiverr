"""Discovery scoring feedback module for S7.6.

This module evaluates scored discovery keywords, persists outcome rows, and
builds compact feedback summaries that can be passed into the next cycle.
"""

from __future__ import annotations

import importlib
import logging
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from src.models import DiscoveryCycleLog, DiscoveryOutcome, Keyword
from src.models.keyword_score import get_latest_keyword_score

log = logging.getLogger(__name__)

GOLD_THRESHOLD = 85.0
HIT_THRESHOLD = 60.0
MISS_THRESHOLD = 40.0
AUTO_RETIRE_THRESHOLD = 30.0

DISCOVERY_MODES = ("adjacent_keyword", "adjacent_niche", "gap_exploit", "trend_chase")


def evaluate_discovery_results(run_id: str, db: Any) -> dict[str, int]:
    """Evaluate scored, unevaluated discovery keywords.

    Idempotency is enforced via `Keyword.discovery_evaluated`.
    """
    keywords = (
        db.query(Keyword)
        .filter(
            Keyword.is_discovery.is_(True),
            Keyword.discovery_evaluated.is_(False),
        )
        .all()
    )

    summary = {"total": 0, "gold": 0, "hits": 0, "misses": 0, "retirements": 0, "monitored": 0}

    for keyword in keywords:
        final_score = _get_keyword_final_score(keyword, db)
        if final_score is None:
            continue

        # Defensive duplicate guard in addition to discovery_evaluated.
        already_written = (
            db.query(DiscoveryOutcome)
            .filter(DiscoveryOutcome.keyword_id == keyword.id)
            .order_by(DiscoveryOutcome.id.desc())
            .first()
        )
        if already_written is not None:
            keyword.discovery_evaluated = True
            continue

        is_gold = final_score >= GOLD_THRESHOLD
        is_hit = final_score >= HIT_THRESHOLD
        is_miss = final_score < MISS_THRESHOLD
        should_retire = final_score < AUTO_RETIRE_THRESHOLD
        actual_tag = _get_keyword_tag(keyword, db)
        confidence = keyword.hypothesis_confidence or 0.0
        score_delta = final_score - (confidence * 100.0)

        outcome = DiscoveryOutcome(
            run_id=run_id,
            keyword_id=keyword.id,
            keyword_text=_get_keyword_text(keyword),
            niche_id=str(keyword.niche_id),
            discovery_mode=keyword.discovery_mode or "unknown",
            hypothesis_confidence=confidence,
            actual_final_score=float(final_score),
            actual_tag=actual_tag,
            score_delta=score_delta,
            is_gold=is_gold,
            is_hit=is_hit,
            is_miss=is_miss,
            evaluated_at=datetime.now(UTC),
            # Legacy compatibility fields.
            is_invalid=False,
            is_contaminated=False,
            relevance_score=None,
            contamination_reason=None,
        )
        db.add(outcome)

        keyword.discovery_evaluated = True
        if should_retire:
            keyword.is_retired = True
            summary["retirements"] += 1

        if is_gold:
            _fire_gold_alert(keyword, float(final_score), db)
            summary["gold"] += 1
        if is_hit:
            summary["hits"] += 1
        elif is_miss:
            summary["misses"] += 1
        else:
            summary["monitored"] += 1
        summary["total"] += 1

    db.commit()
    return summary


def _get_keyword_final_score(keyword: Keyword, db: Any) -> float | None:
    """Return most recent final score for a keyword."""
    score = get_latest_keyword_score(int(keyword.id), db)
    if score is not None and score.final_score is not None:
        return float(score.final_score)
    return None


def _get_keyword_tag(keyword: Keyword, db: Any) -> str | None:
    """Return latest score tag for a keyword."""
    score = get_latest_keyword_score(int(keyword.id), db)
    if score is not None:
        return score.tag
    return None


def _fire_gold_alert(keyword: Keyword, final_score: float, db: Any) -> None:
    """Best-effort gold alert dispatch with graceful fallback."""
    create_alert: Callable[..., Any] | None = None
    try:
        monitors = importlib.import_module("src.monitoring.monitors")
        create_alert = getattr(monitors, "create_alert", None)
    except Exception:
        create_alert = None

    if create_alert is None:
        try:
            alerts = importlib.import_module("src.alerts")
            create_alert = getattr(alerts, "create_alert", None)
        except Exception:
            log.warning("Gold discovery alert skipped: create_alert not available")
            return

    if create_alert is None:
        log.warning("Gold discovery alert skipped: create_alert not available")
        return

    try:
        create_alert(
            alert_type="NEW_GOLD_DISCOVERY",
            severity="HIGH",
            message=f"Gold discovery: '{_get_keyword_text(keyword)}' scored {final_score:.1f}",
            metadata={
                "keyword_id": keyword.id,
                "keyword_text": _get_keyword_text(keyword),
                "final_score": final_score,
                "discovery_mode": keyword.discovery_mode,
            },
            db=db,
        )
    except Exception as exc:
        log.warning("Gold alert dispatch failed for keyword_id=%s: %s", keyword.id, exc)


def build_feedback_summary(db: Any) -> dict[str, Any]:
    """Build aggregate feedback payload for next-cycle context."""
    # Ignore legacy orchestrator-only rows that never received scored outcome fields.
    outcomes = [o for o in db.query(DiscoveryOutcome).all() if o.actual_final_score is not None]
    if not outcomes:
        return {"total_hypotheses": 0, "note": "No discovery history yet - first cycle"}

    total = len(outcomes)
    gold_hits = sum(1 for o in outcomes if bool(o.is_gold))
    hits = sum(1 for o in outcomes if bool(o.is_hit))
    misses = sum(1 for o in outcomes if bool(o.is_miss))
    avg_score = sum(float(o.actual_final_score or 0.0) for o in outcomes) / total

    mode_stats: dict[str, dict[str, Any]] = {}
    for mode in DISCOVERY_MODES:
        mode_outcomes = [o for o in outcomes if (o.discovery_mode or "unknown") == mode]
        mode_total = len(mode_outcomes)
        if mode_total == 0:
            mode_stats[mode] = {"count": 0, "avg_score": 0.0, "hit_rate": 0.0, "gold_count": 0}
            continue
        mode_hits = sum(1 for o in mode_outcomes if bool(o.is_hit))
        mode_stats[mode] = {
            "count": mode_total,
            "avg_score": round(sum(float(o.actual_final_score or 0.0) for o in mode_outcomes) / mode_total, 1),
            "hit_rate": round(mode_hits / mode_total * 100.0, 1),
            "gold_count": sum(1 for o in mode_outcomes if bool(o.is_gold)),
        }

    non_empty_modes = [(name, stats) for name, stats in mode_stats.items() if stats.get("count", 0) > 0]
    sorted_modes = sorted(non_empty_modes, key=lambda item: item[1]["hit_rate"])
    worst_mode = sorted_modes[0][0] if sorted_modes else None
    best_mode = sorted_modes[-1][0] if sorted_modes else None

    hit_niches = [str(o.niche_id) for o in outcomes if bool(o.is_hit)]
    miss_niches = [str(o.niche_id) for o in outcomes if bool(o.is_miss)]
    top_hit_niches = [{"niche": n, "count": c} for n, c in Counter(hit_niches).most_common(3)]
    top_miss_niches = [{"niche": n, "count": c} for n, c in Counter(miss_niches).most_common(3)]

    return {
        "total_hypotheses": total,
        "gold_hits": gold_hits,
        "hits": hits,
        "misses": misses,
        "hit_rate_pct": round((hits / total) * 100.0, 1),
        "avg_actual_score": round(avg_score, 1),
        "mode_stats": mode_stats,
        "best_mode": best_mode,
        "worst_mode": worst_mode,
        "top_hit_niches": top_hit_niches,
        "top_miss_niches": top_miss_niches,
        "pattern_notes": _generate_pattern_notes(outcomes, mode_stats),
    }


def _generate_pattern_notes(outcomes: list[DiscoveryOutcome], mode_stats: dict[str, dict[str, Any]]) -> str:
    """Build concise, human-readable guidance notes."""
    notes: list[str] = []
    for mode, stats in mode_stats.items():
        hit_rate = float(stats.get("hit_rate", 0.0))
        avg_score = float(stats.get("avg_score", 0.0))
        if stats.get("count", 0) == 0:
            notes.append(f"{mode} has no outcomes yet")
        elif hit_rate >= 40.0:
            notes.append(f"{mode} performs well ({hit_rate:.1f}% hit rate, avg {avg_score:.1f})")
        elif hit_rate < 15.0:
            notes.append(f"{mode} underperforms ({hit_rate:.1f}% hit rate)")

    gold_outcomes = [o for o in outcomes if bool(o.is_gold)]
    if gold_outcomes:
        top_modes = Counter((o.discovery_mode or "unknown") for o in gold_outcomes).most_common(2)
        notes.append("gold discoveries concentrated in " + ", ".join(mode for mode, _ in top_modes))

    if not notes:
        notes.append("Insufficient data for pattern analysis - continue collecting")
    return " | ".join(notes)


def get_discovery_cycle_stats(run_id: str, db: Any) -> dict[str, Any]:
    """Return latest cycle-log row by run_id."""
    row = (
        db.query(DiscoveryCycleLog)
        .filter(DiscoveryCycleLog.run_id == run_id)
        .order_by(DiscoveryCycleLog.id.desc())
        .first()
    )
    if row is None:
        return {"run_id": run_id, "found": False}
    return {
        "run_id": row.run_id,
        "modes_run": row.modes_run,
        "hypotheses_generated": row.hypotheses_generated,
        "hypotheses_accepted": row.hypotheses_accepted,
        "total_cost_usd": row.total_cost_usd,
        "cycle_at": str(row.cycle_at),
        "found": True,
    }


def _get_keyword_text(keyword: Keyword) -> str:
    value = getattr(keyword, "keyword", None) or getattr(keyword, "keyword_text", None) or ""
    return str(value)
