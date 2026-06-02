"""Unit tests for new utility modules — AC-1.6.1 through AC-1.6.6."""
from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# AC-1.6.1 / AC-1.6.2  format_duration
# ---------------------------------------------------------------------------

class TestFormatDuration:
    """AC-1.6.1 format_duration(7380) == '2h 3m'
       AC-1.6.2 format_duration(45) == '45s'
    """

    def test_hours_and_minutes_utils(self) -> None:
        from src.utils.datetime import format_duration
        assert format_duration(7380) == "2h 3m"

    def test_seconds_only_utils(self) -> None:
        from src.utils.datetime import format_duration
        assert format_duration(45) == "45s"

    def test_zero_utils(self) -> None:
        from src.utils.datetime import format_duration
        assert format_duration(0) == "0s"

    def test_exact_hour(self) -> None:
        from src.utils.datetime import format_duration
        assert format_duration(3600) == "1h 0m"

    def test_exact_minute(self) -> None:
        from src.utils.datetime import format_duration
        assert format_duration(120) == "2m"

    def test_minutes_and_seconds(self) -> None:
        from src.utils.datetime import format_duration
        assert format_duration(90) == "1m 30s"


class TestDateStamp:
    def test_returns_8_char_string(self) -> None:
        from src.utils.datetime import date_stamp
        result = date_stamp()
        assert len(result) == 8
        assert result.isdigit()

    def test_known_datetime(self) -> None:
        from src.utils.datetime import date_stamp
        dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        assert date_stamp(dt) == "20240115"


class TestParseFiverrDate:
    def test_absolute_mmm_dd_yyyy(self) -> None:
        from src.utils.datetime import parse_fiverr_date
        result = parse_fiverr_date("Jan 15, 2024")
        assert result == date(2024, 1, 15)

    def test_iso_format_utils(self) -> None:
        from src.utils.datetime import parse_fiverr_date
        result = parse_fiverr_date("2024-06-01")
        assert result == date(2024, 6, 1)

    def test_empty_returns_none(self) -> None:
        from src.utils.datetime import parse_fiverr_date
        assert parse_fiverr_date("") is None
        assert parse_fiverr_date(None) is None  # type: ignore[arg-type]

    def test_relative_days_ago(self) -> None:
        from src.utils.datetime import parse_fiverr_date
        result = parse_fiverr_date("3 days ago")
        today = date.today()
        from datetime import timedelta
        assert result == today - timedelta(days=3)

    def test_unparseable_returns_none(self) -> None:
        from src.utils.datetime import parse_fiverr_date
        assert parse_fiverr_date("not a date at all xyz") is None


# ---------------------------------------------------------------------------
# AC-1.6.3  validate_price / validate_url / sanitize_text
# ---------------------------------------------------------------------------

class TestValidatePrice:
    """AC-1.6.3 validate_price(50.0) == True; validate_price(-5.0) == False"""

    def test_valid_positive(self) -> None:
        from src.utils.validation import validate_price
        assert validate_price(50.0) is True

    def test_valid_zero(self) -> None:
        from src.utils.validation import validate_price
        assert validate_price(0) is True

    def test_negative_is_invalid(self) -> None:
        from src.utils.validation import validate_price
        assert validate_price(-5.0) is False

    def test_none_is_invalid(self) -> None:
        from src.utils.validation import validate_price
        assert validate_price(None) is False  # type: ignore[arg-type]

    def test_string_float_is_valid(self) -> None:
        from src.utils.validation import validate_price
        # numeric string converts correctly
        assert validate_price("25.50") is True  # type: ignore[arg-type]

    def test_non_numeric_is_invalid(self) -> None:
        from src.utils.validation import validate_price
        assert validate_price("abc") is False  # type: ignore[arg-type]


class TestValidateUrl:
    def test_valid_https_utils(self) -> None:
        from src.utils.validation import validate_url
        assert validate_url("https://www.fiverr.com/categories") is True

    def test_valid_http_utils(self) -> None:
        from src.utils.validation import validate_url
        assert validate_url("http://example.com/path") is True

    def test_no_scheme_is_invalid(self) -> None:
        from src.utils.validation import validate_url
        assert validate_url("www.fiverr.com") is False

    def test_empty_is_invalid(self) -> None:
        from src.utils.validation import validate_url
        assert validate_url("") is False
        assert validate_url(None) is False  # type: ignore[arg-type]


class TestSanitizeText:
    def test_strips_whitespace(self) -> None:
        from src.utils.validation import sanitize_text
        assert sanitize_text("  hello  ") == "hello"

    def test_collapses_internal_spaces(self) -> None:
        from src.utils.validation import sanitize_text
        assert sanitize_text("a  b   c") == "a b c"

    def test_empty_returns_empty(self) -> None:
        from src.utils.validation import sanitize_text
        assert sanitize_text("") == ""
        assert sanitize_text(None) == ""  # type: ignore[arg-type]

    def test_max_length_truncates(self) -> None:
        from src.utils.validation import sanitize_text
        result = sanitize_text("hello world", max_length=5)
        assert len(result) <= 5


# ---------------------------------------------------------------------------
# AC-1.6.4  jaccard_similarity
# ---------------------------------------------------------------------------

class TestJaccardSimilarity:
    """AC-1.6.4 jaccard_similarity returns float in [0, 1]."""

    def test_identical_strings(self) -> None:
        from src.utils.hashing import jaccard_similarity
        assert jaccard_similarity("ai saas prd", "ai saas prd") == pytest.approx(1.0)

    def test_completely_different(self) -> None:
        from src.utils.hashing import jaccard_similarity
        result = jaccard_similarity("apple orange", "car truck")
        assert 0.0 <= result < 0.5

    def test_partial_overlap_utils(self) -> None:
        from src.utils.hashing import jaccard_similarity
        result = jaccard_similarity("ai saas prd", "ai saas product requirements")
        assert 0.0 < result < 1.0

    def test_above_threshold_for_near_duplicates(self) -> None:
        # AC-1.3.5: 0.65 threshold — similar titles should exceed it
        from src.utils.hashing import jaccard_similarity
        result = jaccard_similarity("AI PRD writing service", "AI PRD writer service")
        assert result >= 0.5  # clearly similar

    def test_empty_strings_utils(self) -> None:
        from src.utils.hashing import jaccard_similarity
        assert jaccard_similarity("", "") == pytest.approx(1.0)

    def test_return_type_is_float(self) -> None:
        from src.utils.hashing import jaccard_similarity
        result = jaccard_similarity("hello world", "goodbye world")
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0


# ---------------------------------------------------------------------------
# AC-1.6.5  sha256_hash
# ---------------------------------------------------------------------------

class TestSha256Hash:
    """AC-1.6.5 sha256_hash returns consistent 64-char hex string."""

    def test_returns_64_char_hex(self) -> None:
        from src.utils.hashing import sha256_hash
        result = sha256_hash("test")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_idempotent_sha256(self) -> None:
        from src.utils.hashing import sha256_hash
        assert sha256_hash("test") == sha256_hash("test")

    def test_different_inputs_differ(self) -> None:
        from src.utils.hashing import sha256_hash
        assert sha256_hash("a") != sha256_hash("b")

    def test_empty_string(self) -> None:
        from src.utils.hashing import sha256_hash
        result = sha256_hash("")
        assert len(result) == 64


# ---------------------------------------------------------------------------
# AC-1.6.6  ensure_export_dirs
# ---------------------------------------------------------------------------

class TestEnsureExportDirs:
    """AC-1.6.6 ensure_export_dirs() creates all export subdirectories."""

    def test_creates_all_subdirectories(self, tmp_path: Path) -> None:
        from src.utils.export import ensure_export_dirs
        export_root = ensure_export_dirs(base_path=tmp_path / "exports")
        assert export_root.exists()
        assert (export_root / "reports").exists()
        assert (export_root / "csv").exists()
        assert (export_root / "json").exists()
        assert (export_root / "markdown").exists()
        assert (export_root / "pdf").exists()
        assert (export_root / "playbook").exists()

    def test_idempotent_export_dirs_utils(self, tmp_path: Path) -> None:
        from src.utils.export import ensure_export_dirs
        root = tmp_path / "exp"
        ensure_export_dirs(base_path=root)
        ensure_export_dirs(base_path=root)  # second call must not raise
        assert root.exists()

    def test_returns_path_object(self, tmp_path: Path) -> None:
        from src.utils.export import ensure_export_dirs
        result = ensure_export_dirs(base_path=tmp_path / "e")
        assert isinstance(result, Path)


class TestGetExportPath:
    def test_creates_correct_subpath(self, tmp_path: Path) -> None:
        from src.utils.export import get_export_path
        path = get_export_path("csv", "test.csv", base_path=tmp_path / "exports")
        assert path.parent.name == "csv"
        assert path.name == "test.csv"

    def test_directory_created(self, tmp_path: Path) -> None:
        from src.utils.export import get_export_path
        path = get_export_path("json", "out.json", base_path=tmp_path / "exports")
        assert path.parent.exists()
