"""Unit tests for Cycle 003 analysis contracts and dry-run engines."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from src.analysis.clustering import cluster_keywords
from src.analysis.competitors import profile_competitors
from src.analysis.contracts import (
    AnalysisError,
    AnalysisRunSummary,
    AnalysisStatus,
    CompetitorProfileInput,
    GigQualityInput,
    GigQualityResult,
    KeywordClusterInput,
)
from src.analysis.gig_quality import score_gig_quality
from src.analysis.keyword_features import normalize_keyword, vectorize_keywords
from src.analysis.orchestrator import run_analysis_dry_run


def test_contracts_serialize_deterministically() -> None:
    result = GigQualityResult(
        source_id="src-1",
        gig_id="gig-123",
        overall_score=78.0,
        component_scores={"title_quality": 80.0, "description_quality": 76.0},
        strengths=["title_quality"],
        weaknesses=[],
        confidence=0.8,
        explanation="deterministic test fixture",
    )

    first_json = result.model_dump_json()
    second_json = result.model_dump_json()
    assert first_json == second_json


def test_contracts_reject_invalid_confidence_or_score_ranges() -> None:
    with pytest.raises(ValidationError):
        GigQualityResult(
            source_id="src-1",
            gig_id="gig-123",
            overall_score=120.0,
            component_scores={"title_quality": 90.0},
            strengths=[],
            weaknesses=[],
            confidence=0.7,
            explanation="bad score range",
        )

    with pytest.raises(ValidationError):
        KeywordClusterInput(source_id="src-1", keywords=["logo"], min_cluster_size=0)


def test_contracts_require_source_id() -> None:
    with pytest.raises(ValidationError):
        KeywordClusterInput(keywords=["logo design"])  # type: ignore[call-arg]


def test_failure_output_contains_sanitized_error_message() -> None:
    err = AnalysisError.from_exception(
        RuntimeError("failed with api_key=sk-test1234567890abcdef"),
        code="analysis_failure",
    )
    assert err.code == "analysis_failure"
    assert "sk-test1234567890abcdef" not in err.message


def test_keyword_normalization_handles_case_and_whitespace() -> None:
    assert normalize_keyword("  Logo   DESIGN  Service ") == "logo design service"


def test_keyword_vectorization_is_deterministic() -> None:
    keywords = ["Logo Design", "modern logo design", "seo audit"]
    vectors_a, vocab_a, warnings_a = vectorize_keywords(keywords, source_id="kw-1")
    vectors_b, vocab_b, warnings_b = vectorize_keywords(keywords, source_id="kw-1")

    assert vectors_a == vectors_b
    assert vocab_a == vocab_b
    assert warnings_a == warnings_b


def test_empty_keyword_returns_controlled_warning() -> None:
    vectors, vocabulary, warnings = vectorize_keywords(["   "], source_id="kw-1")
    assert vectors == []
    assert vocabulary == []
    assert warnings


def test_related_keywords_cluster_together_deterministically() -> None:
    payload = KeywordClusterInput(
        source_id="kw-1",
        keywords=[
            "logo design",
            "modern logo design",
            "logo designer",
            "seo audit",
            "technical seo audit",
        ],
    )
    result = cluster_keywords(payload)

    cluster_keyword_sets = [set(cluster.keywords) for cluster in result.clusters]
    assert any(
        {"logo design", "modern logo design"}.issubset(cluster)
        for cluster in cluster_keyword_sets
    )
    assert any(cluster.label == "logo design" for cluster in result.clusters)


def test_too_few_keywords_returns_low_confidence_or_warning() -> None:
    payload = KeywordClusterInput(source_id="kw-2", keywords=["single keyword"])
    result = cluster_keywords(payload)

    assert result.confidence <= 0.4
    assert result.warnings


def test_cluster_labels_are_stable() -> None:
    payload = KeywordClusterInput(
        source_id="kw-3",
        keywords=["seo audit", "technical seo audit", "seo keyword research"],
    )
    first_labels = [cluster.label for cluster in cluster_keywords(payload).clusters]
    second_labels = [cluster.label for cluster in cluster_keywords(payload).clusters]
    assert first_labels == second_labels


def test_complete_gig_scores_higher_than_sparse_gig() -> None:
    high = score_gig_quality(
        GigQualityInput(
            source_id="gig-src",
            gig_id="high",
            title="I will design a modern minimalist logo for your brand",
            description="Detailed premium logo design service with concepts, revisions, and source files."
            * 3,
            package_count=3,
            rating=4.9,
            review_count=450,
            image_count=6,
            has_faq=True,
        )
    )
    low = score_gig_quality(
        GigQualityInput(
            source_id="gig-src",
            gig_id="low",
            title="logo",
            description="quick logo",
            package_count=0,
            rating=4.0,
            review_count=2,
            image_count=0,
            has_faq=False,
        )
    )
    assert high.overall_score > low.overall_score


def test_gig_quality_missing_fields_produce_warnings_not_crash() -> None:
    result = score_gig_quality(GigQualityInput(source_id="gig-src", gig_id="missing"))
    assert result.warnings
    assert result.missing_data_fields


def test_gig_quality_score_stays_in_bounds() -> None:
    result = score_gig_quality(
        GigQualityInput(
            source_id="gig-src",
            gig_id="bounds",
            title="I will build your automation workflow",
            description="Automation specialist" * 30,
            package_count=3,
            rating=5.0,
            review_count=9999,
            image_count=10,
            has_faq=True,
        )
    )
    assert 0.0 <= result.overall_score <= 100.0


def test_strong_incumbents_trigger_high_competition_warning() -> None:
    result = profile_competitors(
        CompetitorProfileInput(
            source_id="comp-strong",
            competitors=[
                {
                    "seller_id": "s1",
                    "seller_level": "top_rated",
                    "starting_price": 180.0,
                    "rating": 4.9,
                    "review_count": 800,
                },
                {
                    "seller_id": "s2",
                    "seller_level": "level_two",
                    "starting_price": 150.0,
                    "rating": 4.8,
                    "review_count": 500,
                },
                {
                    "seller_id": "s3",
                    "seller_level": "top_rated",
                    "starting_price": 220.0,
                    "rating": 4.9,
                    "review_count": 900,
                },
            ],
        )
    )
    assert any(warning.code == "high_competition" for warning in result.warnings)


def test_weak_competitor_fixture_surfaces_opportunity_signals() -> None:
    result = profile_competitors(
        CompetitorProfileInput(
            source_id="comp-weak",
            competitors=[
                {
                    "seller_id": "w1",
                    "seller_level": "new",
                    "starting_price": 30.0,
                    "rating": 4.2,
                    "review_count": 3,
                },
                {
                    "seller_id": "w2",
                    "seller_level": "new",
                    "starting_price": 45.0,
                    "rating": 4.1,
                    "review_count": 8,
                },
                {
                    "seller_id": "w3",
                    "seller_level": "level_one",
                    "starting_price": 40.0,
                    "rating": 4.3,
                    "review_count": 12,
                },
            ],
        )
    )
    assert result.opportunity_signals
    assert result.competition_intensity_score < 60


def test_empty_competitor_list_returns_low_confidence() -> None:
    result = profile_competitors(CompetitorProfileInput(source_id="comp-empty", competitors=[]))
    assert result.confidence <= 0.2
    assert result.warnings


def test_orchestrator_complete_fixture_succeeds_all_stages() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-complete",
            "source_id": "src-complete",
            "keywords": ["logo design", "modern logo design", "seo audit"],
            "gig": {
                "gig_id": "g-1",
                "title": "I will design a polished logo for your business",
                "description": "Rich and complete description" * 20,
                "package_count": 3,
                "rating": 4.9,
                "review_count": 320,
                "image_count": 5,
                "has_faq": True,
            },
            "competitors": [
                {
                    "seller_id": "a",
                    "seller_level": "top_rated",
                    "starting_price": 140.0,
                    "rating": 4.8,
                    "review_count": 260,
                },
                {
                    "seller_id": "b",
                    "seller_level": "level_one",
                    "starting_price": 55.0,
                    "rating": 4.6,
                    "review_count": 80,
                },
            ],
        }
    )
    assert isinstance(summary, AnalysisRunSummary)
    assert all(stage.status == AnalysisStatus.SUCCESS for stage in summary.stages)


def test_orchestrator_sparse_fixture_returns_warnings() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-sparse",
            "source_id": "src-sparse",
            "keywords": ["single"],
            "gig": {"gig_id": "g-sparse"},
            "competitors": [],
        }
    )
    assert summary.warnings
    assert any(stage.warnings for stage in summary.stages if stage.status == AnalysisStatus.SUCCESS)


def test_orchestrator_invalid_payload_returns_failed_stage_summary() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-invalid",
            "source_id": "src-invalid",
            "keywords": "not-a-list",
            "gig": {"gig_id": "g-invalid", "rating": "bad"},
            "competitors": "invalid",
        }
    )
    assert any(stage.status == AnalysisStatus.FAILED for stage in summary.stages)
