"""S4.12 Keyword ranking and filtering utilities."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


class KeywordRanker:
    """Rank and filter keyword recommendation payloads."""

    def __init__(self) -> None:
        self.last_grouped_by_tag: dict[str, list[dict[str, Any]]] = {}

    def rank(self, keywords: list[dict[str, Any]], profile: str) -> list[dict[str, Any]]:
        """Return deterministic ranking sorted by final_score desc then keyword_id asc."""
        if not keywords:
            self.last_grouped_by_tag = {}
            return []

        ranked = sorted(
            [dict(keyword) for keyword in keywords],
            key=lambda item: (
                -self._as_float(item.get("final_score"), 0.0),
                self._as_int(item.get("keyword_id"), 0),
            ),
        )

        top_score = self._as_float(ranked[0].get("final_score"), 0.0)
        total = len(ranked)
        for index, keyword in enumerate(ranked, start=1):
            score = self._as_float(keyword.get("final_score"), 0.0)
            keyword["rank"] = index
            keyword["profile_used"] = keyword.get("profile_used", profile)
            keyword["percentile"] = self._compute_percentile(index, total)
            keyword["delta_from_top"] = round(top_score - score, 2)

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for keyword in ranked:
            grouped[str(keyword.get("tag", "UNCLASSIFIED"))].append(keyword)
        self.last_grouped_by_tag = dict(grouped)
        return ranked

    def grouped(self) -> dict[str, list[dict[str, Any]]]:
        """Return grouped ranking from the latest rank call."""
        return self.last_grouped_by_tag

    @staticmethod
    def filter_by_tag(keywords: list[dict[str, Any]], tag: str) -> list[dict[str, Any]]:
        return [keyword for keyword in keywords if str(keyword.get("tag")) == tag]

    @staticmethod
    def filter_by_niche(keywords: list[dict[str, Any]], niche_id: str) -> list[dict[str, Any]]:
        return [keyword for keyword in keywords if str(keyword.get("niche_id")) == niche_id]

    @staticmethod
    def filter_by_min_score(keywords: list[dict[str, Any]], min_score: float) -> list[dict[str, Any]]:
        return [
            keyword
            for keyword in keywords
            if KeywordRanker._as_float(keyword.get("final_score"), 0.0) >= min_score
        ]

    @staticmethod
    def _compute_percentile(rank: int, total: int) -> float:
        if total <= 1:
            return 100.0
        percentile = ((total - rank) / (total - 1)) * 100.0
        return round(percentile, 2)

    @staticmethod
    def _as_float(value: Any, default: float) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _as_int(value: Any, default: int) -> int:
        try:
            if value is None:
                return default
            return int(value)
        except (TypeError, ValueError):
            return default
