"""SRDI Tier 0 R1 -- category-constrained Fiverr search URLs.

Spec: PM_Pack/ref/project_plan/04_collection/SEARCH_URL_BUILDER.md
Constrains search by Fiverr category/subcategory with a SUBCATEGORY->CATEGORY->NONE fallback,
records the strictness used, and lets scoring discount unconstrained (NONE) demand.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any
from urllib.parse import quote
from urllib.request import urlopen

from src.collection.search_result_parser import parse_search_results_from_html

logger = logging.getLogger(__name__)

FIVERR_SEARCH_BASE_URL = "https://www.fiverr.com/search/gigs"
SEARCH_STRICTNESS_COLUMN = "search_strictness_used"
FALLBACK_MIN_RESULT_THRESHOLD_KEY = "min_result_threshold"

NICHE_CATEGORY_MAP_VERSION = "1.0"
NICHE_CATEGORY_MAP_NEXT_VALIDATION = date(2026, 8, 29)
DEFAULT_MIN_RESULT_THRESHOLD = 5
RESULTS_PER_PAGE = 16
UNCONSTRAINED_DEMAND_DEDUCTION = -0.08
UNCONSTRAINED_NOTE = "Demand from unconstrained search. Re-collect recommended."


class SearchStrictness(Enum):
    SUBCATEGORY = "SUBCATEGORY"
    CATEGORY = "CATEGORY"
    NONE = "NONE"


@dataclass(frozen=True)
class NicheCategoryMapping:
    fiverr_category_id: str
    fiverr_subcategory_id: str
    search_url_param: str
    fallback_category_id: str


NICHE_CATEGORY_MAP: dict[str, NicheCategoryMapping] = {
    "prd_ai_saas": NicheCategoryMapping(
        fiverr_category_id="10",
        fiverr_subcategory_id="10_7",
        search_url_param="category_id=10&sub_category=technical_writing",
        fallback_category_id="10",
    ),
    "support_kb_readiness": NicheCategoryMapping(
        fiverr_category_id="10",
        fiverr_subcategory_id="10_7",
        search_url_param="category_id=10&sub_category=technical_writing",
        fallback_category_id="10",
    ),
    "python_automation": NicheCategoryMapping(
        fiverr_category_id="6",
        fiverr_subcategory_id="6_2",
        search_url_param="category_id=6&sub_category=desktop_applications",
        fallback_category_id="6",
    ),
    "ai_agent_development": NicheCategoryMapping(
        fiverr_category_id="6",
        fiverr_subcategory_id="6_11",
        search_url_param="category_id=6&sub_category=chatbots",
        fallback_category_id="6",
    ),
    "mcp_ai_agent": NicheCategoryMapping(
        fiverr_category_id="6",
        fiverr_subcategory_id="6_11",
        search_url_param="category_id=6&sub_category=chatbots",
        fallback_category_id="6",
    ),
    "n8n_automation": NicheCategoryMapping(
        fiverr_category_id="6",
        fiverr_subcategory_id="6_2",
        search_url_param="category_id=6&sub_category=desktop_applications",
        fallback_category_id="6",
    ),
    "gumloop_automation": NicheCategoryMapping(
        fiverr_category_id="6",
        fiverr_subcategory_id="6_2",
        search_url_param="category_id=6&sub_category=desktop_applications",
        fallback_category_id="6",
    ),
    "workflow_automation": NicheCategoryMapping(
        fiverr_category_id="6",
        fiverr_subcategory_id="6_2",
        search_url_param="category_id=6&sub_category=desktop_applications",
        fallback_category_id="6",
    ),
    "python_web_scraping": NicheCategoryMapping(
        fiverr_category_id="6",
        fiverr_subcategory_id="6_2",
        search_url_param="category_id=6&sub_category=desktop_applications",
        fallback_category_id="6",
    ),
}

PRODUCTION_NICHES: tuple[str, ...] = tuple(NICHE_CATEGORY_MAP.keys())


def _today() -> date:
    return date.today()


def get_niche_mapping(niche_id: str | None) -> NicheCategoryMapping | None:
    if not niche_id:
        return None
    return NICHE_CATEGORY_MAP.get(niche_id)


def _strictnesses() -> tuple[SearchStrictness, SearchStrictness, SearchStrictness]:
    return (
        SearchStrictness.SUBCATEGORY,
        SearchStrictness.CATEGORY,
        SearchStrictness.NONE,
    )


def build_search_url(keyword: str, niche_id: str | None, strictness: SearchStrictness, page: int = 1) -> str:
    """Return a Fiverr search URL with the requested category constraint.

    Unknown niche -> NONE-strictness URL + WARNING (never raises).
    """
    normalized_page = max(1, int(page))
    offset = (normalized_page - 1) * RESULTS_PER_PAGE
    encoded_keyword = quote(keyword or "", safe="")
    params = [f"query={encoded_keyword}", f"offset={offset}"]

    mapping = get_niche_mapping(niche_id)
    if mapping is None:
        logger.warning("Unknown or missing niche_id=%r; falling back to NONE strictness URL.", niche_id)
    elif strictness == SearchStrictness.SUBCATEGORY:
        params.append(mapping.search_url_param)
    elif strictness == SearchStrictness.CATEGORY:
        params.append(f"category_id={mapping.fallback_category_id}")

    return f"{FIVERR_SEARCH_BASE_URL}?{'&'.join(params)}"


def _resolve_threshold(config: dict[str, Any] | None) -> int:
    if not isinstance(config, dict):
        return DEFAULT_MIN_RESULT_THRESHOLD
    raw = config.get(FALLBACK_MIN_RESULT_THRESHOLD_KEY, DEFAULT_MIN_RESULT_THRESHOLD)
    try:
        return max(1, int(raw))
    except (TypeError, ValueError):
        return DEFAULT_MIN_RESULT_THRESHOLD


def search_with_fallback(
    keyword: str,
    niche_id: str | None,
    config: dict[str, Any] | None,
    collect_fn: Callable[[str], Sequence[Any]],
) -> tuple[list[Any], SearchStrictness]:
    """Try SUBCATEGORY -> CATEGORY -> NONE until results >= threshold. Returns (results, strictness)."""
    threshold = _resolve_threshold(config)
    last_results: list[Any] = []
    last_strictness = SearchStrictness.NONE

    for strictness in _strictnesses():
        url = build_search_url(keyword, niche_id, strictness)
        try:
            collected = list(collect_fn(url))
        except Exception as exc:  # noqa: BLE001
            logger.warning("collect_fn failed for strictness=%s url=%s: %s", strictness.value, url, exc)
            collected = []
        last_results = collected
        last_strictness = strictness
        if len(collected) >= threshold:
            logger.info(
                "Search fallback satisfied threshold=%s at strictness=%s with results=%s.",
                threshold,
                strictness.value,
                len(collected),
            )
            return collected, strictness

    logger.warning(
        "Search fallback reached NONE strictness for niche_id=%r with results=%s (< threshold=%s).",
        niche_id,
        len(last_results),
        threshold,
    )
    return last_results, last_strictness


def check_category_mapping_freshness() -> bool:
    """True when today >= NICHE_CATEGORY_MAP_NEXT_VALIDATION; warns when re-validation due."""
    due = _today() >= NICHE_CATEGORY_MAP_NEXT_VALIDATION
    if due:
        logger.warning(
            "Category-map quarterly validation is due (target date: %s).",
            NICHE_CATEGORY_MAP_NEXT_VALIDATION.isoformat(),
        )
    return due


def _default_count_collector(url: str) -> int:
    with urlopen(url, timeout=30) as response:  # noqa: S310
        html = response.read().decode("utf-8", errors="ignore")
    parsed = parse_search_results_from_html(html)
    if parsed.total_result_count is not None:
        return int(parsed.total_result_count)
    return len(parsed.gig_cards)


def run_validation_sweep(
    niches: Sequence[str],
    keyword_template: str = "{niche} freelance",
    count_collector: Callable[[str], int] | None = None,
) -> list[dict[str, Any]]:
    """Compare constrained vs unconstrained counts and print recommended strictness."""
    collector = count_collector or _default_count_collector
    report_rows: list[dict[str, Any]] = []
    for niche_id in niches:
        if niche_id not in NICHE_CATEGORY_MAP:
            logger.warning("Skipping unknown niche during sweep: %s", niche_id)
            continue
        keyword = keyword_template.format(niche=niche_id.replace("_", " "))
        constrained_url = build_search_url(keyword, niche_id, SearchStrictness.SUBCATEGORY)
        unconstrained_url = build_search_url(keyword, niche_id, SearchStrictness.NONE)

        constrained_count = collector(constrained_url)
        unconstrained_count = collector(unconstrained_url)
        ratio = (constrained_count / unconstrained_count) if unconstrained_count > 0 else 1.0
        recommendation = (
            SearchStrictness.SUBCATEGORY.value
            if constrained_count >= DEFAULT_MIN_RESULT_THRESHOLD
            else SearchStrictness.CATEGORY.value
            if constrained_count > 0
            else SearchStrictness.NONE.value
        )
        row = {
            "niche_id": niche_id,
            "constrained_count": constrained_count,
            "unconstrained_count": unconstrained_count,
            "retention_ratio": round(ratio, 4),
            "recommended_strictness": recommendation,
        }
        report_rows.append(row)
        print(
            f"{niche_id}: constrained={constrained_count} unconstrained={unconstrained_count} "
            f"retention={row['retention_ratio']} recommended={recommendation}"
        )
    print(f"DL-207 sweep summary complete: {len(report_rows)} niche rows evaluated.")
    return report_rows


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Fiverr category-constrained search strictness.")
    parser.add_argument("--sweep", action="store_true", help="Run constrained vs unconstrained count sweep.")
    parser.add_argument(
        "--niches",
        default="all",
        help="Either 'all' or a single niche id from NICHE_CATEGORY_MAP.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.sweep:
        print("No action specified. Use --sweep.")
        return 0
    if args.niches == "all":
        target_niches = PRODUCTION_NICHES
    else:
        target_niches = (str(args.niches),)
    run_validation_sweep(target_niches)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
