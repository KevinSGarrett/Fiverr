"""Compatibility DB session helpers for utility scripts."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from src.models.database import build_engine, create_session_factory, get_session


def get_db_session(database_url: str = "sqlite:///data/cycle037_live.db") -> Generator[Session, None, None]:
    """Yield DB sessions for script-style `next(get_db_session())` callers."""
    engine = build_engine(database_url)
    session_factory = create_session_factory(engine)
    with get_session(session_factory) as session:
        yield session
