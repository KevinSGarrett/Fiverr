"""Database engine, session, and initialization helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, inspect
from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.orm import Session, sessionmaker

from src import models as _models  # noqa: F401 - ensures table modules are imported
from src.models.base import Base
from src.models.registry import get_registered_table_names

DEFAULT_DATABASE_URL = "sqlite:///data/fiverr_research.db"


def normalize_database_url(database_url: str | None = None) -> str:
    """Normalize database URL and fallback to project default."""
    url = (database_url or DEFAULT_DATABASE_URL).strip()
    if not url:
        raise ValueError("Database URL cannot be blank.")

    if url.startswith("sqlite:///"):
        raw_path = url.removeprefix("sqlite:///")
        if raw_path == ":memory:":
            return "sqlite:///:memory:"
        sqlite_path = Path(raw_path.replace("\\", "/"))
        return f"sqlite:///{sqlite_path.as_posix()}"

    return url


def _sqlite_path_from_url(database_url: str) -> Path | None:
    if not database_url.startswith("sqlite:///"):
        return None
    raw_path = database_url.removeprefix("sqlite:///")
    if raw_path == ":memory:":
        return None
    return Path(raw_path)


def _ensure_keyword_intent_class_column(engine: Engine) -> None:
    """
    Backfill `keywords.intent_class` for pre-existing SQLite databases.

    Existing installs may predate this column. `create_all()` does not alter tables,
    so we add the column when missing to keep Workflow 2 writes backward-compatible.
    """
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "keywords" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("keywords")}
    if "intent_class" in existing_columns:
        return

    with engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE keywords ADD COLUMN intent_class VARCHAR(32)")


def _ensure_keyword_embedding_vector_column(engine: Engine) -> None:
    """
    Backfill `keywords.embedding_vector` for pre-existing SQLite databases.

    Existing installs may predate this column. `create_all()` does not alter tables,
    so we add the column when missing to keep Workflow 2 Step 2g writes compatible.
    """
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "keywords" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("keywords")}
    if "embedding_vector" in existing_columns:
        return

    try:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE keywords ADD COLUMN embedding_vector TEXT")
    except Exception:
        # Guard legacy initialization flows where schema introspection can race.
        return


def _ensure_keyword_cluster_id_column(engine: Engine) -> None:
    """
    Backfill `keywords.cluster_id` for pre-existing SQLite databases.

    Existing installs may predate this column. `create_all()` does not alter tables,
    so we add the column when missing to keep Stage 9 clustering writes compatible.
    """
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "keywords" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("keywords")}
    if "cluster_id" in existing_columns:
        return

    try:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE keywords ADD COLUMN cluster_id INTEGER")
    except Exception:
        # Guard legacy initialization flows where schema introspection can race.
        return


def _ensure_cluster_assignments_table(engine: Engine) -> None:
    """Backfill `cluster_assignments` table for legacy SQLite databases."""
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "cluster_assignments" in inspector.get_table_names():
        return

    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS cluster_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword_id INTEGER NOT NULL,
                niche_id VARCHAR(64) NOT NULL,
                cluster_id INTEGER NOT NULL,
                run_id VARCHAR(64) NOT NULL,
                algorithm VARCHAR(16) NOT NULL DEFAULT 'kmeans',
                assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_cluster_assignments_keyword_run UNIQUE (keyword_id, run_id),
                FOREIGN KEY(keyword_id) REFERENCES keywords (id)
            )
            """
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_cluster_assignments_keyword_id ON cluster_assignments (keyword_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_cluster_assignments_niche_id ON cluster_assignments (niche_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_cluster_assignments_cluster_id ON cluster_assignments (cluster_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_cluster_assignments_run_id ON cluster_assignments (run_id)"
        )


def _ensure_cluster_labels_table(engine: Engine) -> None:
    """Backfill `cluster_labels` table for legacy SQLite databases."""
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "cluster_labels" in inspector.get_table_names():
        return

    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS cluster_labels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                niche_id VARCHAR(64) NOT NULL,
                cluster_id INTEGER NOT NULL,
                run_id VARCHAR(64) NOT NULL,
                label_text VARCHAR(256),
                opportunity_narrative TEXT,
                keyword_count INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_cluster_labels_niche_cluster_run UNIQUE (niche_id, cluster_id, run_id)
            )
            """
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_cluster_labels_niche_id ON cluster_labels (niche_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_cluster_labels_cluster_id ON cluster_labels (cluster_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_cluster_labels_run_id ON cluster_labels (run_id)"
        )


def _ensure_competitor_profiles_table(engine: Engine) -> None:
    """Backfill `competitor_profiles` table for legacy SQLite databases."""
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "competitor_profiles" in inspector.get_table_names():
        return

    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS competitor_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                niche_id VARCHAR(64) NOT NULL,
                run_id VARCHAR(64) NOT NULL,
                top_gig_count INTEGER NOT NULL DEFAULT 0,
                median_price FLOAT,
                mean_price FLOAT,
                price_std FLOAT,
                median_rating FLOAT,
                mean_reviews FLOAT,
                seller_level_distribution JSON NOT NULL DEFAULT '{}',
                min_delivery_days INTEGER,
                max_delivery_days INTEGER,
                video_present_rate FLOAT,
                portfolio_present_rate FLOAT,
                new_seller_gap JSON NOT NULL DEFAULT '{}',
                collected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_competitor_profiles_niche_run UNIQUE (niche_id, run_id)
            )
            """
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_competitor_profiles_niche_id ON competitor_profiles (niche_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_competitor_profiles_run_id ON competitor_profiles (run_id)"
        )


def _ensure_competitor_profiles_new_seller_gap_column(engine: Engine) -> None:
    """Backfill `competitor_profiles.new_seller_gap` for legacy SQLite databases."""
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "competitor_profiles" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("competitor_profiles")}
    if "new_seller_gap" in existing_columns:
        return

    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE competitor_profiles ADD COLUMN new_seller_gap JSON NOT NULL DEFAULT '{}'"
            )
    except Exception:
        # Guard legacy initialization flows where schema introspection can race.
        return


def _ensure_gig_quality_analyses_table(engine: Engine) -> None:
    """Backfill `gig_quality_analyses` table for legacy SQLite databases."""
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "gig_quality_analyses" in inspector.get_table_names():
        return

    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS gig_quality_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gig_url VARCHAR(1024) NOT NULL,
                niche_id VARCHAR(64) NOT NULL,
                run_id VARCHAR(64) NOT NULL,
                rubric_score FLOAT NOT NULL DEFAULT 0.0,
                video_absent BOOLEAN NOT NULL DEFAULT 0,
                portfolio_absent BOOLEAN NOT NULL DEFAULT 0,
                description_thin BOOLEAN NOT NULL DEFAULT 0,
                faq_absent BOOLEAN NOT NULL DEFAULT 0,
                thumbnail_quality_flag BOOLEAN NOT NULL DEFAULT 0,
                weakness_flags JSON NOT NULL DEFAULT '[]',
                analyzed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_gig_quality_analyses_gig_url_run UNIQUE (gig_url, run_id)
            )
            """
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_gig_quality_analyses_gig_url ON gig_quality_analyses (gig_url)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_gig_quality_analyses_niche_id ON gig_quality_analyses (niche_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_gig_quality_analyses_run_id ON gig_quality_analyses (run_id)"
        )


def _ensure_review_analyses_table(engine: Engine) -> None:
    """Backfill `review_analyses` table for legacy SQLite databases."""
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "review_analyses" in inspector.get_table_names():
        return

    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS review_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gig_url VARCHAR(1024) NOT NULL,
                niche_id VARCHAR(64) NOT NULL,
                run_id VARCHAR(64) NOT NULL,
                review_count INTEGER NOT NULL DEFAULT 0,
                avg_rating FLOAT,
                review_velocity FLOAT NOT NULL DEFAULT 0.0,
                sentiment_score FLOAT,
                recurring_complaints JSON NOT NULL DEFAULT '[]',
                analyzed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_review_analyses_gig_url_run UNIQUE (gig_url, run_id)
            )
            """
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_review_analyses_gig_url ON review_analyses (gig_url)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_review_analyses_niche_id ON review_analyses (niche_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_review_analyses_run_id ON review_analyses (run_id)"
        )


def _ensure_saturation_scores_table(engine: Engine) -> None:
    """Backfill `saturation_scores` table for legacy SQLite databases."""
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if "saturation_scores" in inspector.get_table_names():
        return

    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS saturation_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword_id INTEGER NOT NULL,
                niche_id VARCHAR(64) NOT NULL,
                run_id VARCHAR(64) NOT NULL,
                saturation_score FLOAT NOT NULL DEFAULT 50.0,
                count_score FLOAT NOT NULL DEFAULT 0.0,
                title_dup_score FLOAT NOT NULL DEFAULT 0.0,
                price_score FLOAT NOT NULL DEFAULT 0.0,
                overlap_score FLOAT NOT NULL DEFAULT 0.0,
                llm_class_score FLOAT NOT NULL DEFAULT 50.0,
                title_duplication_rate FLOAT NOT NULL DEFAULT 0.0,
                price_compression_rate FLOAT NOT NULL DEFAULT 0.0,
                seller_overlap_rate FLOAT NOT NULL DEFAULT 0.0,
                explanation_text TEXT,
                computed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_saturation_scores_keyword_run UNIQUE (keyword_id, run_id),
                FOREIGN KEY(keyword_id) REFERENCES keywords (id)
            )
            """
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_saturation_scores_keyword_id ON saturation_scores (keyword_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_saturation_scores_niche_id ON saturation_scores (niche_id)"
        )
        connection.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS ix_saturation_scores_run_id ON saturation_scores (run_id)"
        )


def build_engine(database_url: str | None = None) -> Engine:
    """Build SQLAlchemy engine without creating filesystem side effects."""
    url = normalize_database_url(database_url)
    connect_args: dict[str, bool] = {}
    if url.startswith("sqlite:///"):
        connect_args["check_same_thread"] = False
    return sa_create_engine(url, future=True, connect_args=connect_args)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Build a session factory with explicit transaction behavior."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


# Backwards-compatible alias for Cycle 001 tests/imports.
get_session_factory = create_session_factory


@contextmanager
def get_session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Yield session and manage commit/rollback behavior."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_db(database_url: str | None = None) -> Iterator[Session]:
    """Compatibility context manager used in tests and scripts."""
    engine = build_engine(database_url=database_url)
    session_factory = create_session_factory(engine)
    with get_session(session_factory) as session:
        yield session


def initialize_database(database_url: str | None = None, engine: Engine | None = None) -> Engine:
    """Initialize all model tables for the provided database."""
    active_engine = engine or build_engine(database_url)
    sqlite_path = _sqlite_path_from_url(str(active_engine.url))
    if sqlite_path is not None:
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(active_engine)
    _ensure_keyword_intent_class_column(active_engine)
    _ensure_keyword_embedding_vector_column(active_engine)
    _ensure_keyword_cluster_id_column(active_engine)
    _ensure_cluster_assignments_table(active_engine)
    _ensure_cluster_labels_table(active_engine)
    _ensure_competitor_profiles_table(active_engine)
    _ensure_competitor_profiles_new_seller_gap_column(active_engine)
    _ensure_gig_quality_analyses_table(active_engine)
    _ensure_review_analyses_table(active_engine)
    _ensure_saturation_scores_table(active_engine)
    return active_engine


def drop_database_for_tests(database_url: str) -> None:
    """Drop test database tables and remove sqlite file when safe."""
    normalized_url = normalize_database_url(database_url)
    safety_tokens = ("test", "pytest", ":memory:")
    if not any(token in normalized_url.lower() for token in safety_tokens):
        raise ValueError("Refusing to drop database outside of test-like URLs.")

    engine = build_engine(normalized_url)
    Base.metadata.drop_all(engine)
    sqlite_path = _sqlite_path_from_url(normalized_url)
    if sqlite_path is not None and sqlite_path.exists():
        sqlite_path.unlink()


def list_tables(engine: Engine) -> list[str]:
    """List all table names present in the bound database."""
    return sorted(inspect(engine).get_table_names())


def verify_required_tables(engine: Engine, required_tables: list[str] | None = None) -> list[str]:
    """Return missing tables from the required or registered set."""
    expected_tables = required_tables or get_registered_table_names()
    existing = set(list_tables(engine))
    missing = sorted(set(expected_tables) - existing)
    return missing
