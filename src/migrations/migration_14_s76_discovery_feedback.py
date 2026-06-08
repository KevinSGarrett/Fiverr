"""C070 migration 14: S7.6 discovery scoring and feedback schema."""

from __future__ import annotations

from sqlalchemy import Engine, inspect, text


def _column_names(engine: Engine, table_name: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table_name)}


def upgrade(engine: Engine) -> None:
    """Apply S7.6 schema updates idempotently."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS discovery_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id VARCHAR(64),
                    keyword_id INTEGER REFERENCES keywords(id),
                    keyword_text VARCHAR(256),
                    niche_id VARCHAR(128),
                    discovery_mode VARCHAR(64),
                    hypothesis_confidence REAL,
                    actual_final_score REAL,
                    actual_tag VARCHAR(32),
                    score_delta REAL,
                    is_gold BOOLEAN DEFAULT 0 NOT NULL,
                    is_hit BOOLEAN DEFAULT 0 NOT NULL,
                    is_miss BOOLEAN DEFAULT 0 NOT NULL,
                    evaluated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_invalid BOOLEAN DEFAULT 0 NOT NULL,
                    is_contaminated BOOLEAN DEFAULT 0 NOT NULL,
                    relevance_score REAL,
                    contamination_reason TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
                """
            )
        )
        outcome_columns = _column_names(engine, "discovery_outcomes")
        if "keyword_id" not in outcome_columns:
            conn.execute(text("ALTER TABLE discovery_outcomes ADD COLUMN keyword_id INTEGER REFERENCES keywords(id)"))
        if "discovery_mode" not in outcome_columns:
            conn.execute(text("ALTER TABLE discovery_outcomes ADD COLUMN discovery_mode VARCHAR(64)"))
        if "hypothesis_confidence" not in outcome_columns:
            conn.execute(text("ALTER TABLE discovery_outcomes ADD COLUMN hypothesis_confidence REAL"))
        if "actual_final_score" not in outcome_columns:
            conn.execute(text("ALTER TABLE discovery_outcomes ADD COLUMN actual_final_score REAL"))
        if "actual_tag" not in outcome_columns:
            conn.execute(text("ALTER TABLE discovery_outcomes ADD COLUMN actual_tag VARCHAR(32)"))
        if "score_delta" not in outcome_columns:
            conn.execute(text("ALTER TABLE discovery_outcomes ADD COLUMN score_delta REAL"))
        if "is_gold" not in outcome_columns:
            conn.execute(text("ALTER TABLE discovery_outcomes ADD COLUMN is_gold BOOLEAN DEFAULT 0 NOT NULL"))
        if "is_hit" not in outcome_columns:
            conn.execute(text("ALTER TABLE discovery_outcomes ADD COLUMN is_hit BOOLEAN DEFAULT 0 NOT NULL"))
        if "is_miss" not in outcome_columns:
            conn.execute(text("ALTER TABLE discovery_outcomes ADD COLUMN is_miss BOOLEAN DEFAULT 0 NOT NULL"))
        if "evaluated_at" not in outcome_columns:
            conn.execute(text("ALTER TABLE discovery_outcomes ADD COLUMN evaluated_at DATETIME"))

        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_discovery_outcomes_keyword_id ON discovery_outcomes (keyword_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_discovery_outcomes_run_id ON discovery_outcomes (run_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_discovery_outcomes_discovery_mode ON discovery_outcomes (discovery_mode)"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS discovery_cycle_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id VARCHAR(64),
                    modes_run JSON,
                    hypotheses_generated INTEGER DEFAULT 0 NOT NULL,
                    hypotheses_gated INTEGER DEFAULT 0 NOT NULL,
                    hypotheses_accepted INTEGER DEFAULT 0 NOT NULL,
                    total_cost_usd REAL,
                    feedback_summary JSON,
                    cycle_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    run_log_id INTEGER REFERENCES run_logs(id),
                    niche_id INTEGER REFERENCES niches(id),
                    cycle_number INTEGER,
                    hypotheses_promoted INTEGER DEFAULT 0 NOT NULL,
                    hypotheses_rejected INTEGER DEFAULT 0 NOT NULL,
                    total_llm_cost_usd REAL DEFAULT 0.0 NOT NULL,
                    enabled_modes VARCHAR(256),
                    status VARCHAR(32) DEFAULT 'completed' NOT NULL,
                    error_message VARCHAR,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
                """
            )
        )
        cycle_columns = _column_names(engine, "discovery_cycle_logs")
        if "modes_run" not in cycle_columns:
            conn.execute(text("ALTER TABLE discovery_cycle_logs ADD COLUMN modes_run JSON"))
        if "hypotheses_generated" not in cycle_columns:
            conn.execute(text("ALTER TABLE discovery_cycle_logs ADD COLUMN hypotheses_generated INTEGER DEFAULT 0 NOT NULL"))
        if "hypotheses_gated" not in cycle_columns:
            conn.execute(text("ALTER TABLE discovery_cycle_logs ADD COLUMN hypotheses_gated INTEGER DEFAULT 0 NOT NULL"))
        if "hypotheses_accepted" not in cycle_columns:
            conn.execute(text("ALTER TABLE discovery_cycle_logs ADD COLUMN hypotheses_accepted INTEGER DEFAULT 0 NOT NULL"))
        if "total_cost_usd" not in cycle_columns:
            conn.execute(text("ALTER TABLE discovery_cycle_logs ADD COLUMN total_cost_usd REAL"))
        if "feedback_summary" not in cycle_columns:
            conn.execute(text("ALTER TABLE discovery_cycle_logs ADD COLUMN feedback_summary JSON"))
        if "cycle_at" not in cycle_columns:
            conn.execute(text("ALTER TABLE discovery_cycle_logs ADD COLUMN cycle_at DATETIME"))
        if "run_log_id" not in cycle_columns:
            conn.execute(text("ALTER TABLE discovery_cycle_logs ADD COLUMN run_log_id INTEGER REFERENCES run_logs(id)"))

        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_discovery_cycle_logs_run_id ON discovery_cycle_logs (run_id)"))

        keyword_columns = _column_names(engine, "keywords")
        if "is_discovery" not in keyword_columns:
            conn.execute(text("ALTER TABLE keywords ADD COLUMN is_discovery BOOLEAN DEFAULT 0 NOT NULL"))
        if "discovery_mode" not in keyword_columns:
            conn.execute(text("ALTER TABLE keywords ADD COLUMN discovery_mode VARCHAR(64)"))
        if "hypothesis_confidence" not in keyword_columns:
            conn.execute(text("ALTER TABLE keywords ADD COLUMN hypothesis_confidence REAL"))
        if "hypothesis_rationale" not in keyword_columns:
            conn.execute(text("ALTER TABLE keywords ADD COLUMN hypothesis_rationale TEXT"))
        if "discovered_in_run" not in keyword_columns:
            conn.execute(text("ALTER TABLE keywords ADD COLUMN discovered_in_run VARCHAR(64)"))
        if "discovery_evaluated" not in keyword_columns:
            conn.execute(text("ALTER TABLE keywords ADD COLUMN discovery_evaluated BOOLEAN DEFAULT 0 NOT NULL"))
        if "is_retired" not in keyword_columns:
            conn.execute(text("ALTER TABLE keywords ADD COLUMN is_retired BOOLEAN DEFAULT 0 NOT NULL"))

        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_keywords_is_discovery ON keywords (is_discovery)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_keywords_discovery_evaluated ON keywords (discovery_evaluated)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_keywords_is_retired ON keywords (is_retired)"))


def downgrade(engine: Engine) -> None:
    """Rollback S7.6 schema updates where possible."""
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS discovery_cycle_logs"))
        conn.execute(text("DROP TABLE IF EXISTS discovery_outcomes"))
        # SQLite column drops are intentionally not attempted here.


def apply(engine: Engine) -> None:
    """Compatibility alias for migration runner."""
    upgrade(engine)


def rollback(engine: Engine) -> None:
    """Compatibility alias for migration runner."""
    downgrade(engine)
