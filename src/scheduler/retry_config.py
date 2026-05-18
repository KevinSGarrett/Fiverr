"""Retry policy lookup and error classification helpers."""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import Any

from src.collection.session_manager import SessionLoginError

RETRY_CONFIG: dict[str, dict[str, Any]] = {
    "FIVERR_SEARCH": {
        "max_retries": 3,
        "backoff_base_seconds": 15,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 120,
        "dead_letter_on": ["HTTP_404", "HTTP_410", "PERMANENT_BAN"],
        "no_retry_on": ["HTTP_404", "HTTP_410"],
        "session_refresh_on": ["SESSION_EXPIRED"],
    },
    "GIG_DETAIL": {
        "max_retries": 3,
        "backoff_base_seconds": 15,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 120,
        "dead_letter_on": ["HTTP_404", "HTTP_410"],
        "no_retry_on": ["HTTP_404", "HTTP_410"],
        "session_refresh_on": ["SESSION_EXPIRED"],
    },
    "SELLER_PROFILE": {
        "max_retries": 3,
        "backoff_base_seconds": 10,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 60,
        "dead_letter_on": ["HTTP_404"],
        "no_retry_on": ["HTTP_404"],
        "session_refresh_on": ["SESSION_EXPIRED"],
    },
    "KEYWORD_EXPAND": {
        "max_retries": 2,
        "backoff_base_seconds": 10,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 60,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": ["SESSION_EXPIRED"],
    },
    "GOOGLE_TRENDS": {
        "max_retries": 5,
        "backoff_base_seconds": 600,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 3600,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },
    "REDDIT_COLLECT": {
        "max_retries": 2,
        "backoff_base_seconds": 60,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 300,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },
    "YOUTUBE_COLLECT": {
        "max_retries": 2,
        "backoff_base_seconds": 300,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 600,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },
    "GIG_QUALITY_TITLE": {
        "max_retries": 2,
        "backoff_base_seconds": 10,
        "backoff_multiplier": 1.0,
        "max_backoff_seconds": 10,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },
    "GIG_QUALITY_DESC": {
        "max_retries": 2,
        "backoff_base_seconds": 10,
        "backoff_multiplier": 1.0,
        "max_backoff_seconds": 10,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },
    "RECOMMEND_TITLES": {
        "max_retries": 2,
        "backoff_base_seconds": 10,
        "backoff_multiplier": 1.0,
        "max_backoff_seconds": 10,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },
    "SCORE_KEYWORD": {
        "max_retries": 3,
        "backoff_base_seconds": 2,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 10,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },
    "_default": {
        "max_retries": 3,
        "backoff_base_seconds": 10,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 60,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },
}


def get_retry_config(job_type: str) -> dict[str, Any]:
    """Return retry config for job type or default fallback."""
    return RETRY_CONFIG.get(job_type, RETRY_CONFIG["_default"])


def should_dead_letter_on_error(job_type: str, error_code: str) -> bool:
    """Return True when this error should send the job to dead-letter."""
    return error_code in get_retry_config(job_type)["dead_letter_on"]


def is_no_retry_error(job_type: str, error_code: str) -> bool:
    """Return True when this error must not be retried."""
    return error_code in get_retry_config(job_type)["no_retry_on"]


def classify_error(error: Exception) -> str:
    """Map known exception types to retry policy error codes."""
    if isinstance(error, asyncio.TimeoutError):
        return "TIMEOUT"
    if isinstance(error, ConnectionError):
        return "CONNECT_ERROR"
    if isinstance(error, SessionLoginError):
        return "PERMANENT_BAN"

    status_code = getattr(error, "status_code", None)
    if status_code == HTTPStatus.NOT_FOUND:
        return "HTTP_404"
    if status_code == HTTPStatus.GONE:
        return "HTTP_410"
    if status_code == HTTPStatus.TOO_MANY_REQUESTS:
        return "HTTP_429"

    return "UNKNOWN"
