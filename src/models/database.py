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
