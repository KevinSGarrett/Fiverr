"""Safe HTML text extraction helpers for collection parsers."""

from __future__ import annotations

import re
from html.parser import HTMLParser

_TAG_RE = re.compile(r"<[^>]+>")


def clean_html_text(value: str) -> str:
    """Collapse HTML-ish text content into deterministic whitespace."""

    return " ".join(_TAG_RE.sub(" ", value).split())


def extract_data_testid_text(html: str, test_id: str) -> str | None:
    """Extract text from the first element with matching data-testid.

    Uses a depth-aware parser so nested tags are included until the matched
    element closes, avoiding premature truncation at child closing tags.
    """

    class _DataTestIdTextParser(HTMLParser):
        def __init__(self, target_test_id: str) -> None:
            super().__init__(convert_charrefs=True)
            self._target_test_id = target_test_id
            self._collect_depth = 0
            self._chunks: list[str] = []
            self.result: str | None = None

        def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if self.result is not None:
                return
            if self._collect_depth > 0:
                self._collect_depth += 1
                return
            if dict(attrs).get("data-testid") == self._target_test_id:
                self._collect_depth = 1

        def handle_endtag(self, _tag: str) -> None:
            if self.result is not None or self._collect_depth == 0:
                return
            self._collect_depth -= 1
            if self._collect_depth == 0:
                cleaned = clean_html_text("".join(self._chunks))
                self.result = cleaned or None

        def handle_data(self, data: str) -> None:
            if self.result is None and self._collect_depth > 0:
                self._chunks.append(data)

    parser = _DataTestIdTextParser(test_id)
    parser.feed(html)
    parser.close()
    return parser.result
