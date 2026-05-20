"""Keyword expansion workflow interfaces for Stage 2."""
from __future__ import annotations

import hashlib
import inspect
import json
import logging
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol, cast

import httpx

from src.collection import keyword_expansion as _mod
from src.llm import TemplateRenderer

logger = logging.getLogger(__name__)

_STAGE02_TEMPLATE_RENDERER = TemplateRenderer(
    template_dir=Path(__file__).resolve().parents[2] / "llm" / "templates"
)

_FEATURE_FLAGS: dict[str, bool] = {
    "step_2a_fiverr_autocomplete": False,
    "step_2c_llm_generation": True,
    "step_2d_llm_relevance_filter": True,
    "step_2f_llm_intent_classification": False,
    "step_2g_embedding_generation": False,
}


class KeywordExpansionLLMClient(Protocol):
    """LLM client protocol used by Workflow 2 Step 2c/2d."""

    def complete(
        self,
        *,
        prompt: str,
        model: str,
        response_format: dict[str, Any] | None = ...,
    ) -> Any:
        ...


class KeywordExpansionCache(Protocol):
    """Cache protocol for keyword expansion LLM steps."""

    def get(self, key: str, *args: Any, **kwargs: Any) -> Any:
        ...

    def set(self, key: str, value: Any, *args: Any, **kwargs: Any) -> Any:
        ...


async def _resolve_maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await cast(Any, value)
    return value


def _cache_key_for_keywords(prefix: str, niche_id: str, values: list[str]) -> str:
    payload = json.dumps({"niche_id": niche_id, "values": sorted(values)}, sort_keys=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def _extract_cached_keywords(cached: Any, value_key: str) -> list[str] | None:
    values: Any = cached
    if isinstance(cached, dict):
        values = cached.get(value_key)
    if not isinstance(values, list):
        return None
    return [item.strip() for item in values if isinstance(item, str) and item.strip()]


async def _cache_get_keywords(
    cache: KeywordExpansionCache | Any | None,
    cache_key: str,
    value_key: str,
) -> list[str] | None:
    if cache is None:
        return None
    try:
        cached: Any = await _resolve_maybe_await(cache.get(cache_key))
    except Exception:
        return None
    return _extract_cached_keywords(cached, value_key)


async def _cache_set_keywords(
    cache: KeywordExpansionCache | Any | None,
    cache_key: str,
    value_key: str,
    values: list[str],
) -> None:
    if cache is None:
        return
    try:
        await _resolve_maybe_await(cache.set(cache_key, values))
        return
    except TypeError:
        pass
    except Exception:
        logger.debug("Cache set failed for key '%s'.", cache_key, exc_info=True)
        return

    try:
        await _resolve_maybe_await(
            cache.set(
                cache_key,
                {value_key: values},
                model="gpt-4o-mini",
                temperature=0.0,
                prompt_text=cache_key,
            )
        )
    except Exception:
        logger.debug("Cache set fallback failed for key '%s'.", cache_key, exc_info=True)


def _render_stage02_template(template_name: str, **context: Any) -> str:
    return _STAGE02_TEMPLATE_RENDERER.render_template(
        f"stage02_keyword_expansion/{template_name}",
        context,
    )


async def _call_llm_json(
    llm_client: KeywordExpansionLLMClient,
    *,
    prompt: str,
    model: str,
) -> str:
    try:
        response = llm_client.complete(
            prompt=prompt,
            model=model,
            response_format={"type": "json_object"},
        )
    except TypeError:
        response = llm_client.complete(prompt=prompt, model=model)
    resolved: Any = await _resolve_maybe_await(response)
    text = getattr(resolved, "text", None)
    if isinstance(text, str):
        return text
    if isinstance(resolved, str):
        return resolved
    return str(resolved)


async def _llm_generate_keywords(
    niche_id: str,
    seeds: list[str],
    llm_client: KeywordExpansionLLMClient | None,
    cache: KeywordExpansionCache | Any | None,
    run_id: str,
) -> list[str]:
    """Step 2c: LLM-based keyword generation. Returns [] on failure per spec."""
    if llm_client is None:
        return []
    cleaned_seeds = [seed.strip() for seed in seeds if isinstance(seed, str) and seed.strip()]
    if not cleaned_seeds:
        return []

    cache_key = _cache_key_for_keywords("kw_gen_v1", niche_id, cleaned_seeds)
    cached_keywords = await _cache_get_keywords(cache, cache_key, "keywords")
    if cached_keywords is not None:
        return cached_keywords

    prompt = _render_stage02_template(
        "llm_generate.j2",
        niche_name=niche_id,
        seeds=cleaned_seeds,
    )
    try:
        response_text = await _call_llm_json(llm_client, prompt=prompt, model="gpt-4o-mini")
        payload = json.loads(response_text)
        if not isinstance(payload, dict):
            raise ValueError("LLM response was not a JSON object")
        raw_keywords = payload.get("keywords", [])
        if not isinstance(raw_keywords, list):
            raw_keywords = []
        keywords = [
            item["text"].strip()
            for item in raw_keywords
            if isinstance(item, dict)
            and isinstance(item.get("text"), str)
            and item["text"].strip()
        ]
    except Exception as exc:
        logger.warning(
            "LLM keyword generation failed niche=%s run_id=%s: %s",
            niche_id,
            run_id,
            exc,
        )
        return []

    keywords = _deduplicate_keywords(keywords)
    if keywords:
        await _cache_set_keywords(cache, cache_key, "keywords", keywords)
    return keywords


def _extract_relevant_keywords(payload: dict[str, Any], batch: list[str]) -> list[str]:
    raw_results = payload.get("results", [])
    if not isinstance(raw_results, list):
        return list(batch)

    decisions: dict[str, bool] = {keyword.strip().lower(): True for keyword in batch}
    for result in raw_results:
        if not isinstance(result, dict):
            continue
        keyword = result.get("keyword")
        if not isinstance(keyword, str):
            continue
        normalized_keyword = keyword.strip().lower()
        if normalized_keyword not in decisions:
            continue
        relevance = result.get("relevance")
        if isinstance(relevance, str) and relevance.strip().upper() == "IRRELEVANT":
            decisions[normalized_keyword] = False
        else:
            # Unknown/missing values are treated as include-all fallback.
            decisions[normalized_keyword] = True
    return [keyword for keyword in batch if decisions.get(keyword.strip().lower(), True)]


async def _llm_relevance_filter(
    niche_id: str,
    candidates: list[str],
    llm_client: KeywordExpansionLLMClient | None,
    cache: KeywordExpansionCache | Any | None,
) -> list[str]:
    """Step 2d: LLM relevance filter. Returns all candidates on failure per spec."""
    if not candidates:
        return []
    if llm_client is None:
        return list(candidates)

    relevant: list[str] = []
    for batch_start in range(0, len(candidates), 50):
        batch = candidates[batch_start : batch_start + 50]
        cache_key = _cache_key_for_keywords("rel_v1", niche_id, batch)
        cached_relevant = await _cache_get_keywords(cache, cache_key, "relevant_keywords")
        if cached_relevant is not None:
            relevant.extend(cached_relevant)
            continue

        prompt = _render_stage02_template(
            "llm_relevance.j2",
            niche_name=niche_id,
            candidate_keywords=batch,
        )
        try:
            response_text = await _call_llm_json(llm_client, prompt=prompt, model="gpt-4o-mini")
            payload = json.loads(response_text)
            if not isinstance(payload, dict):
                raise ValueError("LLM response was not a JSON object")
            batch_relevant = _extract_relevant_keywords(payload, batch)
        except Exception as exc:
            logger.warning(
                "LLM relevance filter failed niche=%s batch_start=%d: %s",
                niche_id,
                batch_start,
                exc,
            )
            batch_relevant = list(batch)

        await _cache_set_keywords(cache, cache_key, "relevant_keywords", batch_relevant)
        relevant.extend(batch_relevant)
    return relevant


async def _safe_pacing_wait(pacing_manager: Any, pacing_key: str, *, dry_run: bool) -> None:
    wait_fn = getattr(pacing_manager, "wait", None)
    if wait_fn is None:
        return
    await wait_fn(pacing_key, dry_run=dry_run)


async def _fetch_google_suggest(seed: str, pacing_manager: Any) -> list[str]:
    """Fetches Google Suggest completions for a seed keyword."""
    cleaned_seed = seed.strip()
    if not cleaned_seed:
        return []

    url = "https://suggestqueries.google.com/complete/search"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                url,
                params={"q": cleaned_seed, "client": "firefox"},
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
            data = resp.json()
            if not (isinstance(data, list) and len(data) > 1 and isinstance(data[1], list)):
                return []
            return [value.strip() for value in data[1] if isinstance(value, str) and value.strip()]
    except (httpx.HTTPError, TimeoutError, ValueError, TypeError):
        logger.warning("Google Suggest fetch failed for seed '%s'.", cleaned_seed)
        return []
    finally:
        await _safe_pacing_wait(pacing_manager, "external_default", dry_run=False)


def _deduplicate_keywords(keyword_list: list[str]) -> list[str]:
    """Case-insensitive deduplication with whitespace cleanup."""
    seen: set[str] = set()
    result: list[str] = []
    for kw in keyword_list:
        normalized = kw.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(kw.strip())
    return result


def _is_session(db: Any) -> bool:
    try:
        from sqlalchemy.orm import Session
    except Exception:
        return False
    return isinstance(db, Session)


def _resolve_niche_pk(niche_id: str, db: Any) -> int | None:
    try:
        from src.models.niche import Niche
    except Exception:
        return int(niche_id) if niche_id.isdigit() else None

    if niche_id.isdigit():
        return int(niche_id)

    try:
        record = db.query(Niche).filter(Niche.slug == niche_id).first()
    except Exception:
        return None
    if record is None:
        return None
    return int(record.id)


def _write_keywords_to_db(niche_id: str, keyword_list: list[str], db: Any) -> int:
    if not _is_session(db):
        return 0

    niche_pk = _resolve_niche_pk(niche_id, db)
    if niche_pk is None:
        logger.warning("Unable to resolve niche '%s' to a DB primary key; skipping keyword writes.", niche_id)
        return 0

    from src.collection.keyword_expansion import normalize_keyword
    from src.models.base import utc_now
    from src.models.market import Keyword

    try:
        existing_rows = (
            db.query(Keyword.normalized_keyword).filter(Keyword.niche_id == niche_pk).all()
        )
        existing_normalized = {row[0] for row in existing_rows if isinstance(row[0], str)}
    except Exception:
        db.rollback()
        logger.warning("Keyword table lookup failed; skipping DB writes for niche '%s'.", niche_id)
        return 0

    inserted = 0
    for keyword_text in keyword_list:
        normalized = normalize_keyword(keyword_text)
        if not normalized or normalized in existing_normalized:
            continue

        db.add(
            Keyword(
                niche_id=niche_pk,
                keyword=keyword_text,
                normalized_keyword=normalized,
                external_source="google_suggest",
                source_collected_at=utc_now(),
                metadata_json={"source": "google_suggest", "autocomplete_position": None},
            )
        )
        existing_normalized.add(normalized)
        inserted += 1

    if inserted > 0:
        db.commit()
    return inserted


async def run_keyword_expansion(
    niche_id: str,
    seeds: list[str],
    depth: str,
    run_id: str,
    db: Any,
    session_manager: Any,
    pacing_manager: Any,
    dry_run: bool = True,
    llm_client: KeywordExpansionLLMClient | None = None,
    cache: KeywordExpansionCache | Any | None = None,
) -> dict[str, Any]:
    """
    Stage 2 keyword expansion stub.

    `dry_run=True` is smoke-safe and performs no live browser/LLM activity.
    """
    _ = (depth, session_manager)
    if dry_run:
        return {
            "niche_id": niche_id,
            "keywords_queued": 0,
            "sources": {
                "fiverr_autocomplete": 0,
                "google_suggest": 0,
                "llm_generated": 0,
            },
            "dry_run": True,
            "note": "Dry run: no real Playwright or LLM calls made",
        }

    if not _FEATURE_FLAGS["step_2a_fiverr_autocomplete"]:
        logger.warning("Workflow 2 Step 2a stubbed: Fiverr autocomplete is feature-flagged off.")
    if not _FEATURE_FLAGS["step_2c_llm_generation"]:
        logger.warning("Workflow 2 Step 2c stubbed: LLM generation is feature-flagged off.")
    if not _FEATURE_FLAGS["step_2d_llm_relevance_filter"]:
        logger.warning("Workflow 2 Step 2d stubbed: LLM relevance filter is feature-flagged off.")
    if not _FEATURE_FLAGS["step_2f_llm_intent_classification"]:
        logger.warning("Workflow 2 Step 2f stubbed: LLM intent classification is feature-flagged off.")
    if not _FEATURE_FLAGS["step_2g_embedding_generation"]:
        logger.warning("Workflow 2 Step 2g stubbed: embedding generation is feature-flagged off.")

    fiverr_autocomplete_keywords: list[str] = []
    llm_generated_keywords: list[str] = []
    _ = (fiverr_autocomplete_keywords, llm_generated_keywords)

    google_suggest_keywords: list[str] = []
    for seed in seeds:
        if not isinstance(seed, str):
            continue
        google_suggest_keywords.extend(await _fetch_google_suggest(seed, pacing_manager))

    deduplicated_google = _deduplicate_keywords(google_suggest_keywords)
    google_suggest_count = len(deduplicated_google)

    combined_keywords = list(deduplicated_google)
    if _FEATURE_FLAGS["step_2c_llm_generation"]:
        llm_generated_keywords = await _llm_generate_keywords(
            niche_id=niche_id,
            seeds=seeds,
            llm_client=llm_client,
            cache=cache,
            run_id=run_id,
        )
        combined_keywords.extend(llm_generated_keywords)
    else:
        llm_generated_keywords = []

    if _FEATURE_FLAGS["step_2d_llm_relevance_filter"]:
        combined_keywords = await _llm_relevance_filter(
            niche_id=niche_id,
            candidates=combined_keywords,
            llm_client=llm_client,
            cache=cache,
        )

    deduplicated_keywords = _deduplicate_keywords(combined_keywords)

    keywords_queued = len(deduplicated_keywords)
    if _is_session(db):
        keywords_queued = _write_keywords_to_db(niche_id, deduplicated_keywords, db)

    return {
        "niche_id": niche_id,
        "keywords_queued": keywords_queued,
        "sources": {
            "fiverr_autocomplete": 0,
            "google_suggest": google_suggest_count,
            "llm_generated": len(llm_generated_keywords),
        },
        "dry_run": False,
    }


async def run_keyword_expansion_stub(
    niche_id: str,
    seeds: list[str],
    depth: str,
    run_id: str,
    db: Any,
    session_manager: Any,
    pacing_manager: Any,
    dry_run: bool = True,
    llm_client: KeywordExpansionLLMClient | None = None,
    cache: KeywordExpansionCache | Any | None = None,
) -> dict[str, Any]:
    """Alias required by workflow package exports."""
    return await run_keyword_expansion(
        niche_id=niche_id,
        seeds=seeds,
        depth=depth,
        run_id=run_id,
        db=db,
        session_manager=session_manager,
        pacing_manager=pacing_manager,
        dry_run=dry_run,
        llm_client=llm_client,
        cache=cache,
    )


class KeywordExpansionWorkflow:
    """Wraps keyword_expansion module; expands seed keywords via Fiverr autocomplete."""

    def run(self, *args: Any, **kwargs: Any) -> ModuleType:
        return _mod
