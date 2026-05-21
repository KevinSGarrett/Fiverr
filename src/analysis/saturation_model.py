"""Stage 13 saturation model analysis implementation."""

from __future__ import annotations

import re
from itertools import combinations
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from src.models.market import Keyword, write_saturation_score
from src.models.niche import Niche
from src.models.search_result import SearchResult
from src.models.search_result import get_latest_search_result as _model_get_latest_search_result

TITLE_STOP_WORDS = {
    "i",
    "will",
    "you",
    "your",
    "the",
    "a",
    "an",
    "for",
    "and",
    "or",
    "to",
    "in",
    "of",
    "with",
    "that",
    "this",
    "my",
    "our",
    "create",
    "make",
    "build",
    "write",
    "provide",
    "give",
    "help",
    "professional",
    "high",
    "quality",
    "best",
    "great",
    "amazing",
    "excellent",
    "perfect",
    "top",
}


def tokenize_title(title: str) -> set[str]:
    """Tokenizes a gig title into a set of meaningful words."""
    words = re.findall(r"\b[a-z]+\b", title.lower())
    return {w for w in words if w not in TITLE_STOP_WORDS and len(w) > 2}


def jaccard_similarity(set_a: set[Any], set_b: set[Any]) -> float:
    """Calculates Jaccard similarity between two token sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union


def calculate_title_duplication_rate(
    gig_cards: list[dict[str, Any]],
    similarity_threshold: float = 0.65,
) -> float:
    """
    Calculates the proportion of gig titles that are near-duplicates.

    Returns a float 0.0–1.0:
        0.0 = all titles are unique (low saturation)
        1.0 = all titles are near-identical (high saturation)

    Uses pairwise Jaccard similarity — two titles with similarity >= threshold
    are considered near-duplicates.
    """
    if len(gig_cards) < 2:
        return 0.0

    titles = [card.get("gig_title", "") for card in gig_cards if card.get("gig_title")]
    tokenized = [tokenize_title(title) for title in titles]

    duplicate_pairs: set[int] = set()
    for i, j in combinations(range(len(tokenized)), 2):
        sim = jaccard_similarity(tokenized[i], tokenized[j])
        if sim >= similarity_threshold:
            duplicate_pairs.add(i)
            duplicate_pairs.add(j)

    return len(duplicate_pairs) / max(1, len(titles))


def calculate_price_compression(gig_cards: list[dict[str, Any]], niche_context: dict[str, Any]) -> float:
    """
    Detects price compression in the search results.
    Returns a float 0.0–1.0 (0 = healthy pricing, 1 = severely compressed).

    Compression signals:
    1. Standard deviation of prices is very low (everyone charges the same)
    2. Median price is declining vs. the niche historical median
    3. Large proportion of gigs are clustered at the absolute lowest price tier
    """
    prices = [
        card.get("starting_price", 0)
        for card in gig_cards
        if _safe_float(card.get("starting_price", 0)) is not None and float(card.get("starting_price", 0)) > 0
    ]
    if len(prices) < 5:
        return 0.3  # Not enough data — return moderate default

    prices_arr = np.array(prices, dtype=float)
    current_median = float(np.median(prices_arr))
    current_std = float(np.std(prices_arr))

    # Signal 1: Low price diversity (coefficient of variation < 0.3)
    cv = current_std / max(1, current_median)
    low_diversity_score = max(0.0, 1.0 - (cv / 0.5))  # CV of 0.5 → no compression signal

    # Signal 2: Price decline vs. historical niche median
    historical_median = niche_context.get("historical_median_price", current_median)
    if historical_median > 0:
        price_decline_ratio = max(0.0, (historical_median - current_median) / historical_median)
        decline_score = min(1.0, price_decline_ratio * 3)  # 33% decline → score 1.0
    else:
        decline_score = 0.0

    # Signal 3: Proportion of gigs at bottom 25% of price range
    _price_min = float(np.min(prices_arr))
    bottom_quartile = np.percentile(prices_arr, 25)
    bottom_clustered = float(np.mean(prices_arr <= bottom_quartile * 1.1))
    bottom_cluster_score = min(1.0, bottom_clustered * 2)
    _ = _price_min

    return float(
        low_diversity_score * 0.40
        + decline_score * 0.35
        + bottom_cluster_score * 0.25
    )


def calculate_seller_overlap(keyword_id: int, niche_id: str, db: Any) -> float:
    """
    Calculates how much seller overlap exists across keywords in this niche.
    High overlap = a small group of sellers dominates the entire niche.
    Returns 0.0–1.0 (0 = all different sellers per keyword, 1 = same sellers everywhere).
    """
    del keyword_id
    if not isinstance(db, Session):
        return 0.0

    niche_pk = _resolve_niche_pk(niche_id, db)
    if niche_pk is None:
        return 0.0

    keyword_query = db.query(Keyword.id).filter(Keyword.niche_id == niche_pk)
    is_active_column = getattr(Keyword, "is_active", None)
    if is_active_column is not None:
        keyword_query = keyword_query.filter(is_active_column.is_(True))
    all_keywords = keyword_query.all()
    all_keyword_ids = [int(row.id) for row in all_keywords]

    if len(all_keyword_ids) < 2:
        return 0.0

    keyword_seller_sets: dict[int, set[str]] = {}
    for keyword_item_id in all_keyword_ids:
        search_result = get_latest_search_result(keyword_item_id, db)
        if search_result and search_result.gig_cards:
            top5 = [card.get("seller_username", "") for card in search_result.gig_cards[:5]]
            keyword_seller_sets[keyword_item_id] = set(filter(None, top5))

    if len(keyword_seller_sets) < 2:
        return 0.0

    sets = list(keyword_seller_sets.values())
    overlaps: list[float] = []
    for i, j in combinations(range(len(sets)), 2):
        sim = jaccard_similarity(sets[i], sets[j])
        overlaps.append(sim)

    return float(np.mean(overlaps)) if overlaps else 0.0


def get_latest_search_result(keyword_id: int, db: Any) -> SearchResult | None:
    """Loads the latest SearchResult row for a keyword."""
    if not isinstance(db, Session):
        return None
    return _model_get_latest_search_result(keyword_id, db)


def get_llm_saturation_score(
    keyword_id: int,
    db: Any,
    llm_client: Any = None,
    cache: Any = None,
) -> float:
    """
    Stub for LLM saturation classification.

    Returns a stable default of 50.0 when no LLM client is available, cache misses,
    or any runtime issue is encountered.
    """
    del db
    cache_key = f"saturation_class_score:{keyword_id}"

    if cache is not None and hasattr(cache, "get"):
        try:
            cached = cache.get(cache_key)
            if hasattr(cached, "__await__"):
                # Keep this helper sync-only by using the stable default for async cache clients.
                return 50.0
            parsed = _safe_float(cached)
            if parsed is not None:
                return max(0.0, min(100.0, parsed))
        except Exception:
            return 50.0

    if llm_client is None:
        return 50.0

    return 50.0


def calculate_saturation_score(
    keyword_id: int,
    niche_id: str,
    db: Any,
    niche_context: dict[str, Any],
) -> float:
    """
    Calculates the Saturation Score for a keyword (0–100).
    Higher = more saturated = harder to stand out.

    Used as Score 7 (inverted) in the Final Recommendation Score.
    """
    components = _calculate_saturation_components(
        keyword_id=keyword_id,
        niche_id=niche_id,
        db=db,
        niche_context=niche_context,
    )
    return float(components["saturation_score"])


async def run_saturation_analysis_for_niche(
    niche_id: str,
    run_id: str,
    db: Any,
    config: dict[str, Any],
    niche_context: dict[str, Any] | None = None,
    llm_client: Any = None,
) -> dict[str, Any]:
    """Run Stage 13 saturation analysis for one niche."""
    cache = config.get("cache") if isinstance(config, dict) else None
    if not isinstance(db, Session):
        return {
            "niche_id": niche_id,
            "run_id": run_id,
            "analyzed": False,
            "reason": "no_session",
        }

    niche_pk = _resolve_niche_pk(niche_id, db)
    if niche_pk is None:
        return {
            "niche_id": niche_id,
            "run_id": run_id,
            "analyzed": False,
            "reason": "niche_not_found",
        }

    keyword_query = db.query(Keyword).filter(Keyword.niche_id == niche_pk)
    is_active_column = getattr(Keyword, "is_active", None)
    if is_active_column is not None:
        keyword_query = keyword_query.filter(is_active_column.is_(True))
    keywords = keyword_query.order_by(Keyword.id.asc()).all()
    if not keywords:
        return {
            "niche_id": niche_id,
            "run_id": run_id,
            "analyzed": False,
            "reason": "no_keywords",
        }

    resolved_context = build_niche_context(
        niche_id=niche_id,
        db=db,
        niche_context=niche_context,
    )
    collected_scores: list[float] = []

    for keyword in keywords:
        components = _calculate_saturation_components(
            keyword_id=int(keyword.id),
            niche_id=niche_id,
            db=db,
            niche_context=resolved_context,
            llm_client=llm_client,
            cache=cache,
        )
        write_saturation_score(
            keyword_id=int(keyword.id),
            niche_id=niche_id,
            run_id=run_id,
            saturation_score=float(components["saturation_score"]),
            count_score=float(components["count_score"]),
            title_dup_score=float(components["title_dup_score"]),
            price_score=float(components["price_score"]),
            overlap_score=float(components["overlap_score"]),
            llm_class_score=float(components["llm_class_score"]),
            title_duplication_rate=float(components["title_duplication_rate"]),
            price_compression_rate=float(components["price_compression_rate"]),
            seller_overlap_rate=float(components["seller_overlap_rate"]),
            explanation_text=str(components["explanation_text"]),
            db=db,
            commit=False,
        )
        collected_scores.append(float(components["saturation_score"]))

    db.commit()
    avg_saturation = float(np.mean(collected_scores)) if collected_scores else 0.0
    return {
        "niche_id": niche_id,
        "run_id": run_id,
        "analyzed": True,
        "keywords_analyzed": len(collected_scores),
        "avg_saturation": round(avg_saturation, 2),
        "niche_context": resolved_context,
    }


async def run_saturation_analysis_for_all_niches(
    run_id: str,
    db: Any,
    config: dict[str, Any],
    llm_client: Any = None,
) -> dict[str, Any]:
    """Run Stage 13 saturation analysis for all active niches in config."""
    results: list[dict[str, Any]] = []
    for niche_id in _extract_niche_ids(config):
        results.append(
            await run_saturation_analysis_for_niche(
                niche_id=niche_id,
                run_id=run_id,
                db=db,
                config=config,
                llm_client=llm_client,
            )
        )

    analyzed_count = sum(1 for row in results if row.get("analyzed") is True)
    return {
        "run_id": run_id,
        "niches_processed": len(results),
        "niches_analyzed": analyzed_count,
        "results": results,
    }


def build_niche_context(
    niche_id: str,
    db: Any,
    niche_context: dict[str, Any] | None = None,
) -> dict[str, float]:
    """Builds niche context defaults and optional overrides for saturation calculations."""
    resolved: dict[str, float] = {"median_result_count": 500.0}

    if isinstance(db, Session):
        niche_pk = _resolve_niche_pk(niche_id, db)
        if niche_pk is not None:
            median_count = _compute_niche_median_result_count(niche_pk, db)
            if median_count is not None:
                resolved["median_result_count"] = float(median_count)

            historical_price = _compute_niche_historical_median_price(niche_pk, db)
            if historical_price is not None:
                resolved["historical_median_price"] = float(historical_price)

    if isinstance(niche_context, dict):
        override_count = _safe_float(niche_context.get("median_result_count"))
        if override_count is not None and override_count > 0:
            resolved["median_result_count"] = float(override_count)
        override_price = _safe_float(niche_context.get("historical_median_price"))
        if override_price is not None and override_price > 0:
            resolved["historical_median_price"] = float(override_price)

    if resolved["median_result_count"] <= 0:
        resolved["median_result_count"] = 500.0
    return resolved


def _calculate_saturation_components(
    keyword_id: int,
    niche_id: str,
    db: Any,
    niche_context: dict[str, Any],
    llm_client: Any = None,
    cache: Any = None,
) -> dict[str, float | str]:
    search_result = get_latest_search_result(keyword_id, db)
    if search_result is None:
        return {
            "saturation_score": 50.0,
            "count_score": 50.0,
            "title_dup_score": 50.0,
            "price_score": 50.0,
            "overlap_score": 50.0,
            "llm_class_score": 50.0,
            "title_duplication_rate": 0.0,
            "price_compression_rate": 0.3,
            "seller_overlap_rate": 0.0,
            "explanation_text": "No search results found; applied neutral default saturation score.",
        }

    gig_cards = search_result.gig_cards or []
    top_30_gigs = gig_cards[:30]

    # Component 1: Total gig count (25%)
    total_count = search_result.total_result_count or len(gig_cards)
    niche_median_count = niche_context.get("median_result_count", 500)
    count_score = min(100.0, (total_count / max(1, niche_median_count)) * 50)
    # At 2× median → score 100; at median → score 50; below median → proportionally lower

    # Component 2: Title duplication rate (25%)
    title_dup_rate = calculate_title_duplication_rate(top_30_gigs)
    title_dup_score = title_dup_rate * 100  # 0.0–1.0 → 0–100

    # Component 3: Price compression (20%)
    price_compression = calculate_price_compression(gig_cards, niche_context)
    price_score = price_compression * 100

    # Component 4: Seller portfolio overlap (15%)
    seller_overlap_rate = calculate_seller_overlap(keyword_id, niche_id, db)
    overlap_score = seller_overlap_rate * 100

    # Component 5: LLM saturation classification (15%)
    llm_class_score = get_llm_saturation_score(keyword_id, db, llm_client=llm_client, cache=cache)

    saturation_score = (
        count_score * 0.25
        + title_dup_score * 0.25
        + price_score * 0.20
        + overlap_score * 0.15
        + llm_class_score * 0.15
    )
    clamped_score = round(min(100.0, max(0.0, saturation_score)), 2)

    return {
        "saturation_score": clamped_score,
        "count_score": round(count_score, 2),
        "title_dup_score": round(title_dup_score, 2),
        "price_score": round(price_score, 2),
        "overlap_score": round(overlap_score, 2),
        "llm_class_score": round(llm_class_score, 2),
        "title_duplication_rate": round(title_dup_rate, 4),
        "price_compression_rate": round(price_compression, 4),
        "seller_overlap_rate": round(seller_overlap_rate, 4),
        "explanation_text": (
            "Saturation score blends result volume, title duplication, price compression, "
            "seller overlap, and qualitative classification."
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


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def _compute_niche_median_result_count(niche_pk: int, db: Session) -> float | None:
    keyword_query = db.query(Keyword.id).filter(Keyword.niche_id == niche_pk)
    is_active_column = getattr(Keyword, "is_active", None)
    if is_active_column is not None:
        keyword_query = keyword_query.filter(is_active_column.is_(True))
    keyword_ids = [int(row.id) for row in keyword_query.all()]
    if not keyword_ids:
        return None
    counts: list[float] = []
    for keyword_id in keyword_ids:
        search_result = get_latest_search_result(keyword_id, db)
        if search_result is None:
            continue
        total_count = search_result.total_result_count or len(search_result.gig_cards or [])
        if total_count > 0:
            counts.append(float(total_count))
    if not counts:
        return None
    return float(np.median(np.array(counts, dtype=float)))


def _compute_niche_historical_median_price(niche_pk: int, db: Session) -> float | None:
    keyword_query = db.query(Keyword.id).filter(Keyword.niche_id == niche_pk)
    is_active_column = getattr(Keyword, "is_active", None)
    if is_active_column is not None:
        keyword_query = keyword_query.filter(is_active_column.is_(True))
    keyword_ids = [int(row.id) for row in keyword_query.all()]
    if not keyword_ids:
        return None

    prices: list[float] = []
    for keyword_id in keyword_ids:
        search_result = get_latest_search_result(keyword_id, db)
        if search_result is None or not search_result.gig_cards:
            continue
        for card in search_result.gig_cards:
            parsed = _safe_float(card.get("starting_price"))
            if parsed is not None and parsed > 0:
                prices.append(parsed)
    if not prices:
        return None
    return float(np.median(np.array(prices, dtype=float)))

