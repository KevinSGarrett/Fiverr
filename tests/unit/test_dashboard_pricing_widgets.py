"""Unit tests for Wave 9 dashboard pricing widgets."""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.dashboard.pages.keywords import (
    get_pricing_summary_for_keyword,
    render_price_heatmap,
)
from src.dashboard.pages.opportunities import render_price_distribution_chart
from src.dashboard.pages.recommendations import render_pricing_strategy_card
from src.dashboard.pages.run_history import render_revenue_projection


class _FakeQuery:
    def __init__(self, rows: list[object]) -> None:
        self._rows = rows

    def filter(self, *_args: object, **_kwargs: object) -> _FakeQuery:
        return self

    def join(self, *_args: object, **_kwargs: object) -> _FakeQuery:
        return self

    def order_by(self, *_args: object, **_kwargs: object) -> _FakeQuery:
        return self

    def all(self) -> list[object]:
        return list(self._rows)

    def first(self) -> object | None:
        return self._rows[0] if self._rows else None


class _FakeDb:
    def __init__(self, mapping: dict[object, list[object]]) -> None:
        self.mapping = mapping

    def query(self, *models: object) -> _FakeQuery:
        if len(models) == 1:
            key: object = models[0]
        else:
            key = tuple(models)
        return _FakeQuery(self.mapping.get(key, []))


@pytest.fixture
def fake_st(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    st = SimpleNamespace(
        caption=MagicMock(),
        info=MagicMock(),
        metric=MagicMock(),
        markdown=MagicMock(),
        write=MagicMock(),
        plotly_chart=MagicMock(),
        columns=MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()]),
    )
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


class TestPriceDistributionChart:
    def test_renders_empty_state_no_price_data(self, fake_st: SimpleNamespace) -> None:
        from src.models.gig import Gig
        from src.models.price_analysis import PriceAnalysis

        db = _FakeDb({PriceAnalysis: [], Gig: []})
        render_price_distribution_chart(keyword_id=1, db=db)
        assert fake_st.caption.called

    def test_renders_histogram_with_data(self, fake_st: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.models.gig import Gig
        from src.models.price_analysis import PriceAnalysis

        monkeypatch.setattr(
            "src.pricing.analysis.extract_tier_prices",
            lambda gigs, tier: [50.0, 75.0, 100.0] if tier == "basic" else [],
        )
        db = _FakeDb(
            {
                PriceAnalysis: [SimpleNamespace(keyword_id=1, basic_n=3, basic_median=75.0)],
                Gig: [SimpleNamespace(keyword_id=1)],
            }
        )
        render_price_distribution_chart(keyword_id=1, db=db)
        assert fake_st.plotly_chart.called

    def test_histogram_excludes_zero_prices(self, fake_st: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.models.gig import Gig
        from src.models.price_analysis import PriceAnalysis

        monkeypatch.setattr(
            "src.pricing.analysis.extract_tier_prices",
            lambda gigs, tier: [0.0, 0.0] if tier == "basic" else [],
        )
        db = _FakeDb(
            {
                PriceAnalysis: [SimpleNamespace(keyword_id=1, basic_n=2, basic_median=0.0)],
                Gig: [SimpleNamespace(keyword_id=1)],
            }
        )
        render_price_distribution_chart(keyword_id=1, db=db)
        assert fake_st.caption.called

    def test_median_line_shown_when_available(self, fake_st: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.models.gig import Gig
        from src.models.price_analysis import PriceAnalysis

        monkeypatch.setattr(
            "src.pricing.analysis.extract_tier_prices",
            lambda gigs, tier: [80.0, 100.0, 120.0] if tier == "basic" else [],
        )
        db = _FakeDb(
            {
                PriceAnalysis: [SimpleNamespace(keyword_id=1, basic_n=3, basic_median=100.0)],
                Gig: [SimpleNamespace(keyword_id=1)],
            }
        )
        render_price_distribution_chart(keyword_id=1, db=db)
        assert fake_st.plotly_chart.called


class TestPricingStrategyCard:
    def test_renders_info_message_no_snapshot(self, fake_st: SimpleNamespace) -> None:
        from src.models.price_analysis import PricingSnapshot

        db = _FakeDb({PricingSnapshot: []})
        render_pricing_strategy_card(1, recommendation=None, db=db)
        assert fake_st.info.called

    def test_renders_entry_prices_when_snapshot_exists(self, fake_st: SimpleNamespace) -> None:
        from src.models.price_analysis import PricingSnapshot

        db = _FakeDb(
            {
                PricingSnapshot: [
                    SimpleNamespace(
                        keyword_id=1,
                        entry_basic=65.0,
                        entry_standard=145.0,
                        entry_premium=280.0,
                        market_type="WIDE_SPREAD",
                        confidence="MEDIUM",
                    )
                ]
            }
        )
        recommendation = SimpleNamespace(pricing_strategy=None)
        render_pricing_strategy_card(1, recommendation, db)
        assert fake_st.columns.called

    def test_renders_llm_narrative_when_present(self, fake_st: SimpleNamespace) -> None:
        from src.models.price_analysis import PricingSnapshot

        db = _FakeDb(
            {
                PricingSnapshot: [
                    SimpleNamespace(
                        keyword_id=1,
                        entry_basic=65.0,
                        entry_standard=145.0,
                        entry_premium=280.0,
                        market_type="COMMODITY",
                        confidence="HIGH",
                    )
                ]
            }
        )
        recommendation = SimpleNamespace(pricing_strategy="Lead with low risk entry pricing.")
        render_pricing_strategy_card(1, recommendation, db)
        assert fake_st.write.called

    def test_hides_narrative_section_when_none(self, fake_st: SimpleNamespace) -> None:
        from src.models.price_analysis import PricingSnapshot

        db = _FakeDb(
            {
                PricingSnapshot: [
                    SimpleNamespace(
                        keyword_id=1,
                        entry_basic=65.0,
                        entry_standard=145.0,
                        entry_premium=280.0,
                        market_type="COMMODITY",
                        confidence="LOW",
                    )
                ]
            }
        )
        recommendation = SimpleNamespace(pricing_strategy=None)
        render_pricing_strategy_card(1, recommendation, db)
        assert fake_st.write.call_count == 0


class TestPriceHeatmap:
    def test_renders_info_message_no_pricing_data(self, fake_st: SimpleNamespace) -> None:
        from src.models import Keyword
        from src.models.price_analysis import PriceAnalysis

        db = _FakeDb({(PriceAnalysis, Keyword): []})
        render_price_heatmap("niche-1", db)
        assert fake_st.info.called

    def test_heatmap_has_correct_column_count(self, fake_st: SimpleNamespace) -> None:
        from src.models import Keyword
        from src.models.price_analysis import PriceAnalysis

        db = _FakeDb(
            {
                (PriceAnalysis, Keyword): [
                    (
                        SimpleNamespace(basic_median=50.0, standard_median=90.0, premium_median=150.0),
                        SimpleNamespace(keyword="keyword one"),
                    ),
                ]
            }
        )
        render_price_heatmap("niche-1", db)
        assert fake_st.plotly_chart.called

    def test_keyword_labels_truncated_to_30_chars(self, fake_st: SimpleNamespace) -> None:
        from src.models import Keyword
        from src.models.price_analysis import PriceAnalysis

        long_keyword = "x" * 50
        db = _FakeDb(
            {
                (PriceAnalysis, Keyword): [
                    (
                        SimpleNamespace(basic_median=60.0, standard_median=100.0, premium_median=180.0),
                        SimpleNamespace(keyword=long_keyword),
                    ),
                ]
            }
        )
        render_price_heatmap("niche-1", db)
        assert fake_st.plotly_chart.called


class TestRevenueProjection:
    def test_renders_caption_no_snapshot(self, fake_st: SimpleNamespace) -> None:
        from src.models.price_analysis import PricingSnapshot

        db = _FakeDb({PricingSnapshot: []})
        render_revenue_projection(1, db)
        assert fake_st.caption.called

    def test_renders_5_milestone_rows(self, fake_st: SimpleNamespace) -> None:
        from src.models.price_analysis import PricingSnapshot

        ladder = [
            {"milestone": 5, "basic": 65},
            {"milestone": 10, "basic": 75},
            {"milestone": 25, "basic": 90},
            {"milestone": 50, "basic": 110},
            {"milestone": 100, "basic": 130},
        ]
        db = _FakeDb({PricingSnapshot: [SimpleNamespace(price_ladder=ladder)]})
        render_revenue_projection(1, db)
        assert fake_st.write.call_count == 5

    def test_revenue_calculation_correct_for_milestone(self, fake_st: SimpleNamespace) -> None:
        from src.models.price_analysis import PricingSnapshot

        db = _FakeDb({PricingSnapshot: [SimpleNamespace(price_ladder=[{"milestone": 5, "basic": 50}])]})
        render_revenue_projection(1, db)
        assert "$200/mo" in fake_st.write.call_args.args[0]

    def test_price_ladder_parsed_from_json_string(self, fake_st: SimpleNamespace) -> None:
        from src.models.price_analysis import PricingSnapshot

        payload = json.dumps([{"milestone": 5, "basic": 50}, {"milestone": 10, "basic": 60}])
        db = _FakeDb({PricingSnapshot: [SimpleNamespace(price_ladder=payload)]})
        render_revenue_projection(1, db)
        assert fake_st.write.call_count == 2


def test_get_pricing_summary_returns_none_shape() -> None:
    from src.models.price_analysis import PriceAnalysis

    db = _FakeDb({PriceAnalysis: []})
    result = get_pricing_summary_for_keyword(1, db)
    assert result == {"basic": None, "standard": None, "premium": None}
