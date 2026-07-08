"""Unit tests for the customer-facing PDF report engine."""

from __future__ import annotations

from pathlib import Path

import pytest
from src.reports.generator import generate_report


def _opportunity_data() -> dict:
    return {
        "summary_metrics": [{"label": "Niches", "value": 1}],
        "niches": [
            {
                "name": "AI Automation",
                "depth": "full",
                "keyword_count": 1,
                "keywords": [
                    {
                        "keyword_text": "ai workflow automation",
                        "tag": "STRONG GO",
                        "final_score": 88.0,
                        "demand": 70.0,
                        "competition": 40.0,
                        "opportunity": 60.0,
                        "feasibility": 80.0,
                        "trend": 55.0,
                        "confidence": 0.9,
                    }
                ],
            }
        ],
    }


def test_generate_report_rejects_unknown_report_type(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown report_type"):
        generate_report("competitor", {}, str(tmp_path / "out.pdf"))


def test_generate_report_writes_pdf_or_raises_install_hint(tmp_path: Path) -> None:
    output = tmp_path / "opportunity.pdf"
    try:
        result = generate_report(
            "opportunity", _opportunity_data(), str(output), niche_name="AI Automation"
        )
        assert result == str(output)
        assert output.exists()
        assert output.stat().st_size > 0
    except ImportError as exc:
        assert "WeasyPrint + Jinja2" in str(exc)


def test_generate_report_run_summary_writes_pdf_or_raises_install_hint(tmp_path: Path) -> None:
    output = tmp_path / "run_summary.pdf"
    data = {
        "run": {
            "duration": "2m 5s",
            "llm_cost": 1.23,
            "keywords_expanded": 10,
            "gigs_collected": 40,
            "error_count": 1,
            "summary_text": "Processed 10 search job(s).",
            "new_strong_go": [],
            "dead_letters": [],
        }
    }
    try:
        result = generate_report("run_summary", data, str(output), run_id="run-abc")
        assert result == str(output)
        assert output.exists()
    except ImportError as exc:
        assert "WeasyPrint + Jinja2" in str(exc)


def test_generate_report_recommendation_writes_pdf_or_raises_install_hint(tmp_path: Path) -> None:
    output = tmp_path / "recommendation.pdf"
    data = {
        "recommendations": [
            {
                "tag": "STRONG GO",
                "keyword_text": "seo blog writing",
                "niche_name": "SEO Writing",
                "final_score": 91.0,
                "generated_at": "2026-07-08",
                "viability": {
                    "viability_assessment": "Healthy demand.",
                    "timing_assessment": "Good entry window.",
                    "blunt_recommendation": "Go.",
                },
                "gig_titles": [
                    {"title": "I will write seo blog content", "positioning_angle": "authority"}
                ],
                "package_structure": {
                    "basic": {
                        "name": "Basic",
                        "price": 50,
                        "deliverables": ["500 words"],
                        "delivery_days": 3,
                        "revisions": 1,
                    },
                    "standard": {
                        "name": "Standard",
                        "price": 100,
                        "deliverables": ["1000 words"],
                        "delivery_days": 5,
                        "revisions": 2,
                    },
                    "premium": {
                        "name": "Premium",
                        "price": 200,
                        "deliverables": ["2000 words"],
                        "delivery_days": 7,
                        "revisions": 3,
                    },
                },
                "differentiation": {
                    "positioning_statement": "Focus on technical SEO depth.",
                    "one_sentence_pitch": "SEO content that ranks.",
                    "differentiators": [{"action": "Publish keyword research alongside copy."}],
                },
                "faq_entries": [{"question": "How fast?", "answer": "3 days"}],
                "red_flags": {
                    "overall_risk_level": "LOW",
                    "red_flags": [
                        {
                            "severity": "LOW",
                            "flag_type": "seasonality",
                            "description": "Slower in Q1.",
                            "mitigation": "Diversify.",
                        }
                    ],
                },
            }
        ]
    }
    try:
        result = generate_report("recommendation", data, str(output))
        assert result == str(output)
        assert output.exists()
    except ImportError as exc:
        assert "WeasyPrint + Jinja2" in str(exc)
