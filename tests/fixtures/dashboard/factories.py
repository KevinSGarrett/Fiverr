"""Deterministic fixture factories for dashboard product pages."""

from __future__ import annotations

from typing import Any


def build_dashboard_fixture_run() -> dict[str, Any]:
    """Return a small, realistic fixture-backed run for dashboard payload tests."""
    return {
        "opportunities": [
            {
                "id": "opp-logo-1",
                "opportunity": "Minimalist Logo Packages",
                "niche": "logo-design",
                "score": 91.2,
                "confidence": 0.88,
                "status": "strong_go",
                "keyword_links": ["kw-logo-design", "kw-brand-kit"],
            },
            {
                "id": "opp-resume-1",
                "opportunity": "ATS Resume Writing",
                "niche": "career-services",
                "score": 79.5,
                "confidence": 0.73,
                "status": "conditional_go",
                "keyword_links": ["kw-ats-resume"],
            },
        ],
        "keywords": [
            {
                "id": "kw-logo-design",
                "keyword": "logo design package",
                "niche": "logo-design",
                "cluster": "Brand Identity",
                "demand": "high",
                "saturation": "medium",
                "score": 88.0,
                "confidence": 0.84,
                "status": "strong_go",
                "opportunity_ids": ["opp-logo-1"],
            },
            {
                "id": "kw-brand-kit",
                "keyword": "brand kit design",
                "niche": "logo-design",
                "cluster": "Brand Identity",
                "demand": "medium",
                "saturation": "medium",
                "score": 75.0,
                "confidence": 0.65,
                "status": "monitor",
                "opportunity_ids": ["opp-logo-1"],
            },
            {
                "id": "kw-ats-resume",
                "keyword": "ats resume writing",
                "niche": "career-services",
                "cluster": None,
                "demand": "high",
                "saturation": "high",
                "score": 71.0,
                "confidence": 0.62,
                "status": "conditional_go",
                "opportunity_ids": ["opp-resume-1"],
            },
        ],
        "run_history": [
            {
                "run_id": "run-014-001",
                "status": "pass",
                "stages": [{"name": "collection"}, {"name": "analysis"}, {"name": "reporting"}],
                "duration_seconds": 742,
                "warning_count": 1,
                "failure_summary": "",
                "next_action": "Review warning and publish report.",
            },
            {
                "run_id": "run-014-000",
                "status": "warning",
                "stages": [{"name": "collection"}, {"name": "analysis"}],
                "duration_seconds": 689,
                "warning_count": 3,
                "failure_summary": "Keyword cluster confidence below threshold.",
                "next_action": "Re-run analysis after fixture refresh.",
            },
        ],
    }

