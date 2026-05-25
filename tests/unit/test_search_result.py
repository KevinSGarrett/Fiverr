"""Unit tests for SearchResult ORM and helper functions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from src.models import Keyword, Niche, SearchResult
from src.models.database import initialize_database
from src.models.search_result import get_latest_search_result, write_search_result


def _build_session(tmp_path: Path, name: str):
    engine = initialize_database(database_url=f"sqlite:///{(tmp_path / name).as_posix()}")
    from sqlalchemy.orm import Session

    return Session(bind=engine)


def _seed_keyword(session) -> int:
    niche = Niche(slug="search-result-niche", name="Search Result", category_path="programming-tech/search")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="fiverr search result keyword",
        normalized_keyword="fiverr search result keyword",
    )
    session.add(keyword)
    session.commit()
    return keyword.id


def test_search_result_table_name() -> None:
    assert SearchResult.__tablename__ == "search_results"


def test_search_result_insert_minimal(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_minimal.db")
    keyword_id = _seed_keyword(session)
    row = SearchResult(keyword_id=keyword_id, run_id="run-min-1")
    session.add(row)
    session.commit()
    fetched = session.query(SearchResult).filter(SearchResult.keyword_id == keyword_id).one()
    assert fetched.run_id == "run-min-1"
    session.close()


def test_search_result_insert_full(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_full.db")
    keyword_id = _seed_keyword(session)
    session.add(
        SearchResult(
            keyword_id=keyword_id,
            run_id="run-full-1",
            total_result_count=1234,
            pagination_depth=12,
            gig_cards=[{"gig_url": "https://www.fiverr.com/gig/1", "position": 1}],
            page_collected=2,
            ttl_hours=72,
            is_stale=True,
            raw_html_ref="s3://raw/run-full-1/page2.html",
        )
    )
    session.commit()
    assert session.query(SearchResult).filter_by(run_id="run-full-1").count() == 1
    session.close()


def test_search_result_gig_cards_json(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_cards.db")
    keyword_id = _seed_keyword(session)
    cards = [{"gig_url": "https://example.com/gig", "price": 50}, {"gig_url": "https://example.com/gig2"}]
    session.add(SearchResult(keyword_id=keyword_id, run_id="run-json", gig_cards=cards))
    session.commit()
    fetched = session.query(SearchResult).filter_by(run_id="run-json").one()
    assert isinstance(fetched.gig_cards, list)
    assert fetched.gig_cards[0]["price"] == 50
    session.close()


def test_search_result_nullable_fields(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_nullable.db")
    keyword_id = _seed_keyword(session)
    session.add(
        SearchResult(
            keyword_id=keyword_id,
            run_id="run-nullable",
            total_result_count=None,
            pagination_depth=None,
        )
    )
    session.commit()
    fetched = session.query(SearchResult).filter_by(run_id="run-nullable").one()
    assert fetched.total_result_count is None
    assert fetched.pagination_depth is None
    session.close()


def test_search_result_default_ttl(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_default_ttl.db")
    keyword_id = _seed_keyword(session)
    session.add(SearchResult(keyword_id=keyword_id, run_id="run-default-ttl"))
    session.commit()
    fetched = session.query(SearchResult).filter_by(run_id="run-default-ttl").one()
    assert fetched.ttl_hours == 168
    session.close()


def test_search_result_default_page(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_default_page.db")
    keyword_id = _seed_keyword(session)
    session.add(SearchResult(keyword_id=keyword_id, run_id="run-default-page"))
    session.commit()
    fetched = session.query(SearchResult).filter_by(run_id="run-default-page").one()
    assert fetched.page_collected == 1
    session.close()


def test_search_result_unique_constraint(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_unique.db")
    keyword_id = _seed_keyword(session)
    session.add(SearchResult(keyword_id=keyword_id, run_id="run-uniq", page_collected=1))
    session.commit()
    session.add(SearchResult(keyword_id=keyword_id, run_id="run-uniq", page_collected=1))
    with pytest.raises(IntegrityError):
        session.commit()
    session.close()


def test_search_result_index_exists(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_indexes.db")
    indexes = inspect(session.bind).get_indexes("search_results")
    names = {index["name"] for index in indexes}
    assert "ix_search_results_run_keyword" in names
    assert "ix_search_results_keyword_collected_at_desc" in names
    session.close()


def test_write_search_result_dict_db() -> None:
    row = write_search_result(
        keyword_id=1,
        run_id="run-non-session",
        total_result_count=10,
        pagination_depth=1,
        gig_cards=[],
        page_collected=1,
        db={},
    )
    assert row is None


def test_write_search_result_orm(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_write.db")
    keyword_id = _seed_keyword(session)
    row = write_search_result(
        keyword_id=keyword_id,
        run_id="run-write",
        total_result_count=150,
        pagination_depth=8,
        gig_cards=[{"gig_url": "https://example.com/gig-a"}],
        page_collected=1,
        db=session,
    )
    assert row is not None
    assert session.query(SearchResult).filter_by(run_id="run-write").count() == 1
    session.close()


def test_write_search_result_populates_rank_from_card_position(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_rank_write.db")
    keyword_id = _seed_keyword(session)
    row = write_search_result(
        keyword_id=keyword_id,
        run_id="run-rank-write",
        total_result_count=40,
        pagination_depth=1,
        gig_cards=[
            {
                "position": 4,
                "gig_url": "https://www.fiverr.com/seller/rank-four",
                "gig_title": "Rank Four Gig",
            }
        ],
        page_collected=1,
        db=session,
    )
    assert row is not None
    assert row.rank == 4
    assert row.result_url == "https://www.fiverr.com/seller/rank-four"
    assert row.title == "Rank Four Gig"
    session.close()


def test_search_result_rank_matches_card_position_order(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_rank_order.db")
    keyword_id = _seed_keyword(session)
    row = write_search_result(
        keyword_id=keyword_id,
        run_id="run-rank-order",
        total_result_count=55,
        pagination_depth=1,
        gig_cards=[
            {
                "position": 5,
                "gig_url": "https://www.fiverr.com/seller/rank-five",
                "gig_title": "Rank Five Gig",
            },
            {
                "position": 1,
                "gig_url": "https://www.fiverr.com/seller/rank-one",
                "gig_title": "Rank One Gig",
            },
            {
                "position": 3,
                "gig_url": "https://www.fiverr.com/seller/rank-three",
                "gig_title": "Rank Three Gig",
            },
        ],
        page_collected=1,
        db=session,
    )
    assert row is not None
    assert row.rank == 1
    assert row.result_url == "https://www.fiverr.com/seller/rank-one"
    assert row.title == "Rank One Gig"
    session.close()


def test_write_search_result_coerces_string_position_and_reuses_legacy_rank_row(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_legacy_rank_reuse.db")
    keyword_id = _seed_keyword(session)
    legacy_row = SearchResult(
        keyword_id=keyword_id,
        run_id="legacy-old",
        page_collected=9,
        rank=7,
        gig_cards=[{"position": 7, "gig_url": "https://www.fiverr.com/seller/legacy-seven"}],
    )
    session.add(legacy_row)
    session.commit()

    row = write_search_result(
        keyword_id=keyword_id,
        run_id="run-string-rank",
        total_result_count=70,
        pagination_depth=1,
        gig_cards=[
            {
                "position": " 7 ",
                "gig_url": "https://www.fiverr.com/seller/string-seven",
                "gig_title": "String Seven Gig",
            }
        ],
        page_collected=1,
        db=session,
    )
    assert row is not None
    assert row.id == legacy_row.id
    assert row.run_id == "run-string-rank"
    assert row.page_collected == 1
    assert row.rank == 7
    assert row.result_url == "https://www.fiverr.com/seller/string-seven"
    assert row.title == "String Seven Gig"
    session.close()


def test_write_search_result_releases_conflicting_legacy_rank_row(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_rank_conflict_release.db")
    keyword_id = _seed_keyword(session)
    legacy_rank_row = SearchResult(
        keyword_id=keyword_id,
        run_id="legacy-conflict",
        page_collected=3,
        rank=3,
        gig_cards=[{"position": 3, "gig_url": "https://www.fiverr.com/seller/legacy-three"}],
    )
    current_row = SearchResult(
        keyword_id=keyword_id,
        run_id="run-target",
        page_collected=1,
        rank=None,
    )
    # Insert the legacy rank row first so unique-rank clearance can flush before reassignment.
    session.add_all([legacy_rank_row, current_row])
    session.commit()

    updated = write_search_result(
        keyword_id=keyword_id,
        run_id="run-target",
        total_result_count=33,
        pagination_depth=1,
        gig_cards=[
            {
                "position": "3",
                "gig_url": "https://www.fiverr.com/seller/new-three",
                "gig_title": "New Rank Three Gig",
            }
        ],
        page_collected=1,
        db=session,
    )
    session.refresh(current_row)
    session.refresh(legacy_rank_row)
    assert updated is not None
    assert updated.id == current_row.id
    assert current_row.rank == 3
    assert legacy_rank_row.rank is None
    assert current_row.result_url == "https://www.fiverr.com/seller/new-three"
    assert current_row.title == "New Rank Three Gig"
    session.close()


def test_write_search_result_upsert(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_upsert.db")
    keyword_id = _seed_keyword(session)
    first = write_search_result(
        keyword_id=keyword_id,
        run_id="run-upsert",
        total_result_count=120,
        pagination_depth=4,
        gig_cards=[{"gig_url": "https://example.com/old"}],
        page_collected=1,
        db=session,
    )
    second = write_search_result(
        keyword_id=keyword_id,
        run_id="run-upsert",
        total_result_count=220,
        pagination_depth=6,
        gig_cards=[{"gig_url": "https://example.com/new"}],
        page_collected=1,
        db=session,
    )
    assert first is not None and second is not None
    assert first.id == second.id
    assert session.query(SearchResult).filter_by(run_id="run-upsert").count() == 1
    assert second.total_result_count == 220
    session.close()


def test_get_latest_search_result_found(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_latest_found.db")
    keyword_id = _seed_keyword(session)
    older = datetime.now(UTC) - timedelta(days=1)
    newer = datetime.now(UTC)
    session.add(
        SearchResult(keyword_id=keyword_id, run_id="run-old", page_collected=1, collected_at=older),
    )
    session.add(
        SearchResult(keyword_id=keyword_id, run_id="run-new", page_collected=2, collected_at=newer),
    )
    session.commit()
    latest = get_latest_search_result(keyword_id=keyword_id, db=session)
    assert latest is not None
    assert latest.run_id == "run-new"
    session.close()


def test_get_latest_search_result_missing(tmp_path: Path) -> None:
    session = _build_session(tmp_path, "search_result_latest_missing.db")
    assert get_latest_search_result(keyword_id=999999, db=session) is None
    session.close()


def test_get_latest_search_result_dict_db() -> None:
    assert get_latest_search_result(keyword_id=1, db={}) is None
