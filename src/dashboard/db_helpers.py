"""Database session utilities for dashboard live-data wiring (C061)."""
from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

_DEFAULT_URL = "sqlite:///data/fiverr_research.db"


def _get_database_url() -> str:
    return os.environ.get("DATABASE_URL", _DEFAULT_URL)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session for dashboard queries and cleanup."""
    url = _get_database_url()
    connect_args = {"check_same_thread": False} if "sqlite" in url else {}
    engine = create_engine(
        url,
        connect_args=connect_args,
        poolclass=StaticPool if "sqlite" in url else None,
    )
    session_factory = sessionmaker(bind=engine)
    db = session_factory()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
