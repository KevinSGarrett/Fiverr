"""Database engine and session helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.models.base import Base

DEFAULT_DATABASE_URL = "sqlite:///data/fiverr_research.db"


def build_engine(database_url: str | None = None) -> Engine:
    url = database_url or DEFAULT_DATABASE_URL
    connect_args: dict[str, bool] = {}

    if url.startswith("sqlite:///"):
        sqlite_path = Path(url.replace("sqlite:///", "", 1))
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        connect_args["check_same_thread"] = False

    return create_engine(url, future=True, connect_args=connect_args)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@contextmanager
def get_db(database_url: str | None = None) -> Iterator[Session]:
    engine = build_engine(database_url=database_url)
    session_factory = get_session_factory(engine)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def initialize_database(engine: Engine | None = None) -> Engine:
    active_engine = engine or build_engine()
    Base.metadata.create_all(active_engine)
    return active_engine
