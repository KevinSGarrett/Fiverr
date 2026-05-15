"""Unit tests for local analysis contracts, models, and stage wiring."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast

import pytest
from pydantic import ValidationError
from src.analysis.clustering import cluster_keywords
from src.analysis.competitors import profile_competitors
from src.analysis.contracts import (
    AnalysisReadinessStatus,
    AnalysisRunSummary,
    AnalysisStageSummary,
    AnalysisStatus,
    AnalysisTaskType,
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
from src.analysis.orchestrator import run_analysis_dry_run, summarize_scoring_readiness
from src.analysis.reviews import analyze_reviews
from src.analysis.saturation import analyze_saturation
from src.analysis.seller_strength import score_seller_strength
from tests.fixtures.analysis.factories import (
    make_complete_market_payload,
    make_empty_upstream_payload,
    make_missing_reviews_payload,
    make_missing_seller_payload,
    make_sparse_gig_only_payload,
)

EXPECTED_STAGE_ORDER = [
    AnalysisTaskType.KEYWORD_CLUSTERING.value,
    AnalysisTaskType.GIG_QUALITY.value,
    AnalysisTaskType.COMPETITOR_PROFILE.value,
    AnalysisTaskType.SELLER_STRENGTH.value,
    AnalysisTaskType.SATURATION.value,
    AnalysisTaskType.REVIEW_ANALYSIS.value,
    AnalysisTaskType.INTENT_CLASSIFICATION.value,
]


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


def _capture_intent_context_from_orchestrator(
    monkeypatch: pytest.MonkeyPatch, payload: dict[str, object]
) -> tuple[IntentInput, AnalysisStageSummary]:
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
    intent_stage = next(stage for stage in summary.stages if stage.stage == AnalysisTaskType.INTENT_CLASSIFICATION)
    assert intent_stage.status == AnalysisStatus.SUCCESS
    return captured["intent_input"], intent_stage


def test_orchestrator_stage_order_metadata_is_deterministic() -> None:
    payload = _load_analysis_fixture("complete_payload.json")
    summary = run_analysis_dry_run(payload)
    assert summary.metadata["stage_order"] == EXPECTED_STAGE_ORDER
    assert [stage.stage.value for stage in summary.stages] == EXPECTED_STAGE_ORDER
    assert summary.metadata["skipped_stages"] == []


def test_orchestrator_records_skipped_stages_when_inputs_are_absent() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-skipped-stage-metadata",
            "source_id": "src-skipped-stage-metadata",
            "intent": {"keyword_text": "need python automation help"},
        }
    )
    assert summary.status == AnalysisStatus.SUCCESS
    assert summary.metadata["successful_stages"] == [AnalysisTaskType.INTENT_CLASSIFICATION.value]
    assert summary.metadata["failed_stages"] == []
    assert summary.metadata["skipped_stages"] == [
        AnalysisTaskType.KEYWORD_CLUSTERING.value,
        AnalysisTaskType.GIG_QUALITY.value,
        AnalysisTaskType.COMPETITOR_PROFILE.value,
        AnalysisTaskType.SELLER_STRENGTH.value,
        AnalysisTaskType.SATURATION.value,
        AnalysisTaskType.REVIEW_ANALYSIS.value,
    ]


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


@pytest.mark.parametrize("nullish_keyword", [None, "", "   ", "None", "null"])
def test_orchestrator_intent_keyword_fallback_order_prefers_payload_before_keywords(
    monkeypatch: pytest.MonkeyPatch, nullish_keyword: str | None
) -> None:
    intent_input = _capture_intent_input_from_orchestrator(
        monkeypatch,
        {
            "run_id": "run-intent-order-payload-first",
            "source_id": "src-intent-order-payload-first",
            "intent": {"keyword_text": nullish_keyword},
            "keyword_text": "payload fallback keyword",
            "keywords": ["keyword list fallback"],
        },
    )
    assert intent_input.keyword_text == "payload fallback keyword"


@pytest.mark.parametrize("nullish_keyword", [None, "", "   ", "None", "null"])
def test_orchestrator_intent_keyword_fallback_order_uses_keywords_before_source_id(
    monkeypatch: pytest.MonkeyPatch, nullish_keyword: str | None
) -> None:
    intent_input = _capture_intent_input_from_orchestrator(
        monkeypatch,
        {
            "run_id": "run-intent-order-keywords-second",
            "source_id": "src-intent-order-keywords-second",
            "intent": {"keyword_text": nullish_keyword},
            "keywords": [None, "   ", "keyword list fallback"],
        },
    )
    assert intent_input.keyword_text == "keyword list fallback"


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


@pytest.mark.parametrize(
    ("payload", "expected_keyword", "expected_reason", "expected_confidence"),
    [
        (
            {
                "run_id": "run-intent-selection-explicit",
                "source_id": "src-intent-selection-explicit",
                "intent": {"keyword_text": "explicit keyword"},
                "keyword_text": "payload keyword",
                "keywords": ["keywords entry"],
            },
            "explicit keyword",
            "explicit_intent_keyword",
            1.0,
        ),
        (
            {
                "run_id": "run-intent-selection-top-level",
                "source_id": "src-intent-selection-top-level",
                "intent": {"keyword_text": "None"},
                "keyword_text": "payload keyword",
                "keywords": ["keywords entry"],
            },
            "payload keyword",
            "top_level_keyword_text",
            0.9,
        ),
        (
            {
                "run_id": "run-intent-selection-keywords",
                "source_id": "src-intent-selection-keywords",
                "intent": {"keyword_text": "   "},
                "keyword_text": "null",
                "keywords": ["   ", "keywords entry", None],
            },
            "keywords entry",
            "keywords_first_entry",
            0.8,
        ),
        (
            {
                "run_id": "run-intent-selection-source-id",
                "source_id": "src-intent-selection-source-id",
                "intent": {"keyword_text": None},
                "keyword_text": "None",
                "keywords": ["   ", "null"],
            },
            "src-intent-selection-source-id",
            "source_id_fallback",
            0.6,
        ),
    ],
)
def test_orchestrator_intent_selection_reason_and_confidence_are_recorded(
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, object],
    expected_keyword: str,
    expected_reason: str,
    expected_confidence: float,
) -> None:
    intent_input, intent_stage = _capture_intent_context_from_orchestrator(monkeypatch, payload)
    assert intent_input.keyword_text == expected_keyword
    assert intent_input.metadata["intent_keyword_selection_reason"] == expected_reason
    assert intent_input.metadata["intent_keyword_selection_confidence"] == expected_confidence
    assert intent_stage.metadata["intent_keyword_selection_reason"] == expected_reason
    assert intent_stage.metadata["intent_keyword_selection_confidence"] == expected_confidence
    assert intent_input.keyword_text not in {"None", "null"}


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


def test_orchestrator_invalid_seller_stage_preserves_failure_metadata_and_runs_others() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-seller-failure-metadata",
            "source_id": "src-seller-failure-metadata",
            "seller": "not-a-dict",
            "intent": {"keyword_text": "need python automation help"},
        }
    )
    assert summary.status == AnalysisStatus.PARTIAL
    seller_stage = next(stage for stage in summary.stages if stage.stage == AnalysisTaskType.SELLER_STRENGTH)
    intent_stage = next(stage for stage in summary.stages if stage.stage == AnalysisTaskType.INTENT_CLASSIFICATION)
    assert seller_stage.status == AnalysisStatus.FAILED
    assert seller_stage.metadata["source_id"] == "src-seller-failure-metadata"
    assert seller_stage.metadata["result_count"] == 0
    assert seller_stage.metadata["warning_count"] == 0
    assert seller_stage.metadata["missing_field_count"] == 0
    assert seller_stage.metadata["error_code"] == "seller_strength_stage_failed"
    assert seller_stage.metadata["failed"] is True
    assert intent_stage.status == AnalysisStatus.SUCCESS
    assert summary.metadata["failed_stages"] == [AnalysisTaskType.SELLER_STRENGTH.value]
    assert AnalysisTaskType.INTENT_CLASSIFICATION.value in summary.metadata["successful_stages"]
    assert AnalysisTaskType.SELLER_STRENGTH.value not in summary.metadata["successful_stages"]
    assert AnalysisTaskType.SELLER_STRENGTH.value in summary.metadata["stage_order"]


def test_orchestrator_invalid_payload_type_is_fundamentally_invalid() -> None:
    summary = run_analysis_dry_run(cast(dict[str, object], "not-a-payload"))
    assert summary.status == AnalysisStatus.FAILED
    assert summary.stages == []
    assert summary.metadata["invalid_input"] is True
    assert summary.metadata["invalid_input_type"] == "str"


def test_orchestrator_stage_metadata_contains_required_summary_keys() -> None:
    payload = _load_analysis_fixture("complete_payload.json")
    summary = run_analysis_dry_run(payload)
    assert summary.stages
    for stage in summary.stages:
        assert "source_id" in stage.metadata
        assert "result_count" in stage.metadata
        assert "warning_count" in stage.metadata
        assert "missing_field_count" in stage.metadata
        assert stage.metadata["source_id"] == summary.source_id


def test_orchestrator_scoring_readiness_is_complete_for_full_fixture() -> None:
    payload = _load_analysis_fixture("complete_payload.json")
    summary = run_analysis_dry_run(payload)
    readiness = summary.metadata["scoring_readiness"]
    assert readiness["demand_inputs"] is True
    assert readiness["competition_inputs"] is True
    assert readiness["saturation_inputs"] is True
    assert readiness["review_signals"] is True
    assert readiness["intent_signals"] is True
    assert readiness["seller_strength"] is True
    assert readiness["gig_quality"] is True
    assert readiness["available_count"] == 7
    assert readiness["total_expected"] == 7


def test_orchestrator_collection_evidence_metadata_is_captured() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-collection-evidence",
            "source_id": "src-collection-evidence",
            "intent": {"keyword_text": "need python automation support"},
            "collection_evidence": {
                "source_stage_names": ["keyword_collection", "seller_collection"],
                "fixture_mode": True,
                "records_seen": 42,
                "records_written": 38,
                "warnings": ["missing optional competitor row"],
            },
        }
    )
    evidence = summary.metadata["collection_evidence"]
    assert evidence["source_stage_names"] == ["keyword_collection", "seller_collection"]
    assert evidence["fixture_mode"] is True
    assert evidence["records_seen"] == 42
    assert evidence["records_written"] == 38
    assert evidence["warnings"] == ["missing optional competitor row"]
    assert evidence["warning_count"] == 1


def test_orchestrator_collection_evidence_malformed_payload_degrades_with_warning() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-collection-evidence-malformed",
            "source_id": "src-collection-evidence-malformed",
            "intent": {"keyword_text": "need python automation support"},
            "collection_evidence": {
                "source_stage_names": "not-a-list",
                "fixture_mode": {"invalid": "type"},
                "records_seen": -1,
                "records_written": "3",
                "warnings": {"invalid": "type"},
            },
        }
    )
    assert any(warning.code == "collection_evidence_invalid" for warning in summary.warnings)
    evidence = summary.metadata["collection_evidence"]
    assert evidence["source_stage_names"] == []
    assert evidence["records_seen"] == 0
    assert evidence["records_written"] == 0
    assert evidence["warnings"] == []


def test_orchestrator_collection_evidence_uses_duck_typing_without_collection_imports() -> None:
    loaded_before = set(sys.modules.keys())
    _ = run_analysis_dry_run(
        {
            "run_id": "run-collection-evidence-duck-typing",
            "source_id": "src-collection-evidence-duck-typing",
            "intent": {"keyword_text": "need python automation support"},
            "collection_evidence": {"source_stage_names": ["keyword_collection"]},
        }
    )
    loaded_during_run = set(sys.modules.keys()) - loaded_before
    assert not any(module_name.startswith("src.collection") for module_name in loaded_during_run)


def test_scoring_readiness_false_when_intent_stage_fails() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-readiness-intent-failed",
            "source_id": "src-readiness-intent-failed",
            "intent": {"keyword_text": "valid keyword", "title_phrases": "invalid-type"},
        }
    )
    readiness = summary.metadata["scoring_readiness"]
    assert readiness["intent_signals"] is False
    assert readiness["demand_inputs"] is False


def test_scoring_readiness_false_when_keyword_stage_fails_without_intent_success() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-readiness-keyword-failed",
            "source_id": "src-readiness-keyword-failed",
            "keywords": "invalid-keyword-list",
            "intent": {"keyword_text": None, "title_phrases": "invalid-type"},
        }
    )
    readiness = summary.metadata["scoring_readiness"]
    assert readiness["demand_inputs"] is False
    assert readiness["intent_signals"] is False


def test_scoring_readiness_blocks_demand_when_keyword_stage_fails_even_if_intent_succeeds() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-readiness-intent-success-keyword-failed",
            "source_id": "src-readiness-intent-success-keyword-failed",
            "keywords": "invalid-keyword-list",
            "intent": {"keyword_text": "need python automation support"},
        }
    )
    readiness = summary.metadata["scoring_readiness"]
    assert readiness["intent_signals"] is True
    assert readiness["demand_inputs"] is False


def test_scoring_readiness_sparse_payload_remains_false() -> None:
    summary = run_analysis_dry_run({"run_id": "run-readiness-sparse", "source_id": "src-readiness-sparse"})
    readiness = summary.metadata["scoring_readiness"]
    assert readiness["available_count"] == 0
    assert readiness["demand_inputs"] is False
    assert readiness["competition_inputs"] is False
    assert readiness["saturation_inputs"] is False
    assert readiness["review_signals"] is False
    assert readiness["intent_signals"] is False
    assert readiness["seller_strength"] is False
    assert readiness["gig_quality"] is False


def test_scoring_readiness_helper_handles_sparse_and_complete_stage_sets() -> None:
    sparse_readiness = summarize_scoring_readiness([], {})
    assert sparse_readiness["available_count"] == 0
    assert sparse_readiness["demand_inputs"] is False

    keyword_only_payload_readiness = summarize_scoring_readiness([], {"keywords": ["python automation"]})
    assert keyword_only_payload_readiness["demand_inputs"] is False

    complete_readiness = summarize_scoring_readiness(
        [
            AnalysisStageSummary(stage=task_type, status=AnalysisStatus.SUCCESS, result_type=task_type.value)
            for task_type in (
                AnalysisTaskType.KEYWORD_CLUSTERING,
                AnalysisTaskType.GIG_QUALITY,
                AnalysisTaskType.COMPETITOR_PROFILE,
                AnalysisTaskType.SELLER_STRENGTH,
                AnalysisTaskType.SATURATION,
                AnalysisTaskType.REVIEW_ANALYSIS,
                AnalysisTaskType.INTENT_CLASSIFICATION,
            )
        ],
        {"keywords": ["python automation"]},
    )
    assert complete_readiness["available_count"] == 7
    assert all(
        complete_readiness[key]
        for key in (
            "demand_inputs",
            "competition_inputs",
            "saturation_inputs",
            "review_signals",
            "intent_signals",
            "seller_strength",
            "gig_quality",
        )
    )


def test_orchestrator_dry_run_does_not_require_openai_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    summary = run_analysis_dry_run(
        {
            "run_id": "run-no-openai-key",
            "source_id": "src-no-openai-key",
            "keywords": ["python automation"],
            "intent": {"keyword_text": "need python automation"},
        }
    )
    assert summary.status == AnalysisStatus.SUCCESS


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


def _stage_by_type(summary: AnalysisRunSummary, stage_type: AnalysisTaskType) -> AnalysisStageSummary:
    return next(stage for stage in summary.stages if stage.stage == stage_type)


@pytest.mark.parametrize(
    ("payload", "expected_keyword", "expected_reason", "expected_bucket"),
    [
        (
            {
                "run_id": "run-intent-contract-explicit",
                "source_id": "src-intent-contract-explicit",
                "intent": {"keyword_text": "explicit intent keyword"},
                "keyword_text": "payload keyword",
                "keywords": ["keyword fallback"],
            },
            "explicit intent keyword",
            "explicit_intent_keyword",
            "high",
        ),
        (
            {
                "run_id": "run-intent-contract-payload",
                "source_id": "src-intent-contract-payload",
                "intent": {"keyword_text": None},
                "keyword_text": "payload keyword",
            },
            "payload keyword",
            "top_level_keyword_text",
            "high",
        ),
        (
            {
                "run_id": "run-intent-contract-keyword-list",
                "source_id": "src-intent-contract-keyword-list",
                "intent": {"keyword_text": ""},
                "keywords": ["list keyword"],
            },
            "list keyword",
            "keywords_first_entry",
            "medium",
        ),
        (
            {
                "run_id": "run-intent-contract-source",
                "source_id": "src-intent-contract-source",
                "intent": {"keyword_text": ""},
                "keywords": ["", "null"],
            },
            "src-intent-contract-source",
            "source_id_fallback",
            "low",
        ),
    ],
)
def test_orchestrator_intent_selection_contract_tracks_keyword_boundaries(
    payload: dict[str, object],
    expected_keyword: str,
    expected_reason: str,
    expected_bucket: str,
) -> None:
    summary = run_analysis_dry_run(payload)
    intent_stage = _stage_by_type(summary, AnalysisTaskType.INTENT_CLASSIFICATION)
    contract = intent_stage.metadata["intent_selection_contract"]
    assert contract["selected_keyword"] == expected_keyword
    assert contract["selection_reason"] == expected_reason
    assert contract["confidence_bucket"] == expected_bucket


def test_orchestrator_intent_selection_contract_reports_missing_all_sources() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-intent-contract-missing-all",
            "source_id": "src-intent-contract-missing-all",
            "intent": {},
        }
    )
    intent_stage = _stage_by_type(summary, AnalysisTaskType.INTENT_CLASSIFICATION)
    contract = intent_stage.metadata["intent_selection_contract"]
    assert contract["selection_reason"] == "source_id_fallback"
    assert "all_keyword_sources_missing" in contract["missing_input_warnings"]


def test_orchestrator_keyword_placeholder_contract_degrades_safely_for_sparse_input() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-keyword-placeholder-sparse",
            "source_id": "src-keyword-placeholder-sparse",
            "keywords": [],
        }
    )
    keyword_stage = _stage_by_type(summary, AnalysisTaskType.KEYWORD_CLUSTERING)
    contract = keyword_stage.metadata["readiness_contract"]
    assert contract["status"] == "empty"
    assert contract["downstream_scoring_status"] == "blocked_for_demand_scoring"
    assert contract["future_contract_fields"] == [
        "cluster_id",
        "label",
        "member_count",
        "confidence",
        "source_keywords",
    ]


@pytest.mark.parametrize(
    ("keywords", "expected_status", "expected_downstream"),
    [
        (["python"], "sparse", "blocked_for_demand_scoring"),
        (["python automation", "workflow automation"], "ready", "ready_for_demand_scoring"),
    ],
)
def test_orchestrator_keyword_placeholder_contract_distinguishes_sparse_and_ready(
    keywords: list[str],
    expected_status: str,
    expected_downstream: str,
) -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-keyword-placeholder-statuses",
            "source_id": "src-keyword-placeholder-statuses",
            "keywords": keywords,
        }
    )
    keyword_stage = _stage_by_type(summary, AnalysisTaskType.KEYWORD_CLUSTERING)
    contract = keyword_stage.metadata["readiness_contract"]
    assert contract["status"] == expected_status
    assert contract["downstream_scoring_status"] == expected_downstream


@pytest.mark.parametrize(
    ("gig_payload", "expected_status"),
    [
        (
            {
                "gig_id": "gig-ready",
                "title": "I will design a professional logo",
                "description": "Experienced designer with premium package options.",
                "package_count": 3,
                "rating": 4.9,
                "review_count": 120,
            },
            "ready",
        ),
        (
            {
                "gig_id": "gig-sparse",
                "title": "I will design a logo",
            },
            "sparse",
        ),
        (
            {
                "gig_id": "gig-empty",
            },
            "empty",
        ),
        (
            "malformed-gig",
            "blocked",
        ),
    ],
)
def test_orchestrator_gig_quality_placeholder_contract_handles_fixture_shapes(
    gig_payload: dict[str, object] | str,
    expected_status: str,
) -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-gig-placeholder",
            "source_id": "src-gig-placeholder",
            "gig": gig_payload,
        }
    )
    gig_stage = _stage_by_type(summary, AnalysisTaskType.GIG_QUALITY)
    contract = gig_stage.metadata["readiness_contract"]
    assert contract["status"] == expected_status


def test_orchestrator_competitor_placeholder_avoids_fabricated_weakness_signals() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-competitor-placeholder-missing",
            "source_id": "src-competitor-placeholder-missing",
            "competitors": [{"seller_id": "c1"}],
        }
    )
    competitor_stage = _stage_by_type(summary, AnalysisTaskType.COMPETITOR_PROFILE)
    contract = competitor_stage.metadata["readiness_contract"]
    assert contract["status"] == "sparse"
    assert contract["weakness_signal_available"] is False


def test_orchestrator_seller_strength_placeholder_reports_blocked_when_fields_missing() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-seller-placeholder-sparse",
            "source_id": "src-seller-placeholder-sparse",
            "seller": {"seller_id": "seller-1"},
        }
    )
    seller_stage = _stage_by_type(summary, AnalysisTaskType.SELLER_STRENGTH)
    contract = seller_stage.metadata["readiness_contract"]
    assert contract["status"] in {"empty", "sparse"}
    assert contract["downstream_status"] == "blocked_for_scoring"
    assert contract["readiness_state"] in {"missing_seller_data", "sparse_profile_signals"}


@pytest.mark.parametrize(
    ("competitors", "expected_status"),
    [
        ([], "blocked"),
        ([{"seller_id": "c1", "seller_level": "new", "rating": 4.2, "review_count": 8}], "sparse"),
        (
            [
                {"seller_id": "c1", "seller_level": "level_two", "rating": 4.7, "review_count": 120},
                {"seller_id": "c2", "seller_level": "top_rated", "rating": 4.9, "review_count": 500},
                {"seller_id": "c3", "seller_level": "level_one", "rating": 4.5, "review_count": 70},
            ],
            "ready",
        ),
    ],
)
def test_orchestrator_saturation_placeholder_contract_uses_competitor_signal_counts(
    competitors: list[dict[str, object]],
    expected_status: str,
) -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-saturation-placeholder",
            "source_id": "src-saturation-placeholder",
            "keywords": ["python automation"],
            "gig_quality_scores": [72.0],
            "competitors": competitors,
        }
    )
    saturation_stage = _stage_by_type(summary, AnalysisTaskType.SATURATION)
    contract = saturation_stage.metadata["readiness_contract"]
    assert contract["status"] == expected_status


@pytest.mark.parametrize(
    ("reviews", "expected_status"),
    [
        ([], "empty"),
        ([{"text": "Good work", "rating": 4.0}], "sparse"),
        (
            [
                {"text": "Fast delivery and strong communication", "rating": 5.0},
                {"text": "Great quality and quick turnaround", "rating": 5.0},
                {"text": "Excellent work and polite seller", "rating": 5.0},
            ],
            "ready",
        ),
    ],
)
def test_orchestrator_review_placeholder_contract_distinguishes_fixture_readiness(
    reviews: list[dict[str, object]],
    expected_status: str,
) -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-review-placeholder",
            "source_id": "src-review-placeholder",
            "reviews": reviews,
        }
    )
    review_stage = _stage_by_type(summary, AnalysisTaskType.REVIEW_ANALYSIS)
    contract = review_stage.metadata["readiness_contract"]
    assert contract["status"] == expected_status
    assert "warning_count" in contract


def test_orchestrator_review_placeholder_contract_blocks_unsupported_review_payload() -> None:
    summary = run_analysis_dry_run(
        {
            "run_id": "run-review-placeholder-unsupported",
            "source_id": "src-review-placeholder-unsupported",
            "reviews": "not-a-list",
        }
    )
    review_stage = _stage_by_type(summary, AnalysisTaskType.REVIEW_ANALYSIS)
    contract = review_stage.metadata["readiness_contract"]
    assert review_stage.status == AnalysisStatus.SUCCESS
    assert contract["status"] == "blocked"
    assert contract["source_availability"]["supported_review_payload"] is False
    assert any(warning.code == "reviews_fixture_unsupported" for warning in summary.warnings)


def test_orchestrator_scoring_readiness_exposes_future_contract_mapping() -> None:
    summary = run_analysis_dry_run(_load_analysis_fixture("complete_payload.json"))
    readiness = summary.metadata["scoring_readiness"]
    contracts = readiness["contracts"]
    assert "demand_scoring" in contracts
    assert "competition_scoring" in contracts
    assert "opportunity_scoring" in contracts
    assert "confidence_scoring" in contracts
    interfaces = readiness["interfaces"]
    assert "demand_scoring" in interfaces
    assert "competition_scoring" in interfaces
    assert "opportunity_scoring" in interfaces
    assert "confidence_scoring" in interfaces
    assert "conversion_intent_scoring" in interfaces
    assert "trend_scoring" in interfaces
    assert readiness["interface_statuses"]["confidence_scoring"] in {"ready", "sparse", "blocked", "empty"}


def test_fixture_factories_provide_required_analysis_shapes() -> None:
    complete_payload = make_complete_market_payload()
    assert complete_payload["keywords"]
    assert complete_payload["competitors"]
    assert complete_payload["reviews"]

    sparse_payload = make_sparse_gig_only_payload()
    assert sparse_payload["gig"]["gig_id"] == "gig-factory-sparse"

    missing_seller_payload = make_missing_seller_payload()
    assert "seller" not in missing_seller_payload
    assert "sellers" not in missing_seller_payload

    missing_reviews_payload = make_missing_reviews_payload()
    assert "reviews" not in missing_reviews_payload

    empty_payload = make_empty_upstream_payload()
    assert sorted(empty_payload.keys()) == ["run_id", "source_id"]


def test_intent_invalid_mock_label_degrades_with_warning() -> None:
    result = classify_intent(
        IntentInput(
            source_id="intent-src",
            keyword_text="need automation support",
            metadata={"mock_label": "out_of_taxonomy"},
        )
    )
    assert result.label == IntentLabel.AMBIGUOUS
    assert result.warnings
    assert any(warning.code == "intent_mock_label_invalid" for warning in result.warnings)
    assert result.status in {AnalysisReadinessStatus.PARTIAL, AnalysisReadinessStatus.BLOCKED}


def test_intent_valid_mock_label_is_accepted_for_deterministic_path() -> None:
    result = classify_intent(
        IntentInput(
            source_id="intent-src",
            keyword_text="need automation support",
            metadata={"mock_label": "buyer_ready"},
        )
    )
    assert result.label == IntentLabel.BUYER_READY
    assert result.status == AnalysisReadinessStatus.PARTIAL
    assert result.downstream_readiness["status"] == "partial"


def test_analysis_results_include_shared_envelope_fields_and_persistence_dict() -> None:
    payload = make_complete_market_payload()
    summary = run_analysis_dry_run(payload)
    intent_stage = _stage_by_type(summary, AnalysisTaskType.INTENT_CLASSIFICATION)
    assert intent_stage.readiness_status in {
        AnalysisReadinessStatus.READY,
        AnalysisReadinessStatus.PARTIAL,
        AnalysisReadinessStatus.BLOCKED,
        AnalysisReadinessStatus.SKIPPED,
    }

    quality = score_gig_quality(
        GigQualityInput(
            source_id="gig-src",
            gig_id="serialize-gig",
            title="I will build python automation",
            description="Deterministic quality contract payload." * 10,
            package_count=2,
            rating=4.8,
            review_count=35,
            image_count=3,
            has_faq=True,
        )
    )
    persisted = quality.to_persistence_dict()
    assert "status" in persisted
    assert "source_context" in persisted
    assert "evidence" in persisted
    assert "downstream_readiness" in persisted


def test_orchestrator_stage_log_summary_and_dashboard_handoff_contract_present() -> None:
    summary = run_analysis_dry_run(make_complete_market_payload())
    stage_logs = summary.metadata["stage_log_summary"]
    assert len(stage_logs) == len(summary.stages)
    assert all("duration_ms" in log_row for log_row in stage_logs)
    dashboard_contract = summary.metadata["dashboard_handoff_contract"]
    assert "opportunity_cards" in dashboard_contract
    assert "keyword_table" in dashboard_contract
    assert "run_history" in dashboard_contract
