"""Scheduler and collection retry exception types."""


class RateLimitError(Exception):
    """Raised when a 429 or rate limit is detected during collection."""

    def __init__(self, source: str = "unknown", retry_after_seconds: int = 600):
        self.source = source
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limit on {source}. Retry after {retry_after_seconds}s.")


class SessionExpiredError(Exception):
    """Raised when Fiverr session verification fails during collection."""


class PermanentError(Exception):
    """Raised for non-retryable errors (404, 410, permanent ban)."""

    def __init__(self, error_code: str, message: str = ""):
        self.error_code = error_code
        super().__init__(f"Permanent error [{error_code}]: {message}")


class CollectionError(Exception):
    """Base class for all collection-layer errors."""
