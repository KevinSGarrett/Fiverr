"""C064 migration 13: ladder snapshots, revenue gates, llm task_type observability."""

from __future__ import annotations

from sqlalchemy import Engine, inspect, text


def _column_names(engine: Engine, table_name: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table_name)}


def upgrade(engine: Engine) -> None:
    """Apply migration 13 schema changes idempotently."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS price_ladder_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword_id INTEGER NOT NULL REFERENCES keywords(id),
                    niche_id VARCHAR(100) NOT NULL,
                    run_id VARCHAR(100),
                    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reviews_at_snapshot INTEGER,
                    ladder_milestone INTEGER,
                    actual_basic_price REAL,
                    actual_standard_price REAL,
                    actual_premium_price REAL,
                    recommended_basic_price REAL,
                    recommended_standard_price REAL,
                    recommended_premium_price REAL,
                    price_delta_pct REAL,
                    on_track BOOLEAN DEFAULT 1,
                    tolerance REAL DEFAULT 0.15
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_price_ladder_snapshots_keyword_id ON price_ladder_snapshots (keyword_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_price_ladder_snapshots_niche_id ON price_ladder_snapshots (niche_id)"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS revenue_gate_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword_id INTEGER NOT NULL REFERENCES keywords(id),
                    niche_id VARCHAR(100),
                    run_id VARCHAR(100),
                    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    milestone_reviews INTEGER,
                    gate_triggered BOOLEAN DEFAULT 0,
                    recommended_price_at_gate REAL,
                    actual_price_at_gate REAL,
                    revenue_delta_usd REAL,
                    monthly_orders_estimate INTEGER DEFAULT 4,
                    gate_alert_text VARCHAR(500)
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_revenue_gate_records_keyword_id ON revenue_gate_records (keyword_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_revenue_gate_records_niche_id ON revenue_gate_records (niche_id)"))

        try:
            existing = _column_names(engine, "llm_usage_logs")
            if "task_type" not in existing:
                conn.execute(text("ALTER TABLE llm_usage_logs ADD COLUMN task_type VARCHAR(64) DEFAULT NULL"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_llm_usage_logs_task_type ON llm_usage_logs (task_type)"))
        except Exception:
            pass


def downgrade(engine: Engine) -> None:
    """Drop migration 13 tables while preserving existing logs table."""
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS revenue_gate_records"))
        conn.execute(text("DROP TABLE IF EXISTS price_ladder_snapshots"))


def apply(engine: Engine) -> None:
    """Compatibility alias used by SRDI migration runner style."""
    upgrade(engine)


def rollback(engine: Engine) -> None:
    """Compatibility alias used by SRDI migration runner style."""
    downgrade(engine)
