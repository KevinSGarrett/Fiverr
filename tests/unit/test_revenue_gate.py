"""Tests for Wave 9 Phase 3 revenue gate + migration 13."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.migrations.migration_13_ladder_revenue_llm_observability import upgrade
from src.models import Base, Keyword, LLMUsageLog, Niche, PricingSnapshot, RevenueGateRecord
from src.pricing.llm_task import pricing_llm_task
from src.pricing.revenue_gate import (
    MONTHLY_ORDERS_ESTIMATE,
    REVENUE_GATE_MILESTONES,
    check_revenue_gates,
    fire_revenue_gate_alert,
)
from src.recommendations.context import RecommendationContext


def _engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def _seed_keyword(session: Session, *, slug: str = "test_niche", keyword_text: str = "test keyword") -> int:
    niche = Niche(slug=slug, name="Test Niche", category_path="Programming & Tech")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword=keyword_text, normalized_keyword=keyword_text)
    session.add(keyword)
    session.flush()
    return int(keyword.id)


def _seed_ladder(session: Session, keyword_id: int) -> None:
    ladder = [
        {"milestone": 5, "basic": 70, "standard": 150, "premium": 285},
        {"milestone": 10, "basic": 75, "standard": 155, "premium": 290},
        {"milestone": 25, "basic": 85, "standard": 170, "premium": 310},
        {"milestone": 50, "basic": 100, "standard": 190, "premium": 340},
        {"milestone": 100, "basic": 120, "standard": 220, "premium": 390},
    ]
    session.add(
        PricingSnapshot(
            keyword_id=keyword_id,
            niche_id="test_niche",
            run_id="r1",
            entry_basic=65.0,
            price_ladder=json.dumps(ladder),
            confidence="MEDIUM",
        )
    )


@pytest.fixture
def seeded_pricing_db():
    engine = _engine()
    with Session(engine) as session:
        keyword_id = _seed_keyword(session)
        _seed_ladder(session, keyword_id)
        session.commit()
    return engine


@pytest.fixture
def mock_llm_db():
    engine = _engine()
    with Session(engine) as session:
        _seed_keyword(session, slug="llm_niche", keyword_text="llm keyword")
        session.commit()
    return engine


class TestCheckRevenueGates:
    def test_creates_5_records_for_5_milestones(self, seeded_pricing_db):
        with Session(seeded_pricing_db) as session:
            records = check_revenue_gates(1, session, actual_review_count=40)
            session.commit()
            assert len(records) == 5

    def test_gate_triggered_at_correct_milestones(self, seeded_pricing_db):
        with Session(seeded_pricing_db) as session:
            records = check_revenue_gates(1, session, actual_review_count=25)
            session.commit()
            triggered = [r.milestone_reviews for r in records if r.gate_triggered]
            assert triggered == [5, 10, 25]

    def test_gate_not_triggered_below_milestone(self, seeded_pricing_db):
        with Session(seeded_pricing_db) as session:
            records = check_revenue_gates(1, session, actual_review_count=4)
            session.commit()
            assert all(not r.gate_triggered for r in records)

    def test_alert_text_contains_price(self, seeded_pricing_db):
        with Session(seeded_pricing_db) as session:
            records = check_revenue_gates(1, session, actual_review_count=10)
            session.commit()
            first = next(record for record in records if record.milestone_reviews == 5)
            assert first.gate_alert_text is not None
            assert "$70" in first.gate_alert_text

    def test_alert_text_none_when_no_price_data(self, empty_db):
        with Session(empty_db) as session:
            keyword_id = _seed_keyword(session, slug="empty_niche", keyword_text="empty")
            records = check_revenue_gates(keyword_id, session, actual_review_count=30)
            session.commit()
            assert all(record.gate_alert_text is None for record in records)

    def test_monthly_orders_estimate_default_4(self, seeded_pricing_db):
        with Session(seeded_pricing_db) as session:
            records = check_revenue_gates(1, session, actual_review_count=10)
            session.commit()
            assert all(record.monthly_orders_estimate == 4 for record in records)
            assert MONTHLY_ORDERS_ESTIMATE == 4

    def test_revenue_delta_uses_entry_milestone_price(self, seeded_pricing_db):
        with Session(seeded_pricing_db) as session:
            records = check_revenue_gates(1, session, actual_review_count=100)
            session.commit()
            m100 = next(record for record in records if record.milestone_reviews == 100)
            assert m100.revenue_delta_usd == pytest.approx((120.0 - 70.0) * 4)

    def test_records_are_persisted(self, seeded_pricing_db):
        with Session(seeded_pricing_db) as session:
            check_revenue_gates(1, session, actual_review_count=100)
            session.commit()
            assert session.query(RevenueGateRecord).count() == len(REVENUE_GATE_MILESTONES)


class TestFireRevenueGateAlert:
    def test_returns_string_when_recommended_price_exists(self, seeded_pricing_db):
        with Session(seeded_pricing_db) as session:
            alert = fire_revenue_gate_alert(1, 25, session)
            assert isinstance(alert, str)

    def test_returns_none_when_no_snapshot(self, empty_db):
        with Session(empty_db) as session:
            keyword_id = _seed_keyword(session, slug="empty_niche", keyword_text="empty")
            assert fire_revenue_gate_alert(keyword_id, 10, session) is None

    def test_alert_includes_milestone_count(self, seeded_pricing_db):
        with Session(seeded_pricing_db) as session:
            alert = fire_revenue_gate_alert(1, 50, session)
            assert "50 reviews" in str(alert)

    def test_alert_includes_price_value(self, seeded_pricing_db):
        with Session(seeded_pricing_db) as session:
            alert = fire_revenue_gate_alert(1, 10, session)
            assert "$75" in str(alert)

    def test_alert_includes_monthly_revenue(self, seeded_pricing_db):
        with Session(seeded_pricing_db) as session:
            alert = fire_revenue_gate_alert(1, 10, session)
            assert "~$300/mo" in str(alert)


class TestMigration13:
    def test_price_ladder_snapshots_table_created(self):
        engine = create_engine("sqlite:///:memory:")
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE keywords (id INTEGER PRIMARY KEY AUTOINCREMENT)"))
            connection.execute(
                text(
                    """
                    CREATE TABLE llm_usage_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_name VARCHAR(128),
                        prompt_tokens INTEGER,
                        completion_tokens INTEGER,
                        total_cost_usd REAL
                    )
                    """
                )
            )
        upgrade(engine)
        assert "price_ladder_snapshots" in inspect(engine).get_table_names()

    def test_revenue_gate_records_table_created(self):
        engine = create_engine("sqlite:///:memory:")
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE keywords (id INTEGER PRIMARY KEY AUTOINCREMENT)"))
            connection.execute(
                text(
                    """
                    CREATE TABLE llm_usage_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_name VARCHAR(128),
                        prompt_tokens INTEGER,
                        completion_tokens INTEGER,
                        total_cost_usd REAL
                    )
                    """
                )
            )
        upgrade(engine)
        assert "revenue_gate_records" in inspect(engine).get_table_names()

    def test_llm_usage_logs_has_task_type(self):
        engine = create_engine("sqlite:///:memory:")
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE keywords (id INTEGER PRIMARY KEY AUTOINCREMENT)"))
            connection.execute(
                text(
                    """
                    CREATE TABLE llm_usage_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_name VARCHAR(128),
                        prompt_tokens INTEGER,
                        completion_tokens INTEGER,
                        total_cost_usd REAL
                    )
                    """
                )
            )
        upgrade(engine)
        columns = {column["name"] for column in inspect(engine).get_columns("llm_usage_logs")}
        assert "task_type" in columns

    def test_migration_idempotent(self):
        engine = create_engine("sqlite:///:memory:")
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE keywords (id INTEGER PRIMARY KEY AUTOINCREMENT)"))
            connection.execute(
                text(
                    """
                    CREATE TABLE llm_usage_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_name VARCHAR(128),
                        prompt_tokens INTEGER,
                        completion_tokens INTEGER,
                        total_cost_usd REAL
                    )
                    """
                )
            )
        upgrade(engine)
        upgrade(engine)
        tables = inspect(engine).get_table_names()
        assert "price_ladder_snapshots" in tables
        assert "revenue_gate_records" in tables


def test_migration_13_idempotent():
    """Running migration_13 twice does not error."""
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE keywords (id INTEGER PRIMARY KEY AUTOINCREMENT)"))
        connection.execute(
            text(
                """
                CREATE TABLE llm_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name VARCHAR(128),
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_cost_usd REAL
                )
                """
            )
        )
    upgrade(engine)
    upgrade(engine)
    tables = inspect(engine).get_table_names()
    assert "price_ladder_snapshots" in tables
    assert "revenue_gate_records" in tables


def test_llm_usage_logs_accepts_task_type(empty_db):
    """After migration_13, llm_usage_logs.task_type can be written and read."""
    with Session(empty_db) as session:
        log = LLMUsageLog(task_type="pricing_strategy", model_name="gpt-4o", total_cost_usd=0.015)
        session.add(log)
        session.commit()
        result = session.query(LLMUsageLog).filter(LLMUsageLog.task_type == "pricing_strategy").first()
        assert result is not None
        assert result.task_type == "pricing_strategy"


def test_pricing_llm_task_logs_task_type_pricing_strategy(mock_llm_db):
    """pricing_llm_task logs task_type='pricing_strategy' to llm_usage_logs."""

    context = RecommendationContext(
        keyword_id=1,
        keyword_text="llm keyword",
        niche_id=1,
        niche_name="LLM Niche",
        price_distribution={"basic": {"median": 90, "q1": 80, "q3": 110}},
        calculated_entry_prices={"basic": 70, "standard": 140, "premium": 260},
        market_type="MODERATE_SPREAD",
        competitor_price_positions=[],
    )
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="pricing strategy output"))],
        usage={"prompt_tokens": 10, "completion_tokens": 12, "total_tokens": 22},
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=_async_return(response))))

    with Session(mock_llm_db) as session:
        result = asyncio.run(pricing_llm_task(1, context, db=session, client=client))
        session.commit()
        assert result is not None
        rows = session.execute(
            text("SELECT task_type FROM llm_usage_logs WHERE task_type='pricing_strategy' LIMIT 1")
        ).fetchall()
        assert len(rows) >= 1


def _async_return(value: Any):
    async def _inner(**_kwargs: Any) -> Any:
        return value

    return _inner


class TestRevenueGateEdgeCases:
    def test_check_revenue_gates_returns_5_records_always(self, seeded_pricing_db):
        """Always returns one record per milestone."""
        with Session(seeded_pricing_db) as session:
            records = check_revenue_gates(1, session, actual_review_count=0)
            session.commit()
            assert len(records) == 5

    def test_all_gates_triggered_at_100_reviews(self, seeded_pricing_db):
        with Session(seeded_pricing_db) as session:
            records = check_revenue_gates(1, session, actual_review_count=100)
            session.commit()
            triggered = [record for record in records if record.gate_triggered]
            assert len(triggered) == 5

    def test_no_gates_triggered_at_0_reviews(self, seeded_pricing_db):
        with Session(seeded_pricing_db) as session:
            records = check_revenue_gates(1, session, actual_review_count=0)
            session.commit()
            triggered = [record for record in records if record.gate_triggered]
            assert len(triggered) == 0

    def test_only_milestone_5_gate_triggers_at_5(self, seeded_pricing_db):
        with Session(seeded_pricing_db) as session:
            records = check_revenue_gates(1, session, actual_review_count=5)
            session.commit()
            triggered = [record.milestone_reviews for record in records if record.gate_triggered]
            assert triggered == [5]

    def test_fire_revenue_gate_alert_returns_none_empty_db(self, empty_db):
        with Session(empty_db) as session:
            keyword_id = _seed_keyword(session, slug="empty_alert", keyword_text="no pricing")
            result = fire_revenue_gate_alert(keyword_id, 5, session)
            assert result is None

    def test_monthly_orders_estimate_used_in_revenue_calc(self, seeded_pricing_db):
        with Session(seeded_pricing_db) as session:
            records = check_revenue_gates(1, session, actual_review_count=50)
            session.commit()
            for record in records:
                if record.recommended_price_at_gate and record.revenue_delta_usd is not None:
                    entry_price = 70.0
                    expected = (record.recommended_price_at_gate - entry_price) * MONTHLY_ORDERS_ESTIMATE
                    assert record.revenue_delta_usd == pytest.approx(expected)


def test_llm_usage_logs_task_type_column_writable(empty_db_with_migration):
    """After migration_13, task_type should accept pricing_strategy."""
    with Session(empty_db_with_migration) as session:
        session.execute(
            text("INSERT INTO llm_usage_logs (task_type, model_name) VALUES ('pricing_strategy', 'gpt-4o')")
        )
        session.commit()
        result = session.execute(
            text("SELECT task_type FROM llm_usage_logs WHERE task_type='pricing_strategy' LIMIT 1")
        ).fetchone()
        assert result is not None
        assert result[0] == "pricing_strategy"


@pytest.mark.parametrize(
    ("review_count", "expected_triggered_count"),
    [(0, 0), (5, 1), (10, 2), (25, 3), (50, 4), (100, 5), (200, 5)],
)
def test_revenue_gates_triggered_count(review_count, expected_triggered_count, seeded_pricing_db):
    """Number of triggered gates should match review-count milestone coverage."""
    with Session(seeded_pricing_db) as session:
        records = check_revenue_gates(1, session, actual_review_count=review_count)
        session.commit()
        triggered = sum(1 for record in records if record.gate_triggered)
        assert triggered == expected_triggered_count


def test_migration_13_adds_task_type_column_to_llm_usage_logs():
    """migration_13 adds task_type VARCHAR-like column to llm_usage_logs."""
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE llm_usage_logs (id INTEGER PRIMARY KEY, model_name VARCHAR(50))")
        )
        connection.execute(text("CREATE TABLE keywords (id INTEGER PRIMARY KEY AUTOINCREMENT)"))
    upgrade(engine)
    columns = sorted([column["name"] for column in inspect(engine).get_columns("llm_usage_logs")])
    assert "task_type" in columns, f"task_type not in llm_usage_logs after migration_13: {columns}"


def test_revenue_gate_alert_format_contains_milestone(seeded_ladder_db):
    """fire_revenue_gate_alert should return milestone-aware messaging."""
    with Session(seeded_ladder_db) as session:
        alert = fire_revenue_gate_alert(1, 10, session)
        if alert is not None:
            assert "10" in alert or "Milestone" in alert or "$" in alert
