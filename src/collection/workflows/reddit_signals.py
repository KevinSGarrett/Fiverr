"""Reddit signals workflow interfaces for Stage 6."""
from __future__ import annotations

from types import ModuleType
from typing import Any

from src.collection import community_signals as _mod


async def run_reddit_signals_collection(
    niche_id: str,
    seed_keywords: list[str],
    subreddits: list[str],
    run_id: str,
    db: Any,
    pacing_manager: Any,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Stage 6: Reddit collection per niche.

    Spec: COLLECTION_WORKFLOWS.md Workflow 7.
    Uses praw Reddit client for subreddit search + LLM demand intent parse.
    `dry_run=True` (default): returns stub without real praw calls.
    `dry_run=False`: raises NotImplementedError (praw auth not yet configured).
    """
    _ = (seed_keywords, subreddits, run_id, db, pacing_manager)
    if dry_run:
        return {
            "niche_id": niche_id,
            "subreddits_searched": 0,
            "posts_collected": 0,
            "signals_written": 0,
            "demand_intent_score": None,
            "dry_run": True,
            "note": "Dry run: no real praw calls made",
        }

    raise NotImplementedError(
        "Reddit collection with real praw not yet implemented. "
        "Requires: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET in .env. "
        "Set dry_run=True for stub execution."
    )


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
    return {
        "reddit_post_count_90d": post_count_90d,
        "demand_intent_score": demand_intent_score,
        "intent_phrases": intent_phrases,
        "subreddits_searched": subreddits_searched,
    }


class RedditSignalWorkflow:
    """Collects Reddit demand/activity signals for each niche."""

    def run(self, *args: Any, **kwargs: Any) -> ModuleType:
        _ = (args, kwargs)
        return _mod
