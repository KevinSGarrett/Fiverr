"""Tests for new audit-remediation modules: utils, models, recommendations, workflows."""
from __future__ import annotations

import pytest

# ── src/utils/datetime ─────────────────────────────────────────────────────────


class TestFormatDuration:
    def test_seconds_only_duration(self) -> None:
        from src.utils.datetime import format_duration
        assert format_duration(45) == "45s"

    def test_minutes_exact(self) -> None:
        from src.utils.datetime import format_duration
        assert format_duration(120) == "2m"

    def test_minutes_with_seconds(self) -> None:
        from src.utils.datetime import format_duration
        assert format_duration(90) == "1m 30s"

    def test_hours_and_minutes_duration(self) -> None:
        from src.utils.datetime import format_duration
        assert format_duration(7380) == "2h 3m"

    def test_zero_duration(self) -> None:
        from src.utils.datetime import format_duration
        assert format_duration(0) == "0s"

    def test_one_hour(self) -> None:
        from src.utils.datetime import format_duration
        assert format_duration(3600) == "1h 0m"

    def test_float_input(self) -> None:
        from src.utils.datetime import format_duration
        assert format_duration(45.9) == "45s"


class TestDateStamp:
    def test_returns_string(self) -> None:
        from src.utils.datetime import date_stamp
        result = date_stamp()
        assert isinstance(result, str)
        assert len(result) == 8
        assert result.isdigit()

    def test_timestamp_stamp(self) -> None:
        from src.utils.datetime import timestamp_stamp
        result = timestamp_stamp()
        assert isinstance(result, str)
        assert len(result) == 15  # YYYYMMDD_HHMMSS
        assert "_" in result


class TestParseFiverrDate:
    def test_none_input(self) -> None:
        from src.utils.datetime import parse_fiverr_date
        assert parse_fiverr_date("") is None
        assert parse_fiverr_date(None) is None  # type: ignore[arg-type]

    def test_iso_format_date(self) -> None:
        from src.utils.datetime import parse_fiverr_date
        result = parse_fiverr_date("2024-01-15")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_short_month_format(self) -> None:
        from src.utils.datetime import parse_fiverr_date
        result = parse_fiverr_date("Jan 15, 2024")
        assert result is not None
        assert result.year == 2024

    def test_relative_days(self) -> None:
        from src.utils.datetime import parse_fiverr_date
        result = parse_fiverr_date("3 days ago")
        assert result is not None

    def test_relative_weeks(self) -> None:
        from src.utils.datetime import parse_fiverr_date
        result = parse_fiverr_date("2 weeks ago")
        assert result is not None

    def test_relative_months(self) -> None:
        from src.utils.datetime import parse_fiverr_date
        result = parse_fiverr_date("6 months ago")
        assert result is not None

    def test_relative_years(self) -> None:
        from src.utils.datetime import parse_fiverr_date
        result = parse_fiverr_date("1 year ago")
        assert result is not None

    def test_unparseable(self) -> None:
        from src.utils.datetime import parse_fiverr_date
        assert parse_fiverr_date("not a date at all xyz") is None


# ── src/utils/validation ──────────────────────────────────────────────────────


class TestValidateUrl:
    def test_valid_https_url(self) -> None:
        from src.utils.validation import validate_url
        assert validate_url("https://www.fiverr.com/services/ai") is True

    def test_valid_http_url(self) -> None:
        from src.utils.validation import validate_url
        assert validate_url("http://example.com") is True

    def test_none_url(self) -> None:
        from src.utils.validation import validate_url
        assert validate_url(None) is False  # type: ignore[arg-type]

    def test_empty_url(self) -> None:
        from src.utils.validation import validate_url
        assert validate_url("") is False

    def test_no_protocol(self) -> None:
        from src.utils.validation import validate_url
        assert validate_url("www.example.com") is False


class TestValidatePrice:
    def test_positive(self) -> None:
        from src.utils.validation import validate_price
        assert validate_price(50.0) is True

    def test_zero_price(self) -> None:
        from src.utils.validation import validate_price
        assert validate_price(0) is True

    def test_negative(self) -> None:
        from src.utils.validation import validate_price
        assert validate_price(-5.0) is False

    def test_none_price(self) -> None:
        from src.utils.validation import validate_price
        assert validate_price(None) is False  # type: ignore[arg-type]

    def test_nan(self) -> None:
        from src.utils.validation import validate_price
        assert validate_price(float("nan")) is False

    def test_inf(self) -> None:
        from src.utils.validation import validate_price
        assert validate_price(float("inf")) is False


class TestSanitizeText:
    def test_basic(self) -> None:
        from src.utils.validation import sanitize_text
        assert sanitize_text("  hello world  ") == "hello world"

    def test_empty_text(self) -> None:
        from src.utils.validation import sanitize_text
        assert sanitize_text("") == ""

    def test_none_text(self) -> None:
        from src.utils.validation import sanitize_text
        assert sanitize_text(None) == ""  # type: ignore[arg-type]

    def test_max_length(self) -> None:
        from src.utils.validation import sanitize_text
        result = sanitize_text("abcdef", max_length=3)
        assert result == "abc"

    def test_collapses_whitespace(self) -> None:
        from src.utils.validation import sanitize_text
        assert sanitize_text("hello   world") == "hello world"


# ── src/utils/hashing ────────────────────────────────────────────────────────


class TestSha256Hash:
    def test_returns_64_chars(self) -> None:
        from src.utils.hashing import sha256_hash
        result = sha256_hash("test")
        assert len(result) == 64

    def test_deterministic(self) -> None:
        from src.utils.hashing import sha256_hash
        assert sha256_hash("hello") == sha256_hash("hello")

    def test_different_inputs(self) -> None:
        from src.utils.hashing import sha256_hash
        assert sha256_hash("a") != sha256_hash("b")


class TestJaccardSimilarity:
    def test_identical(self) -> None:
        from src.utils.hashing import jaccard_similarity
        assert jaccard_similarity("ai saas prd", "ai saas prd") == 1.0

    def test_no_overlap(self) -> None:
        from src.utils.hashing import jaccard_similarity
        result = jaccard_similarity("hello world", "foo bar baz")
        assert result == 0.0

    def test_partial_overlap_jaccard(self) -> None:
        from src.utils.hashing import jaccard_similarity
        result = jaccard_similarity("hello world", "goodbye world")
        assert 0.0 < result < 1.0

    def test_empty_strings_jaccard(self) -> None:
        from src.utils.hashing import jaccard_similarity
        assert jaccard_similarity("", "") == 1.0

    def test_above_threshold(self) -> None:
        from src.utils.hashing import jaccard_similarity
        result = jaccard_similarity("ai prd writing", "ai prd writer")
        assert result >= 0.5


# ── src/utils/export ─────────────────────────────────────────────────────────


class TestEnsureExportDirs:
    def test_creates_dirs(self, tmp_path) -> None:
        from src.utils.export import ensure_export_dirs
        root = ensure_export_dirs(tmp_path / "exports")
        assert root.exists()
        assert (root / "reports").exists()
        assert (root / "csv").exists()
        assert (root / "json").exists()
        assert (root / "markdown").exists()

    def test_idempotent_export_dirs(self, tmp_path) -> None:
        from src.utils.export import ensure_export_dirs
        root = tmp_path / "exports"
        ensure_export_dirs(root)
        ensure_export_dirs(root)  # second call should not raise
        assert root.exists()


class TestGetExportPath:
    def test_returns_path_in_subdir(self, tmp_path) -> None:
        from src.utils.export import get_export_path
        path = get_export_path("csv", "test.csv", base_path=tmp_path / "exports")
        assert path.name == "test.csv"
        assert "csv" in str(path)


# ── src/recommendations ──────────────────────────────────────────────────────


class TestRecommendationContracts:
    def test_recommendation_context_completeness_empty(self) -> None:
        from src.recommendations.contracts import RecommendationContext
        ctx = RecommendationContext(niche_id="test", keyword="kw")
        assert ctx.completeness_ratio() == 0.0

    def test_recommendation_context_completeness_partial(self) -> None:
        from src.recommendations.contracts import RecommendationContext
        ctx = RecommendationContext(
            niche_id="test", keyword="kw",
            score_data={"demand": 75}, competitor_data={"count": 5}
        )
        ratio = ctx.completeness_ratio()
        assert 0.0 < ratio < 1.0

    def test_recommendation_output_completeness_zero(self) -> None:
        from src.recommendations.contracts import RecommendationOutput
        out = RecommendationOutput(niche_id="n", keyword="k")
        assert out.completeness_ratio() == 0.0

    def test_recommendation_output_completeness_partial(self) -> None:
        from src.recommendations.contracts import GigTitle, RecommendationOutput
        out = RecommendationOutput(
            niche_id="n", keyword="k",
            gig_titles=[GigTitle(title="Test title")]
        )
        ratio = out.completeness_ratio()
        assert ratio == pytest.approx(1 / 14, rel=0.01)

    def test_gig_title_model(self) -> None:
        from src.recommendations.contracts import GigTitle
        t = GigTitle(title="I will build your Python automation")
        assert t.title == "I will build your Python automation"
        assert t.rationale is None

    def test_tag_set_model(self) -> None:
        from src.recommendations.contracts import TagSet
        ts = TagSet(tags=["ai automation", "python script"])
        assert len(ts.tags) == 2

    def test_package_structure(self) -> None:
        from src.recommendations.contracts import PackageStructure, PackageTier
        pkg = PackageStructure(
            basic=PackageTier(name="Basic", price=25.0, delivery_days=3),
            standard=PackageTier(name="Standard", price=50.0, delivery_days=5),
            premium=PackageTier(name="Premium", price=100.0, delivery_days=7),
        )
        assert pkg.basic.price < pkg.standard.price < pkg.premium.price

    def test_niche_viability_model(self) -> None:
        from src.recommendations.contracts import NicheViability
        nv = NicheViability(viability_rating=8.5, reasoning="Strong demand, low competition")
        assert nv.viability_rating == 8.5

    def test_red_flags_default_risk(self) -> None:
        from src.recommendations.contracts import RedFlagsAssessment
        rf = RedFlagsAssessment(risks=["High entry bar"])
        assert rf.risk_level == "MEDIUM"


class TestRecommendationOrchestrator:
    def test_stub_returns_unscored(self) -> None:
        from src.recommendations import RecommendationContext, RecommendationOrchestrator
        orch = RecommendationOrchestrator()
        ctx = RecommendationContext(niche_id="prd_ai_saas", keyword="ai prd writer", run_id=1)
        result = orch.generate(ctx)
        assert result.generation_complete is False
        assert result.niche_id == "prd_ai_saas"
        assert result.keyword == "ai prd writer"
        assert result.run_id == 1


# ── src/models new models ────────────────────────────────────────────────────


class TestNewModels:
    def test_keyword_gig_association_tablename(self) -> None:
        from src.models.associations import KeywordGigAssociation
        assert KeywordGigAssociation.__tablename__ == "keyword_gig_associations"

    def test_gig_visual_analysis_tablename(self) -> None:
        from src.models.visual import GigVisualAnalysis
        assert GigVisualAnalysis.__tablename__ == "gig_visual_analyses"

    def test_discovery_cycle_log_tablename(self) -> None:
        from src.models.discovery_cycle import DiscoveryCycleLog
        assert DiscoveryCycleLog.__tablename__ == "discovery_cycle_logs"

    def test_auto_promotion_log_tablename(self) -> None:
        from src.models.auto_promotion import AutoPromotionLog
        assert AutoPromotionLog.__tablename__ == "auto_promotion_logs"

    def test_order_tablename(self) -> None:
        from src.models.order import Order
        assert Order.__tablename__ == "orders"

    def test_keyword_has_discovery_fields(self) -> None:
        from sqlalchemy import inspect as sa_inspect
        from src.models.market import Keyword
        cols = {c.name for c in sa_inspect(Keyword).c}
        assert "is_discovery" in cols
        assert "discovery_mode" in cols
        assert "hypothesis_confidence" in cols

    def test_new_models_in_package(self) -> None:
        from src.models import (
            AutoPromotionLog,
            DiscoveryCycleLog,
            GigVisualAnalysis,
            KeywordGigAssociation,
            Order,
        )
        assert KeywordGigAssociation is not None
        assert GigVisualAnalysis is not None
        assert DiscoveryCycleLog is not None
        assert AutoPromotionLog is not None
        assert Order is not None


# ── src/collection/workflows ────────────────────────────────────────────────


class TestWorkflowClasses:
    def test_keyword_expansion_workflow_exists(self) -> None:
        from src.collection.workflows import KeywordExpansionWorkflow
        w = KeywordExpansionWorkflow()
        result = w.run()
        assert result is not None  # returns module

    def test_gig_detail_workflow_exists(self) -> None:
        from src.collection.workflows import GigDetailWorkflow
        w = GigDetailWorkflow()
        result = w.run()
        assert result is not None

    def test_google_trends_workflow_exists(self) -> None:
        from src.collection.workflows import GoogleTrendsWorkflow
        w = GoogleTrendsWorkflow()
        result = w.run()
        assert result is not None

    def test_youtube_count_workflow_exists(self) -> None:
        from src.collection.workflows import YoutubeCountWorkflow
        w = YoutubeCountWorkflow()
        result = w.run()
        assert result is not None

    def test_reddit_signal_workflow_exists(self) -> None:
        from src.collection.workflows import RedditSignalWorkflow
        w = RedditSignalWorkflow()
        result = w.run()
        assert result is not None

    def test_seller_profile_workflow_exists(self) -> None:
        from src.collection.workflows import SellerProfileWorkflow
        w = SellerProfileWorkflow()
        result = w.run()
        assert result is not None

    def test_autocomplete_workflow_exists(self) -> None:
        from src.collection.workflows import AutocompleteWorkflow
        w = AutocompleteWorkflow()
        result = w.run()
        assert result is not None

    def test_fiverr_search_raises(self) -> None:
        from src.collection.workflows import FiverrSearchWorkflow
        w = FiverrSearchWorkflow()
        with pytest.raises(NotImplementedError):
            w.run()

    def test_auto_promotion_raises(self) -> None:
        from src.collection.workflows import AutoPromotionWorkflow
        w = AutoPromotionWorkflow()
        with pytest.raises(NotImplementedError):
            w.run()


# ── src/collection aliases ────────────────────────────────────────────────────


class TestCollectionAliases:
    def test_session_manager_alias(self) -> None:
        from src.collection import ManagedBrowserSession, SessionManager
        assert SessionManager is ManagedBrowserSession

    def test_queue_processor_alias(self) -> None:
        from src.collection import CollectionQueue, QueueProcessor
        assert QueueProcessor is CollectionQueue


# ── src/collection/selectors VISUAL group ────────────────────────────────────


class TestVisualSelectors:
    def test_visual_group_in_registry(self) -> None:
        from src.collection.selectors import SELECTOR_REGISTRY
        assert "visual" in SELECTOR_REGISTRY

    def test_visual_has_required_keys(self) -> None:
        from src.collection.selectors import SELECTOR_REGISTRY
        visual = SELECTOR_REGISTRY["visual"]
        for key in ("gig_thumbnail", "gallery_item", "video_indicator", "seller_avatar"):
            assert key in visual, f"Missing visual selector: {key}"

    def test_get_visual_selector(self) -> None:
        from src.collection.selectors import get_selector
        result = get_selector("visual", "gig_thumbnail")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_selector_validation_includes_visual(self) -> None:
        from src.collection.selectors import validate_selector_registry
        errors = validate_selector_registry()
        assert errors == [], f"Selector validation errors: {errors}"


# ── src/dashboard/pages ───────────────────────────────────────────────────────


class TestDashboardPages:
    def test_opportunities_raises(self) -> None:
        from src.dashboard.pages import render_opportunities_page
        with pytest.raises(NotImplementedError):
            render_opportunities_page()

    def test_keywords_raises(self) -> None:
        from src.dashboard.pages import render_keywords_page
        with pytest.raises(NotImplementedError):
            render_keywords_page()

    def test_competitors_raises(self) -> None:
        from src.dashboard.pages import render_competitors_page
        with pytest.raises(NotImplementedError):
            render_competitors_page()

    def test_recommendations_raises(self) -> None:
        from src.dashboard.pages import render_recommendations_page
        with pytest.raises(NotImplementedError):
            render_recommendations_page()

    def test_run_history_raises(self) -> None:
        from src.dashboard.pages import render_run_history_page
        with pytest.raises(NotImplementedError):
            render_run_history_page()

    def test_llm_costs_raises(self) -> None:
        from src.dashboard.pages import render_llm_costs_page
        with pytest.raises(NotImplementedError):
            render_llm_costs_page()

    def test_discovery_raises(self) -> None:
        from src.dashboard.pages import render_discovery_page
        with pytest.raises(NotImplementedError):
            render_discovery_page()

    def test_pricing_raises(self) -> None:
        from src.dashboard.pages import render_pricing_page
        with pytest.raises(NotImplementedError):
            render_pricing_page()

    def test_playbook_raises(self) -> None:
        from src.dashboard.pages import render_playbook_page
        with pytest.raises(NotImplementedError):
            render_playbook_page()

    def test_legacy_exports_still_present(self) -> None:
        from src.dashboard.pages import (
            build_registered_page_payloads,
            get_dashboard_page_payload_builders,
        )
        assert callable(build_registered_page_payloads)
        assert callable(get_dashboard_page_payload_builders)


# ── src/orchestrator AVAILABLE_MODES ──────────────────────────────────────────


class TestAvailableModes:
    def test_all_nine_modes_present(self) -> None:
        from src.orchestrator import AVAILABLE_MODES
        required = {
            "full", "collect-only", "score-only", "analyze-only",
            "price-analysis",
            "recommendations-only", "discovery-only", "discovery-collect", "resume",
        }
        assert required.issubset(set(AVAILABLE_MODES)), (
            f"Missing modes: {required - set(AVAILABLE_MODES)}"
        )

    def test_discovery_collect_in_stage_availability(self) -> None:
        from src.orchestrator import STAGE_AVAILABILITY
        assert "discovery-collect" in STAGE_AVAILABILITY
