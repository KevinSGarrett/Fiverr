"""Focused unit tests for Workflow 4 real implementation."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.collection.gig_detail import parse_gig_detail_from_html
from src.collection.workflows.gig_detail import (
    _parse_rating,
    _parse_review_count,
    _parse_starting_price,
    _safe_inner_text,
    build_gig_detail_url,
    run_gig_detail_collection,
)
from src.models.gig import Gig
from src.models.job import Job


def _run(coro):
    return asyncio.run(coro)


class _FakeNode:
    def __init__(self, text: str | None = None, mapping: dict[str, _FakeNode | None] | None = None):
        self._text = text
        self._mapping = mapping or {}

    async def inner_text(self) -> str:
        return self._text or ""

    async def query_selector(self, selector: str):
        return self._mapping.get(selector)


def _build_real_gig_detail_mocks(
    *,
    title: str = "Gig Title",
    description: str = "Long description",
    has_video: bool = True,
    portfolio_count: int = 2,
    review_text: str | None = "1,234 reviews",
    rating_text: str | None = "4.9",
) -> tuple[AsyncMock, AsyncMock, AsyncMock]:
    from src.collection.fiverr_selectors import (
        GIG_DETAIL_DESCRIPTION,
        GIG_DETAIL_FAQ_ANSWER,
        GIG_DETAIL_FAQ_ITEMS,
        GIG_DETAIL_FAQ_QUESTION,
        GIG_DETAIL_PACKAGE_PRICE,
        GIG_DETAIL_PACKAGES,
        GIG_DETAIL_PORTFOLIO,
        GIG_DETAIL_RATING,
        GIG_DETAIL_REVIEW_COUNT,
        GIG_DETAIL_TAGS,
        GIG_DETAIL_TITLE,
        GIG_DETAIL_VIDEO,
    )

    package = _FakeNode(mapping={GIG_DETAIL_PACKAGE_PRICE: _FakeNode("$50")})
    faq = _FakeNode(mapping={GIG_DETAIL_FAQ_QUESTION: _FakeNode("Q1"), GIG_DETAIL_FAQ_ANSWER: _FakeNode("A1")})
    tags = [_FakeNode("Tag 1"), _FakeNode("Tag 2")]
    portfolios = [_FakeNode("P") for _ in range(portfolio_count)]

    selector_map = {
        GIG_DETAIL_TITLE: _FakeNode(title),
        GIG_DETAIL_DESCRIPTION: _FakeNode(description),
        GIG_DETAIL_VIDEO: _FakeNode("video") if has_video else None,
        GIG_DETAIL_REVIEW_COUNT: _FakeNode(review_text) if review_text else None,
        GIG_DETAIL_RATING: _FakeNode(rating_text) if rating_text else None,
    }
    selector_all_map = {
        GIG_DETAIL_PACKAGES: [package],
        GIG_DETAIL_TAGS: tags,
        GIG_DETAIL_FAQ_ITEMS: [faq],
        GIG_DETAIL_PORTFOLIO: portfolios,
    }

    page = AsyncMock()
    page.goto = AsyncMock()
    page.query_selector = AsyncMock(side_effect=lambda selector: selector_map.get(selector))
    page.query_selector_all = AsyncMock(side_effect=lambda selector: selector_all_map.get(selector, []))

    session_manager = AsyncMock()
    session_manager.new_page = AsyncMock(return_value=page)
    session_manager.close_page = AsyncMock()

    pacing_manager = AsyncMock()
    pacing_manager.wait = AsyncMock()
    return page, session_manager, pacing_manager


def test_w4_real_navigates_to_gig_url() -> None:
    page, session_manager, pacing_manager = _build_real_gig_detail_mocks()
    gig_url = "https://www.fiverr.com/seller/gig-4"
    _run(
        run_gig_detail_collection(
            gig_url=gig_url,
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-1",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    page.goto.assert_awaited_once_with(gig_url, wait_until="domcontentloaded", timeout=30_000)


def test_w4_real_calls_pacing_wait() -> None:
    _page, session_manager, pacing_manager = _build_real_gig_detail_mocks()
    _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-5",
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-2",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    pacing_manager.wait.assert_awaited_once_with("fiverr_gig_detail", dry_run=False)


def test_w4_real_extracts_title() -> None:
    _page, session_manager, pacing_manager = _build_real_gig_detail_mocks(title="Exact Gig Title")
    result = _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-title",
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-3",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    assert result["title"] == "Exact Gig Title"


def test_w4_real_extracts_description() -> None:
    _page, session_manager, pacing_manager = _build_real_gig_detail_mocks(description="Detailed description body")
    result = _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-description",
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-4",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    assert result["description_length"] == len("Detailed description body")


def test_w4_real_video_present() -> None:
    _page, session_manager, pacing_manager = _build_real_gig_detail_mocks(has_video=True)
    result = _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-video",
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-5",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    assert result["has_video"] is True


def test_w4_real_video_absent() -> None:
    _page, session_manager, pacing_manager = _build_real_gig_detail_mocks(has_video=False)
    result = _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-no-video",
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-6",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    assert result["has_video"] is False


def test_w4_real_portfolio_count() -> None:
    _page, session_manager, pacing_manager = _build_real_gig_detail_mocks(portfolio_count=3)
    result = _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-portfolio",
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-7",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    assert result["portfolio_count"] == 3


def test_w4_real_updates_gig_row() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Gig.__table__.create(bind=engine, checkfirst=True)
    db = sessionmaker(bind=engine, future=True)()
    try:
        db.add(Gig(gig_url="https://www.fiverr.com/seller/gig-db", seller_username="seller"))
        db.commit()

        _page, session_manager, pacing_manager = _build_real_gig_detail_mocks(title="DB Title")
        _run(
            run_gig_detail_collection(
                gig_url="https://www.fiverr.com/seller/gig-db",
                keyword_id=1,
                niche_id="niche",
                depth="standard",
                run_id="run-w4-8",
                db=db,
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                checkpoint_manager=None,
                dry_run=False,
            )
        )
        row = db.query(Gig).filter(Gig.gig_url == "https://www.fiverr.com/seller/gig-db").first()
        assert row is not None
        assert row.detail_collected is True
        assert row.detail_collected_at is not None
    finally:
        db.close()


def test_w4_real_closes_page_on_success() -> None:
    _page, session_manager, pacing_manager = _build_real_gig_detail_mocks()
    _run(
        run_gig_detail_collection(
            gig_url="https://www.fiverr.com/seller/gig-close-ok",
            keyword_id=1,
            niche_id="niche",
            depth="standard",
            run_id="run-w4-9",
            db=object(),
            session_manager=session_manager,
            pacing_manager=pacing_manager,
            checkpoint_manager=None,
            dry_run=False,
        )
    )
    session_manager.close_page.assert_awaited_once()


def test_w4_real_closes_page_on_error() -> None:
    page, session_manager, pacing_manager = _build_real_gig_detail_mocks()
    page.goto.side_effect = RuntimeError("boom")
    try:
        _run(
            run_gig_detail_collection(
                gig_url="https://www.fiverr.com/seller/gig-close-error",
                keyword_id=1,
                niche_id="niche",
                depth="standard",
                run_id="run-w4-10",
                db=object(),
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                checkpoint_manager=None,
                dry_run=False,
            )
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected RuntimeError from page.goto")
    session_manager.close_page.assert_awaited_once()


def test_w4_real_no_gig_row_in_db() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Gig.__table__.create(bind=engine, checkfirst=True)
    db = sessionmaker(bind=engine, future=True)()
    try:
        _page, session_manager, pacing_manager = _build_real_gig_detail_mocks()
        result = _run(
            run_gig_detail_collection(
                gig_url="https://www.fiverr.com/seller/not-found",
                keyword_id=1,
                niche_id="niche",
                depth="standard",
                run_id="run-w4-11",
                db=db,
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                checkpoint_manager=None,
                dry_run=False,
            )
        )
        assert result["detail_collected"] is True
    finally:
        db.close()


def test_parse_review_count_with_commas() -> None:
    assert _parse_review_count("1,234 reviews") == 1234


def test_parse_review_count_none() -> None:
    assert _parse_review_count(None) is None


def test_parse_rating_decimal() -> None:
    assert _parse_rating("Rated 4.9 stars") == 4.9


def test_parse_rating_none() -> None:
    assert _parse_rating(None) is None


def test_build_gig_detail_url_relative_path() -> None:
    assert build_gig_detail_url("/services/test-gig") == "https://www.fiverr.com/services/test-gig"


def test_build_gig_detail_url_plain_text_passthrough() -> None:
    assert build_gig_detail_url("seller/test-gig") == "seller/test-gig"


def test_safe_inner_text_none_node_returns_none() -> None:
    page = AsyncMock()
    page.query_selector = AsyncMock(return_value=None)
    result = _run(_safe_inner_text(page, ".missing"))
    assert result is None


def test_safe_inner_text_blank_string_returns_none() -> None:
    node = AsyncMock()
    node.inner_text = AsyncMock(return_value="   ")
    page = AsyncMock()
    page.query_selector = AsyncMock(return_value=node)
    result = _run(_safe_inner_text(page, ".blank"))
    assert result is None


def test_parse_starting_price_skips_non_string_entries() -> None:
    packages = [{"price_text": 99}, {"price_text": None}, {"price_text": "$42"}]
    assert _parse_starting_price(packages) == 42.0


def test_parse_starting_price_returns_min_value() -> None:
    packages = [{"price_text": "$120"}, {"price_text": "From $1,050"}, {"price_text": "$95"}]
    assert _parse_starting_price(packages) == 95.0


def test_w4_real_queues_seller_profile_job() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE run_logs (run_id VARCHAR(64) PRIMARY KEY)"))
        conn.execute(text("CREATE TABLE niche_configs (niche_id VARCHAR(64) PRIMARY KEY)"))
        conn.execute(text("INSERT INTO run_logs(run_id) VALUES ('run-seller')"))
        conn.execute(text("INSERT INTO niche_configs(niche_id) VALUES ('niche')"))

    Gig.__table__.create(bind=engine, checkfirst=True)
    Job.__table__.create(bind=engine, checkfirst=True)
    db = sessionmaker(bind=engine, future=True)()
    try:
        db.add(Gig(gig_url="https://www.fiverr.com/seller-queue/gig", seller_username="seller-queue"))
        db.commit()

        _page, session_manager, pacing_manager = _build_real_gig_detail_mocks()
        result = _run(
            run_gig_detail_collection(
                gig_url="https://www.fiverr.com/seller-queue/gig",
                keyword_id=1,
                niche_id="niche",
                depth="standard",
                run_id="run-seller",
                db=db,
                session_manager=session_manager,
                pacing_manager=pacing_manager,
                checkpoint_manager=None,
                dry_run=False,
            )
        )

        assert result["seller_queued"] is True
        jobs = db.query(Job).all()
        assert len(jobs) == 1
        assert jobs[0].job_type == "SELLER_PROFILE"
        assert jobs[0].status == "QUEUED"
        assert jobs[0].payload == {"seller_username": "seller-queue", "niche_id": "niche"}
    finally:
        db.close()


def test_parse_gig_detail_from_html_extracts_title_from_next_data() -> None:
    html = """
    <html><body>
    <script id="__NEXT_DATA__" type="application/json">
      {"props":{"pageProps":{"gig":{"gigTitle":"Next Data Gig Title","description":"Detailed scope"}}}}
    </script>
    </body></html>
    """
    parsed = parse_gig_detail_from_html(html)
    assert parsed.title == "Next Data Gig Title"
    assert parsed.description == "Detailed scope"


def test_parse_gig_detail_from_html_extracts_packages_from_next_data() -> None:
    html = """
    <html><body>
    <script id="__NEXT_DATA__" type="application/json">
      {"props":{"pageProps":{"packages":[{"name":"Basic","price":55},{"name":"Standard","price":"125"}]}}}
    </script>
    </body></html>
    """
    parsed = parse_gig_detail_from_html(html)
    assert [package.name for package in parsed.packages] == ["Basic", "Standard"]
    assert [package.price_cents for package in parsed.packages] == [5500, 12500]


def test_parse_gig_detail_from_html_empty_html_returns_warnings() -> None:
    parsed = parse_gig_detail_from_html("")
    assert parsed.title is None
    assert any("malformed" in warning.lower() for warning in parsed.warnings)
