"""Pricing LLM task utilities for Wave 9 recommendation generation."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from src.models import LLMCacheRecord, LLMUsageLog

if TYPE_CHECKING:
    from src.recommendations.context import RecommendationContext

PRICING_TASK_NUM = 12
PRICING_MODEL = "gpt-4o"
PRICING_TEMPERATURE = 0.2
PRICING_CACHE_PREFIX = "pricing_strategy"


async def pricing_llm_task(
    keyword_id: int,
    context: RecommendationContext,
    db: Any,
    client: Any,
) -> str | None:
    """
    LLM task #12: generate a pricing strategy narrative for a keyword.

    Returns pricing strategy text, or None if no price data is available.
    This task never raises; all exceptions are swallowed and return None.
    """
    if not context.price_distribution or not context.calculated_entry_prices:
        return None
    if client is None:
        return None

    dist_hash = hashlib.sha256(_stable_json(context.price_distribution).encode("utf-8")).hexdigest()[:12]
    competitor_hash = hashlib.sha256(
        _stable_json(context.competitor_price_positions or []).encode("utf-8")
    ).hexdigest()[:8]
    cache_key = (
        f"{PRICING_CACHE_PREFIX}:{context.keyword_text}:{dist_hash}:{competitor_hash}"
    )

    cached = await check_cache(client, cache_key, db=db)
    if cached:
        return cached

    prompt = build_pricing_prompt(context)
    try:
        if hasattr(client, "chat") and getattr(client.chat, "completions", None) is not None:
            response = await client.chat.completions.create(
                model=PRICING_MODEL,
                temperature=PRICING_TEMPERATURE,
                messages=[
                    {"role": "system", "content": "You are a Fiverr pricing strategist."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=600,
            )
            content = response.choices[0].message.content if response.choices else None
            result = content.strip() if isinstance(content, str) else None
            usage = getattr(response, "usage", None)
        else:
            response = client.complete(
                prompt=prompt,
                model=PRICING_MODEL,
                temperature=PRICING_TEMPERATURE,
            )
            if hasattr(response, "__await__"):
                response = await response
            text = getattr(response, "text", None)
            result = text.strip() if isinstance(text, str) else str(response).strip()
            usage = {
                "prompt_tokens": int(getattr(response, "prompt_tokens", 0) or 0),
                "completion_tokens": int(getattr(response, "completion_tokens", 0) or 0),
                "total_tokens": int(getattr(response, "total_tokens", 0) or 0),
            }

        if not result:
            return None

        await store_cache(client, cache_key, result, db=db)
        await log_llm_usage(
            keyword_id=keyword_id,
            model_name=PRICING_MODEL,
            usage=usage,
            task_type="pricing_strategy",
            db=db,
            request_hash=cache_key,
        )
        return result
    except Exception:
        return None


def build_pricing_prompt(context: RecommendationContext) -> str:
    """Build a concise pricing strategy prompt from recommendation context."""
    distribution = context.price_distribution or {}
    basic = distribution.get("basic", {}) if isinstance(distribution, Mapping) else {}
    entry = context.calculated_entry_prices or {}

    return (
        f"Keyword: {context.keyword_text}\n"
        f"Market type: {context.market_type or 'UNKNOWN'}\n"
        f"Basic tier - Median: ${_as_price(basic.get('median'))}, "
        f"Q1: ${_as_price(basic.get('q1'))}, "
        f"Q3: ${_as_price(basic.get('q3'))}\n"
        f"Your entry price: Basic ${_as_price(entry.get('basic'))} / "
        f"Standard ${_as_price(entry.get('standard'))} / "
        f"Premium ${_as_price(entry.get('premium'))}\n"
        "Write a 3-4 sentence pricing strategy for a new seller. Focus on: "
        "(1) how to position your entry price, "
        "(2) how to increase prices as reviews grow, "
        "(3) one key market insight."
    )


async def check_cache(client: Any, cache_key: str, *, db: Any) -> str | None:
    """Look up cached pricing strategy result by key."""
    del client
    if isinstance(db, Session):
        row = db.query(LLMCacheRecord).filter(LLMCacheRecord.cache_key == cache_key).first()
        if row and isinstance(row.value_json, dict):
            value = row.value_json.get("value")
            if isinstance(value, str) and value.strip():
                return value
    return None


async def store_cache(client: Any, cache_key: str, value: str, *, db: Any) -> None:
    """Persist pricing strategy output to cache table when DB is available."""
    del client
    if not isinstance(db, Session):
        return
    row = db.query(LLMCacheRecord).filter(LLMCacheRecord.cache_key == cache_key).first()
    if row is None:
        row = LLMCacheRecord(cache_key=cache_key, model_name=PRICING_MODEL, value_json={})
        db.add(row)
    row.model_name = PRICING_MODEL
    row.value_json = {"value": value}
    try:
        db.flush()
    except Exception:
        db.rollback()


async def log_llm_usage(
    keyword_id: int,
    model_name: str,
    usage: Any,
    task_type: str,
    db: Any,
    request_hash: str,
) -> None:
    """Write a pricing-task usage record into llm_usage_logs when possible."""
    del keyword_id
    if not isinstance(db, Session):
        return

    prompt_tokens = _usage_value(usage, "prompt_tokens")
    completion_tokens = _usage_value(usage, "completion_tokens")
    total_tokens = _usage_value(usage, "total_tokens")

    row = LLMUsageLog(
        model_name=model_name,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_cost_usd=None,
        task_type=task_type,
        request_hash=request_hash,
        request_json={"task_type": task_type},
        response_json={"total_tokens": total_tokens},
    )
    db.add(row)
    try:
        db.flush()
    except Exception:
        db.rollback()


def _usage_value(usage: Any, key: str) -> int:
    if usage is None:
        return 0
    if isinstance(usage, Mapping):
        raw = usage.get(key)
    else:
        raw = getattr(usage, key, 0)
    try:
        return int(raw or 0)
    except (TypeError, ValueError):
        return 0


def _stable_json(payload: Any) -> str:
    return repr(payload if payload is not None else "")


def _as_price(value: Any) -> str:
    try:
        return f"{float(value):.0f}"
    except (TypeError, ValueError):
        return "0"
