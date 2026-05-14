"""Unit tests for local analysis contracts, models, and stage wiring."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.analysis.clustering import cluster_keywords
from src.analysis.competitors import profile_competitors
from src.analysis.contracts import (
    AnalysisRunSummary,
    AnalysisStatus,
    CompetitorProfileInput,
    GigQualityInput,
    IntentInput,
    IntentLabel,
    KeywordClusterInput,
    ReviewAnalysisInput,
    SaturationInput,
    SaturationLevel,
    SellerStrengthInput,
)
from src.analysis.gig_quality import score_gig_quality
from src.analysis.intent import classify_intent
from src.analysis.orchestrator import run_analysis_dry_run
from src.analysis.reviews import analyze_reviews
from src.analysis.saturation import analyze_saturation
from src.analysis.seller_strength import score_seller_strength


def _load_analysis_fixture(name: str) -> dict[str, object]:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "analysis" / name
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def test_complete_fixture_schema_validation() -> None:
    payload = _load_analysis_fixture("complete_payload.json")
    assert isinstance(payload["run_id"], str)
    assert isinstance(payload["source_id"], str)
    assert isinstance(payload["keywords"], list)
    assert isinstance(payload["gig"], dict)
    assert isinstance(payload["competitors"], list)
    assert isinstance(payload["reviews"], list)
    assert isinstance(payload["intent"], dict)


def test_contracts_reject_invalid_ranges() -> None:
    with pytest.raises(ValidationError):
        SellerStrengthInput(
            source_id="src",
            seller_id="seller",
            rating=7.2,
        )

    with pytest.raises(ValidationError):
        SaturationInput(source_id="src", seller_strength_scores=[-2.0])


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
    labels_a = [cluster.label for cluster in result.clusters]
    labels_b = [cluster.label for cluster in cluster_keywords(payload).clusters]
    assert labels_a == labels_b


def test_gig_quality_score_stays_in_bounds() -> None:
    result = score_gig_quality(
        GigQualityInput(
            source_id="gig-src",
            gig_id="bounds",
            title="I will build your automation workflow",
            description="Automation specialist " * 30,
            package_count=3,
            rating=5.0,
            review_count=9999,
            image_count=10,
            has_faq=True,
        )
    )
    assert 0.0 <= result.overall_score <= 100.0


def test_seller_strength_strong_seller_scores_higher_than_weak() -> None:
    strong = score_seller_strength(
        SellerStrengthInput(
            source_id="seller-src",
            seller_id="strong",
            level="top rated",
            rating=4.9,
            review_count=700,
            response_time="1 hour",
            delivery_consistency=0.95,
            active_gig_count=6,
            languages=["English", "Spanish"],
            account_tenure_months=60,
        )
    )
    weak = score_seller_strength(
        SellerStrengthInput(
            source_id="seller-src",
            seller_id="weak",
            level="new",
            rating=4.1,
            review_count=6,
            response_time="2 days",
            delivery_consistency=0.62,
            active_gig_count=1,
            languages=["English"],
            account_tenure_months=3,
        )
    )
    assert strong.score > weak.score


def test_seller_strength_missing_fields_reduce_confidence_without_crash() -> None:
    sparse = score_seller_strength(
        SellerStrengthInput(source_id="seller-src", seller_id="sparse", level="level one")
    )
    assert sparse.confidence < 0.6
    assert sparse.warnings
    assert sparse.missing_data_fields


def test_seller_strength_serialization_deterministic_and_bounds_safe() -> None:
    payload = SellerStrengthInput(
        source_id="seller-src",
        seller_id="serialize",
        level="level two",
        rating=4.7,
        review_count=220,
        response_time="3 hours",
        delivery_consistency=0.88,
        active_gig_count=7,
        languages=["English", "German"],
        account_tenure_months=30,
    )
    result = score_seller_strength(payload)
    assert 0.0 <= result.score <= 100.0
    assert result.model_dump_json() == score_seller_strength(payload).model_dump_json()


def test_seller_strength_unknown_level_and_slow_response_reduce_components() -> None:
    result = score_seller_strength(
        SellerStrengthInput(
            source_id="seller-src",
            seller_id="unknown-level",
            level="legendary",
            rating=4.4,
            review_count=50,
            response_time="5 days",
            delivery_consistency=0.7,
            active_gig_count=20,
            languages=["English"],
            account_tenure_months=12,
        )
    )
    assert result.components["level"] == 30.0
    assert result.components["response_time"] == 20.0
    assert result.components["active_gig_count"] == 50.0


def test_saturation_high_competitor_density_yields_high_score() -> None:
    result = analyze_saturation(
        SaturationInput(
            source_id="sat-src",
            keyword_count=26,
            search_result_count=2500,
            competitor_count=48,
            seller_strength_scores=[88.0, 84.0, 83.0, 79.0, 74.0],
            prices=[95.0, 96.0, 97.0, 94.0, 95.0, 96.0],
            gig_quality_scores=[80.0, 82.0, 81.0, 79.0],
        )
    )
    assert result.saturation_level == SaturationLevel.HIGH
    assert result.score >= 70.0


def test_saturation_sparse_data_returns_unknown_with_low_confidence() -> None:
    result = analyze_saturation(SaturationInput(source_id="sat-src"))
    assert result.saturation_level == SaturationLevel.UNKNOWN
    assert result.confidence <= 0.2
    assert result.warnings


def test_saturation_price_crowding_increases_score() -> None:
    compressed = analyze_saturation(
        SaturationInput(
            source_id="sat-src",
            keyword_count=12,
            search_result_count=900,
            competitor_count=20,
            seller_strength_scores=[70.0, 72.0, 68.0, 74.0],
            prices=[50.0, 50.0, 50.0, 50.0, 49.0],
            gig_quality_scores=[70.0, 71.0, 70.0, 69.0],
        )
    )
    diverse = analyze_saturation(
        SaturationInput(
            source_id="sat-src",
            keyword_count=12,
            search_result_count=900,
            competitor_count=20,
            seller_strength_scores=[70.0, 72.0, 68.0, 74.0],
            prices=[30.0, 55.0, 75.0, 110.0, 180.0],
            gig_quality_scores=[70.0, 71.0, 70.0, 69.0],
        )
    )
    assert compressed.components["price_crowding"] > diverse.components["price_crowding"]
    assert compressed.score > diverse.score


def test_saturation_ties_are_deterministic() -> None:
    payload = SaturationInput(
        source_id="sat-src",
        keyword_count=10,
        search_result_count=1000,
        competitor_count=22,
        seller_strength_scores=[60.0, 60.0, 60.0],
        prices=[100.0, 100.0, 100.0],
        gig_quality_scores=[75.0, 75.0, 75.0],
    )
    assert analyze_saturation(payload).model_dump_json() == analyze_saturation(payload).model_dump_json()


def test_saturation_zero_average_prices_use_fallback_crowding_score() -> None:
    result = analyze_saturation(
        SaturationInput(
            source_id="sat-src",
            keyword_count=8,
            search_result_count=300,
            competitor_count=10,
            seller_strength_scores=[55.0, 61.0, 58.0],
            prices=[0.0, 0.0, 0.0],
            gig_quality_scores=[62.0, 61.0, 63.0],
        )
    )
    assert result.components["price_crowding"] == 45.0
    assert result.score >= 0.0


def test_review_analysis_repeated_complaints_surface_as_weaknesses() -> None:
    result = analyze_reviews(
        ReviewAnalysisInput(
            source_id="rev-src",
            reviews=[
                {"text": "Delivery was late and communication was poor.", "rating": 2.0},
                {"text": "Late delivery again and hard to reach seller.", "rating": 1.0},
                {"text": "Missed deadline and quality was poor.", "rating": 2.0},
            ],
        )
    )
    assert "late_delivery" in result.complaint_frequency
    assert result.sentiment_hints["negative"] >= 2
    assert result.opportunity_gaps


def test_review_analysis_positive_reviews_surface_strength_signals() -> None:
    result = analyze_reviews(
        ReviewAnalysisInput(
            source_id="rev-src",
            reviews=[
                {"text": "Great communication and excellent quality.", "rating": 5.0},
                {"text": "Fast delivery and worth every penny.", "rating": 5.0},
            ],
        )
    )
    assert "high_quality" in result.praise_frequency
    assert result.sentiment_hints["positive"] == 2


def test_review_analysis_empty_reviews_returns_low_confidence_warning() -> None:
    result = analyze_reviews(ReviewAnalysisInput(source_id="rev-src", reviews=[]))
    assert result.confidence <= 0.2
    assert any(warning.code == "reviews_missing" for warning in result.warnings)


def test_review_analysis_redacts_secret_like_strings() -> None:
    secret = "api_key=sk-test1234567890abcdef"
    result = analyze_reviews(
        ReviewAnalysisInput(
            source_id="rev-src",
            reviews=[{"text": f"Work was okay. {secret}", "rating": 3.0}],
        )
    )
    assert any(warning.code == "review_text_redacted" for warning in result.warnings)
    assert secret not in result.model_dump_json()


def test_review_analysis_without_ratings_uses_text_sentiment_fallback() -> None:
    result = analyze_reviews(
        ReviewAnalysisInput(
            source_id="rev-src",
            reviews=[
                {"text": "No response and late delivery."},
                {"text": "Great communication and clean code."},
            ],
        )
    )
    assert any(warning.code == "review_rating_missing" for warning in result.warnings)
    assert result.sentiment_hints["negative"] >= 1
    assert result.sentiment_hints["positive"] >= 1
    assert "review.rating" in result.missing_data_fields


def test_intent_buyer_ready_examples_classify_correctly() -> None:
    result = classify_intent(
        IntentInput(
            source_id="intent-src",
            keyword_text="need to hire python automation expert today",
            title_phrases=["urgent freelancer", "hire now"],
        )
    )
    assert result.label == IntentLabel.BUYER_READY
    assert result.confidence >= 0.8


def test_intent_price_language_and_urgency_contribute_to_buyer_ready() -> None:
    result = classify_intent(
        IntentInput(
            source_id="intent-src",
            keyword_text="need automation expert under $200 asap",
            title_phrases=["budget is 200 usd", "hire now"],
        )
    )
    assert result.label == IntentLabel.BUYER_READY
    assert any(rule.startswith("price_language:") for rule in result.matched_rules)
    assert any(rule.startswith("urgency:") for rule in result.matched_rules)


def test_intent_ambiguous_queries_return_low_confidence() -> None:
    result = classify_intent(IntentInput(source_id="intent-src", keyword_text="python automation"))
    assert result.label == IntentLabel.AMBIGUOUS
    assert result.confidence <= 0.5


def test_intent_service_provider_language_not_misclassified_as_buyer_demand() -> None:
    result = classify_intent(
        IntentInput(
            source_id="intent-src",
            keyword_text="I will build python automation workflows",
            title_phrases=["my service portfolio"],
        )
    )
    assert result.label == IntentLabel.SERVICE_PROVIDER


def test_intent_serialization_is_deterministic() -> None:
    payload = IntentInput(source_id="intent-src", keyword_text="how to automate invoice parsing")
    assert classify_intent(payload).model_dump_json() == classify_intent(payload).model_dump_json()


def test_intent_low_intent_examples_classify_correctly() -> None:
    result = classify_intent(
        IntentInput(
            source_id="intent-src",
            keyword_text="free python automation template example",
            title_phrases=["cheap sample workflow"],
        )
    )
    assert result.label == IntentLabel.LOW_INTENT
    assert any(rule.startswith("low_intent:") for rule in result.matched_rules)


def test_orchestrator_complete_fixture_runs_all_stages_successfully() -> None:
    payload = _load_analysis_fixture("complete_payload.json")
    summary = run_analysis_dry_run(payload)
    assert isinstance(summary, AnalysisRunSummary)
    assert summary.status == AnalysisStatus.SUCCESS
    assert len(summary.stages) == 7
    assert all(stage.status == AnalysisStatus.SUCCESS for stage in summary.stages)


def test_orchestrator_sparse_fixture_reports_warnings_count() -> None:
    payload = _load_analysis_fixture("sparse_payload.json")
    summary = run_analysis_dry_run(payload)
    assert summary.metadata["executed_stage_count"] == 7
    assert len(summary.warnings) >= 3


def test_orchestrator_missing_reviews_does_not_fail_other_stages() -> None:
    payload = _load_analysis_fixture("complete_payload.json")
    payload.pop("reviews")
    summary = run_analysis_dry_run(payload)
    assert all(stage.status == AnalysisStatus.SUCCESS for stage in summary.stages)
    assert summary.status == AnalysisStatus.SUCCESS


def test_orchestrator_invalid_seller_input_fails_only_seller_stage() -> None:
    payload = _load_analysis_fixture("complete_payload.json")
    payload["seller"] = "not-a-dict"
    payload.pop("sellers")
    summary = run_analysis_dry_run(payload)
    failed_stages = [stage for stage in summary.stages if stage.status == AnalysisStatus.FAILED]
    assert len(failed_stages) == 1
    assert failed_stages[0].stage.value == "seller_strength"
    assert summary.status == AnalysisStatus.PARTIAL


def test_orchestrator_status_failed_when_all_stages_fail() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-failed",
            "source_id": "src-failed",
            "intent": {"keyword_text": ""},
        }
    )
    assert summary.status == AnalysisStatus.FAILED


def test_orchestrator_stage_order_is_deterministic_for_complete_fixture() -> None:
    payload = _load_analysis_fixture("complete_payload.json")
    summary = run_analysis_dry_run(payload)
    stage_order = [stage.stage.value for stage in summary.stages]
    assert stage_order == [
        "keyword_clustering",
        "gig_quality",
        "competitor_profile",
        "seller_strength",
        "saturation",
        "review_analysis",
        "intent_classification",
    ]


def test_orchestrator_sparse_payload_without_reviews_runs_remaining_stages() -> None:
    payload = _load_analysis_fixture("sparse_payload.json")
    payload.pop("reviews")
    summary = run_analysis_dry_run(payload)
    assert summary.status == AnalysisStatus.SUCCESS
    assert summary.metadata["executed_stage_count"] == 6
    assert all(stage.status == AnalysisStatus.SUCCESS for stage in summary.stages)
    assert all(stage.stage.value != "review_analysis" for stage in summary.stages)


def test_orchestrator_handles_empty_competitor_and_seller_lists() -> None:
    payload = _load_analysis_fixture("complete_payload.json")
    payload["competitors"] = []
    payload["sellers"] = []
    payload.pop("seller", None)
    summary = run_analysis_dry_run(payload)

    competitor_stage = next(stage for stage in summary.stages if stage.stage.value == "competitor_profile")
    seller_stage = next(stage for stage in summary.stages if stage.stage.value == "seller_strength")
    assert competitor_stage.status == AnalysisStatus.SUCCESS
    assert competitor_stage.metadata["competitor_count"] == 0
    assert seller_stage.status == AnalysisStatus.SUCCESS
    assert seller_stage.metadata["evaluated_sellers"] == 1
    assert summary.status == AnalysisStatus.SUCCESS
    assert any(warning.code == "seller_strength_missing_fields" for warning in summary.warnings)


def test_orchestrator_skips_invalid_additional_sellers_without_failing_stage() -> None:
    payload = _load_analysis_fixture("complete_payload.json")
    fixture_sellers = payload.get("sellers")
    assert isinstance(fixture_sellers, list)
    payload["sellers"] = [
        fixture_sellers[0],
        {
            "seller_id": "broken-row",
            "level": "level two",
            "rating": 7.8,
            "review_count": 20,
        },
    ]
    summary = run_analysis_dry_run(payload)
    seller_stage = next(stage for stage in summary.stages if stage.stage.value == "seller_strength")
    assert seller_stage.status == AnalysisStatus.SUCCESS
    assert seller_stage.metadata["evaluated_sellers"] == 1


def test_orchestrator_non_dict_intent_uses_keyword_fallback() -> None:
    payload = _load_analysis_fixture("complete_payload.json")
    payload["intent"] = "not-a-dict"
    payload["keyword_text"] = "hire automation expert now"
    summary = run_analysis_dry_run(payload)
    intent_stage = next(stage for stage in summary.stages if stage.stage.value == "intent_classification")
    assert intent_stage.status == AnalysisStatus.SUCCESS
    assert intent_stage.metadata["label"] in {"buyer_ready", "ambiguous"}


def test_orchestrator_saturation_stage_fails_on_invalid_numeric_input() -> None:
    payload = _load_analysis_fixture("complete_payload.json")
    payload["search_result_count"] = "a lot"
    summary = run_analysis_dry_run(payload)
    saturation_stage = next(stage for stage in summary.stages if stage.stage.value == "saturation")
    assert saturation_stage.status == AnalysisStatus.FAILED
    assert saturation_stage.error is not None
    assert summary.status == AnalysisStatus.PARTIAL


def test_fixture_golden_seller_score_ordering() -> None:
    payload = _load_analysis_fixture("complete_payload.json")
    sellers = payload["sellers"]
    assert isinstance(sellers, list)
    strong = score_seller_strength(SellerStrengthInput(source_id="src", **sellers[0]))
    weak = score_seller_strength(
        SellerStrengthInput(
            source_id="src",
            seller_id="weak-golden",
            level="new",
            rating=4.1,
            review_count=3,
            response_time="2 days",
            delivery_consistency=0.55,
            active_gig_count=1,
            languages=["English"],
            account_tenure_months=2,
        )
    )
    assert strong.score > weak.score


def test_legacy_competitor_profile_still_operates() -> None:
    result = profile_competitors(
        CompetitorProfileInput(
            source_id="comp-src",
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
                    "seller_level": "new",
                    "starting_price": 40.0,
                    "rating": 4.2,
                    "review_count": 5,
                },
            ],
        )
    )
    assert 0.0 <= result.competition_intensity_score <= 100.0
