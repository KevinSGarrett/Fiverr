"""Database session utilities for dashboard live-data wiring (C061)."""
from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session, sessionmaker

from src.models.database import initialize_database

_DEFAULT_URL = "sqlite:///data/fiverr_research.db"


def _get_database_url() -> str:
    return os.environ.get("DATABASE_URL", _DEFAULT_URL)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session for dashboard queries and cleanup.

    Uses initialize_database() (not a bare create_engine()) so a dashboard opened
    directly against an existing DB file always gets the full, current schema first —
    otherwise a DB created before a later migration (e.g. migration_15's PriceAnalysis
    min/max columns) would hit a missing-column error the moment a page queries a
    column added since that file was created (SCRUM-1111 Codex review finding).
    """
    url = _get_database_url()
    engine = initialize_database(database_url=url)
    session_factory = sessionmaker(bind=engine)
    db = session_factory()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
