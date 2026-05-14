"""Shared logging configuration helpers."""

from __future__ import annotations

import logging
import re
from typing import Any

API_KEY_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{10,}"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)([A-Za-z0-9_\-]{8,})"),
]


class RedactingFilter(logging.Filter):
    """Redact common API key patterns from log messages."""

    def _redact(self, value: str) -> str:
        redacted = value
        redacted = API_KEY_PATTERNS[0].sub("[REDACTED_API_KEY]", redacted)
        redacted = API_KEY_PATTERNS[1].sub(r"\1[REDACTED]", redacted)
        return redacted

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._redact(str(record.msg))
        if record.args:
            args: Any = record.args
            if isinstance(args, tuple):
                record.args = tuple(self._redact(str(item)) for item in args)
            elif isinstance(args, dict):
                record.args = {k: self._redact(str(v)) for k, v in args.items()}
        return True


def configure_logging(log_level: str = "INFO", redact_secrets: bool = True) -> None:
    """Configure root logging with optional secret redaction."""
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    )
    if redact_secrets:
        handler.addFilter(RedactingFilter())

    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
