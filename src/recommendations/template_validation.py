"""Validation helpers for Stage 13 recommendation templates."""

from __future__ import annotations


def validate_template_has_json_instruction(template_content: str) -> bool:
    """Return True when the template includes the JSON-only instruction."""
    return "Return JSON only" in template_content


__all__ = ["validate_template_has_json_instruction"]
