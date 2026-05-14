"""Template rendering helpers for LLM prompts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from src.llm.validation import redact_sensitive_text, truncate_for_error_message

_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*)([^\s,;]+)"),
)


def _redact_secrets(value: str) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(r"\1[REDACTED]" if "api" in pattern.pattern.lower() else "[REDACTED]", redacted)
    return redacted


class TemplateRenderer:
    """Render Jinja2 templates from prompt directories."""

    def __init__(self, template_dir: str | Path | None = None) -> None:
        if template_dir is None:
            base_dir = Path(__file__).resolve().parent
            template_dir = base_dir / "prompts"
        self._template_dir = Path(template_dir)
        self._environment = Environment(
            loader=FileSystemLoader(str(self._template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_template(self, template_name: str, context: Mapping[str, Any]) -> str:
        """Render a named template using provided context."""
        try:
            template = self._environment.get_template(template_name)
        except TemplateNotFound as exc:
            raise FileNotFoundError(
                f"Template '{template_name}' not found in '{self._template_dir}'."
            ) from exc
        return template.render(**dict(context))


def build_validation_retry_prompt(original_prompt: str, validation_error: Exception) -> str:
    """Append concise validation guidance to a prompt, with basic secret redaction."""
    safe_prompt = _redact_secrets(original_prompt)
    error_text = _redact_secrets(str(validation_error))
    guidance = (
        "Validation failed. Return a corrected response that strictly matches the required "
        "schema and constraints. Keep the answer concise and well-structured."
    )
    return f"{safe_prompt}\n\n{guidance}\nFailure details: {error_text}"


def build_self_correction_prompt(
    original_task_name: str,
    schema_hint: str,
    validation_error: Exception,
) -> str:
    """Build a safe correction prompt that avoids leaking full prompt contents."""
    safe_task = redact_sensitive_text(original_task_name)
    safe_schema_hint = redact_sensitive_text(schema_hint)
    safe_error = truncate_for_error_message(redact_sensitive_text(str(validation_error)))
    return (
        "Your previous response failed validation.\n"
        f"Task: {safe_task}\n"
        f"Required output schema: {safe_schema_hint}\n"
        f"Validation details: {safe_error}\n\n"
        "Return corrected structured JSON only. No markdown, no prose, and no extra fields."
    )
