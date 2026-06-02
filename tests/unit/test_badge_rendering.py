"""Tests for R10 keyword integrity badge rendering. AC-R10.1."""

from __future__ import annotations

import pytest
from src.dashboard.badge_renderer import BADGE_TYPES, render_keyword_integrity_badge


class MockKS:
    def __init__(
        self,
        tag: str | None = None,
        ghost: bool = False,
        autocomplete_status: str | None = None,
    ) -> None:
        self.tag = tag
        self.ghost_market_flag = ghost
        self.autocomplete_status = autocomplete_status


def test_strong_go_badge() -> None:
    badge = render_keyword_integrity_badge(MockKS(tag="STRONG_GO"))
    assert badge["type"] == "STRONG_GO"
    assert badge["color"] == "green"


def test_conditional_go_badge() -> None:
    badge = render_keyword_integrity_badge(MockKS(tag="CONDITIONAL_GO"))
    assert badge["type"] == "CONDITIONAL_GO"


def test_ghost_market_overrides_tag() -> None:
    badge = render_keyword_integrity_badge(MockKS(tag="STRONG_GO", ghost=True))
    assert badge["type"] == "GHOST_MARKET"


def test_null_row_returns_data_integrity_gap() -> None:
    badge = render_keyword_integrity_badge(None)
    assert badge["type"] == "DATA_INTEGRITY_GAP"


def test_unknown_tag_returns_data_integrity_gap() -> None:
    badge = render_keyword_integrity_badge(MockKS(tag="UNKNOWN_VALUE"))
    assert badge["type"] == "DATA_INTEGRITY_GAP"


def test_emerging_overlay_on_emerging_keyword() -> None:
    badge = render_keyword_integrity_badge(
        MockKS(tag="CONDITIONAL_GO", autocomplete_status="emerging")
    )
    assert badge.get("emerging_overlay") is True


def test_all_7_badge_types_defined() -> None:
    for btype in [
        "STRONG_GO",
        "CONDITIONAL_GO",
        "MONITOR",
        "CAUTION",
        "GHOST_MARKET",
        "EMERGING",
        "DATA_INTEGRITY_GAP",
    ]:
        assert btype in BADGE_TYPES


def test_monitor_badge() -> None:
    badge = render_keyword_integrity_badge(MockKS(tag="MONITOR"))
    assert badge["type"] == "MONITOR" and badge["color"] == "orange"


def test_caution_badge() -> None:
    badge = render_keyword_integrity_badge(MockKS(tag="CAUTION"))
    assert badge["type"] == "CAUTION" and badge["color"] == "red"


@pytest.mark.parametrize(
    "tag,expected_color",
    [
        ("STRONG_GO", "green"),
        ("CONDITIONAL_GO", "yellow"),
        ("MONITOR", "orange"),
        ("CAUTION", "red"),
        ("EMERGING", "blue"),
        ("DATA_INTEGRITY_GAP", "gray"),
    ],
)
def test_tag_to_color_mapping(tag: str, expected_color: str) -> None:
    badge = BADGE_TYPES[tag]
    assert badge["color"] == expected_color
