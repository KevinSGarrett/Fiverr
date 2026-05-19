"""Retry execution engine for queue jobs."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import Session

from src.scheduler.exceptions import PermanentError, RateLimitError, SessionExpiredError
from src.scheduler.retry_config import (
    classify_error,
    get_retry_config,
    is_no_retry_error,
    should_dead_letter_on_error,
)

if TYPE_CHECKING:
    from src.collection.pacing import PacingManager
    from src.collection.session_manager import SessionManager
    from src.models.job import Job


async def execute_with_retry(
    job_func: Callable,
    job: Job,
    pacing_manager: PacingManager,
    session_manager: SessionManager,
    db: Any,
) -> bool:
    """
    Executes a job function with full retry/backoff logic.
    Returns True on success, False if job is dead-lettered.
    Uses RETRY_CONFIG per job_type for backoff and dead-letter rules.
    """
    _ = pacing_manager
    config = get_retry_config(job.job_type)

    for attempt in range(config["max_retries"] + 1):
        try:
            job.status = "RUNNING"
            job.started_at = datetime.now(UTC)
            if isinstance(db, Session):
                db.commit()

            await job_func(job)

            job.status = "COMPLETE"
            job.completed_at = datetime.now(UTC)
            if job.started_at:
                job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
            if isinstance(db, Session):
                db.commit()
            return True

        except RateLimitError as e:
            wait = e.retry_after_seconds or config["backoff_base_seconds"]
            job.error_log = (job.error_log or []) + [
                f"Attempt {attempt+1}: RateLimit — {e.source} — wait {wait}s"
            ]
            job.retry_count += 1
            if isinstance(db, Session):
                db.commit()
            if job.retry_count > config["max_retries"]:
                job.status = "DEAD_LETTER"
                job.completed_at = datetime.now(UTC)
                if isinstance(db, Session):
                    db.commit()
                return False
            await asyncio.sleep(wait)

        except SessionExpiredError:
            await session_manager.force_relogin()
            job.error_log = (job.error_log or []) + [
                f"Attempt {attempt+1}: Session expired — re-logged in"
            ]
            job.retry_count += 1
            if isinstance(db, Session):
                db.commit()

        except PermanentError as e:
            job.status = "DEAD_LETTER"
            job.error_log = (job.error_log or []) + [f"Permanent error [{e.error_code}]: {str(e)}"]
            job.completed_at = datetime.now(UTC)
            if isinstance(db, Session):
                db.commit()
            return False

        except Exception as e:
            error_code = classify_error(e)
            if is_no_retry_error(job.job_type, error_code):
                job.status = "DEAD_LETTER"
                job.error_log = (job.error_log or []) + [f"No-retry error [{error_code}]: {str(e)}"]
                job.completed_at = datetime.now(UTC)
                if isinstance(db, Session):
                    db.commit()
                return False
            if should_dead_letter_on_error(job.job_type, error_code):
                job.status = "DEAD_LETTER"
                job.error_log = (job.error_log or []) + [f"Dead-letter error [{error_code}]: {str(e)}"]
                job.completed_at = datetime.now(UTC)
                if isinstance(db, Session):
                    db.commit()
                return False

            error_msg = f"Attempt {attempt+1}/{config['max_retries']+1}: {type(e).__name__}: {str(e)[:200]}"
            job.error_log = (job.error_log or []) + [error_msg]
            job.retry_count += 1
            if isinstance(db, Session):
                db.commit()

            if job.retry_count > config["max_retries"]:
                job.status = "DEAD_LETTER"
                job.completed_at = datetime.now(UTC)
                if isinstance(db, Session):
                    db.commit()
                return False

            wait = min(
                config["backoff_base_seconds"] * (config["backoff_multiplier"] ** attempt),
                config["max_backoff_seconds"],
            )
            await asyncio.sleep(wait)

    job.status = "DEAD_LETTER"
    if isinstance(db, Session):
        db.commit()
    return False
