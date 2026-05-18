"""Unit tests for scheduler retry handler and retry exceptions."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.scheduler.exceptions import (
    CollectionError,
    PermanentError,
    RateLimitError,
    SessionExpiredError,
)
from src.scheduler.retry_handler import execute_with_retry


def _run(coro):
    return asyncio.run(coro)


def _make_job(job_type: str = "FIVERR_SEARCH") -> SimpleNamespace:
    return SimpleNamespace(
        job_type=job_type,
        status="QUEUED",
        started_at=None,
        completed_at=None,
        duration_seconds=None,
        error_log=[],
        retry_count=0,
    )


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_execute_with_retry_success() -> None:
    job = _make_job()
    job_func = AsyncMock(return_value=None)

    result = _run(
        execute_with_retry(job_func, job, pacing_manager=object(), session_manager=AsyncMock(), db={})
    )

    assert result is True
    assert job.status == "COMPLETE"


def test_execute_with_retry_updates_job_timing() -> None:
    job = _make_job()
    job_func = AsyncMock(return_value=None)

    _run(execute_with_retry(job_func, job, pacing_manager=object(), session_manager=AsyncMock(), db={}))

    assert job.started_at is not None
    assert job.completed_at is not None
    assert job.duration_seconds is not None
    assert job.duration_seconds >= 0


def test_execute_with_retry_generic_exception_retries() -> None:
    job = _make_job()
    job_func = AsyncMock(side_effect=[RuntimeError("boom"), None])

    with patch("src.scheduler.retry_handler.asyncio.sleep", new=AsyncMock()) as sleep_mock:
        result = _run(execute_with_retry(
            job_func,
            job,
            pacing_manager=object(),
            session_manager=AsyncMock(),
            db={},
        ))

    assert result is True
    assert job.retry_count == 1
    assert sleep_mock.await_count == 1


def test_execute_with_retry_max_retries_dead_letter() -> None:
    job = _make_job()
    job_func = AsyncMock(side_effect=RuntimeError("always fails"))

    with patch("src.scheduler.retry_handler.asyncio.sleep", new=AsyncMock()):
        result = _run(execute_with_retry(
            job_func,
            job,
            pacing_manager=object(),
            session_manager=AsyncMock(),
            db={},
        ))

    assert result is False
    assert job.status == "DEAD_LETTER"


def test_execute_with_retry_rate_limit_waits() -> None:
    job = _make_job()
    job_func = AsyncMock(side_effect=[RateLimitError("fiverr", 7), None])

    with patch("src.scheduler.retry_handler.asyncio.sleep", new=AsyncMock()) as sleep_mock:
        result = _run(execute_with_retry(
            job_func,
            job,
            pacing_manager=object(),
            session_manager=AsyncMock(),
            db={},
        ))

    assert result is True
    sleep_mock.assert_awaited_once_with(7)


def test_execute_with_retry_rate_limit_dead_letters_without_sleep_when_exhausted() -> None:
    job = _make_job()
    job_func = AsyncMock(side_effect=RateLimitError("fiverr", 9))

    with (
        patch("src.scheduler.retry_handler.asyncio.sleep", new=AsyncMock()) as sleep_mock,
        patch(
            "src.scheduler.retry_handler.get_retry_config",
            return_value={
                "max_retries": 0,
                "backoff_base_seconds": 1,
                "backoff_multiplier": 2.0,
                "max_backoff_seconds": 2,
            },
        ),
    ):
        result = _run(
            execute_with_retry(
                job_func,
                job,
                pacing_manager=object(),
                session_manager=AsyncMock(),
                db={},
            )
        )

    assert result is False
    assert job.status == "DEAD_LETTER"
    sleep_mock.assert_not_awaited()


def test_execute_with_retry_rate_limit_dead_letters_with_session_commit(db_session: Session) -> None:
    job = _make_job()
    job_func = AsyncMock(side_effect=RateLimitError("fiverr", 1))

    with (
        patch("src.scheduler.retry_handler.asyncio.sleep", new=AsyncMock()) as sleep_mock,
        patch(
            "src.scheduler.retry_handler.get_retry_config",
            return_value={
                "max_retries": 0,
                "backoff_base_seconds": 1,
                "backoff_multiplier": 2.0,
                "max_backoff_seconds": 2,
            },
        ),
    ):
        result = _run(
            execute_with_retry(
                job_func,
                job,
                pacing_manager=object(),
                session_manager=AsyncMock(),
                db=db_session,
            )
        )

    assert result is False
    assert job.status == "DEAD_LETTER"
    sleep_mock.assert_not_awaited()


def test_execute_with_retry_session_expired_relogins() -> None:
    job = _make_job()
    job_func = AsyncMock(side_effect=[SessionExpiredError(), None])
    session_manager = AsyncMock()

    result = _run(execute_with_retry(
        job_func,
        job,
        pacing_manager=object(),
        session_manager=session_manager,
        db={},
    ))

    assert result is True
    session_manager.force_relogin.assert_awaited_once()


def test_execute_with_retry_permanent_error_dead_letters() -> None:
    job = _make_job()
    job_func = AsyncMock(side_effect=PermanentError("HTTP_410", "gone"))

    result = _run(execute_with_retry(
        job_func,
        job,
        pacing_manager=object(),
        session_manager=AsyncMock(),
        db={},
    ))

    assert result is False
    assert job.status == "DEAD_LETTER"
    assert job.retry_count == 0


def test_execute_with_retry_no_retry_error_dead_letters() -> None:
    job = _make_job("FIVERR_SEARCH")

    class NotFoundError(Exception):
        status_code = 404

    job_func = AsyncMock(side_effect=NotFoundError("not found"))

    result = _run(execute_with_retry(
        job_func,
        job,
        pacing_manager=object(),
        session_manager=AsyncMock(),
        db={},
    ))

    assert result is False
    assert job.status == "DEAD_LETTER"
    assert job.retry_count == 0


def test_execute_with_retry_dead_letter_error_classification() -> None:
    job = _make_job("FIVERR_SEARCH")
    job_func = AsyncMock(side_effect=RuntimeError("session ban"))

    with (
        patch("src.scheduler.retry_handler.classify_error", return_value="PERMANENT_BAN"),
        patch("src.scheduler.retry_handler.asyncio.sleep", new=AsyncMock()) as sleep_mock,
    ):
        result = _run(
            execute_with_retry(
                job_func,
                job,
                pacing_manager=object(),
                session_manager=AsyncMock(),
                db={},
            )
        )

    assert result is False
    assert job.status == "DEAD_LETTER"
    assert job.retry_count == 0
    sleep_mock.assert_not_awaited()


def test_execute_with_retry_dead_letter_error_classification_commits_session(
    db_session: Session,
) -> None:
    job = _make_job("FIVERR_SEARCH")
    job_func = AsyncMock(side_effect=RuntimeError("session ban"))

    with (
        patch("src.scheduler.retry_handler.classify_error", return_value="PERMANENT_BAN"),
        patch("src.scheduler.retry_handler.asyncio.sleep", new=AsyncMock()) as sleep_mock,
    ):
        result = _run(
            execute_with_retry(
                job_func,
                job,
                pacing_manager=object(),
                session_manager=AsyncMock(),
                db=db_session,
            )
        )

    assert result is False
    assert job.status == "DEAD_LETTER"
    assert job.retry_count == 0
    sleep_mock.assert_not_awaited()


def test_execute_with_retry_exponential_backoff() -> None:
    job = _make_job("SCORE_KEYWORD")
    job_func = AsyncMock(side_effect=[RuntimeError("1"), RuntimeError("2"), None])

    with patch("src.scheduler.retry_handler.asyncio.sleep", new=AsyncMock()) as sleep_mock:
        result = _run(execute_with_retry(
            job_func,
            job,
            pacing_manager=object(),
            session_manager=AsyncMock(),
            db={},
        ))

    assert result is True
    waits = [call.args[0] for call in sleep_mock.await_args_list]
    assert waits == [2.0, 4.0]


def test_execute_with_retry_max_backoff_capped() -> None:
    job = _make_job("GOOGLE_TRENDS")
    job_func = AsyncMock(
        side_effect=[RuntimeError("1"), RuntimeError("2"), RuntimeError("3"), RuntimeError("4"), None]
    )

    with patch("src.scheduler.retry_handler.asyncio.sleep", new=AsyncMock()) as sleep_mock:
        result = _run(execute_with_retry(
            job_func,
            job,
            pacing_manager=object(),
            session_manager=AsyncMock(),
            db={},
        ))

    assert result is True
    waits = [call.args[0] for call in sleep_mock.await_args_list]
    assert waits == [600.0, 1200.0, 2400.0, 3600]


def test_rate_limit_error_attributes() -> None:
    err = RateLimitError(source="google_trends", retry_after_seconds=123)
    assert err.source == "google_trends"
    assert err.retry_after_seconds == 123


def test_session_expired_error_message() -> None:
    err = SessionExpiredError()
    assert isinstance(err, Exception)


def test_permanent_error_code() -> None:
    err = PermanentError(error_code="HTTP_404", message="missing")
    assert err.error_code == "HTTP_404"


def test_collection_error_hierarchy() -> None:
    assert issubclass(CollectionError, Exception)


def test_execute_with_retry_error_log_appends() -> None:
    job = _make_job("SCORE_KEYWORD")
    job_func = AsyncMock(side_effect=[RuntimeError("first"), RuntimeError("second"), None])

    with patch("src.scheduler.retry_handler.asyncio.sleep", new=AsyncMock()):
        result = _run(execute_with_retry(
            job_func,
            job,
            pacing_manager=object(),
            session_manager=AsyncMock(),
            db={},
        ))

    assert result is True
    assert len(job.error_log) == 2


def test_execute_with_retry_dict_db_no_crash() -> None:
    job = _make_job()
    job_func = AsyncMock(return_value=None)

    result = _run(execute_with_retry(
        job_func,
        job,
        pacing_manager=object(),
        session_manager=AsyncMock(),
        db={},
    ))

    assert result is True


def test_execute_with_retry_rate_limit_commits_session(db_session: Session) -> None:
    job = _make_job()
    job_func = AsyncMock(side_effect=[RateLimitError("fiverr", 1), None])

    with patch("src.scheduler.retry_handler.asyncio.sleep", new=AsyncMock()):
        result = _run(
            execute_with_retry(
                job_func,
                job,
                pacing_manager=object(),
                session_manager=AsyncMock(),
                db=db_session,
            )
        )

    assert result is True


def test_execute_with_retry_session_expired_commits_session(db_session: Session) -> None:
    job = _make_job()
    job_func = AsyncMock(side_effect=[SessionExpiredError(), None])
    session_manager = AsyncMock()

    result = _run(
        execute_with_retry(
            job_func,
            job,
            pacing_manager=object(),
            session_manager=session_manager,
            db=db_session,
        )
    )

    assert result is True
    session_manager.force_relogin.assert_awaited_once()


def test_execute_with_retry_permanent_error_commits_session(db_session: Session) -> None:
    job = _make_job()
    job_func = AsyncMock(side_effect=PermanentError("PERMANENT_BAN", "blocked"))

    result = _run(
        execute_with_retry(
            job_func,
            job,
            pacing_manager=object(),
            session_manager=AsyncMock(),
            db=db_session,
        )
    )

    assert result is False
    assert job.status == "DEAD_LETTER"


def test_execute_with_retry_no_retry_commits_session(db_session: Session) -> None:
    job = _make_job("FIVERR_SEARCH")

    class GoneError(Exception):
        status_code = 410

    job_func = AsyncMock(side_effect=GoneError("gone"))

    result = _run(
        execute_with_retry(
            job_func,
            job,
            pacing_manager=object(),
            session_manager=AsyncMock(),
            db=db_session,
        )
    )

    assert result is False
    assert job.status == "DEAD_LETTER"


def test_execute_with_retry_safety_net_dead_letter() -> None:
    job = _make_job()
    job_func = AsyncMock(return_value=None)

    with patch(
        "src.scheduler.retry_handler.get_retry_config",
        return_value={
            "max_retries": -1,
            "backoff_base_seconds": 1,
            "backoff_multiplier": 2.0,
            "max_backoff_seconds": 2,
        },
    ):
        result = _run(
            execute_with_retry(
                job_func,
                job,
                pacing_manager=object(),
                session_manager=AsyncMock(),
                db={},
            )
        )

    assert result is False
    assert job.status == "DEAD_LETTER"


def test_execute_with_retry_safety_net_dead_letter_commits_session(db_session: Session) -> None:
    job = _make_job()
    job_func = AsyncMock(return_value=None)

    with patch(
        "src.scheduler.retry_handler.get_retry_config",
        return_value={
            "max_retries": -1,
            "backoff_base_seconds": 1,
            "backoff_multiplier": 2.0,
            "max_backoff_seconds": 2,
        },
    ):
        result = _run(
            execute_with_retry(
                job_func,
                job,
                pacing_manager=object(),
                session_manager=AsyncMock(),
                db=db_session,
            )
        )

    assert result is False
    assert job.status == "DEAD_LETTER"
