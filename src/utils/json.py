"""Safe JSON serialization helpers."""

from __future__ import annotations

import json
from typing import Any


def safe_json_dumps(value: Any, *, sort_keys: bool = True) -> str:
    """Serialize value to JSON with stable defaults."""
    try:
        return json.dumps(value, sort_keys=sort_keys)
    except TypeError as exc:
        raise ValueError(f"Failed to serialize value to JSON: {exc}") from exc


def safe_json_loads(value: str) -> Any:
    """Parse JSON string with explicit error context."""
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Malformed JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
