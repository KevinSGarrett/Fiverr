"""Human event helpers used by session-managed Playwright pages."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page


def random_viewport() -> dict[str, int]:
    """Returns a random viewport dict."""
    widths = [1280, 1366, 1440, 1536, 1920]
    heights = [720, 768, 800, 864, 900, 1080]
    return {"width": random.choice(widths), "height": random.choice(heights)}


def random_user_agent() -> str:
    """Returns a random Chrome user agent string."""
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    ]
    return random.choice(agents)


def attach_human_events(page: Page, pacing_config: dict) -> None:
    """
    Attaches human-like event simulation to a Playwright page.

    Stub: no-op in v1. Future: add random scroll timing and mouse movement.
    """
    _ = page
    _ = pacing_config
