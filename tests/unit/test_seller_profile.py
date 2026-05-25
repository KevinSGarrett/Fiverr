"""Unit tests for Workflow 5 seller profile helper functions and real path."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.collection import seller_profile as seller_profile_module
from src.collection.fiverr_selectors import (
    SELLER_BADGE,
    SELLER_BIO,
    SELLER_GIG_COUNT,
    SELLER_GIG_TITLE,
    SELLER_LANGUAGES,
    SELLER_LEVEL_BADGE,
    SELLER_MEMBER_SINCE,
    SELLER_PORTFOLIO_ITEM,
    SELLER_RESPONSE_RATE,
    SELLER_RESPONSE_TIME,
    SELLER_REVIEW_COUNT,
    SELLER_TOTAL_GIGS,
    SELLER_TOTAL_REVIEWS,
)
from src.collection.workflows.seller_profile import (
    SellerProfileWorkflow,
    _parse_int,
    _safe_count,
    _safe_text,
    _safe_text_list,
    _write_stage05_checkpoint,
    build_seller_profile_url,
    parse_member_since,
    parse_response_rate,
    parse_seller_level,
    parse_seller_profile_fields,
    run_seller_profile_collection,
)
from src.models import Base


class _FakeElement:
    def __init__(self, text: str) -> None:
        self._text = text

    async def inner_text(self) -> str:
        return self._text


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return factory()


def _run(coro):
    return asyncio.run(coro)


def _base_selector_texts() -> dict[str, str | None]:
    return {
        SELLER_LEVEL_BADGE: "Level 2 Seller",
        SELLER_MEMBER_SINCE: "Member since Jan 2022",
        SELLER_RESPONSE_TIME: "1 hour",
        SELLER_RESPONSE_RATE: "98%",
        SELLER_TOTAL_REVIEWS: "1,234 Reviews",
        SELLER_TOTAL_GIGS: "56 gigs",
        SELLER_BIO: "Experienced seller bio",
    }


def _base_selector_lists() -> dict[str, list[str]]:
    return {
        SELLER_LANGUAGES: ["English - Fluent", "Spanish - Conversational"],
        SELLER_GIG_TITLE: ["Gig One", "Gig Two", "Gig Three"],
        SELLER_PORTFOLIO_ITEM: ["Portfolio A", "Portfolio B", "Portfolio C", "Portfolio D"],
        SELLER_BADGE: ["Top Rated", "Pro Verified"],
    }


def _build_page(
    selector_texts: dict[str, str | None] | None = None,
    selector_lists: dict[str, list[str]] | None = None,
    *,
    goto_exception: Exception | None = None,
) -> AsyncMock:
    texts = selector_texts if selector_texts is not None else _base_selector_texts()
    lists = selector_lists if selector_lists is not None else _base_selector_lists()

    page = AsyncMock()
    page.goto = AsyncMock(side_effect=goto_exception) if goto_exception else AsyncMock()

    async def _query_selector(selector: str) -> _FakeElement | None:
        value = texts.get(selector)
        return _FakeElement(value) if value is not None else None

    async def _query_selector_all(selector: str) -> list[_FakeElement]:
        return [_FakeElement(value) for value in lists.get(selector, [])]

    page.query_selector = AsyncMock(side_effect=_query_selector)
    page.query_selector_all = AsyncMock(side_effect=_query_selector_all)
    return page


def _build_managers(page: AsyncMock) -> tuple[AsyncMock, AsyncMock, MagicMock]:
    session_manager = AsyncMock()
    session_manager.new_page = AsyncMock(return_value=page)
    session_manager.close_page = AsyncMock()

    pacing_manager = AsyncMock()
    pacing_manager.wait = AsyncMock()

    checkpoint_manager = MagicMock()
    checkpoint_manager.write = MagicMock()
    return session_manager, pacing_manager, checkpoint_manager


async def _run_collection(
    *,
    db: object,
    selector_texts: dict[str, str | None] | None = None,
    selector_lists: dict[str, list[str]] | None = None,
    goto_exception: Exception | None = None,
) -> tuple[dict[str, object], AsyncMock, AsyncMock, AsyncMock, MagicMock]:
    page = _build_page(selector_texts, selector_lists, goto_exception=goto_exception)
    session_manager, pacing_manager, checkpoint_manager = _build_managers(page)
    result = await run_seller_profile_collection(
        seller_username="top_seller",
        niche_id="ai_saas",
        run_id="run-029",
        db=db,
        session_manager=session_manager,
        pacing_manager=pacing_manager,
        checkpoint_manager=checkpoint_manager,
        dry_run=False,
    )
    return result, page, session_manager, pacing_manager, checkpoint_manager


def test_build_seller_url() -> None:
    assert build_seller_profile_url("sample_user") == "https://www.fiverr.com/sample_user"


def test_parse_member_since_jan() -> None:
    assert parse_member_since("Member since Jan 2022") == "2022-01"


def test_parse_member_since_none() -> None:
    assert parse_member_since(None) is None


def test_parse_member_since_no_date_pattern() -> None:
    assert parse_member_since("Member for years") is None


def test_parse_seller_level_trs() -> None:
    assert parse_seller_level("Top Rated Seller") == "TRS"


def test_parse_seller_level_no_level() -> None:
    assert parse_seller_level(None) == "NO_LEVEL"


def test_parse_seller_level_level_2() -> None:
    assert parse_seller_level("Level 2 Seller") == "LEVEL_2"


def test_parse_seller_level_level_1() -> None:
    assert parse_seller_level("Level 1 Seller") == "LEVEL_1"


def test_parse_seller_level_pro() -> None:
    assert parse_seller_level("Pro Verified") == "PRO"


def test_parse_seller_level_unknown_defaults_to_no_level() -> None:
    assert parse_seller_level("Rookie") == "NO_LEVEL"


def test_parse_response_rate_percent() -> None:
    assert parse_response_rate("98%") == 98


def test_parse_response_rate_none() -> None:
    assert parse_response_rate(None) is None


def test_parse_response_rate_no_digits() -> None:
    assert parse_response_rate("N/A") is None


def test_parse_int_handles_commas() -> None:
    assert _parse_int("1,234") == 1234


def test_parse_int_none_input() -> None:
    assert _parse_int(None) is None


def test_seller_review_count_alias_matches_value() -> None:
    assert SELLER_REVIEW_COUNT == SELLER_TOTAL_REVIEWS


def test_seller_gig_count_alias_matches_value() -> None:
    assert SELLER_GIG_COUNT == SELLER_TOTAL_GIGS


def test_w5_non_dry_requires_managers() -> None:
    with pytest.raises(NotImplementedError):
        _run(
            run_seller_profile_collection(
                seller_username="top_seller",
                niche_id="ai_saas",
                run_id="run-029",
                db={},
                session_manager=None,
                pacing_manager=None,
                checkpoint_manager=None,
                dry_run=False,
            )
        )


def test_w5_skips_when_fresh_row_exists() -> None:
    session = _session()
    page = _build_page()
    session_manager, pacing_manager, checkpoint_manager = _build_managers(page)
    fresh_row = SimpleNamespace(
        profile_collected=True,
        profile_collected_at=datetime.now(UTC) - timedelta(hours=1),
        ttl_hours=720,
    )
    with patch("src.collection.workflows.seller_profile.get_seller", return_value=fresh_row):
        result = _run(
            run_seller_profile_collection(
                seller_username="top_seller",
                niche_id="ai_saas",
                run_id="run-029",
                db=session,
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                checkpoint_manager=checkpoint_manager,
                dry_run=False,
            )
        )
    assert result["skipped"] is True
    assert result["reason"] == "fresh_row_exists"
    session_manager.new_page.assert_not_awaited()
    session.close()


def test_w5_staleness_handles_naive_datetime() -> None:
    session = _session()
    page = _build_page()
    session_manager, pacing_manager, checkpoint_manager = _build_managers(page)
    fresh_row = SimpleNamespace(
        profile_collected=True,
        profile_collected_at=datetime.now() - timedelta(hours=1),
        ttl_hours=720,
    )
    with patch("src.collection.workflows.seller_profile.get_seller", return_value=fresh_row):
        result = _run(
            run_seller_profile_collection(
                seller_username="top_seller",
                niche_id="ai_saas",
                run_id="run-029",
                db=session,
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                checkpoint_manager=checkpoint_manager,
                dry_run=False,
            )
        )
    assert result["reason"] == "fresh_row_exists"
    session.close()


def test_w5_does_not_skip_when_stale_row() -> None:
    session = _session()
    stale_row = SimpleNamespace(
        profile_collected=True,
        profile_collected_at=datetime.now(UTC) - timedelta(hours=1000),
        ttl_hours=1,
    )
    with patch("src.collection.workflows.seller_profile.get_seller", return_value=stale_row):
        result, page, _, _, _ = _run(_run_collection(db=session))
    assert result["collected"] is True
    page.goto.assert_awaited_once()
    session.close()


def test_w5_does_not_skip_when_no_row() -> None:
    session = _session()
    with patch("src.collection.workflows.seller_profile.get_seller", return_value=None):
        result, page, _, _, _ = _run(_run_collection(db=session))
    assert result["collected"] is True
    page.goto.assert_awaited_once()
    session.close()


def test_w5_skips_when_already_collected_this_run() -> None:
    with patch("src.collection.workflows.seller_profile.should_skip_seller_profile", return_value=True):
        result = _run(
            run_seller_profile_collection(
                seller_username="top_seller",
                niche_id="ai_saas",
                run_id="run-029",
                db={},
                session_manager=AsyncMock(),
                pacing_manager=AsyncMock(),
                checkpoint_manager=None,
                dry_run=False,
            )
        )
    assert result["skipped"] is True
    assert result["reason"] == "already_collected_this_run"


def test_w5_guards_not_triggered_when_db_not_session() -> None:
    with patch("src.collection.workflows.seller_profile.get_seller") as get_seller_mock:
        result, _, _, _, _ = _run(_run_collection(db={}))
    get_seller_mock.assert_not_called()
    assert result["collected"] is True


def test_w5_real_navigates_to_correct_url() -> None:
    result, page, _, _, _ = _run(_run_collection(db={}))
    assert result["collected"] is True
    page.goto.assert_awaited_once_with(
        "https://www.fiverr.com/top_seller",
        wait_until="domcontentloaded",
        timeout=30_000,
    )


def test_w5_real_calls_pacing_wait() -> None:
    _, _, _, pacing_manager, _ = _run(_run_collection(db={}))
    pacing_manager.wait.assert_awaited_once_with("fiverr_seller_profile", dry_run=False)


def test_w5_real_handles_404_gracefully() -> None:
    result, _, session_manager, _, _ = _run(
        _run_collection(
            db={},
            goto_exception=RuntimeError("404 not found"),
        )
    )
    assert result["collected"] is False
    assert result["error"] == "404"
    session_manager.close_page.assert_awaited_once()


def test_w5_real_handles_private_deactivated_gracefully() -> None:
    result, _, session_manager, _, _ = _run(
        _run_collection(
            db={},
            goto_exception=RuntimeError("private account deactivated"),
        )
    )
    assert result["collected"] is False
    assert result["error"] == "private_or_deactivated"
    session_manager.close_page.assert_awaited_once()


def test_safe_text_returns_none_when_selector_not_found() -> None:
    page = AsyncMock()
    page.query_selector = AsyncMock(return_value=None)
    assert _run(_safe_text(page, ".missing-selector")) is None


def test_safe_text_returns_none_on_selector_error() -> None:
    page = AsyncMock()
    page.query_selector = AsyncMock(side_effect=RuntimeError("boom"))
    assert _run(_safe_text(page, ".broken-selector")) is None


def test_safe_text_list_returns_empty_on_query_error() -> None:
    page = AsyncMock()
    page.query_selector_all = AsyncMock(side_effect=RuntimeError("boom"))
    assert _run(_safe_text_list(page, ".broken")) == []


def test_safe_text_list_skips_elements_with_inner_text_errors() -> None:
    broken_element = AsyncMock()
    broken_element.inner_text = AsyncMock(side_effect=RuntimeError("bad element"))
    page = AsyncMock()
    page.query_selector_all = AsyncMock(return_value=[broken_element, _FakeElement("Good text")])
    assert _run(_safe_text_list(page, ".mixed")) == ["Good text"]


def test_safe_count_returns_zero_when_query_fails() -> None:
    page = AsyncMock()
    page.query_selector_all = AsyncMock(side_effect=RuntimeError("count failed"))
    assert _run(_safe_count(page, ".broken-count")) == 0


def test_write_stage05_checkpoint_handles_missing_write_method() -> None:
    _run(
        _write_stage05_checkpoint(
            checkpoint_manager=SimpleNamespace(),
            run_id="run-029",
            niche_id="ai_saas",
            seller_username="top_seller",
        )
    )


def test_write_stage05_checkpoint_falls_back_to_legacy_signature() -> None:
    class _LegacyCheckpoint:
        def __init__(self) -> None:
            self.calls: list[tuple[object, ...]] = []

        def write(self, *args: object) -> None:
            self.calls.append(args)
            if args and args[0] == "stage05":
                raise TypeError("legacy signature")

    legacy = _LegacyCheckpoint()
    _run(
        _write_stage05_checkpoint(
            checkpoint_manager=legacy,
            run_id="run-029",
            niche_id="ai_saas",
            seller_username="top_seller",
        )
    )
    assert legacy.calls[0][0] == "stage05"
    assert legacy.calls[1][0] == "run-029"
    assert legacy.calls[1][1] == "stage05_ai_saas"


def test_write_stage05_checkpoint_awaits_async_write() -> None:
    checkpoint_manager = MagicMock()
    checkpoint_manager.write = AsyncMock(return_value=None)
    _run(
        _write_stage05_checkpoint(
            checkpoint_manager=checkpoint_manager,
            run_id="run-029",
            niche_id="ai_saas",
            seller_username="top_seller",
        )
    )
    checkpoint_manager.write.assert_awaited_once_with(
        "stage05",
        "ai_saas",
        {"seller_username": "top_seller", "collected": True},
    )


def test_parse_seller_profile_fields_stub_shape() -> None:
    result = parse_seller_profile_fields({"payload": "ignored"})
    assert set(result.keys()) == {
        "seller_level",
        "member_since",
        "response_time",
        "response_rate",
        "languages",
        "bio_text",
        "total_reviews",
        "total_gigs",
        "active_gig_titles",
        "portfolio_count",
        "badges",
    }


def test_seller_profile_workflow_wrapper_returns_module() -> None:
    assert SellerProfileWorkflow().run() is seller_profile_module


def test_w5_real_extracts_seller_level() -> None:
    result, _, _, _, _ = _run(_run_collection(db={}))
    assert result["seller_level"] == "LEVEL_2"


def test_w5_real_extracts_member_since() -> None:
    result, _, _, _, _ = _run(_run_collection(db={}))
    assert result["member_since"] == "2022-01"


def test_w5_real_extracts_response_rate() -> None:
    result, _, _, _, _ = _run(_run_collection(db={}))
    assert result["response_rate"] == 98


def test_w5_real_extracts_total_reviews() -> None:
    result, _, _, _, _ = _run(_run_collection(db={}))
    assert result["total_reviews"] == 1234


def test_w5_real_extracts_active_gig_titles() -> None:
    result, _, _, _, _ = _run(_run_collection(db={}))
    assert result["active_gig_titles"] == ["Gig One", "Gig Two", "Gig Three"]


def test_w5_real_caps_active_gig_titles_at_20() -> None:
    titles = [f"Gig {i}" for i in range(25)]
    lists = _base_selector_lists()
    lists[SELLER_GIG_TITLE] = titles
    result, _, _, _, _ = _run(_run_collection(db={}, selector_lists=lists))
    assert len(result["active_gig_titles"]) == 20
    assert result["active_gig_titles"][0] == "Gig 0"
    assert result["active_gig_titles"][-1] == "Gig 19"


def test_w5_real_extracts_portfolio_count() -> None:
    result, _, _, _, _ = _run(_run_collection(db={}))
    assert result["portfolio_count"] == 4


def test_w5_real_extracts_badges() -> None:
    result, _, _, _, _ = _run(_run_collection(db={}))
    assert result["badges"] == ["Top Rated", "Pro Verified"]


def test_w5_real_bio_text_none_when_missing() -> None:
    texts = _base_selector_texts()
    texts[SELLER_BIO] = None
    result, _, _, _, _ = _run(_run_collection(db={}, selector_texts=texts))
    assert result["bio_text"] is None


def test_w5_real_writes_seller_row() -> None:
    with patch("src.collection.workflows.seller_profile.write_seller_profile") as write_mock:
        result, _, _, _, _ = _run(_run_collection(db={}))
    assert result["collected"] is True
    write_mock.assert_called_once()
    kwargs = write_mock.call_args.kwargs
    assert kwargs["seller_username"] == "top_seller"
    assert kwargs["run_id"] == "run-029"
    assert kwargs["seller_level"] == "LEVEL_2"
    assert kwargs["member_since"] == "2022-01"
    assert kwargs["response_time"] == "1 hour"
    assert kwargs["total_reviews"] == 1234
    assert kwargs["total_gigs"] == 56


def test_w5_real_closes_page_on_success() -> None:
    _, _, session_manager, _, _ = _run(_run_collection(db={}))
    session_manager.close_page.assert_awaited_once()


def test_w5_real_closes_page_on_exception() -> None:
    page = _build_page()
    session_manager, pacing_manager, checkpoint_manager = _build_managers(page)
    pacing_manager.wait = AsyncMock(side_effect=RuntimeError("boom"))

    with pytest.raises(RuntimeError):
        _run(
            run_seller_profile_collection(
                seller_username="top_seller",
                niche_id="ai_saas",
                run_id="run-029",
                db={},
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                checkpoint_manager=checkpoint_manager,
                dry_run=False,
            )
        )

    session_manager.close_page.assert_awaited_once()


def test_w5_real_returns_collected_true_with_all_fields() -> None:
    result, _, _, _, _ = _run(_run_collection(db={}))
    assert result["collected"] is True
    assert result["seller_username"] == "top_seller"
    assert result["seller_level"] == "LEVEL_2"
    assert result["member_since"] == "2022-01"
    assert result["response_time"] == "1 hour"
    assert result["response_rate"] == 98
    assert result["languages"] == ["English - Fluent", "Spanish - Conversational"]
    assert result["bio_text"] == "Experienced seller bio"
    assert result["total_reviews"] == 1234
    assert result["total_gigs"] == 56
    assert result["active_gig_titles"] == ["Gig One", "Gig Two", "Gig Three"]
    assert result["portfolio_count"] == 4
    assert result["badges"] == ["Top Rated", "Pro Verified"]


def test_seller_profile_dry_run_preserved() -> None:
    result = _run(
        run_seller_profile_collection(
            seller_username="top_seller",
            niche_id="ai_saas",
            run_id="run-029",
            db=None,
            session_manager=None,
            pacing_manager=None,
            checkpoint_manager=None,
            dry_run=True,
        )
    )
    assert result["seller_username"] == "top_seller"
    assert result["collected"] is False
    assert result["fields_collected"] == []
    assert result["dry_run"] is True


def test_parse_seller_profile_from_html_keeps_zero_review_count_from_hydration() -> None:
    html = """
    <html><body>
      <script id="perseus-initial-props" type="application/json">
        {"reviewsData":{"selling_reviews":{"total_count":0}}}
      </script>
      <div>12 Reviews</div>
      <script type="application/ld+json">
        {"aggregateRating":{"reviewCount":"45"}}
      </script>
    </body></html>
    """
    parsed = seller_profile_module.parse_seller_profile_from_html(html)
    assert parsed.review_count == 0
