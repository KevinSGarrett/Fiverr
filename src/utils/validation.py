"""Data validation utilities — AC-1.6.3."""

from __future__ import annotations

import re
import unicodedata


def validate_url(url: str | None) -> bool:
    """Return True if *url* looks like a valid HTTP/HTTPS URL.

    Args:
        url: String to validate.

    Returns:
        ``True`` if the string starts with ``http://`` or ``https://`` and
        contains a dot-separated host; ``False`` otherwise.
    """
    if not url:
        return False
    pattern = re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
        r"localhost|"
        r"\d{1,3}(?:\.\d{1,3}){3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(pattern.match(url))


def validate_price(price: float | int | None) -> bool:
    """Return True if *price* is a valid non-negative monetary value.

    Args:
        price: Numeric price to validate.

    Returns:
        ``True`` if price is a finite non-negative number; ``False`` otherwise.

    Examples:
        >>> validate_price(50.0)
        True
        >>> validate_price(-5.0)
        False
        >>> validate_price(0)
        True
    """
    if price is None:
        return False
    try:
        f = float(price)
    except (TypeError, ValueError):
        return False
    import math
    return math.isfinite(f) and f >= 0.0


def sanitize_text(text: str | None, *, max_length: int | None = None) -> str:
    """Clean and normalise text scraped from web pages.

    Strips leading/trailing whitespace, collapses internal whitespace runs,
    removes non-printable control characters, and optionally truncates.

    Args:
        text: Raw text string.
        max_length: Optional maximum character length to truncate to.

    Returns:
        Cleaned string, never ``None``.
    """
    if not text:
        return ""
    # Unicode normalise to NFC
    text = unicodedata.normalize("NFC", text)
    # Strip control characters (keep printable + standard whitespace)
    text = "".join(ch for ch in text if ch.isprintable() or ch in (" ", "\t"))
    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text).strip()
    if max_length and len(text) > max_length:
        text = text[:max_length]
    return text
