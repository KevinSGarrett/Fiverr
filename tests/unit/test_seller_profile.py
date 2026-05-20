"""Unit tests for Workflow 5 seller profile helper functions."""

from __future__ import annotations

from src.collection.workflows.seller_profile import (
    build_seller_profile_url,
    parse_member_since,
    parse_response_rate,
    parse_seller_level,
)


def test_build_seller_url() -> None:
    assert build_seller_profile_url("sample_user") == "https://www.fiverr.com/sample_user"


def test_parse_member_since_jan() -> None:
    assert parse_member_since("Member since Jan 2022") == "2022-01"


def test_parse_member_since_none() -> None:
    assert parse_member_since(None) is None


def test_parse_member_since_no_date_pattern() -> None:
    assert parse_member_since("Member for years") is None


def test_parse_seller_level_trs() -> None:
    assert parse_seller_level("Top Rated Seller") == "TRS"


def test_parse_seller_level_no_level() -> None:
    assert parse_seller_level(None) == "NO_LEVEL"


def test_parse_seller_level_level_2() -> None:
    assert parse_seller_level("Level 2 Seller") == "LEVEL_2"


def test_parse_seller_level_level_1() -> None:
    assert parse_seller_level("Level 1 Seller") == "LEVEL_1"


def test_parse_seller_level_pro() -> None:
    assert parse_seller_level("Pro Verified") == "PRO"


def test_parse_seller_level_unknown_defaults_to_no_level() -> None:
    assert parse_seller_level("Rookie") == "NO_LEVEL"


def test_parse_response_rate_percent() -> None:
    assert parse_response_rate("98%") == 98


def test_parse_response_rate_none() -> None:
    assert parse_response_rate(None) is None


def test_parse_response_rate_no_digits() -> None:
    assert parse_response_rate("N/A") is None
