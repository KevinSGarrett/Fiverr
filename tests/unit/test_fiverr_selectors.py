"""Unit tests for Fiverr selector constant hygiene."""

from __future__ import annotations

import pytest
from src.collection import fiverr_selectors as selectors

# Focus on selectors exercised in live-cycle workflows.
SELECTOR_NAMES = [
    "SEARCH_BOX",
    "AUTOCOMPLETE_ITEM",
    "AUTOCOMPLETE_ITEM_TEXT",
    "GIG_CARD_CONTAINER",
    "GIG_CARD_LINK",
    "GIG_CARD_PRICE",
    "GIG_CARD_TITLE",
    "GIG_DETAIL_DESCRIPTION",
    "GIG_DETAIL_RATING",
    "GIG_DETAIL_REVIEW_COUNT",
    "SELLER_LEVEL_BADGE",
    "SELLER_MEMBER_SINCE",
    "SELLER_RESPONSE_TIME",
    "SELLER_TOTAL_REVIEWS",
]


@pytest.mark.parametrize("selector_name", SELECTOR_NAMES)
def test_selector_value_is_non_empty(selector_name: str) -> None:
    value = getattr(selectors, selector_name)
    assert isinstance(value, str)
    assert value.strip() != ""


@pytest.mark.parametrize("selector_name", SELECTOR_NAMES)
def test_selector_is_not_placeholder(selector_name: str) -> None:
    value = getattr(selectors, selector_name)
    assert value.strip().upper() != "UNVERIFIED"
