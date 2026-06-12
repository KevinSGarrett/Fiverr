"""Unit tests for Job ORM model and QueueProcessor."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base
from src.models.job import Job
from src.models.niche import NicheConfigRecord
from src.models.runtime import RunLog
from src.scheduler.queue_processor import QueueProcessor, execute_with_retry


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = session_factory()

    session.add(
        RunLog(
            run_id="run_cycle_024",
            mode="collect-only",
            stage="collection",
            message="queue test bootstrap",
        )
    )
    session.add(
        NicheConfigRecord(
            niche_id="niche_001",
            name="Niche 001",
            depth="standard",
            category_path="programming-tech/testing",
        )
    )
    session.commit()

    try:
        yield session
    finally:
        session.close()


def _make_job(**overrides: object) -> Job:
    data = {
        "job_id": "job_20260518_fiverr_search_kw123",
        "run_id": "run_cycle_024",
        "job_type": "FIVERR_SEARCH",
        "stage": 3,
        "niche_id": "niche_001",
        "priority": "STANDARD",
    }
    data.update(overrides)
    return Job(**data)



@pytest.fixture(autouse=True)
def _mock_asyncio_sleep(monkeypatch):
    """Mock asyncio.sleep to prevent real retry backoff waits."""
    async def fast_sleep(_seconds):
        pass
    monkeypatch.setattr("asyncio.sleep", fast_sleep)


def test_job_table_name() -> None:
    assert Job.__tablename__ == "jobs"


def test_job_insert_minimal(db_session: Session) -> None:
    job = _make_job()
    db_session.add(job)
    db_session.commit()
    fetched = db_session.query(Job).filter(Job.job_id == job.job_id).first()
    assert fetched is not None
    assert fetched.status == "QUEUED"


def test_job_mark_running(db_session: Session) -> None:
    job = _make_job()
    db_session.add(job)
    db_session.commit()
    job.mark_running()
    assert job.status == "RUNNING"
    assert job.started_at is not None


def test_job_mark_complete(db_session: Session) -> None:
    job = _make_job()
    db_session.add(job)
    db_session.commit()
    job.mark_running()
    job.mark_complete()
    assert job.status == "COMPLETE"
    assert job.completed_at is not None
    assert job.duration_seconds is not None
    assert job.duration_seconds >= 0


def test_job_mark_failed_first_failure(db_session: Session) -> None:
    job = _make_job(max_retries=3)
    db_session.add(job)
    db_session.commit()
    job.mark_failed("first failure")
    assert job.retry_count == 1
    assert job.status == "FAILED"


def test_job_mark_failed_max_retries(db_session: Session) -> None:
    job = _make_job(max_retries=1)
    db_session.add(job)
    db_session.commit()
    job.mark_failed("fails permanently")
    assert job.retry_count == 1
    assert job.status == "DEAD_LETTER"
    assert job.should_dead_letter() is True


def test_job_error_log_appends(db_session: Session) -> None:
    job = _make_job(max_retries=4)
    db_session.add(job)
    db_session.commit()
    job.mark_failed("one")
    job.mark_failed("two")
    assert job.error_log == ["one", "two"]


def test_job_priority_enum(db_session: Session) -> None:
    db_session.add(_make_job(job_id="job_invalid_priority", priority="URGENT"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_job_status_enum(db_session: Session) -> None:
    db_session.add(_make_job(job_id="job_invalid_status", status="NOT_A_STATE"))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_queue_processor_register_handler(db_session: Session) -> None:
    processor = QueueProcessor(db=db_session, config={}, session_manager=object(), pacing_manager=object())

    def handler(*_args, **_kwargs) -> None:
        return None

    processor.register_handler("FIVERR_SEARCH", handler)
    assert processor._job_handlers["FIVERR_SEARCH"] is handler


def test_queue_processor_no_jobs(db_session: Session) -> None:
    processor = QueueProcessor(db=db_session, config={}, session_manager=object(), pacing_manager=object())
    result = _run(processor.run_until_empty("run_cycle_024"))
    assert result == (0, 0)


def test_queue_processor_processes_job(db_session: Session) -> None:
    called = {"count": 0}

    async def handler(_job: Job, **_kwargs) -> None:
        called["count"] += 1

    job = _make_job(job_id="job_processes")
    db_session.add(job)
    db_session.commit()

    processor = QueueProcessor(db=db_session, config={}, session_manager=object(), pacing_manager=object())
    processor.register_handler("FIVERR_SEARCH", handler)
    processed, failed = _run(processor.run_until_empty("run_cycle_024"))
    db_session.refresh(job)

    assert called["count"] == 1
    assert processed == 1
    assert failed == 0
    assert job.status == "COMPLETE"


def test_queue_processor_handler_failure(db_session: Session) -> None:
    async def handler(_job: Job, **_kwargs) -> None:
        raise RuntimeError("boom")

    job = _make_job(job_id="job_failure", max_retries=1)
    db_session.add(job)
    db_session.commit()

    processor = QueueProcessor(db=db_session, config={}, session_manager=object(), pacing_manager=object())
    processor.register_handler("FIVERR_SEARCH", handler)
    processed, failed = _run(processor.run_until_empty("run_cycle_024"))
    db_session.refresh(job)

    assert processed == 1
    assert failed == 1
    assert job.status == "DEAD_LETTER"


def test_queue_processor_missing_handler_marks_dead_letter(db_session: Session) -> None:
    job = _make_job(job_id="job_missing_handler", job_type="UNKNOWN_HANDLER")
    db_session.add(job)
    db_session.commit()

    processor = QueueProcessor(db=db_session, config={}, session_manager=object(), pacing_manager=object())
    processed, failed = _run(processor.run_until_empty("run_cycle_024"))
    db_session.refresh(job)

    assert processed == 1
    assert failed == 1
    assert job.status == "DEAD_LETTER"
    assert job.error_log == ["No handler registered for job_type: UNKNOWN_HANDLER"]


def test_queue_processor_stop(db_session: Session) -> None:
    async def handler(_job: Job, **_kwargs) -> None:
        processor.stop()

    job_1 = _make_job(job_id="job_stop_1", created_at=datetime(2026, 5, 18, 0, 0, tzinfo=UTC))
    job_2 = _make_job(job_id="job_stop_2", created_at=datetime(2026, 5, 18, 0, 0, 1, tzinfo=UTC))
    db_session.add_all([job_1, job_2])
    db_session.commit()

    processor = QueueProcessor(db=db_session, config={}, session_manager=object(), pacing_manager=object())
    processor.register_handler("FIVERR_SEARCH", handler)
    processed, failed = _run(processor.run_until_empty("run_cycle_024"))
    db_session.refresh(job_1)
    db_session.refresh(job_2)

    assert processed == 1
    assert failed == 0
    assert job_1.status == "COMPLETE"
    assert job_2.status == "QUEUED"


def test_queue_processor_count_queued_and_stats(db_session: Session) -> None:
    db_session.add(_make_job(job_id="job_stats_1"))
    db_session.add(_make_job(job_id="job_stats_2", status="RUNNING"))
    db_session.commit()

    processor = QueueProcessor(db=db_session, config={}, session_manager=object(), pacing_manager=object())
    assert processor._count_queued("run_cycle_024") == 1
    assert processor.get_stats() == {"processed": 0, "failed": 0, "success_rate": 0.0}


def test_execute_with_retry_success(db_session: Session) -> None:
    async def handler(_job: Job, **_kwargs) -> None:
        return None

    job = _make_job(job_id="job_retry_success")
    db_session.add(job)
    db_session.commit()

    success = _run(
        execute_with_retry(
            job_func=handler,
            job=job,
            pacing_manager=object(),
            session_manager=object(),
            db=db_session,
        )
    )
    db_session.refresh(job)

    assert success is True
    assert job.status == "COMPLETE"


def test_execute_with_retry_failure(db_session: Session) -> None:
    async def handler(_job: Job, **_kwargs) -> None:
        raise RuntimeError("retry failure")

    job = _make_job(job_id="job_retry_failure")
    db_session.add(job)
    db_session.commit()

    success = _run(
        execute_with_retry(
            job_func=handler,
            job=job,
            pacing_manager=object(),
            session_manager=object(),
            db=db_session,
        )
    )
    db_session.refresh(job)

    assert success is False
    assert job.status == "DEAD_LETTER"


def test_execute_with_retry_failure_dead_letters_at_max_retries(db_session: Session) -> None:
    async def handler(_job: Job, **_kwargs) -> None:
        raise RuntimeError("retry failure")

    job = _make_job(job_id="job_retry_dead_letter", max_retries=1)
    db_session.add(job)
    db_session.commit()

    success = _run(
        execute_with_retry(
            job_func=handler,
            job=job,
            pacing_manager=object(),
            session_manager=object(),
            db=db_session,
        )
    )
    db_session.refresh(job)

    assert success is False
    assert job.status == "DEAD_LETTER"


def test_queue_processor_retries_then_completes(db_session: Session) -> None:
    attempts = {"count": 0}

    async def handler(_job: Job, **_kwargs) -> None:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("transient")

    job = _make_job(job_id="job_retry_then_success", max_retries=3)
    db_session.add(job)
    db_session.commit()

    processor = QueueProcessor(db=db_session, config={}, session_manager=object(), pacing_manager=object())
    processor.register_handler("FIVERR_SEARCH", handler)
    processed, failed = _run(processor.run_until_empty("run_cycle_024"))
    db_session.refresh(job)

    assert attempts["count"] == 2
    assert processed == 1
    assert failed == 0
    assert job.status == "COMPLETE"
