"""Stage 12 review-signal extraction and complaint analysis."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.models.gig import Gig
from src.models.market import Keyword, write_review_analysis
from src.models.niche import Niche
from src.models.search_result import SearchResult

_TOP_GIGS_PER_KEYWORD = 10
_RED_FLAG_PATTERNS: dict[str, tuple[str, ...]] = {
    "late_delivery": (
        "late",
        "overdue",
        "missed deadline",
        "took longer",
        "delayed",
    ),
    "revision_dispute": (
        "refused",
        "wouldn't fix",
        "extra charge",
        "revision",
    ),
    "scope_creep": (
        "charged more",
        "added cost",
        "hidden fee",
        "bait and switch",
    ),
    "quality_mismatch": (
        "not what i expected",
        "poor quality",
        "unusable",
        "misleading",
    ),
    "communication_failure": (
        "ghosted",
        "didn't respond",
        "hard to reach",
        "ignored",
    ),
}


def _is_session(db: Any) -> bool:
    return isinstance(db, Session)


def _resolve_niche_pk(niche_id: str, db: Any) -> int | None:
    if niche_id.isdigit():
        return int(niche_id)
    if not _is_session(db):
        return None
    row = db.query(Niche).filter(Niche.slug == niche_id).one_or_none()
    return None if row is None else int(row.id)


def _safe_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        normalized = value.strip().replace(",", "")
        if not normalized:
            return None
        try:
            return int(float(normalized))
        except ValueError:
            return None
    return None


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        normalized = value.strip().replace(",", "")
        if not normalized:
            return None
        try:
            return float(normalized)
        except ValueError:
            return None
    return None


def _extract_review_texts(review_snippets: Any) -> list[str]:
    if not isinstance(review_snippets, list):
        return []
    texts: list[str] = []
    for snippet in review_snippets:
        if not isinstance(snippet, dict):
            continue
        snippet_text = snippet.get("snippet") or snippet.get("text") or snippet.get("review_text")
        if isinstance(snippet_text, str) and snippet_text.strip():
            texts.append(snippet_text.strip())
    return texts


def _recent_review_count(review_snippets: Any) -> int:
    if not isinstance(review_snippets, list):
        return 0
    recent_markers = ("today", "yesterday", "hour", "day", "week")
    count = 0
    for snippet in review_snippets:
        if not isinstance(snippet, dict):
            continue
        raw_date = snippet.get("date") or snippet.get("review_date_text")
        if not isinstance(raw_date, str):
            continue
        normalized = raw_date.strip().lower()
        if any(marker in normalized for marker in recent_markers):
            count += 1
    return count


def load_review_data_for_niche(niche_id: str, run_id: str, db: Any) -> list[dict[str, Any]]:
    """Load run-scoped top-10 gigs with review payloads for one niche."""
    if not _is_session(db):
        return []

    niche_pk = _resolve_niche_pk(niche_id, db)
    if niche_pk is None:
        return []

    rows = (
        db.query(
            Gig.gig_url.label("gig_url"),
            Gig.keyword_id.label("keyword_id"),
            SearchResult.rank.label("search_rank"),
            Gig.review_count_exact.label("review_count_exact"),
            Gig.review_count.label("review_count"),
            Gig.rating_exact.label("rating_exact"),
            Gig.avg_rating.label("avg_rating"),
            Gig.review_snippets.label("review_snippets"),
        )
        .join(Keyword, Keyword.id == Gig.keyword_id)
        .join(
            SearchResult,
            and_(
                SearchResult.gig_id == Gig.id,
                SearchResult.keyword_id == Gig.keyword_id,
                SearchResult.run_id == run_id,
            ),
        )
        .filter(
            Keyword.niche_id == niche_pk,
            SearchResult.rank <= _TOP_GIGS_PER_KEYWORD,
        )
        .order_by(
            Keyword.id.asc(),
            SearchResult.rank.asc(),
            Gig.id.asc(),
        )
        .all()
    )

    if not rows:
        return []

    records: list[dict[str, Any]] = []
    keyword_counts: dict[int, int] = {}
    seen_per_keyword: dict[int, set[str]] = {}
    for row in rows:
        if row.keyword_id is None:
            continue
        keyword_id = int(row.keyword_id)
        gig_url = str(row.gig_url)
        seen = seen_per_keyword.setdefault(keyword_id, set())
        if gig_url in seen:
            continue
        if keyword_counts.get(keyword_id, 0) >= _TOP_GIGS_PER_KEYWORD:
            continue
        seen.add(gig_url)
        keyword_counts[keyword_id] = keyword_counts.get(keyword_id, 0) + 1
        records.append(
            {
                "gig_url": gig_url,
                "keyword_id": keyword_id,
                "search_rank": row.search_rank,
                "review_count": row.review_count_exact
                if row.review_count_exact is not None
                else row.review_count,
                "avg_rating": row.rating_exact if row.rating_exact is not None else row.avg_rating,
                "review_snippets": row.review_snippets,
            }
        )
    return records


def extract_review_signals(gig_row: dict[str, Any]) -> dict[str, float | int | None]:
    """Extract review-count, average-rating, and review-velocity signals for one gig."""
    review_count = _safe_int(gig_row.get("review_count")) or 0
    avg_rating = _safe_float(gig_row.get("avg_rating"))
    review_snippets = gig_row.get("review_snippets")
    recent_reviews = _recent_review_count(review_snippets)
    review_velocity = (float(recent_reviews) / float(review_count)) if review_count > 0 else 0.0
    return {
        "review_count": review_count,
        "avg_rating": avg_rating,
        "review_velocity": round(max(0.0, review_velocity), 4),
    }


async def _resolve_maybe_await(value: Any) -> Any:
    if hasattr(value, "__await__"):
        return await value
    return value


def _complaint_cache_key(niche_id: str, review_texts: list[str]) -> str:
    normalized_texts = sorted(text.strip().lower() for text in review_texts if text.strip())
    digest = hashlib.sha256(json.dumps(normalized_texts, sort_keys=True).encode("utf-8")).hexdigest()
    return f"review_complaints_v1:{niche_id}:{digest}"


def _fallback_complaints(review_texts: list[str]) -> list[str]:
    if not review_texts:
        return []
    joined = " ".join(review_texts).lower()
    matches: list[str] = []
    for flag_name, patterns in _RED_FLAG_PATTERNS.items():
        if any(pattern in joined for pattern in patterns):
            matches.append(flag_name)
    return sorted(matches)


def _parse_complaint_payload(payload: Any) -> list[str]:
    if isinstance(payload, list):
        return sorted(
            {
                str(item).strip().lower().replace(" ", "_")
                for item in payload
                if isinstance(item, str) and item.strip()
            }
        )
    if isinstance(payload, dict):
        raw = payload.get("complaints")
        if isinstance(raw, list):
            return _parse_complaint_payload(raw)
    if isinstance(payload, str):
        stripped = payload.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = [item.strip() for item in stripped.split(",") if item.strip()]
        return _parse_complaint_payload(parsed)
    return []


async def detect_recurring_complaints(
    review_texts: list[str],
    llm_client: Any = None,
    *,
    cache: Any = None,
    niche_id: str = "global",
) -> list[str]:
    """Detect recurring review complaints with optional cached LLM extraction."""
    normalized_texts = [text.strip() for text in review_texts if isinstance(text, str) and text.strip()]
    if not normalized_texts:
        return []
    if llm_client is None:
        return []

    cache_key = _complaint_cache_key(niche_id=niche_id, review_texts=normalized_texts)
    if cache is not None and hasattr(cache, "get"):
        try:
            cached_payload = await _resolve_maybe_await(cache.get(cache_key))
            cached_complaints = _parse_complaint_payload(cached_payload)
            if cached_complaints:
                return cached_complaints
        except Exception:
            pass

    prompt = (
        "Extract recurring buyer complaint themes from these Fiverr reviews. "
        "Return JSON with a `complaints` array of concise snake_case strings. Reviews:\n- "
        + "\n- ".join(normalized_texts[:25])
    )
    try:
        try:
            completion = llm_client.complete(
                prompt=prompt,
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
            )
        except TypeError:
            completion = llm_client.complete(prompt=prompt, model="gpt-4o-mini")
        response = await _resolve_maybe_await(completion)
        response_text = response if isinstance(response, str) else getattr(response, "text", str(response))
        complaints = _parse_complaint_payload(response_text)
        if not complaints:
            complaints = _fallback_complaints(normalized_texts)
    except Exception:
        complaints = _fallback_complaints(normalized_texts)

    if cache is not None and hasattr(cache, "set"):
        try:
            await _resolve_maybe_await(cache.set(cache_key, {"complaints": complaints}))
        except Exception:
            pass
    return complaints


async def run_review_analysis_for_niche(
    niche_id: str,
    run_id: str,
    db: Any,
    config: dict[str, Any],
    llm_client: Any = None,
) -> dict[str, Any]:
    """Run Stage 12 review analysis for one niche."""
    cache = config.get("cache") if isinstance(config, dict) else None
    rows = load_review_data_for_niche(niche_id=niche_id, run_id=run_id, db=db)
    if not rows:
        return {
            "niche_id": niche_id,
            "run_id": run_id,
            "analyzed": False,
            "reason": "no_review_data",
            "gigs_analyzed": 0,
        }

    for row in rows:
        signals = extract_review_signals(row)
        review_texts = _extract_review_texts(row.get("review_snippets"))
        complaints = await detect_recurring_complaints(
            review_texts=review_texts,
            llm_client=llm_client,
            cache=cache,
            niche_id=niche_id,
        )
        review_count = _safe_int(signals.get("review_count")) or 0
        avg_rating = _safe_float(signals.get("avg_rating"))
        review_velocity = _safe_float(signals.get("review_velocity")) or 0.0
        sentiment_score = None if avg_rating is None else round(max(0.0, min(10.0, avg_rating * 2.0)), 2)
        write_review_analysis(
            gig_url=str(row["gig_url"]),
            niche_id=niche_id,
            run_id=run_id,
            review_count=review_count,
            avg_rating=avg_rating,
            review_velocity=review_velocity,
            sentiment_score=sentiment_score,
            recurring_complaints=complaints,
            db=db,
            commit=False,
        )

    if _is_session(db):
        db.commit()

    return {
        "niche_id": niche_id,
        "run_id": run_id,
        "analyzed": True,
        "gigs_analyzed": len(rows),
    }


def _extract_niche_ids(config: dict[str, Any]) -> list[str]:
    niches = config.get("niches", []) if isinstance(config, dict) else []
    extracted: list[str] = []
    if not isinstance(niches, list):
        return extracted
    for niche in niches:
        if not isinstance(niche, dict):
            continue
        if niche.get("is_active", True) is False:
            continue
        niche_id = niche.get("niche_id")
        if isinstance(niche_id, str) and niche_id.strip():
            extracted.append(niche_id.strip())
    return extracted


async def run_review_analysis_for_all_niches(
    run_id: str,
    db: Any,
    config: dict[str, Any],
    llm_client: Any = None,
) -> dict[str, Any]:
    """Run Stage 12 review analysis across all active niches."""
    results: list[dict[str, Any]] = []
    for niche_id in _extract_niche_ids(config):
        results.append(
            await run_review_analysis_for_niche(
                niche_id=niche_id,
                run_id=run_id,
                db=db,
                config=config,
                llm_client=llm_client,
            )
        )

    analyzed_count = sum(1 for result in results if result.get("analyzed") is True)
    return {
        "run_id": run_id,
        "niches_processed": len(results),
        "niches_analyzed": analyzed_count,
        "results": results,
    }

