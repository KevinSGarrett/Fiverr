"""Structured output parsing and sanitized validation errors."""

from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

ModelT = TypeVar("ModelT", bound=BaseModel)

_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)([^\s,;]+)"),
)


def redact_sensitive_text(value: str) -> str:
    """Redact common secret patterns from text."""
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(
            r"\1[REDACTED]" if "api" in pattern.pattern.lower() else "[REDACTED]",
            redacted,
        )
    return redacted


def truncate_for_error_message(value: str, max_chars: int = 240) -> str:
    """Truncate text for safe error details."""
    if len(value) <= max_chars:
        return value
    return f"{value[:max_chars]}...(truncated)"


class LLMValidationError(ValueError):
    """Raised when provider output cannot be safely parsed."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


def parse_json_response(model_cls: type[ModelT], raw_text: str) -> ModelT:
    """Parse and validate a JSON string into a typed Pydantic model."""
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        safe_snippet = truncate_for_error_message(redact_sensitive_text(raw_text))
        raise LLMValidationError(
            "Malformed JSON response from LLM.",
            details={"error": str(exc), "raw_text_preview": safe_snippet},
        ) from exc

    try:
        return model_cls.model_validate(payload)
    except ValidationError as exc:
        safe_errors = redact_sensitive_text(truncate_for_error_message(str(exc)))
        raise LLMValidationError(
            "LLM response failed schema validation.",
            details={"error": safe_errors},
        ) from exc
