"""Unit tests for template rendering and retry prompt sanitization."""

from __future__ import annotations

from pathlib import Path

import pytest
from src.llm.template_renderer import (
    TemplateRenderer,
    build_validation_retry_prompt,
)


def test_template_renderer_renders_template_from_custom_directory(tmp_path: Path) -> None:
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "sample.j2").write_text("Hello {{ name }}!", encoding="utf-8")

    renderer = TemplateRenderer(template_dir=template_dir)
    rendered = renderer.render_template("sample.j2", {"name": "Agent"})
    assert rendered == "Hello Agent!"


def test_template_renderer_raises_file_not_found_for_missing_template(tmp_path: Path) -> None:
    renderer = TemplateRenderer(template_dir=tmp_path)
    with pytest.raises(FileNotFoundError, match="not found"):
        renderer.render_template("missing_template.j2", {})


def test_validation_retry_prompt_redacts_common_secret_patterns() -> None:
    prompt = "Use key sk-test1234567890 and api_key=my-secret-value"
    rendered = build_validation_retry_prompt(prompt, ValueError("api_key=another-secret"))
    assert "sk-test1234567890" not in rendered
    assert "my-secret-value" not in rendered
    assert "another-secret" not in rendered
    assert "[REDACTED]" in rendered
