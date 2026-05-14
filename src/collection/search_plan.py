"""Read-only search planning for future collection execution."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from urllib.parse import urlencode

from src.collection.keyword_expansion import ExpandedKeyword


@dataclass(frozen=True, slots=True)
class SearchPlanItem:
    """Single planned search query/page item."""

    keyword_id: str
    query: str
    url: str
    page_number: int
    max_pages: int
    source: str
    estimated_priority: int
    source_seed: str


@dataclass(frozen=True, slots=True)
class SearchPlan:
    """Collection-safe search plan from expanded keywords."""

    items: list[SearchPlanItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def build_search_plan(
    expanded_keywords: Sequence[ExpandedKeyword],
    *,
    region: str | None = None,
    language: str | None = None,
    sort: str | None = None,
    max_pages: int = 1,
) -> SearchPlan:
    """Build deterministic Fiverr search URLs without making requests."""

    if max_pages < 1:
        raise ValueError("max_pages must be >= 1.")

    items: list[SearchPlanItem] = []
    for keyword_index, expanded in enumerate(expanded_keywords):
        for page_number in range(1, max_pages + 1):
            query_params: dict[str, str | int] = {"query": expanded.keyword, "page": page_number}
            if region:
                query_params["location"] = region
            if language:
                query_params["language"] = language
            if sort:
                query_params["source"] = sort

            url = f"https://www.fiverr.com/search/gigs?{urlencode(query_params)}"
            items.append(
                SearchPlanItem(
                    keyword_id=expanded.keyword_id,
                    query=expanded.keyword,
                    url=url,
                    page_number=page_number,
                    max_pages=max_pages,
                    source=expanded.expansion_method,
                    estimated_priority=max(1, 10_000 - (keyword_index * 100) - page_number),
                    source_seed=expanded.source_seed,
                )
            )
    return SearchPlan(items=items)
