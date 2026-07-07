"""Migration 15: add real min/max price columns to price_analysis.

_apply_distribution_to_row (src/pricing/analysis.py) computes true min_price/max_price
in PriceDistribution but never persists them - only n/median/mean/mode/std/q1/q3/p10/p90/
skewness/cv/clusters/gaps reach the DB row. Downstream consumers (e.g.
src/recommendations/context.py) then substitute basic_p90 mislabeled as "max" and read a
nonexistent basic_min attribute (always None) for "min" - a wrong price range shown to
paying users (SCRUM-1108/SCRUM-1109).
"""

from __future__ import annotations

from sqlalchemy import Engine, inspect, text

_TIERS = ("basic", "standard", "premium")


def _column_names(engine: Engine, table_name: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table_name)}


def upgrade(engine: Engine) -> None:
    """Add {tier}_min / {tier}_max columns to price_analysis idempotently."""
    with engine.begin() as conn:
        if not inspect(engine).has_table("price_analysis"):
            return
        existing = _column_names(engine, "price_analysis")
        for tier in _TIERS:
            for suffix in ("min", "max"):
                column = f"{tier}_{suffix}"
                if column not in existing:
                    conn.execute(text(f"ALTER TABLE price_analysis ADD COLUMN {column} REAL"))


def downgrade(engine: Engine) -> None:
    """Rollback is a no-op: SQLite column drops are intentionally not attempted."""
    del engine


def apply(engine: Engine) -> None:
    """Compatibility alias for migration runner."""
    upgrade(engine)


def rollback(engine: Engine) -> None:
    """Compatibility alias for migration runner."""
    downgrade(engine)
