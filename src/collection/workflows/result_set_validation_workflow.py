"""Stage 3.5 result-set relevance validation workflow."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from src.analysis.result_set_validator import get_validation_config, validate_result_set
from src.collection.search_url_builder import SearchStrictness
from src.models import Gig, Keyword, Niche, ResultSetValidation, SearchResult

log = logging.getLogger(__name__)


def _config_enabled(config: Any) -> bool:
    if isinstance(config, dict):
        relevance = config.get("relevance", {})
        return bool(isinstance(relevance, dict) and relevance.get("enable_stage_3_5", False))
    relevance = getattr(config, "relevance", None)
    if relevance is None:
        return False
    return bool(getattr(relevance, "enable_stage_3_5", False))


def _config_thresholds(config: Any) -> tuple[float, float]:
    if isinstance(config, dict):
        relevance = config.get("relevance", {})
        if isinstance(relevance, dict):
            return (
                float(relevance.get("relevance_flag_threshold", 0.35)),
                float(relevance.get("ghost_market_threshold_default", 0.20)),
            )
    relevance = getattr(config, "relevance", None)
    if relevance is None:
        return (0.35, 0.20)
    return (
        float(getattr(relevance, "relevance_flag_threshold", 0.35)),
        float(getattr(relevance, "ghost_market_threshold_default", 0.20)),
    )


def _now() -> datetime:
    return datetime.now(UTC)


def _keywords_for_run_niche(db: Session, run_id: str, niche_id: str | int) -> list[Keyword]:
    query = db.query(Keyword).join(SearchResult, SearchResult.keyword_id == Keyword.id).filter(SearchResult.run_id == run_id)
    if isinstance(niche_id, int):
        query = query.filter(Keyword.niche_id == niche_id)
    else:
        niche_text = str(niche_id).strip()
        if niche_text.isdigit():
            query = query.filter(Keyword.niche_id == int(niche_text))
        else:
            query = query.join(Niche, Niche.id == Keyword.niche_id).filter(Niche.slug == niche_text)
    return query.order_by(Keyword.id.asc()).all()


def _gig_cards_for_keyword(db: Session, keyword_id: int, run_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(SearchResult)
        .filter(SearchResult.keyword_id == keyword_id, SearchResult.run_id == run_id)
        .order_by(SearchResult.collected_at.desc(), SearchResult.id.desc())
        .all()
    )
    cards: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row.gig_cards, list):
            cards.extend([card for card in row.gig_cards if isinstance(card, dict)])
    return cards


def _strictness_for(db: Session, keyword_id: int, run_id: str) -> str | None:
    row = (
        db.query(SearchResult)
        .filter(SearchResult.keyword_id == keyword_id, SearchResult.run_id == run_id)
        .order_by(SearchResult.collected_at.desc(), SearchResult.id.desc())
        .first()
    )
    if row is None:
        return None
    return row.search_strictness_used


def _upsert_rsv(db: Session, keyword_id: int, run_id: str, rs: Any) -> ResultSetValidation:
    rsv = db.query(ResultSetValidation).filter_by(keyword_id=keyword_id, run_id=run_id).first()
    if rsv is None:
        rsv = ResultSetValidation(keyword_id=keyword_id, run_id=run_id)
        db.add(rsv)

    rsv.result_count = rs.total_analyzed
    rsv.relevant_count = rs.relevant_count
    rsv.sponsored_count = rs.sponsored_count
    rsv.result_set_relevance_score = rs.result_set_relevance_score
    rsv.ghost_market_flag = rs.ghost_market_flag
    rsv.category_contamination_flag = rs.category_contamination_flag
    rsv.relevance_deduction = rs.confidence_deduction
    rsv.per_gig_relevance = [
        {
            "gig_url": gig.gig_url,
            "score": gig.relevance_score,
            "flag": gig.relevance_flag,
            "reason": gig.rejection_reason,
            "signals": gig.relevance_signals,
        }
        for gig in rs.gig_results
    ]
    rsv.ghost_evidence = (
        {
            "score": rs.result_set_relevance_score,
            "total": rs.total_analyzed,
            "relevant": rs.relevant_count,
            "warnings": rs.warnings,
        }
        if rs.ghost_market_flag
        else None
    )
    rsv.validation_method = "result_set_validator_v1"
    rsv.search_strictness_used = _strictness_for(db, keyword_id, run_id)
    rsv.used_fallback_strictness = rsv.search_strictness_used not in (None, SearchStrictness.SUBCATEGORY.value)
    rsv.validated_at = _now()
    db.flush()
    return rsv


def _link_search_result(db: Session, keyword_id: int, run_id: str, rsv_id: int) -> None:
    row = db.query(SearchResult).filter_by(keyword_id=keyword_id, run_id=run_id).first()
    if row is not None:
        row.rsv_id = rsv_id


def _normalize_url(url: str) -> str:
    parsed = urlparse((url or "").strip())
    host = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    return f"{host}{path}"


def _write_gig_flags(db: Session, run_id: str, gig_results: list[Any]) -> None:
    by_url = {_normalize_url(result.gig_url): result for result in gig_results if result.gig_url}
    if not by_url:
        return
    for gig in db.query(Gig).filter(Gig.run_id == run_id).all():
        result = by_url.get(_normalize_url(gig.gig_url or ""))
        if result is None:
            continue
        gig.relevance_flag = result.relevance_flag
        gig.relevance_score = result.relevance_score


def run_stage_3_5_validation(
    run_id: str,
    niche_id: str | int,
    db: Any,
    config: Any,
) -> dict[str, Any]:
    if not _config_enabled(config):
        return {"skipped": True}
    if not isinstance(db, Session):
        return {"skipped": True}

    relevance_flag_threshold, ghost_default = _config_thresholds(config)
    stats = {"keywords_validated": 0, "ghost_markets_detected": 0, "contamination_flags": 0}
    keywords = _keywords_for_run_niche(db, run_id=run_id, niche_id=niche_id)

    for keyword in keywords:
        try:
            cards = _gig_cards_for_keyword(db, keyword.id, run_id)
            validation_config = get_validation_config(niche_id)
            validation_config["relevance_flag_threshold"] = relevance_flag_threshold
            validation_config.setdefault("ghost_market_threshold", ghost_default)
            result = validate_result_set(cards, keyword.keyword, niche_id, validation_config)
            rsv = _upsert_rsv(db, keyword.id, run_id, result)
            _link_search_result(db, keyword.id, run_id, rsv.id)
            _write_gig_flags(db, run_id, result.gig_results)

            stats["keywords_validated"] += 1
            stats["ghost_markets_detected"] += int(result.ghost_market_flag)
            stats["contamination_flags"] += int(result.category_contamination_flag)
            if result.ghost_market_flag:
                log.warning(
                    "ghost_market_detected kw=%s score=%.2f signals=%s",
                    keyword.id,
                    result.result_set_relevance_score,
                    result.warnings,
                )
        except Exception as exc:  # noqa: BLE001
            log.warning("stage_3_5 keyword %s failed: %s", keyword.id, exc)
            continue

    db.commit()
    log.info("stage_3_5 run=%s niche=%s stats=%s", run_id, niche_id, stats)
    return stats
