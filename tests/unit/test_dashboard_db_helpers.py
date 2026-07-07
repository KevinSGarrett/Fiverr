"""Codex review finding on PR #165 (SCRUM-1111): the dashboard's get_db_session() built
a bare create_engine() and never called initialize_database()/run_srdi_r8_migrations(),
so opening the dashboard directly against an existing DB file created before a later
migration (e.g. migration_15's PriceAnalysis min/max columns) would hit a missing-column
error the moment a page queried that column.
"""
from __future__ import annotations

from sqlalchemy import create_engine, inspect, text


def test_get_db_session_heals_a_legacy_pre_migration_db(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "legacy_fiverr_research.db"

    # Build a legacy DB file matching migration_12's real original price_analysis shape -
    # i.e. exactly what a DB created before migration_15 existed actually looks like
    # (migration_12 creates price_analysis with CREATE TABLE IF NOT EXISTS and does not
    # backfill missing columns onto an existing table, so this is the realistic case).
    legacy_engine = create_engine(f"sqlite:///{db_path.as_posix()}", future=True)
    with legacy_engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE price_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword_id INTEGER NOT NULL,
                    niche_id VARCHAR(128) NOT NULL,
                    run_id VARCHAR(128) NOT NULL,
                    basic_n INTEGER,
                    basic_median FLOAT,
                    basic_mean FLOAT,
                    basic_mode FLOAT,
                    basic_std FLOAT,
                    basic_q1 FLOAT,
                    basic_q3 FLOAT,
                    basic_p10 FLOAT,
                    basic_p90 FLOAT,
                    basic_skewness FLOAT,
                    basic_cv FLOAT,
                    basic_clusters JSON,
                    basic_gaps JSON,
                    standard_n INTEGER,
                    standard_median FLOAT,
                    standard_mean FLOAT,
                    standard_mode FLOAT,
                    standard_std FLOAT,
                    standard_q1 FLOAT,
                    standard_q3 FLOAT,
                    standard_p10 FLOAT,
                    standard_p90 FLOAT,
                    standard_skewness FLOAT,
                    standard_cv FLOAT,
                    standard_clusters JSON,
                    standard_gaps JSON,
                    premium_n INTEGER,
                    premium_median FLOAT,
                    premium_mean FLOAT,
                    premium_mode FLOAT,
                    premium_std FLOAT,
                    premium_q1 FLOAT,
                    premium_q3 FLOAT,
                    premium_p10 FLOAT,
                    premium_p90 FLOAT,
                    premium_skewness FLOAT,
                    premium_cv FLOAT,
                    premium_clusters JSON,
                    premium_gaps JSON,
                    price_review_correlation FLOAT,
                    moat_strength VARCHAR(16),
                    review_premium_usd FLOAT,
                    new_seller_avg_price FLOAT,
                    new_seller_discount_pct FLOAT,
                    market_type VARCHAR(32),
                    avg_extras_count FLOAT,
                    avg_extras_price FLOAT,
                    extras_price_range JSON,
                    analyzed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(keyword_id) REFERENCES keywords (id),
                    CONSTRAINT uq_price_analysis_keyword_run UNIQUE (keyword_id, run_id)
                )
                """
            )
        )
    legacy_engine.dispose()

    columns_before = {c["name"] for c in inspect(legacy_engine).get_columns("price_analysis")}
    assert "basic_min" not in columns_before  # confirms this really is a pre-migration_15 shape

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    from src.dashboard.db_helpers import get_db_session
    from src.models.price_analysis import PriceAnalysis

    with get_db_session() as db:
        # Must not raise "no such column: price_analysis.basic_min" - proves the session
        # is backed by a fully-migrated engine, not the raw legacy file.
        rows = db.query(PriceAnalysis).all()
        assert rows == []

    healed_engine = create_engine(f"sqlite:///{db_path.as_posix()}", future=True)
    columns_after = {c["name"] for c in inspect(healed_engine).get_columns("price_analysis")}
    assert "basic_min" in columns_after
    assert "basic_max" in columns_after
    healed_engine.dispose()
