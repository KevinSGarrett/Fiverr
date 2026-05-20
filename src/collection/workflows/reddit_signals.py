"""Reddit signals workflow interfaces for Stage 6."""
from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import logging
import os
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol, cast

from src.collection import community_signals as _mod
from src.llm import TemplateRenderer
from src.models import Keyword
from src.models.external_signal import ExternalSignal, write_external_signal

logger = logging.getLogger(__name__)

SIGNAL_REDDIT_DEMAND = ExternalSignal.SIGNAL_REDDIT_DEMAND
SIGNAL_REDDIT_ACTIVITY = ExternalSignal.SIGNAL_REDDIT_ACTIVITY

_STAGE06_TEMPLATE_RENDERER = TemplateRenderer(
    template_dir=Path(__file__).resolve().parents[2] / "llm" / "templates"
)


class RedditLLMClient(Protocol):
    """LLM client contract for Workflow 7 demand parsing."""

    def complete(
        self,
        *,
        prompt: str,
        model: str,
        response_format: dict[str, Any] | None = ...,
    ) -> Any:
        ...


class RedditCache(Protocol):
    """Cache contract for Workflow 7 demand parsing."""

    def get(self, key: str, *args: Any, **kwargs: Any) -> Any:
        ...

    def set(self, key: str, value: Any, *args: Any, **kwargs: Any) -> Any:
        ...


async def _resolve_maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await cast(Any, value)
    return value


async def run_reddit_signals_collection(
    niche_id: str,
    seed_keywords: list[str],
    subreddits: list[str],
    run_id: str,
    db: Any,
    pacing_manager: Any,
    llm_client: RedditLLMClient | Any | None = None,
    cache: RedditCache | Any | None = None,
    checkpoint_manager: Any | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Stage 6: Reddit collection per niche.

    Spec: COLLECTION_WORKFLOWS.md Workflow 7.
    `dry_run=True` (default): returns stub without real praw calls.
    `dry_run=False`: executes authenticated praw search workflow and writes demand signals.
    """
    cleaned_seeds = [seed.strip() for seed in seed_keywords if isinstance(seed, str) and seed.strip()]
    cleaned_subreddits = [
        subreddit.strip() for subreddit in subreddits if isinstance(subreddit, str) and subreddit.strip()
    ]
    if dry_run:
        return {
            "niche_id": niche_id,
            "subreddits_searched": 0,
            "subreddits_accessed": [],
            "posts_collected": 0,
            "post_count_90d": 0,
            "signals_written": 0,
            "demand_intent_score": None,
            "intent_phrases": [],
            "dry_run": True,
            "note": "Dry run: no real praw calls made",
        }

    try:
        import importlib

        praw = importlib.import_module("praw")
    except Exception as exc:  # pragma: no cover - guarded by dependency check tests
        raise RuntimeError("praw is required for Reddit collection. Install praw>=7.7,<8.0.") from exc

    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ.get("REDDIT_USER_AGENT", "FiverrResearchSystem/0.1"),
    )

    subreddits_accessed: list[str] = []
    all_posts: list[dict[str, Any]] = []
    for subreddit_name in cleaned_subreddits:
        subreddit_ref = reddit.subreddit(subreddit_name)
        try:
            _ = subreddit_ref.id
        except Exception as exc:  # noqa: BLE001 - fail-soft per workflow spec
            logger.warning("Subreddit %s inaccessible: %s", subreddit_name, exc)
            continue

        subreddits_accessed.append(subreddit_name)
        for seed in cleaned_seeds:
            try:
                results = subreddit_ref.search(
                    seed,
                    sort="relevance",
                    time_filter="year",
                    limit=25,
                )
                for post in results:
                    all_posts.append(
                        {
                            "title": str(getattr(post, "title", "")),
                            "body_snippet": str(getattr(post, "selftext", "") or "")[:200],
                            "upvotes": int(getattr(post, "score", 0) or 0),
                            "created_utc": getattr(post, "created_utc", None),
                            "subreddit": subreddit_name,
                        }
                    )
                await _safe_pacing_wait(pacing_manager, "reddit_api", dry_run=False)
            except Exception as exc:  # noqa: BLE001 - workflow intentionally degrades safely
                error_text = str(exc)
                if "429" in error_text or "toomany" in error_text.lower():
                    await asyncio.sleep(60)
                    continue
                logger.warning("Reddit search %s/%s failed: %s", subreddit_name, seed, exc)

    post_count_90d = parse_reddit_post_count_90d(all_posts)
    top_posts = select_top_posts_for_llm(all_posts, n=10)
    demand_intent_score, intent_phrases = await _llm_reddit_demand_parse(
        top_posts,
        niche_id,
        llm_client,
        cache,
    )
    signal_json = build_reddit_demand_signal_json(
        post_count_90d,
        demand_intent_score,
        intent_phrases,
        subreddits_accessed,
    )
    signals_written = 0
    for seed in cleaned_seeds:
        keyword_id = _resolve_keyword_id(seed, niche_id, db)
        if keyword_id is None:
            continue
        write_external_signal(
            keyword_id=keyword_id,
            signal_type=SIGNAL_REDDIT_DEMAND,
            signal_value=demand_intent_score,
            signal_json=signal_json,
            run_id=run_id,
            collection_method="reddit_api",
            db=db,
        )
        signals_written += 1

    if checkpoint_manager is not None:
        try:
            await _resolve_maybe_await(
                checkpoint_manager.write(
                    "stage06_reddit",
                    niche_id,
                    {
                        "niche_id": niche_id,
                        "run_id": run_id,
                        "posts_collected": len(all_posts),
                        "signals_written": signals_written,
                    },
                )
            )
        except Exception:
            logger.warning(
                "Failed to write Reddit checkpoint for run '%s' and niche '%s'.",
                run_id,
                niche_id,
                exc_info=True,
            )

    return {
        "niche_id": niche_id,
        "subreddits_searched": len(subreddits_accessed),
        "subreddits_accessed": subreddits_accessed,
        "posts_collected": len(all_posts),
        "post_count_90d": post_count_90d,
        "signals_written": signals_written,
        "demand_intent_score": demand_intent_score,
        "intent_phrases": intent_phrases,
        "dry_run": False,
    }


async def _safe_pacing_wait(pacing_manager: Any, pacing_key: str, *, dry_run: bool) -> None:
    wait_fn = getattr(pacing_manager, "wait", None)
    if wait_fn is None:
        return
    await _resolve_maybe_await(wait_fn(pacing_key, dry_run=dry_run))


def _resolve_niche_pk(niche_id: str, db: Any) -> int | None:
    from src.models.niche import Niche

    if niche_id.isdigit():
        return int(niche_id)
    row = db.query(Niche).filter(Niche.slug == niche_id).first()
    return int(row.id) if row is not None else None


def _resolve_keyword_id(keyword_text: str, niche_id: str, db: Any) -> int | None:
    """
    Lookup keyword_id by both text and niche_id to prevent cross-niche signal writes.

    Pattern established by Cycle 028 Codex Fix #1 in google_trends.py.
    """
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


async def _llm_reddit_demand_parse(
    top_posts: list[dict[str, Any]],
    niche_id: str,
    llm_client: RedditLLMClient | Any | None,
    cache: RedditCache | Any | None,
) -> tuple[float | None, list[str]]:
    """W7 Step 5: parse top Reddit posts for demand intent. Returns (None, []) on failure."""
    if not top_posts or llm_client is None:
        return None, []

    post_titles = [str(post.get("title", "")) for post in top_posts if isinstance(post, dict)]
    cache_key = "reddit_intent_v1:" + hashlib.sha256((niche_id + str(post_titles)).encode()).hexdigest()
    if cache is not None:
        try:
            cached = await _resolve_maybe_await(cache.get(cache_key))
        except Exception:
            cached = None
        if isinstance(cached, dict):
            cached_score = cached.get("demand_intent_score")
            cached_phrases = cached.get("intent_phrases")
            if isinstance(cached_phrases, list):
                phrases = [item for item in cached_phrases if isinstance(item, str)]
                if cached_score is None:
                    score = 0.0
                else:
                    try:
                        score = min(10.0, max(0.0, float(cached_score)))
                    except (TypeError, ValueError):
                        score = 0.0
                return score, phrases

    prompt = _STAGE06_TEMPLATE_RENDERER.render_template(
        "stage06_reddit/reddit_demand_parse.j2",
        {"niche_name": niche_id, "top_posts": top_posts},
    )
    try:
        try:
            response = llm_client.complete(
                prompt=prompt,
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
            )
        except TypeError:
            response = llm_client.complete(prompt=prompt, model="gpt-4o-mini")

        resolved_response = await _resolve_maybe_await(response)
        text_value = getattr(resolved_response, "text", resolved_response)
        payload = text_value if isinstance(text_value, str) else str(text_value)
        data = json.loads(payload)

        raw_score = data.get("demand_intent_score", 0)
        try:
            score = min(10.0, max(0.0, float(raw_score)))
        except (TypeError, ValueError):
            score = 0.0
        raw_phrases = data.get("intent_phrases", [])
        phrases = [item for item in raw_phrases if isinstance(item, str)]
        if cache is not None:
            try:
                await _resolve_maybe_await(
                    cache.set(
                        cache_key,
                        {"demand_intent_score": score, "intent_phrases": phrases},
                    )
                )
            except Exception:
                logger.debug("Reddit LLM cache set failed for key '%s'.", cache_key, exc_info=True)
        return score, phrases
    except Exception as exc:
        logger.warning("Reddit LLM demand parse failed niche=%s: %s", niche_id, exc)
        return None, []


def build_subreddit_search_url(subreddit: str, query: str) -> str:
    """Spec W7 Step 1b: subreddit.search() URL for reference/debugging."""
    import urllib.parse

    encoded_query = urllib.parse.quote(query)
    return f"https://www.reddit.com/r/{subreddit}/search/?q={encoded_query}&restrict_sr=1&t=year"


def parse_reddit_post_count_90d(posts: list[dict[str, Any]]) -> int:
    """Spec W7 Step 3: count posts with created_utc > 90 days ago."""
    import time

    cutoff = time.time() - (90 * 24 * 3600)
    return sum(
        1
        for post in posts
        if isinstance(post, dict) and isinstance(post.get("created_utc"), int | float) and post["created_utc"] > cutoff
    )


def select_top_posts_for_llm(posts: list[dict[str, Any]], n: int = 10) -> list[dict[str, Any]]:
    """Spec W7 Step 4: select top-N posts by upvotes for LLM analysis."""
    return sorted(
        (post for post in posts if isinstance(post, dict)),
        key=lambda post: post.get("upvotes", 0),
        reverse=True,
    )[:n]


def build_reddit_demand_signal_json(
    post_count_90d: int,
    demand_intent_score: float | None,
    intent_phrases: list[str],
    subreddits_searched: list[str],
) -> dict[str, Any]:
    """Build the signal_json payload for external_signals writes."""
    payload = {
        "post_count_90d": post_count_90d,
        "demand_intent_score": demand_intent_score,
        "intent_phrases": intent_phrases,
        "subreddits_searched": subreddits_searched,
    }
    payload["reddit_post_count_90d"] = post_count_90d
    if demand_intent_score is None:
        payload["confidence_adjustment"] = -0.05
    return payload


class RedditSignalWorkflow:
    """Collects Reddit demand/activity signals for each niche."""

    def run(self, *args: Any, **kwargs: Any) -> ModuleType:
        _ = (args, kwargs)
        return _mod
