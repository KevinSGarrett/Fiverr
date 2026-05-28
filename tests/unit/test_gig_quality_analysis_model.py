"""Compatibility wrapper tests for src.models.gig_quality_analysis."""

from __future__ import annotations

from src.models.gig_quality_analysis import GigQualityAnalysis
from src.models.market import GigQualityAnalysis as MarketGigQualityAnalysis


def test_gig_quality_analysis_import_works() -> None:
    assert GigQualityAnalysis is not None


def test_gig_quality_analysis_exports_correct_class() -> None:
    assert GigQualityAnalysis is MarketGigQualityAnalysis


def test_gig_quality_analysis_overall_weakness_score_accessor() -> None:
    row = GigQualityAnalysis(
        gig_url="https://www.fiverr.com/model/compat",
        niche_id="compat",
        run_id="compat-run",
        rubric_score=70.0,
        video_absent=False,
        portfolio_absent=False,
        description_thin=False,
        faq_absent=False,
        thumbnail_quality_flag=False,
        weakness_flags=[],
    )
    assert row.overall_weakness_score == 3.0
