"""Pricing-focused fixtures for dashboard and llm task tests."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from src.migrations.migration_13_ladder_revenue_llm_observability import upgrade
from src.models import (
    Base,
    Gig,
    Keyword,
    Niche,
    NichePriceAnalysis,
    PriceAnalysis,
    PriceLadderSnapshot,
    PricingSnapshot,
    Recommendation,
    RevenueGateRecord,
)


def _engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def _seed_keyword(session: Session, *, slug: str = "test_niche", keyword_text: str = "test keyword") -> Keyword:
    niche = Niche(slug=slug, name="Test Niche", category_path="Programming & Tech")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword=keyword_text,
        normalized_keyword=keyword_text,
        cluster_id=1,
    )
    session.add(keyword)
    session.flush()
    return keyword


@pytest.fixture
def seeded_price_db():
    """DB with 1 keyword + PriceAnalysis + 5 gigs with basic prices."""
    engine = _engine()
    with Session(engine) as session:
        keyword = _seed_keyword(session)
        session.add(
            PriceAnalysis(
                keyword_id=keyword.id,
                niche_id="test_niche",
                run_id="test-run",
                basic_n=5,
                basic_median=95.0,
                basic_mean=100.0,
                standard_n=5,
                standard_median=200.0,
                premium_n=5,
                premium_median=380.0,
                market_type="WIDE_SPREAD",
                moat_strength="LOW",
            )
        )
        for price in [75, 95, 95, 100, 125]:
            session.add(
                Gig(
                    keyword_id=keyword.id,
                    packages={"basic": {"price": price}},
                )
            )
        session.commit()
    return engine


@pytest.fixture
def seeded_analysis_no_gigs():
    """DB with PriceAnalysis present but no Gig package rows."""
    engine = _engine()
    with Session(engine) as session:
        keyword = _seed_keyword(session)
        session.add(
            PriceAnalysis(
                keyword_id=keyword.id,
                niche_id="test_niche",
                run_id="test-run",
                basic_n=5,
                basic_median=95.0,
                market_type="WIDE_SPREAD",
            )
        )
        session.commit()
    return engine


@pytest.fixture
def seeded_snapshot_db():
    """DB with PricingSnapshot for keyword 1."""
    engine = _engine()
    with Session(engine) as session:
        keyword = _seed_keyword(session)
        ladder = [
            {"milestone": m, "basic": 65 + m, "standard": 145 + m, "premium": 280 + m}
            for m in [5, 10, 25, 50, 100]
        ]
        session.add(
            PricingSnapshot(
                keyword_id=keyword.id,
                niche_id="test_niche",
                run_id="test-run",
                entry_basic=65.0,
                entry_standard=145.0,
                entry_premium=280.0,
                price_ladder=ladder,
                market_type="WIDE_SPREAD",
                confidence="MEDIUM",
            )
        )
        session.commit()
    return engine


@pytest.fixture
def seeded_snapshot_json_db():
    """DB with PricingSnapshot price_ladder stored as JSON string."""
    engine = _engine()
    with Session(engine) as session:
        keyword = _seed_keyword(session)
        ladder = [
            {"milestone": m, "basic": 65 + m, "standard": 145 + m, "premium": 280 + m}
            for m in [5, 10, 25, 50, 100]
        ]
        session.add(
            PricingSnapshot(
                keyword_id=keyword.id,
                niche_id="test_niche",
                run_id="test-run",
                entry_basic=65.0,
                entry_standard=145.0,
                entry_premium=280.0,
                price_ladder=json.dumps(ladder),
                market_type="WIDE_SPREAD",
                confidence="MEDIUM",
            )
        )
        session.commit()
    return engine


@pytest.fixture
def seeded_pricing_export_db():
    """DB with rows in all pricing export sources for keyword 1."""
    engine = _engine()
    with Session(engine) as session:
        keyword = _seed_keyword(session)
        ladder = [
            {"milestone": m, "basic": 60 + m, "standard": 140 + m, "premium": 270 + m}
            for m in [5, 10, 25, 50, 100]
        ]
        session.add(
            NichePriceAnalysis(
                niche_id="test_niche",
                run_id="r1",
                keywords_analyzed=1,
                basic_median=95.0,
                standard_median=145.0,
                premium_median=280.0,
                moat_strength="LOW",
            )
        )
        session.add(
            PriceAnalysis(
                keyword_id=keyword.id,
                niche_id="test_niche",
                run_id="r1",
                basic_n=5,
                basic_median=95.0,
                basic_mean=98.0,
                standard_n=5,
                standard_median=145.0,
                premium_n=5,
                premium_median=280.0,
                market_type="WIDE_SPREAD",
            )
        )
        session.add(
            PricingSnapshot(
                keyword_id=keyword.id,
                niche_id="test_niche",
                run_id="r1",
                entry_basic=65.0,
                entry_standard=145.0,
                entry_premium=280.0,
                price_ladder=json.dumps(ladder),
                market_type="WIDE_SPREAD",
                confidence="MEDIUM",
            )
        )
        session.add(
            PriceLadderSnapshot(
                keyword_id=keyword.id,
                niche_id="test_niche",
                run_id="r1",
                reviews_at_snapshot=5,
                ladder_milestone=5,
                actual_basic_price=68.0,
                recommended_basic_price=65.0,
                price_delta_pct=0.046,
                on_track=True,
            )
        )
        session.add(
            RevenueGateRecord(
                keyword_id=keyword.id,
                niche_id="test_niche",
                run_id="r1",
                milestone_reviews=5,
                gate_triggered=True,
                recommended_price_at_gate=65.0,
                revenue_delta_usd=260.0,
            )
        )
        session.add(
            Recommendation(
                keyword_id=keyword.id,
                recommendation_type="pricing_strategy",
                recommendation_text="Use ladder progression anchored to milestone wins.",
                confidence=0.88,
                raw_json={"pricing_strategy": {"entry": 65.0, "confidence": "MEDIUM"}},
            )
        )
        session.commit()
    return engine


@pytest.fixture
def seeded_multi_keyword_db():
    """DB with multiple keywords and price analyses in same niche."""
    engine = _engine()
    with Session(engine) as session:
        niche = Niche(slug="prd_ai_saas", name="PRD AI SaaS", category_path="Programming & Tech")
        session.add(niche)
        session.flush()
        for idx, name in enumerate(["kw one", "kw two", "kw three"], start=1):
            keyword = Keyword(
                niche_id=niche.id,
                keyword=name,
                normalized_keyword=name,
                cluster_id=idx,
            )
            session.add(keyword)
            session.flush()
            session.add(
                PriceAnalysis(
                    keyword_id=keyword.id,
                    niche_id=niche.slug,
                    run_id="test-run",
                    basic_median=90.0 + idx,
                    standard_median=180.0 + idx,
                    premium_median=300.0 + idx,
                )
            )
        session.commit()
    return engine


@pytest.fixture
def seeded_large_pricing_db():
    """DB with >20 ladder rows to test markdown row caps."""
    engine = _engine()
    with Session(engine) as session:
        keyword = _seed_keyword(session)
        session.add(
            PriceAnalysis(
                keyword_id=keyword.id,
                niche_id="test_niche",
                run_id="test-run",
                basic_n=30,
                basic_median=95.0,
                standard_n=30,
                standard_median=145.0,
                premium_n=30,
                premium_median=280.0,
                market_type="WIDE_SPREAD",
            )
        )
        for idx in range(30):
            session.add(
                PriceLadderSnapshot(
                    keyword_id=keyword.id,
                    niche_id="test_niche",
                    run_id=f"r{idx}",
                    reviews_at_snapshot=idx + 1,
                    ladder_milestone=5,
                    actual_basic_price=70.0 + idx,
                    recommended_basic_price=65.0,
                    price_delta_pct=0.1,
                    on_track=True,
                )
            )
        session.commit()
    return engine


@pytest.fixture
def seeded_long_name_db():
    """DB with long keyword names for truncation checks."""
    engine = _engine()
    with Session(engine) as session:
        niche = Niche(slug="test_niche", name="Test Niche", category_path="Programming & Tech")
        session.add(niche)
        session.flush()
        long_name = "x" * 80
        keyword = Keyword(
            niche_id=niche.id,
            keyword=long_name,
            normalized_keyword=long_name,
            cluster_id=1,
        )
        session.add(keyword)
        session.flush()
        session.add(
            PriceAnalysis(
                keyword_id=keyword.id,
                niche_id=niche.slug,
                run_id="test-run",
                basic_median=101.0,
                standard_median=201.0,
                premium_median=301.0,
            )
        )
        session.commit()
    return engine


@pytest.fixture
def mock_recommendation():
    """Recommendation-like object for pricing narrative tests."""
    return SimpleNamespace(pricing_strategy=None)


@pytest.fixture
def empty_db():
    """In-memory DB with schema and no seeded rows."""
    return _engine()


@pytest.fixture
def seeded_ladder_db():
    """DB with PricingSnapshot containing a ladder and one PriceLadderSnapshot."""
    engine = _engine()
    with Session(engine) as session:
        keyword = _seed_keyword(session)
        ladder = [
            {"milestone": m, "basic": 65 + m, "standard": 145 + m, "premium": 280 + m}
            for m in [5, 10, 25, 50, 100]
        ]
        session.add(
            PricingSnapshot(
                keyword_id=keyword.id,
                niche_id="test_niche",
                run_id="test",
                entry_basic=65.0,
                entry_standard=145.0,
                entry_premium=280.0,
                price_ladder=json.dumps(ladder),
                market_type="WIDE_SPREAD",
                confidence="MEDIUM",
            )
        )
        session.add(
            PriceLadderSnapshot(
                keyword_id=keyword.id,
                niche_id="test_niche",
                run_id="test",
                reviews_at_snapshot=5,
                ladder_milestone=5,
                actual_basic_price=70.0,
                recommended_basic_price=70.0,
                price_delta_pct=0.0,
                on_track=True,
                tolerance=0.15,
            )
        )
        session.commit()
    return engine


@pytest.fixture
def seeded_exact_match_db():
    """DB where actual basic price can exactly match recommendation (delta=0)."""
    engine = _engine()
    with Session(engine) as session:
        keyword = _seed_keyword(session)
        ladder = [{"milestone": 5, "basic": 95.0, "standard": 200.0, "premium": 380.0}]
        session.add(
            PricingSnapshot(
                keyword_id=keyword.id,
                niche_id="test",
                run_id="test",
                entry_basic=65.0,
                entry_standard=145.0,
                entry_premium=280.0,
                price_ladder=json.dumps(ladder),
                market_type="WIDE_SPREAD",
                confidence="HIGH",
            )
        )
        session.commit()
    return engine


@pytest.fixture
def seeded_off_track_snapshot_db():
    """DB with a PriceLadderSnapshot where price_delta_pct > 0.15."""
    engine = _engine()
    with Session(engine) as session:
        keyword = _seed_keyword(session)
        session.add(
            PriceLadderSnapshot(
                keyword_id=keyword.id,
                niche_id="test",
                run_id="test",
                reviews_at_snapshot=10,
                ladder_milestone=10,
                actual_basic_price=120.0,
                recommended_basic_price=95.0,
                price_delta_pct=0.263,
                on_track=False,
                tolerance=0.15,
            )
        )
        session.commit()
    return engine


@pytest.fixture
def empty_db_with_migration():
    """Pre-migration schema for llm_usage_logs then upgrade() to add task_type."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE llm_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name VARCHAR(128)
                )
                """
            )
        )
        connection.execute(text("CREATE TABLE keywords (id INTEGER PRIMARY KEY AUTOINCREMENT)"))
    upgrade(engine)
    return engine
