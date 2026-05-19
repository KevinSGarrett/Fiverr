"""Unit tests for Seller ORM model and Stage-5 helper functions."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base, Seller, get_seller, write_seller_profile


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return factory()


def test_seller_table_name() -> None:
    assert Seller.__tablename__ == "sellers"


def test_seller_insert_minimal() -> None:
    session = _session()
    session.add(Seller(seller_username="seller_minimal"))
    session.commit()
    persisted = session.query(Seller).filter(Seller.seller_username == "seller_minimal").one()
    assert persisted.seller_username == "seller_minimal"
    session.close()


def test_seller_insert_full() -> None:
    session = _session()
    row = Seller(
        seller_username="seller_full",
        run_id="run-full",
        seller_level="LEVEL_2",
        member_since="2021-07",
        response_time="1 hour",
        response_rate="98%",
        languages=["English", "Spanish"],
        bio_text="Experienced Fiverr seller.",
        total_reviews=320,
        total_gigs=14,
        gig_titles=["I will build your app", "I will fix your bug"],
        portfolio_item_count=9,
        badges=["Top Rated", "Pro"],
        profile_url="https://www.fiverr.com/seller_full",
        profile_collected=True,
    )
    session.add(row)
    session.commit()
    assert row.id is not None
    session.close()


def test_seller_unique_username() -> None:
    session = _session()
    session.add_all([Seller(seller_username="seller_dup"), Seller(seller_username="seller_dup")])
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
    else:
        raise AssertionError("Expected IntegrityError for duplicate seller_username")
    session.close()


def test_seller_default_ttl() -> None:
    row = Seller(seller_username="seller_ttl")
    assert row.ttl_hours == 720


def test_seller_profile_collected_default() -> None:
    row = Seller(seller_username="seller_default")
    assert row.profile_collected is False


def test_write_seller_dict_db() -> None:
    row = write_seller_profile(
        seller_username="seller_dict",
        run_id="run-dict",
        seller_level="LEVEL_1",
        member_since="2022-02",
        response_time="2 hours",
        total_reviews=11,
        total_gigs=5,
        db={},
    )
    assert row is None


def test_write_seller_orm() -> None:
    session = _session()
    row = write_seller_profile(
        seller_username="seller_orm",
        run_id="run-orm",
        seller_level="TRS",
        member_since="2020-09",
        response_time="1 hour",
        total_reviews=501,
        total_gigs=22,
        db=session,
    )
    assert row is not None
    persisted = session.query(Seller).filter(Seller.seller_username == "seller_orm").one()
    assert persisted.profile_collected is True
    assert persisted.total_reviews == 501
    session.close()


def test_write_seller_upsert() -> None:
    session = _session()
    write_seller_profile(
        seller_username="seller_upsert",
        run_id="run-a",
        seller_level="LEVEL_1",
        member_since="2023-01",
        response_time="2 hours",
        total_reviews=5,
        total_gigs=2,
        db=session,
    )
    write_seller_profile(
        seller_username="seller_upsert",
        run_id="run-b",
        seller_level="LEVEL_2",
        member_since="2023-01",
        response_time="1 hour",
        total_reviews=9,
        total_gigs=4,
        db=session,
    )
    rows = session.query(Seller).filter(Seller.seller_username == "seller_upsert").all()
    assert len(rows) == 1
    assert rows[0].run_id == "run-b"
    assert rows[0].seller_level == "LEVEL_2"
    assert rows[0].total_reviews == 9
    session.close()


def test_get_seller_found() -> None:
    session = _session()
    session.add(Seller(seller_username="seller_found"))
    session.commit()
    row = get_seller("seller_found", session)
    assert row is not None
    assert row.seller_username == "seller_found"
    session.close()


def test_get_seller_missing() -> None:
    session = _session()
    row = get_seller("missing_seller", session)
    assert row is None
    session.close()


def test_get_seller_dict_db_returns_none() -> None:
    assert get_seller("any_seller", {}) is None


def test_seller_handle_property_alias() -> None:
    row = Seller(seller_username="alias_user")
    assert row.seller_handle == "alias_user"
    row.seller_handle = "alias_changed"
    assert row.seller_username == "alias_changed"


def test_level_property_alias() -> None:
    row = Seller(seller_username="level_user", seller_level="LEVEL_1")
    assert row.level == "LEVEL_1"
    row.level = "TRS"
    assert row.seller_level == "TRS"


def test_active_gig_titles_alias() -> None:
    row = Seller(seller_username="gig_titles_user", gig_titles=["A"])
    assert row.active_gig_titles == ["A"]
    row.active_gig_titles = ["B", "C"]
    assert row.gig_titles == ["B", "C"]


def test_portfolio_count_alias() -> None:
    row = Seller(seller_username="portfolio_user", portfolio_item_count=3)
    assert row.portfolio_count == 3
    row.portfolio_count = 10
    assert row.portfolio_item_count == 10


def test_seller_in_base_metadata() -> None:
    assert "sellers" in Base.metadata.tables
