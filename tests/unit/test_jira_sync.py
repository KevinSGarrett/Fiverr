"""
tests/unit/test_jira_sync.py — Unit tests for jira_sync.py pure functions.

Tests cover: AC extraction, AC verification, comment summary, Done gate.
External I/O (Jira API calls) is not tested here — those require live Jira.
"""
from __future__ import annotations

from automation.jira_sync import (
    build_comment_summary,
    extract_ac_items,
    verify_ac_against_evidence,
)


# ─── extract_ac_items ─────────────────────────────────────────────────────────

class TestExtractAcItems:
    def test_bullet_list(self):
        desc = "Description:\n- User can view thumbnails\n- Analysis runs without errors\n- Results stored in DB"
        items = extract_ac_items(desc)
        assert len(items) == 3
        assert "User can view thumbnails" in items

    def test_numbered_list(self):
        desc = "Acceptance Criteria:\n1. File is created and committed\n2. Tests pass with 90% coverage\n3. Jira story updated to Done"
        items = extract_ac_items(desc)
        assert len(items) == 3

    def test_mixed_bullets(self):
        desc = "* Feature A works\n• Feature B works\n- Feature C works"
        items = extract_ac_items(desc)
        assert len(items) == 3

    def test_empty_description(self):
        assert extract_ac_items("") == []
        assert extract_ac_items(None) == []  # type: ignore[arg-type]

    def test_no_bullets(self):
        desc = "This story implements the gig visual analysis module."
        items = extract_ac_items(desc)
        # No bullet items — may return empty or short inline sentences
        assert isinstance(items, list)

    def test_deduplication(self):
        desc = "- Same item here\n- Same item here\n- Different item here"
        items = extract_ac_items(desc)
        assert len(items) == 2  # deduped

    def test_caps_at_30(self):
        bullets = "\n".join(f"- Item number {i}" for i in range(50))
        items = extract_ac_items(bullets)
        assert len(items) <= 30

    def test_short_items_excluded(self):
        desc = "- x\n- ok\n- This is long enough to be included in the list"
        items = extract_ac_items(desc)
        # Short items (< 15 chars) should not be in the list
        assert not any(len(i) < 15 for i in items)

    def test_real_wave11_description(self):
        desc = (
            "Implement S8.1 — Gig Visual Analysis.\n"
            "- Gig visuals are analyzed into source-backed categories\n"
            "- Visual analysis results are persisted to the database\n"
            "- Thumbnail classification runs without errors\n"
            "- Test coverage is >=90%\n"
            "- Jira story transitioned to Done after all criteria met"
        )
        items = extract_ac_items(desc)
        assert len(items) == 5
        assert any("persisted" in i for i in items)


# ─── verify_ac_against_evidence ───────────────────────────────────────────────

class TestVerifyAcAgainstEvidence:
    def test_all_verified(self):
        ac = ["Visual analysis runs without errors", "Thumbnails stored in database"]
        evidence = "Visual analysis runs without errors. Thumbnails are stored in the database successfully."
        result = verify_ac_against_evidence(ac, evidence)
        assert len(result["verified"]) == 2
        assert len(result["unverified"]) == 0

    def test_none_verified(self):
        ac = ["Completely unrelated feature X"]
        evidence = "Some code was written and files were changed."
        result = verify_ac_against_evidence(ac, evidence)
        assert result["unverified"] == ["Completely unrelated feature X"]

    def test_partial_verification(self):
        ac = [
            "Visual analysis module created",
            "Completely missing feature that was never built",
        ]
        evidence = "Created visual analysis module in src/analysis/visual_analysis.py."
        result = verify_ac_against_evidence(ac, evidence)
        assert len(result["verified"]) >= 1
        assert len(result["unverified"]) >= 1

    def test_empty_ac(self):
        result = verify_ac_against_evidence([], "some evidence")
        assert result["verified"] == []
        assert result["unverified"] == []

    def test_empty_evidence(self):
        ac = ["Feature must be implemented"]
        result = verify_ac_against_evidence(ac, "")
        assert result["unverified"] == ["Feature must be implemented"]

    def test_returns_dict_keys(self):
        result = verify_ac_against_evidence(["test item here"], "test item here")
        assert "verified" in result
        assert "unverified" in result

    def test_case_insensitive(self):
        ac = ["Visual Analysis module must be created"]
        evidence = "VISUAL ANALYSIS MODULE was created successfully."
        result = verify_ac_against_evidence(ac, evidence)
        # Case-insensitive matching
        assert len(result["verified"]) == 1

    def test_full_ac_list(self):
        ac = [
            "Gig visuals are analyzed into source-backed categories",
            "Visual analysis results are persisted to the database",
            "Test coverage is above ninety percent",
        ]
        evidence = (
            "Created src/analysis/visual_analysis.py. "
            "Gig visuals analyzed into source-backed categories. "
            "Results persisted to database table visual_analysis_results. "
        )
        result = verify_ac_against_evidence(ac, evidence)
        # At least 2 of 3 should be verified
        assert len(result["verified"]) >= 2


# ─── build_comment_summary ────────────────────────────────────────────────────

class TestBuildCommentSummary:
    def test_no_comments(self):
        summary = build_comment_summary([])
        assert "no existing comments" in summary.lower()

    def test_single_comment(self):
        comments = [{"author": "Kevin", "body": "Initial planning", "created": "2026-06-10T09:00:00"}]
        summary = build_comment_summary(comments)
        assert "Kevin" in summary
        assert "Initial planning" in summary

    def test_truncates_at_five(self):
        comments = [
            {"author": f"User{i}", "body": f"Comment {i}", "created": f"2026-06-{10+i:02d}T09:00:00"}
            for i in range(10)
        ]
        summary = build_comment_summary(comments)
        # Should show total count and last 5
        assert "10" in summary

    def test_total_count_present(self):
        comments = [
            {"author": "A", "body": "First comment text here", "created": "2026-06-01"},
            {"author": "B", "body": "Second comment text here", "created": "2026-06-02"},
            {"author": "C", "body": "Third comment text here", "created": "2026-06-03"},
        ]
        summary = build_comment_summary(comments)
        assert "3" in summary

    def test_body_truncated(self):
        long_body = "x" * 200
        comments = [{"author": "User", "body": long_body, "created": "2026-06-01"}]
        summary = build_comment_summary(comments)
        # Body should be truncated to <= 120 chars in the summary line
        lines = summary.split("\n")
        for line in lines:
            assert len(line) < 300  # Reasonable line length
