"""YouTube count workflow — Stage 6c."""
from __future__ import annotations

import inspect
import logging
import re
from types import ModuleType
from typing import Any
from urllib.parse import quote_plus

import httpx

from src.collection import external_signals as _mod
from src.models import Keyword
from src.models.external_signal import ExternalSignal, write_external_signal

logger = logging.getLogger(__name__)

SIGNAL_YOUTUBE_COUNT = ExternalSignal.SIGNAL_YOUTUBE_COUNT

_RESULT_COUNT_PATTERNS = (
    re.compile(r"About\s+([\d,]+)\s+results", re.IGNORECASE),
    re.compile(r"([\d,]+)\s+results", re.IGNORECASE),
    re.compile(r'"resultCount"\s*:\s*"([\d,]+)"', re.IGNORECASE),
)


def build_youtube_search_url(seed: str) -> str:
    """Build the public YouTube search URL for a seed keyword."""
    return f"https://www.youtube.com/results?search_query={quote_plus(seed)}"


def parse_youtube_result_count(html: str) -> int | None:
    """Extract result count from initial YouTube HTML payload."""
    for pattern in _RESULT_COUNT_PATTERNS:
        match = pattern.search(html)
        if match is None:
            continue
        try:
            return int(match.group(1).replace(",", "").strip())
        except ValueError:
            continue
    return None


async def _safe_pacing_wait(pacing_manager: Any, pacing_key: str) -> None:
    wait_fn = getattr(pacing_manager, "wait", None)
    if wait_fn is None:
        return
    maybe = wait_fn(pacing_key, dry_run=False)
    if inspect.isawaitable(maybe):
        await maybe


async def _fetch_youtube_count(seed: str, pacing_manager: Any) -> int | None:
    """Fetch and parse YouTube search result count for one seed."""
    cleaned_seed = seed.strip()
    if not cleaned_seed:
        return None

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            response = await client.get(
                build_youtube_search_url(cleaned_seed),
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/123.0.0.0 Safari/537.36"
                    )
                },
            )
            response.raise_for_status()
            count = parse_youtube_result_count(response.text)
            if count is None:
                logger.warning("YouTube count parse missing for seed='%s'.", cleaned_seed)
            return count
    except Exception as exc:  # noqa: BLE001 - fail-soft per workflow spec
        logger.warning("YouTube count fetch failed for seed='%s': %s", cleaned_seed, exc)
        return None
    finally:
        try:
            await _safe_pacing_wait(pacing_manager, "youtube")
        except Exception:  # noqa: BLE001 - pacing must not fail the workflow
            logger.debug("YouTube pacing wait failed.", exc_info=True)


def _resolve_niche_pk(niche_id: str, db: Any) -> int | None:
    from src.models.niche import Niche

    if niche_id.isdigit():
        return int(niche_id)
    row = db.query(Niche).filter(Niche.slug == niche_id).first()
    return int(row.id) if row is not None else None


def _resolve_keyword_id(keyword_text: str, niche_id: str, db: Any) -> int | None:
    """Resolve keyword ID scoped to niche to avoid cross-niche signal writes."""
    from sqlalchemy.orm import Session

    if not isinstance(db, Session):
        return None

    niche_pk = _resolve_niche_pk(niche_id, db)
    if niche_pk is None:
        return None

    cleaned = keyword_text.strip()
    if not cleaned:
        return None
    normalized = cleaned.lower()
    row = (
        db.query(Keyword)
        .filter(
            Keyword.niche_id == niche_pk,
            (Keyword.keyword == cleaned) | (Keyword.normalized_keyword == normalized),
        )
        .first()
    )
    return int(row.id) if row is not None else None


async def run_youtube_count_collection(
    niche_id: str,
    seed_keywords: list[str],
    run_id: str,
    db: Any,
    pacing_manager: Any,
    checkpoint_manager: Any | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Stage 6c: collect YouTube result-count signals per seed keyword."""
    cleaned_seeds = [seed.strip() for seed in seed_keywords if isinstance(seed, str) and seed.strip()]
    if dry_run:
        return {
            "niche_id": niche_id,
            "seeds_processed": 0,
            "signals_written": 0,
            "dry_run": True,
        }

    signals_written = 0
    for seed in cleaned_seeds:
        count = await _fetch_youtube_count(seed, pacing_manager)
        keyword_id = _resolve_keyword_id(seed, niche_id, db)
        if keyword_id is None:
            continue
        write_external_signal(
            keyword_id=keyword_id,
            signal_type=SIGNAL_YOUTUBE_COUNT,
            signal_value=float(count) if count is not None else None,
            signal_json={
                "seed_keyword": seed,
                "youtube_result_count": count,
                "source_url": build_youtube_search_url(seed),
            },
            run_id=run_id,
            collection_method="youtube_search_html",
            db=db,
        )
        signals_written += 1

    if checkpoint_manager is not None:
        write_fn = getattr(checkpoint_manager, "write", None)
        if callable(write_fn):
            try:
                payload = {
                    "niche_id": niche_id,
                    "run_id": run_id,
                    "seeds_processed": len(cleaned_seeds),
                    "signals_written": signals_written,
                }
                maybe = write_fn("stage06_youtube", niche_id, payload)
                if inspect.isawaitable(maybe):
                    await maybe
            except Exception:  # noqa: BLE001 - checkpoint write is non-blocking
                logger.warning(
                    "Failed to write YouTube checkpoint for run '%s' and niche '%s'.",
                    run_id,
                    niche_id,
                    exc_info=True,
                )

    return {
        "niche_id": niche_id,
        "seeds_processed": len(cleaned_seeds),
        "signals_written": signals_written,
        "dry_run": False,
    }


class YoutubeCountWorkflow:
    """Collects YouTube result-count demand signals per niche."""

    def run(self, *args: Any, **kwargs: Any) -> ModuleType:
        _ = (args, kwargs)
        return _mod
