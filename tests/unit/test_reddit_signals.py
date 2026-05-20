"""Unit tests for Workflow 7 Reddit signal interfaces."""
from __future__ import annotations

import asyncio
import time
from typing import Any

import pytest
from src.collection.workflows.reddit_signals import (
    build_reddit_demand_signal_json,
    build_subreddit_search_url,
    parse_reddit_post_count_90d,
    run_reddit_signals_collection,
    select_top_posts_for_llm,
)


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_reddit_dry_run() -> None:
    result = _run(
        run_reddit_signals_collection(
            niche_id="ai_agents",
            seed_keywords=["ai agent"],
            subreddits=["Entrepreneur"],
            run_id="run-1",
            db=None,
            pacing_manager=None,
            dry_run=True,
        )
    )

    required_keys = {
        "niche_id",
        "subreddits_searched",
        "posts_collected",
        "signals_written",
        "demand_intent_score",
        "dry_run",
        "note",
    }
    assert required_keys.issubset(result.keys())
    assert result["dry_run"] is True


def test_reddit_dry_run_default() -> None:
    result = _run(
        run_reddit_signals_collection(
            niche_id="ai_agents",
            seed_keywords=["ai agent"],
            subreddits=["Entrepreneur"],
            run_id="run-2",
            db=None,
            pacing_manager=None,
        )
    )

    assert result["dry_run"] is True
    assert result["signals_written"] == 0


def test_reddit_raises_without_dry_run() -> None:
    with pytest.raises(NotImplementedError):
        _run(
            run_reddit_signals_collection(
                niche_id="ai_agents",
                seed_keywords=["ai agent"],
                subreddits=["Entrepreneur"],
                run_id="run-3",
                db=None,
                pacing_manager=None,
                dry_run=False,
            )
        )


def test_reddit_result_has_niche_id() -> None:
    result = _run(
        run_reddit_signals_collection(
            niche_id="my_niche",
            seed_keywords=[],
            subreddits=[],
            run_id="run-4",
            db=None,
            pacing_manager=None,
        )
    )

    assert result["niche_id"] == "my_niche"


def test_build_subreddit_search_url() -> None:
    assert (
        build_subreddit_search_url("Entrepreneur", "fiverr")
        == "https://www.reddit.com/r/Entrepreneur/search/?q=fiverr&restrict_sr=1&t=year"
    )


def test_build_subreddit_search_url_encodes_spaces() -> None:
    url = build_subreddit_search_url("freelance", "buyer intent")
    assert "buyer%20intent" in url
    assert "+" not in url


def test_parse_post_count_90d_all_recent() -> None:
    now = time.time()
    posts = [{"created_utc": now - 1000}, {"created_utc": now - 2000}, {"created_utc": now - 3000}]
    assert parse_reddit_post_count_90d(posts) == len(posts)


def test_parse_post_count_90d_all_old() -> None:
    old_timestamp = time.time() - (100 * 24 * 3600)
    posts = [{"created_utc": old_timestamp}, {"created_utc": old_timestamp - 1}]
    assert parse_reddit_post_count_90d(posts) == 0


def test_parse_post_count_90d_mixed() -> None:
    now = time.time()
    old_timestamp = now - (100 * 24 * 3600)
    posts = [
        {"created_utc": now - 100},
        {"created_utc": now - 200},
        {"created_utc": now - 300},
        {"created_utc": old_timestamp},
        {"created_utc": old_timestamp - 200},
    ]
    assert parse_reddit_post_count_90d(posts) == 3


def test_select_top_posts_by_upvotes() -> None:
    posts = [
        {"title": "a", "upvotes": 5},
        {"title": "b", "upvotes": 11},
        {"title": "c", "upvotes": 2},
    ]
    selected = select_top_posts_for_llm(posts, n=3)
    assert [post["title"] for post in selected] == ["b", "a", "c"]


def test_select_top_posts_limit() -> None:
    posts = [{"upvotes": idx} for idx in range(20)]
    selected = select_top_posts_for_llm(posts, n=4)
    assert len(selected) == 4
    assert selected[0]["upvotes"] == 19


def test_build_demand_signal_json() -> None:
    payload = build_reddit_demand_signal_json(
        post_count_90d=12,
        demand_intent_score=7.5,
        intent_phrases=["need help", "hire freelancer"],
        subreddits_searched=["Entrepreneur", "smallbusiness"],
    )

    assert payload["reddit_post_count_90d"] == 12
    assert payload["demand_intent_score"] == 7.5
    assert payload["intent_phrases"] == ["need help", "hire freelancer"]
    assert payload["subreddits_searched"] == ["Entrepreneur", "smallbusiness"]
