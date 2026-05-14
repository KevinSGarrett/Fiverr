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
    IntentResult,
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


def test_orchestrator_status_success_when_intent_keyword_falls_back_to_source_id() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-failed",
            "source_id": "src-failed",
            "intent": {"keyword_text": ""},
        }
    )
    assert summary.status == AnalysisStatus.SUCCESS


def _capture_intent_input_from_orchestrator(
    monkeypatch: pytest.MonkeyPatch, payload: dict[str, object]
) -> IntentInput:
    captured: dict[str, IntentInput] = {}

    def _fake_classify_intent(intent_input: IntentInput) -> IntentResult:
        captured["intent_input"] = intent_input
        return IntentResult(
            source_id=intent_input.source_id,
            keyword_text=intent_input.keyword_text,
            label=IntentLabel.AMBIGUOUS,
            confidence=0.35,
            matched_rules=["test:captured"],
            explanation="Captured intent payload for orchestrator tests.",
            metadata=intent_input.metadata,
        )

    monkeypatch.setattr("src.analysis.orchestrator.classify_intent", _fake_classify_intent)
    summary = run_analysis_dry_run(payload)
    intent_stages = [stage for stage in summary.stages if stage.stage.value == "intent_classification"]
    assert len(intent_stages) == 1
    assert intent_stages[0].status == AnalysisStatus.SUCCESS
    return captured["intent_input"]


def test_orchestrator_intent_keyword_prefers_valid_intent_keyword_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intent_input = _capture_intent_input_from_orchestrator(
        monkeypatch,
        {
            "run_id": "run-intent-priority",
            "source_id": "src-intent-priority",
            "intent": {"keyword_text": "keep intent keyword"},
            "keyword_text": "payload keyword",
            "keywords": ["keyword list value"],
        },
    )
    assert intent_input.keyword_text == "keep intent keyword"


@pytest.mark.parametrize("nullish_keyword", [None, "", "   "])
def test_orchestrator_intent_keyword_uses_payload_keyword_when_intent_keyword_is_nullish(
    monkeypatch: pytest.MonkeyPatch, nullish_keyword: str | None
) -> None:
    intent_input = _capture_intent_input_from_orchestrator(
        monkeypatch,
        {
            "run_id": "run-intent-nullish",
            "source_id": "src-intent-nullish",
            "intent": {"keyword_text": nullish_keyword},
            "keyword_text": "payload fallback keyword",
        },
    )
    assert intent_input.keyword_text == "payload fallback keyword"
    assert intent_input.keyword_text != "None"


def test_orchestrator_intent_keyword_uses_payload_keyword_when_intent_keyword_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intent_input = _capture_intent_input_from_orchestrator(
        monkeypatch,
        {
            "run_id": "run-intent-missing",
            "source_id": "src-intent-missing",
            "intent": {"title_phrases": ["intent phrase"]},
            "keyword_text": "payload fallback keyword",
        },
    )
    assert intent_input.keyword_text == "payload fallback keyword"


def test_orchestrator_intent_keyword_falls_back_to_first_non_empty_keyword(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intent_input = _capture_intent_input_from_orchestrator(
        monkeypatch,
        {
            "run_id": "run-intent-keywords",
            "source_id": "src-intent-keywords",
            "intent": {"keyword_text": None},
            "keywords": [None, "   ", "first non-empty keyword", "second keyword"],
        },
    )
    assert intent_input.keyword_text == "first non-empty keyword"


def test_orchestrator_intent_keyword_falls_back_to_source_id_when_other_values_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intent_input = _capture_intent_input_from_orchestrator(
        monkeypatch,
        {
            "run_id": "run-intent-source",
            "source_id": "src-intent-source",
            "intent": {"keyword_text": None},
            "keywords": [None, "   "],
        },
    )
    assert intent_input.keyword_text == "src-intent-source"


def test_orchestrator_intent_keyword_none_literal_is_not_generated_from_null(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intent_input = _capture_intent_input_from_orchestrator(
        monkeypatch,
        {
            "run_id": "run-intent-no-none-literal",
            "source_id": "src-intent-no-none-literal",
            "intent": {"keyword_text": None},
            "keywords": [],
        },
    )
    assert intent_input.keyword_text == "src-intent-no-none-literal"
    assert intent_input.keyword_text != "None"


def test_orchestrator_intent_keyword_literal_none_is_treated_as_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intent_input = _capture_intent_input_from_orchestrator(
        monkeypatch,
        {
            "run_id": "run-intent-literal-none",
            "source_id": "src-intent-literal-none",
            "intent": {"keyword_text": "None"},
        },
    )
    assert intent_input.keyword_text == "src-intent-literal-none"


def test_orchestrator_intent_keyword_literal_null_is_treated_as_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intent_input = _capture_intent_input_from_orchestrator(
        monkeypatch,
        {
            "run_id": "run-intent-literal-null",
            "source_id": "src-intent-literal-null",
            "intent": {"keyword_text": "null"},
        },
    )
    assert intent_input.keyword_text == "src-intent-literal-null"


def test_orchestrator_intent_title_phrases_survive_keyword_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intent_input = _capture_intent_input_from_orchestrator(
        monkeypatch,
        {
            "run_id": "run-intent-title-phrases",
            "source_id": "src-intent-title-phrases",
            "intent": {
                "keyword_text": None,
                "title_phrases": ["urgent order", "budget is 200 usd"],
            },
            "keyword_text": "payload fallback keyword",
        },
    )
    assert intent_input.keyword_text == "payload fallback keyword"
    assert intent_input.title_phrases == ["urgent order", "budget is 200 usd"]


def test_orchestrator_intent_non_dict_section_uses_top_level_title_phrases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intent_input = _capture_intent_input_from_orchestrator(
        monkeypatch,
        {
            "run_id": "run-intent-non-dict",
            "source_id": "src-intent-non-dict",
            "intent": "invalid-intent-section",
            "keyword_text": "payload keyword",
            "title_phrases": ["top-level title phrase"],
        },
    )
    assert intent_input.keyword_text == "payload keyword"
    assert intent_input.title_phrases == ["top-level title phrase"]


def test_orchestrator_intent_keyword_supports_non_string_keyword_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    intent_input = _capture_intent_input_from_orchestrator(
        monkeypatch,
        {
            "run_id": "run-intent-non-string-keyword",
            "source_id": "src-intent-non-string-keyword",
            "intent": {"keyword_text": None},
            "keywords": [12345],
        },
    )
    assert intent_input.keyword_text == "12345"


def test_orchestrator_intent_stage_validation_error_marks_stage_failed() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-intent-validation-error",
            "source_id": "src-intent-validation-error",
            "intent": {
                "keyword_text": "valid keyword",
                "title_phrases": "not-a-list",
            },
        }
    )
    assert summary.status == AnalysisStatus.FAILED
    intent_stage = next(stage for stage in summary.stages if stage.stage.value == "intent_classification")
    assert intent_stage.status == AnalysisStatus.FAILED


def test_orchestrator_status_failed_when_no_stages_execute() -> None:
    summary = run_analysis_dry_run({"run_id": "run-no-stages", "source_id": "src-no-stages"})
    assert summary.status == AnalysisStatus.FAILED
    assert summary.stages == []


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
