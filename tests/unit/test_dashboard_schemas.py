"""Unit tests for dashboard display schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from src.dashboard.schemas import (
    OpportunityCardSchema,
    PriceLadderDisplayStep,
    PricingDisplaySchema,
    ScoreBreakdown,
)


def _keyword_score_stub() -> SimpleNamespace:
    return SimpleNamespace(
        keyword_id=101,
        demand_score=70.0,
        competition_score=60.0,
        opportunity_score=75.0,
        feasibility_score=68.0,
        profitability_score=72.0,
        confidence_modifier=0.91,
        tag="STRONG_GO",
        final_score=82.3,
        red_flags=[{"flag": "HIGH_COMPETITION"}, {"flag": "LOW_MARGIN"}],
        missing_data_warnings=["Google Trends unavailable"],
        explanation_text="Strong demand with manageable competition.",
        scored_at=datetime(2026, 5, 18, 9, 0, tzinfo=UTC),
    )


def _pricing_rec_stub() -> SimpleNamespace:
    return SimpleNamespace(
        keyword_id=101,
        market_type="MODERATE_SPREAD",
        entry_basic=50.0,
        entry_standard=100.0,
        entry_premium=180.0,
        acquisition_basic=45.0,
        target_basic=75.0,
        target_standard=140.0,
        target_premium=240.0,
        undercut_pct=20.0,
        confidence="MEDIUM",
        price_ladder=[
            {
                "milestone_reviews": 0,
                "label": "Launch (0 reviews)",
                "basic": 50.0,
                "standard": 100.0,
                "premium": 180.0,
                "basic_increase_pct": 0.0,
            },
            {
                "milestone_reviews": 25,
                "label": "Growing (25 reviews)",
                "basic": 62.0,
                "standard": 122.0,
                "premium": 205.0,
                "basic_increase_pct": 24.0,
            },
        ],
    )


def test_opportunity_card_valid_construction() -> None:
    schema = OpportunityCardSchema(
        keyword_id=1,
        keyword_text="python automation",
        niche_id="12",
        tag="STRONG_GO",
        final_score=82.0,
        confidence_modifier=0.9,
        score_breakdown=ScoreBreakdown(demand=70.0),
    )
    assert schema.keyword_text == "python automation"


def test_opportunity_card_tag_required() -> None:
    with pytest.raises(ValidationError):
        OpportunityCardSchema(
            keyword_id=1,
            keyword_text="python automation",
            niche_id="12",
            final_score=82.0,
            confidence_modifier=0.9,
            score_breakdown=ScoreBreakdown(),
        )


def test_opportunity_card_score_range() -> None:
    with pytest.raises(ValidationError):
        OpportunityCardSchema(
            keyword_id=1,
            keyword_text="python automation",
            niche_id="12",
            tag="STRONG_GO",
            final_score=101.0,
            confidence_modifier=0.9,
            score_breakdown=ScoreBreakdown(),
        )


def test_opportunity_card_from_keyword_score() -> None:
    card = OpportunityCardSchema.from_keyword_score(_keyword_score_stub(), rank=2)
    assert card.keyword_id == 101
    assert card.rank == 2
    assert card.score_breakdown.opportunity == 75.0


def test_opportunity_card_red_flags_extracted() -> None:
    card = OpportunityCardSchema.from_keyword_score(_keyword_score_stub())
    assert card.red_flags == ["HIGH_COMPETITION", "LOW_MARGIN"]


def test_opportunity_card_defaults() -> None:
    card = OpportunityCardSchema(
        keyword_id=1,
        keyword_text="python automation",
        niche_id="12",
        tag="MONITOR",
        final_score=50.0,
        confidence_modifier=0.5,
        score_breakdown=ScoreBreakdown(),
    )
    assert card.red_flags == []
    assert card.missing_data_warnings == []


def test_pricing_display_valid_construction() -> None:
    schema = PricingDisplaySchema(
        keyword_id=101,
        keyword_text="python automation",
        entry_basic=50.0,
        entry_standard=100.0,
        entry_premium=180.0,
    )
    assert schema.entry_premium == 180.0


def test_pricing_display_price_ladder_empty() -> None:
    schema = PricingDisplaySchema(
        keyword_id=101,
        keyword_text="python automation",
        entry_basic=50.0,
        entry_standard=100.0,
        entry_premium=180.0,
        price_ladder=[],
    )
    assert schema.price_ladder == []


def test_pricing_display_from_pricing_rec() -> None:
    schema = PricingDisplaySchema.from_pricing_recommendation(_pricing_rec_stub(), "python automation")
    assert schema.keyword_id == 101
    assert schema.target_premium == 240.0


def test_pricing_display_ladder_steps() -> None:
    schema = PricingDisplaySchema.from_pricing_recommendation(_pricing_rec_stub(), "python automation")
    assert len(schema.price_ladder) == 2
    assert isinstance(schema.price_ladder[0], PriceLadderDisplayStep)
    assert schema.price_ladder[1].milestone_reviews == 25


def test_score_breakdown_all_none() -> None:
    breakdown = ScoreBreakdown()
    assert breakdown.model_dump() == {
        "demand": None,
        "competition": None,
        "opportunity": None,
        "feasibility": None,
        "profitability": None,
        "confidence_modifier": None,
    }


def test_score_breakdown_populated() -> None:
    breakdown = ScoreBreakdown(demand=70.0, competition=60.0, opportunity=75.0)
    assert breakdown.demand == 70.0
    assert breakdown.competition == 60.0
    assert breakdown.opportunity == 75.0


def test_pricing_display_narrative_none() -> None:
    schema = PricingDisplaySchema(
        keyword_id=101,
        keyword_text="python automation",
        entry_basic=50.0,
        entry_standard=100.0,
        entry_premium=180.0,
    )
    assert schema.strategy_narrative is None


def test_opportunity_card_json_serializable() -> None:
    card = OpportunityCardSchema.from_keyword_score(_keyword_score_stub())
    payload = card.model_dump()
    assert isinstance(payload["score_breakdown"], dict)
    assert payload["scored_at"].startswith("2026-05-18T09:00:00")
