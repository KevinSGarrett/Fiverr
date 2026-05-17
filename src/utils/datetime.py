"""Date/time utility functions — AC-1.6.1, AC-1.6.2."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime


def format_duration(seconds: int | float) -> str:
    """Format a duration in seconds to a human-readable string.

    Examples:
        >>> format_duration(7380)
        '2h 3m'
        >>> format_duration(45)
        '45s'
        >>> format_duration(3600)
        '1h 0m'
    """
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {secs}s" if secs else f"{minutes}m"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins}m"


def date_stamp(dt: datetime | None = None) -> str:
    """Return a compact date stamp string (YYYYMMDD).

    Args:
        dt: Datetime to format; defaults to current UTC time.

    Returns:
        String in ``YYYYMMDD`` format.
    """
    if dt is None:
        dt = datetime.now(tz=UTC)
    return dt.strftime("%Y%m%d")


def timestamp_stamp(dt: datetime | None = None) -> str:
    """Return a compact datetime stamp (YYYYMMDD_HHMMSS).

    Args:
        dt: Datetime to format; defaults to current UTC time.

    Returns:
        String in ``YYYYMMDD_HHMMSS`` format, suitable for run IDs.
    """
    if dt is None:
        dt = datetime.now(tz=UTC)
    return dt.strftime("%Y%m%d_%H%M%S")


_FIVERR_DATE_PATTERNS: list[str] = [
    "%b %d, %Y",   # Jan 01, 2024
    "%B %d, %Y",   # January 01, 2024
    "%Y-%m-%d",    # 2024-01-01
    "%d/%m/%Y",    # 01/01/2024
]

_RELATIVE_RE = re.compile(r"(\d+)\s+(day|week|month|year)s?\s+ago", re.IGNORECASE)


def parse_fiverr_date(raw: str) -> date | None:
    """Parse a Fiverr-style date string into a ``date`` object.

    Handles absolute date formats and relative expressions such as
    ``"3 months ago"`` or ``"1 year ago"``.

    Args:
        raw: Raw date string scraped from Fiverr.

    Returns:
        A :class:`datetime.date` or ``None`` if parsing fails.
    """
    if not raw:
        return None
    raw = raw.strip()

    # Try absolute formats first
    for fmt in _FIVERR_DATE_PATTERNS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue

    # Try relative expressions
    m = _RELATIVE_RE.search(raw)
    if m:
        amount = int(m.group(1))
        unit = m.group(2).lower()
        today = date.today()
        if unit == "day":
            from datetime import timedelta
            return today - timedelta(days=amount)
        if unit == "week":
            from datetime import timedelta
            return today - timedelta(weeks=amount)
        if unit == "month":
            month = today.month - amount
            year = today.year + month // 12
            month = month % 12 or 12
            return today.replace(year=year, month=month, day=min(today.day, 28))
        if unit == "year":
            return today.replace(year=today.year - amount)

    return None
