"""Unit tests for Gig ORM model and Stage-4 helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base, Gig, Keyword, Niche, get_gigs_for_keyword, write_gig_card


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return factory()


def _seed_keyword(session: Session, value: str = "gig model keyword") -> int:
    niche = Niche(slug=f"{value.replace(' ', '-')}-slug", name=value, category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword=value, normalized_keyword=value)
    session.add(keyword)
    session.commit()
    return int(keyword.id)


def test_gig_table_name() -> None:
    assert Gig.__tablename__ == "gigs"


def test_gig_insert_minimal() -> None:
    session = _session()
    session.add(Gig(gig_url="https://www.fiverr.com/gigs/minimal", seller_username="seller_min"))
    session.commit()
    persisted = session.query(Gig).filter(Gig.gig_url == "https://www.fiverr.com/gigs/minimal").one()
    assert persisted.seller_username == "seller_min"
    session.close()


def test_gig_insert_full() -> None:
    session = _session()
    keyword_id = _seed_keyword(session, "gig full insert")
    row = Gig(
        gig_url="https://www.fiverr.com/gigs/full",
        keyword_id=keyword_id,
        run_id="run-full",
        seller_username="seller_full",
        gig_title_full="Full Gig Title",
        description_text="Full description text",
        packages=[{"tier": "Basic", "price": 95, "delivery_days": 3, "items": ["A", "B"]}],
        gig_extras=[{"name": "Extra fast", "price": 25, "description": "24h delivery"}],
        tags=["ai", "automation"],
        faq_text="Q: turnaround? A: 2 days",
        video_present=True,
        portfolio_count=4,
        review_count_exact=102,
        rating_exact=4.9,
        review_snippets=[{"reviewer": "alice", "rating": 5, "text": "great"}],
        starting_price=95.0,
        thumbnail_url="https://cdn.example/thumb.jpg",
        orders_in_queue=6,
        position=2,
        detail_collected=True,
        detail_collected_at=datetime.now(UTC),
        ttl_hours=168,
        sponsored_flag=True,
    )
    session.add(row)
    session.commit()
    assert row.id is not None
    session.close()


def test_gig_unique_gig_url() -> None:
    session = _session()
    session.add_all(
        [
            Gig(gig_url="https://www.fiverr.com/gigs/dup", seller_username="dup_1"),
            Gig(gig_url="https://www.fiverr.com/gigs/dup", seller_username="dup_2"),
        ]
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.close()


def test_gig_detail_collected_default() -> None:
    row = Gig(gig_url="https://www.fiverr.com/gigs/default", seller_username="seller_default")
    assert row.detail_collected is False


def test_gig_is_stale_not_collected() -> None:
    row = Gig(gig_url="https://www.fiverr.com/gigs/stale-none", seller_username="seller_none")
    assert row.is_stale() is True


def test_gig_is_stale_fresh() -> None:
    row = Gig(
        gig_url="https://www.fiverr.com/gigs/stale-fresh",
        seller_username="seller_fresh",
        detail_collected=True,
        detail_collected_at=datetime.now(UTC) - timedelta(hours=1),
        ttl_hours=168,
    )
    assert row.is_stale() is False


def test_gig_is_stale_expired() -> None:
    row = Gig(
        gig_url="https://www.fiverr.com/gigs/stale-expired",
        seller_username="seller_expired",
        detail_collected=True,
        detail_collected_at=datetime.now(UTC) - timedelta(hours=170),
        ttl_hours=168,
    )
    assert row.is_stale() is True


def test_write_gig_card_dict_db() -> None:
    row = write_gig_card(
        gig_url="https://www.fiverr.com/gigs/helper-dict",
        keyword_id=1,
        run_id="run-dict",
        seller_username="seller_dict",
        position=1,
        starting_price=50.0,
        gig_title="Dict DB",
        sponsored_flag=False,
        db={},
    )
    assert row is None


def test_write_gig_card_orm() -> None:
    session = _session()
    keyword_id = _seed_keyword(session, "write gig card")
    row = write_gig_card(
        gig_url="https://www.fiverr.com/gigs/helper-orm",
        keyword_id=keyword_id,
        run_id="run-orm",
        seller_username="seller_orm",
        position=3,
        starting_price=75.0,
        gig_title="ORM Gig Card",
        sponsored_flag=True,
        db=session,
    )
    assert row is not None
    persisted = session.query(Gig).filter(Gig.gig_url == "https://www.fiverr.com/gigs/helper-orm").one()
    assert persisted.position == 3
    session.close()


def test_write_gig_card_upsert() -> None:
    session = _session()
    keyword_id = _seed_keyword(session, "upsert gig card")
    write_gig_card(
        gig_url="https://www.fiverr.com/gigs/helper-upsert",
        keyword_id=keyword_id,
        run_id="run-a",
        seller_username="seller_a",
        position=10,
        starting_price=40.0,
        gig_title="Initial",
        sponsored_flag=False,
        db=session,
    )
    write_gig_card(
        gig_url="https://www.fiverr.com/gigs/helper-upsert",
        keyword_id=keyword_id,
        run_id="run-b",
        seller_username="seller_b",
        position=1,
        starting_price=120.0,
        gig_title="Updated",
        sponsored_flag=True,
        db=session,
    )
    rows = session.query(Gig).filter(Gig.gig_url == "https://www.fiverr.com/gigs/helper-upsert").all()
    assert len(rows) == 1
    assert rows[0].run_id == "run-b"
    assert rows[0].position == 1
    assert rows[0].seller_username == "seller_b"
    session.close()


def test_get_gigs_for_keyword_empty() -> None:
    session = _session()
    keyword_id = _seed_keyword(session, "empty lookup")
    assert get_gigs_for_keyword(keyword_id=keyword_id, db=session) == []
    session.close()


def test_get_gigs_for_keyword_dict_db() -> None:
    assert get_gigs_for_keyword(keyword_id=1, db={}) == []


def test_get_gigs_for_keyword_ordered() -> None:
    session = _session()
    keyword_id = _seed_keyword(session, "ordered lookup")
    other_keyword_id = _seed_keyword(session, "other lookup")
    session.add_all(
        [
            Gig(gig_url="https://www.fiverr.com/gigs/order-3", seller_username="seller3", keyword_id=keyword_id, position=3),
            Gig(gig_url="https://www.fiverr.com/gigs/order-1", seller_username="seller1", keyword_id=keyword_id, position=1),
            Gig(gig_url="https://www.fiverr.com/gigs/order-none", seller_username="sellern", keyword_id=keyword_id, position=None),
            Gig(gig_url="https://www.fiverr.com/gigs/order-other", seller_username="sellero", keyword_id=other_keyword_id, position=0),
        ]
    )
    session.commit()
    ordered = get_gigs_for_keyword(keyword_id=keyword_id, db=session, limit=20)
    assert [row.gig_url for row in ordered] == [
        "https://www.fiverr.com/gigs/order-1",
        "https://www.fiverr.com/gigs/order-3",
        "https://www.fiverr.com/gigs/order-none",
    ]
    session.close()


def test_gig_packages_json() -> None:
    session = _session()
    packages = [
        {"tier": "Basic", "price": 50, "delivery_days": 3, "items": ["feature_a"]},
        {"tier": "Premium", "price": 150, "delivery_days": 7, "items": ["feature_a", "feature_b"]},
    ]
    session.add(Gig(gig_url="https://www.fiverr.com/gigs/json", seller_username="json_seller", packages=packages))
    session.commit()
    persisted = session.query(Gig).filter(Gig.gig_url == "https://www.fiverr.com/gigs/json").one()
    assert persisted.packages == packages
    session.close()
