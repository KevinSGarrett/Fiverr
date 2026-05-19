"""Google Trends workflow — Stage 6a (Story 2.11)."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

from src.collection import external_signals as _mod
from src.models import Keyword
from src.models.external_signal import ExternalSignal, write_external_signal

try:
    import importlib

    _pytrends_request = importlib.import_module("pytrends.request")
    _TrendReq = getattr(_pytrends_request, "TrendReq", None)
except Exception:  # pragma: no cover - dependency guard for environments without pytrends installed
    _TrendReq = None

logger = logging.getLogger(__name__)

SIGNAL_GOOGLE_TRENDS = ExternalSignal.SIGNAL_GOOGLE_TRENDS
TrendReq = _TrendReq


async def run_google_trends_collection(
    niche_id: str,
    keywords: list[str],
    run_id: str,
    db: Any,
    pacing_manager: Any,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Stage 6: Google Trends collection per niche.

    Spec: COLLECTION_WORKFLOWS.md Workflow 6.
    `dry_run=True` returns a smoke-safe stub and avoids all pytrends calls.
    """
    if dry_run:
        return {
            "niche_id": niche_id,
            "keywords_processed": 0,
            "signals_written": 0,
            "rate_limited": False,
            "rate_limit_count": 0,
            "dead_lettered_batches": 0,
            "dry_run": True,
        }

    if TrendReq is None:
        raise RuntimeError("pytrends is not installed. Add dependency `pytrends>=4.9,<5.0`.")

    batches = [keywords[idx : idx + 5] for idx in range(0, len(keywords), 5)]
    signals_written = 0
    rate_limited = False
    rate_limit_count = 0
    dead_lettered_batches = 0
    stop_processing = False

    for batch_index, batch in enumerate(batches):

        processed_batch = False
        for attempt in range(3):
            try:
                pytrends = TrendReq(hl="en-US", tz=360)
                pytrends.build_payload(kw_list=batch, timeframe="today 12-m", geo="")
                dataframe = pytrends.interest_over_time()
                related_queries = _safe_related_payload(pytrends.related_queries())
                related_topics = _safe_related_payload(pytrends.related_topics())

                if not _is_dataframe_like(dataframe):
                    dataframe = None

                for keyword in batch:
                    keyword_id = _resolve_keyword_id(keyword, db)
                    if keyword_id is None:
                        continue

                    if dataframe is None or bool(dataframe.empty) or keyword not in dataframe.columns:
                        write_external_signal(
                            keyword_id=keyword_id,
                            signal_type=SIGNAL_GOOGLE_TRENDS,
                            signal_value=0.0,
                            signal_json={
                                "trends_12mo_score": 0.0,
                                "trends_3mo_score": 0.0,
                                "trends_12mo_avg": 0.0,
                                "trends_3mo_avg": 0.0,
                                "google_trends_slope": 0.0,
                                "trend_direction": "FLAT",
                                "google_trends_12mo_series": [],
                                "google_trends_3mo_series": [],
                                "trends_related_queries": _extract_related_for_keyword(
                                    related_queries,
                                    keyword,
                                    top_limit=10,
                                ),
                                "trends_related_topics": _extract_related_for_keyword(
                                    related_topics,
                                    keyword,
                                    top_limit=5,
                                ),
                                "no_data": True,
                            },
                            run_id=run_id,
                            collection_method="pytrends_api",
                            db=db,
                        )
                        signals_written += 1
                        continue

                    series = dataframe[keyword].dropna()
                    weekly_scores = [float(value) for value in series.tolist()]
                    trends_12mo_score = float(series.mean()) if len(series) > 0 else 0.0
                    trends_3mo_series = weekly_scores[-13:] if len(weekly_scores) >= 13 else weekly_scores
                    trends_3mo_score = (
                        (sum(trends_3mo_series) / len(trends_3mo_series))
                        if len(trends_3mo_series) > 0
                        else trends_12mo_score
                    )
                    slope = _calculate_slope(weekly_scores)
                    trend_direction = _classify_trend_direction(slope)

                    write_external_signal(
                        keyword_id=keyword_id,
                        signal_type=SIGNAL_GOOGLE_TRENDS,
                        signal_value=trends_12mo_score,
                        signal_json={
                            "trends_12mo_score": trends_12mo_score,
                            "trends_3mo_score": trends_3mo_score,
                            "trends_12mo_avg": trends_12mo_score,
                            "trends_3mo_avg": trends_3mo_score,
                            "google_trends_slope": slope,
                            "trend_direction": trend_direction,
                            "google_trends_12mo_series": weekly_scores[-52:],
                            "google_trends_3mo_series": trends_3mo_series,
                            "trends_related_queries": _extract_related_for_keyword(
                                related_queries,
                                keyword,
                                top_limit=10,
                            ),
                            "trends_related_topics": _extract_related_for_keyword(
                                related_topics,
                                keyword,
                                top_limit=5,
                            ),
                            "no_data": False,
                        },
                        run_id=run_id,
                        collection_method="pytrends_api",
                        db=db,
                    )
                    signals_written += 1

                await _safe_pacing_wait(pacing_manager, "google_trends", dry_run=False)
                _write_trends_checkpoint(
                    run_id=run_id,
                    niche_id=niche_id,
                    batch_index=batch_index,
                    total_batches=len(batches),
                    keywords_total=len(keywords),
                    keywords_complete=min((batch_index + 1) * 5, len(keywords)),
                    last_keyword=batch[-1],
                    signals_written=signals_written,
                    rate_limit_count=rate_limit_count,
                )
                processed_batch = True
                break
            except Exception as exc:  # noqa: BLE001 - workflow is intentionally fail-soft per spec
                if _is_rate_limit_error(exc):
                    rate_limited = True
                    rate_limit_count += 1
                    logger.warning(
                        "Google Trends 429 encountered for niche '%s' (count=%s).",
                        niche_id,
                        rate_limit_count,
                    )
                    if rate_limit_count >= 3:
                        dead_lettered_batches = len(batches) - batch_index
                        stop_processing = True
                        logger.error(
                            "Google Trends 429 threshold reached for niche '%s'; stopping remaining batches.",
                            niche_id,
                        )
                        break
                    pause_minutes = _resolve_rate_limit_pause_minutes(pacing_manager)
                    _increase_google_trends_delay(pacing_manager)
                    await asyncio.sleep(float(pause_minutes) * 60.0)
                    continue
                if _is_timeout_error(exc) and attempt < 2:
                    await asyncio.sleep(15.0)
                    continue
                logger.warning(
                    "Google Trends batch failed for niche '%s' (batch=%s, attempt=%s): %s",
                    niche_id,
                    batch_index + 1,
                    attempt + 1,
                    exc,
                )
                break

        if not processed_batch and stop_processing:
            break

    return {
        "niche_id": niche_id,
        "keywords_processed": len(keywords),
        "signals_written": signals_written,
        "rate_limited": rate_limited,
        "rate_limit_count": rate_limit_count,
        "dead_lettered_batches": dead_lettered_batches,
        "dry_run": False,
    }


async def _safe_pacing_wait(pacing_manager: Any, pacing_key: str, *, dry_run: bool) -> None:
    wait_fn = getattr(pacing_manager, "wait", None)
    if wait_fn is None:
        return
    await wait_fn(pacing_key, dry_run=dry_run)


def _resolve_rate_limit_pause_minutes(pacing_manager: Any) -> int:
    config_getter = getattr(pacing_manager, "get_delay_config", None)
    if callable(config_getter):
        cfg = config_getter("google_trends")
        if isinstance(cfg, dict):
            raw_value = cfg.get("rate_limit_pause_minutes")
            if isinstance(raw_value, int | float) and raw_value > 0:
                return int(raw_value)
    pacing_map = getattr(pacing_manager, "pacing", None)
    if isinstance(pacing_map, dict):
        source_cfg = pacing_map.get("google_trends")
        if isinstance(source_cfg, dict):
            raw_value = source_cfg.get("rate_limit_pause_minutes")
            if isinstance(raw_value, int | float) and raw_value > 0:
                return int(raw_value)
    return 10


def _increase_google_trends_delay(pacing_manager: Any) -> None:
    pacing_map = getattr(pacing_manager, "pacing", None)
    if not isinstance(pacing_map, dict):
        return
    source_cfg = pacing_map.get("google_trends")
    if not isinstance(source_cfg, dict):
        source_cfg = {}
        pacing_map["google_trends"] = source_cfg
    current_delay = source_cfg.get("base_delay_seconds", 10.0)
    if not isinstance(current_delay, int | float):
        current_delay = 10.0
    source_cfg["base_delay_seconds"] = float(current_delay) * 1.5


def _is_rate_limit_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "429" in text or "too many requests" in text or "toomanyrequest" in text


def _is_timeout_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "timeout" in text or "timed out" in text


def _calculate_slope(values: list[float]) -> float:
    if len(values) < 3:
        return 0.0
    n = len(values)
    x_sum = sum(range(n))
    y_sum = sum(values)
    x2_sum = sum(index * index for index in range(n))
    xy_sum = sum(index * value for index, value in enumerate(values))
    denominator = (n * x2_sum) - (x_sum * x_sum)
    return ((n * xy_sum) - (x_sum * y_sum)) / denominator


def _is_dataframe_like(value: Any) -> bool:
    return hasattr(value, "empty") and hasattr(value, "columns") and hasattr(value, "__getitem__")


def _classify_trend_direction(slope: float) -> str:
    if slope > 0.3:
        return "RISING"
    if slope < -0.3:
        return "DECLINING"
    return "FLAT"


def _safe_related_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    return {}


def _extract_related_for_keyword(
    payload: dict[str, Any],
    keyword: str,
    *,
    top_limit: int,
) -> list[dict[str, Any]]:
    keyword_payload = payload.get(keyword, {})
    if not isinstance(keyword_payload, dict):
        return []

    top_records = _records_from_frame(keyword_payload.get("top"), limit=top_limit)
    rising_records = _records_from_frame(keyword_payload.get("rising"), limit=top_limit)
    return top_records + rising_records


def _records_from_frame(frame: Any, *, limit: int) -> list[dict[str, Any]]:
    if frame is None:
        return []
    if hasattr(frame, "head") and hasattr(frame, "to_dict"):
        try:
            trimmed = frame.head(limit)
            if hasattr(trimmed, "to_dict"):
                return list(trimmed.to_dict(orient="records"))
        except Exception:  # noqa: BLE001 - best-effort extraction only
            return []
    if isinstance(frame, list):
        return [item for item in frame[:limit] if isinstance(item, dict)]
    return []


def _write_trends_checkpoint(
    *,
    run_id: str,
    niche_id: str,
    batch_index: int,
    total_batches: int,
    keywords_total: int,
    keywords_complete: int,
    last_keyword: str,
    signals_written: int,
    rate_limit_count: int,
) -> None:
    checkpoint_dir = Path("data") / "checkpoints" / run_id
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint_dir / f"stage06_trends_{niche_id}.json"
    temp_path = checkpoint_path.with_suffix(".tmp")

    payload = {
        "run_id": run_id,
        "stage": 6,
        "stage_name": "GOOGLE_TRENDS_COLLECTION",
        "niche_id": niche_id,
        "batch_index": batch_index + 1,
        "batches_total": total_batches,
        "records_complete": keywords_complete,
        "records_total": keywords_total,
        "last_record_id": last_keyword,
        "signals_written": signals_written,
        "rate_limit_count": rate_limit_count,
        "checkpoint_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(checkpoint_path)


def _resolve_keyword_id(keyword_text: str, db: Any) -> int | None:
    """Look up `keywords.id` by keyword text. Returns None if not found."""
    from sqlalchemy.orm import Session

    if not isinstance(db, Session):
        return None

    cleaned = keyword_text.strip()
    if not cleaned:
        return None
    normalized = cleaned.lower()
    row = (
        db.query(Keyword)
        .filter(
            (Keyword.keyword == cleaned)
            | (Keyword.normalized_keyword == normalized)
        )
        .first()
    )
    return int(row.id) if row is not None else None


class GoogleTrendsWorkflow:
    """Fetches Google Trends interest-over-time data for each keyword."""

    def run(self, *args: Any, **kwargs: Any) -> ModuleType:
        return _mod
