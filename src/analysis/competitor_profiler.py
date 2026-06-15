"""Stage 10 competitor profiling orchestration and benchmark helpers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from src.models.gig import Gig
from src.models.gig_quality_score import GigQualityScore
from src.models.market import Keyword, write_competitor_profile
from src.models.niche import Niche
from src.models.search_result import SearchResult
from src.models.seller import Seller

_GIG_DATA_COLUMNS = [
    "gig_url",
    "seller_username",
    "price",
    "rating",
    "review_count",
    "queue",
    "delivery_days",
    "has_video",
    "portfolio_count",
]


def _is_session(db: Any) -> bool:
    return isinstance(db, Session)


def _config_section(config: dict[str, Any], key: str) -> dict[str, Any]:
    section = config.get(key, {}) if isinstance(config, dict) else {}
    return section if isinstance(section, dict) else {}


def _coerce_int(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return default
    return default


def _coerce_float(value: Any, default: float) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _resolve_niche_pk(niche_id: str, db: Any) -> int | None:
    if niche_id.isdigit():
        return int(niche_id)
    if not _is_session(db):
        return None
    row = db.query(Niche).filter(Niche.slug == niche_id).one_or_none()
    return None if row is None else int(row.id)


def _extract_niche_ids(config: dict[str, Any]) -> list[str]:
    niches = config.get("niches", []) if isinstance(config, dict) else []
    extracted: list[str] = []
    if not isinstance(niches, list):
        return extracted
    for niche in niches:
        if not isinstance(niche, dict):
            continue
        if niche.get("is_active", True) is False:
            continue
        niche_id = niche.get("niche_id")
        if isinstance(niche_id, str) and niche_id.strip():
            extracted.append(niche_id.strip())
    return extracted


def _resolve_top_n_per_keyword(config: dict[str, Any] | None) -> int:
    cfg = config if isinstance(config, dict) else {}
    analysis_cfg = _config_section(cfg, "analysis")
    profiling_cfg = _config_section(cfg, "competitor_profiling")
    return max(
        1,
        _coerce_int(
            profiling_cfg.get(
                "top_gigs_per_keyword",
                analysis_cfg.get("top_gigs_per_keyword", 20),
            ),
            20,
        ),
    )


def _resolve_top_competitor_gigs(config: dict[str, Any] | None) -> int:
    cfg = config if isinstance(config, dict) else {}
    profiling_cfg = _config_section(cfg, "competitor_profiling")
    return max(1, _coerce_int(profiling_cfg.get("top_competitor_gigs", 10), 10))


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        normalized = value.strip().replace(",", "")
        if not normalized:
            return None
        try:
            return float(normalized)
        except ValueError:
            return None
    return None


def _safe_int(value: Any) -> int | None:
    parsed = _safe_float(value)
    return None if parsed is None else int(parsed)


def _extract_delivery_days(packages: Any) -> int | None:
    if not isinstance(packages, list):
        return None
    candidates: list[int] = []
    for package in packages:
        if not isinstance(package, dict):
            continue
        delivery_days = _safe_int(package.get("delivery_days"))
        if delivery_days is not None:
            candidates.append(delivery_days)
    return min(candidates) if candidates else None


def _extract_price(starting_price: Any, packages: Any) -> float | None:
    parsed_price = _safe_float(starting_price)
    if parsed_price is not None:
        return parsed_price
    if not isinstance(packages, list):
        return None
    candidates: list[float] = []
    for package in packages:
        if not isinstance(package, dict):
            continue
        package_price = _safe_float(package.get("price"))
        if package_price is not None:
            candidates.append(package_price)
    return min(candidates) if candidates else None


def _empty_gig_dataframe() -> pd.DataFrame:
    return pd.DataFrame(columns=_GIG_DATA_COLUMNS)


def _empty_seller_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "seller_username",
            "seller_level",
            "total_reviews",
            "total_gigs",
            "response_rate",
            "member_since",
        ]
    )


def load_gig_data_for_niche(
    niche_id: str,
    run_id: str,
    db: Any,
    config: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Load top-N gig rows for a niche/run as a pandas DataFrame."""
    if not _is_session(db):
        return _empty_gig_dataframe()

    niche_pk = _resolve_niche_pk(niche_id, db)
    if niche_pk is None:
        return _empty_gig_dataframe()
    top_n = _resolve_top_n_per_keyword(config)

    query = (
        db.query(
            Gig.keyword_id.label("keyword_id"),
            Gig.gig_url.label("gig_url"),
            Gig.seller_username.label("seller_username"),
            Gig.starting_price.label("starting_price"),
            Gig.rating_exact.label("rating_exact"),
            Gig.avg_rating.label("avg_rating"),
            Gig.review_count_exact.label("review_count_exact"),
            Gig.review_count.label("review_count"),
            Gig.orders_in_queue.label("orders_in_queue"),
            Gig.packages.label("packages"),
            Gig.video_present.label("gig_video_present"),
            Gig.portfolio_count.label("gig_portfolio_count"),
            Gig.position.label("position"),
            SearchResult.rank.label("search_rank"),
            GigQualityScore.video_present.label("quality_video_present"),
            GigQualityScore.portfolio_count.label("quality_portfolio_count"),
        )
        .join(Keyword, Keyword.id == Gig.keyword_id)
        .outerjoin(
            SearchResult,
            and_(
                SearchResult.gig_id == Gig.id,
                SearchResult.keyword_id == Gig.keyword_id,
                SearchResult.run_id == run_id,
            ),
        )
        .outerjoin(
            GigQualityScore,
            and_(
                GigQualityScore.gig_url == Gig.gig_url,
                GigQualityScore.run_id == run_id,
            ),
        )
        .filter(Keyword.niche_id == niche_pk)
        .order_by(
            Gig.keyword_id.asc(),
            SearchResult.rank.asc().nullslast(),
            Gig.position.asc().nullslast(),
        )
    )
    if run_id.strip():
        query = query.filter(or_(Gig.run_id == run_id, Gig.run_id.is_(None)))

    rows = query.all()
    if not rows:
        return _empty_gig_dataframe()

    records: list[dict[str, Any]] = []
    keyword_counts: dict[int, int] = {}
    seen_gigs_per_keyword: dict[int, set[str]] = {}
    for row in rows:
        if row.keyword_id is None:
            continue
        keyword_id = int(row.keyword_id)
        gig_url = str(row.gig_url)
        seen_for_keyword = seen_gigs_per_keyword.setdefault(keyword_id, set())
        if gig_url in seen_for_keyword:
            continue
        if keyword_counts.get(keyword_id, 0) >= top_n:
            continue

        price = _extract_price(row.starting_price, row.packages)
        rating = _safe_float(row.rating_exact)
        if rating is None:
            rating = _safe_float(row.avg_rating)
        review_count = _safe_int(row.review_count_exact)
        if review_count is None:
            review_count = _safe_int(row.review_count)
        queue = _safe_int(row.orders_in_queue)
        delivery_days = _extract_delivery_days(row.packages)
        has_video = row.quality_video_present
        if has_video is None:
            has_video = row.gig_video_present
        portfolio_count = _safe_int(row.quality_portfolio_count)
        if portfolio_count is None:
            portfolio_count = _safe_int(row.gig_portfolio_count)

        rank_order = _safe_int(row.search_rank)
        if rank_order is None:
            rank_order = _safe_int(row.position)
        if rank_order is None:
            rank_order = 9_999

        seen_for_keyword.add(gig_url)
        keyword_counts[keyword_id] = keyword_counts.get(keyword_id, 0) + 1
        records.append(
            {
                "keyword_id": keyword_id,
                "gig_url": gig_url,
                "seller_username": str(row.seller_username),
                "price": price,
                "rating": rating,
                "review_count": review_count,
                "queue": queue,
                "delivery_days": delivery_days,
                "has_video": bool(has_video) if has_video is not None else False,
                "portfolio_count": portfolio_count,
                "rank_order": rank_order,
            }
        )

    gig_df = pd.DataFrame.from_records(records)
    if gig_df.empty:
        return _empty_gig_dataframe()
    return gig_df[_GIG_DATA_COLUMNS].reset_index(drop=True)


def _numeric_series(frame: pd.DataFrame, column: str) -> pd.Series | None:
    if column not in frame.columns:
        return None
    numeric = pd.to_numeric(frame[column], errors="coerce").dropna()
    return None if numeric.empty else numeric.astype(float)


def _metric_mean(series: pd.Series | None) -> float | None:
    return None if series is None else float(series.mean())


def _metric_median(series: pd.Series | None) -> float | None:
    return None if series is None else float(series.median())


def _metric_std(series: pd.Series | None) -> float | None:
    if series is None:
        return None
    std_value = float(series.std(ddof=0))
    if np.isnan(std_value):
        return 0.0
    return std_value


def _metric_min_int(series: pd.Series | None) -> int | None:
    return None if series is None else int(series.min())


def _metric_max_int(series: pd.Series | None) -> int | None:
    return None if series is None else int(series.max())


def compute_market_benchmarks(gig_df: pd.DataFrame) -> dict[str, float | int | None]:
    """Compute market benchmark summary metrics from gig rows."""
    if gig_df.empty:
        return {}

    price = _numeric_series(gig_df, "price")
    rating = _numeric_series(gig_df, "rating")
    review_count = _numeric_series(gig_df, "review_count")
    delivery_days = _numeric_series(gig_df, "delivery_days")

    video_present_rate: float | None = None
    if "has_video" in gig_df.columns:
        video_present_rate = float(pd.Series(gig_df["has_video"]).fillna(False).astype(bool).mean())

    portfolio_present_rate: float | None = None
    if "portfolio_count" in gig_df.columns:
        portfolio = pd.to_numeric(gig_df["portfolio_count"], errors="coerce").fillna(0)
        portfolio_present_rate = float((portfolio > 0).mean())

    return {
        "median_price": _metric_median(price),
        "mean_price": _metric_mean(price),
        "price_std": _metric_std(price),
        "median_rating": _metric_median(rating),
        "mean_rating": _metric_mean(rating),
        "mean_reviews": _metric_mean(review_count),
        "median_reviews": _metric_median(review_count),
        "min_delivery_days": _metric_min_int(delivery_days),
        "max_delivery_days": _metric_max_int(delivery_days),
        "median_delivery_days": _metric_median(delivery_days),
        "video_present_rate": video_present_rate,
        "portfolio_present_rate": portfolio_present_rate,
    }


def load_seller_data_for_niche(
    niche_id: str,
    run_id: str,
    db: Any,
    seller_usernames: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Load seller rows for niche/run context in a single query."""
    if not _is_session(db):
        return _empty_seller_dataframe()

    niche_pk = _resolve_niche_pk(niche_id, db)
    if niche_pk is None:
        return _empty_seller_dataframe()

    query = (
        db.query(
            Seller.seller_username.label("seller_username"),
            Seller.seller_level.label("seller_level"),
            Seller.total_reviews.label("total_reviews"),
            Seller.total_gigs.label("total_gigs"),
            Seller.response_rate.label("response_rate"),
            Seller.member_since.label("member_since"),
        )
        .join(Gig, Gig.seller_username == Seller.seller_username)
        .join(Keyword, Keyword.id == Gig.keyword_id)
        .filter(Keyword.niche_id == niche_pk)
    )
    if run_id.strip():
        query = query.filter(or_(Gig.run_id == run_id, Gig.run_id.is_(None)))
    if seller_usernames:
        query = query.filter(Seller.seller_username.in_(list({str(username) for username in seller_usernames})))

    rows = query.all()
    if not rows:
        return _empty_seller_dataframe()

    seller_df = pd.DataFrame.from_records([dict(row._mapping) for row in rows])
    if seller_df.empty:
        return _empty_seller_dataframe()
    seller_df = seller_df.sort_values(by=["seller_username"]).drop_duplicates(
        subset=["seller_username"], keep="first"
    )
    return seller_df.reset_index(drop=True)


def compute_seller_level_distribution(seller_df: pd.DataFrame) -> dict[str, float]:
    """Return seller-level distribution fractions (sum ~= 1.0)."""
    if seller_df.empty or "seller_level" not in seller_df.columns:
        return {"UNKNOWN": 1.0}

    normalized = (
        pd.Series(seller_df["seller_level"])
        .fillna("UNKNOWN")
        .astype(str)
        .str.strip()
        .replace("", "UNKNOWN")
        .str.upper()
        .str.replace(" ", "_", regex=False)
    )
    counts = normalized.value_counts(dropna=False)
    total = int(counts.sum())
    if total <= 0:
        return {"UNKNOWN": 1.0}
    return {str(level): round(float(count) / float(total), 4) for level, count in counts.items()}


def _serialize_scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, float):
        return float(value)
    if isinstance(value, int):
        return int(value)
    return value


def extract_top_n_competitor_gigs(gig_df: pd.DataFrame, n: int = 10) -> list[dict[str, Any]]:
    """Return top-N gigs ranked by quality-weighted score."""
    if gig_df.empty:
        return []

    top_n = max(1, int(n))
    ranked_df = gig_df.copy()
    rating_source = ranked_df["rating"] if "rating" in ranked_df.columns else pd.Series([0.0] * len(ranked_df))
    review_source = (
        ranked_df["review_count"] if "review_count" in ranked_df.columns else pd.Series([0.0] * len(ranked_df))
    )
    rating = pd.to_numeric(rating_source, errors="coerce").fillna(0.0)
    review_count = pd.to_numeric(review_source, errors="coerce").fillna(0.0)
    ranked_df["quality_rank_score"] = rating * np.log1p(review_count)
    ranked_df = ranked_df.sort_values(by=["quality_rank_score"], ascending=False).head(top_n)

    payload_columns = [
        "gig_url",
        "seller_username",
        "price",
        "rating",
        "review_count",
        "queue",
        "delivery_days",
        "has_video",
        "portfolio_count",
        "quality_rank_score",
    ]
    records: list[dict[str, Any]] = []
    for row in ranked_df[payload_columns].to_dict(orient="records"):
        records.append({str(key): _serialize_scalar(value) for key, value in row.items()})
    return records


def compute_new_seller_gap(
    benchmarks: dict[str, float | int | None],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute market opportunity flags for a new seller."""
    cfg = config if isinstance(config, dict) else {}
    profiling_cfg = _config_section(cfg, "competitor_profiling")

    video_threshold = _coerce_float(profiling_cfg.get("video_present_rate_threshold", 0.6), 0.6)
    portfolio_threshold = _coerce_float(profiling_cfg.get("portfolio_present_rate_threshold", 0.6), 0.6)
    price_std_threshold = _coerce_float(profiling_cfg.get("price_std_threshold", 20.0), 20.0)

    gap_flags: list[str] = []
    score = 0.0

    video_rate = _safe_float(benchmarks.get("video_present_rate"))
    if video_rate is not None and video_rate < video_threshold:
        gap_flags.append("low_video_presence")
        score += 35.0

    portfolio_rate = _safe_float(benchmarks.get("portfolio_present_rate"))
    if portfolio_rate is not None and portfolio_rate < portfolio_threshold:
        gap_flags.append("low_portfolio_presence")
        score += 35.0

    price_std = _safe_float(benchmarks.get("price_std"))
    if price_std is not None and price_std > price_std_threshold:
        gap_flags.append("high_price_variance")
        score += 30.0

    return {
        "gap_flags": gap_flags,
        "opportunity_score": round(min(100.0, max(0.0, score)), 2),
    }


async def run_competitor_profiling_for_niche(
    niche_id: str,
    run_id: str,
    db: Any,
    config: dict[str, Any],
    llm_client: Any = None,
) -> dict[str, Any]:
    """Run Stage 10 competitor profiling for one niche."""
    _ = llm_client  # Reserved for future LLM-assisted gap synthesis.

    gig_df = load_gig_data_for_niche(niche_id=niche_id, run_id=run_id, db=db, config=config)
    if gig_df.empty:
        return {
            "niche_id": niche_id,
            "run_id": run_id,
            "profiled": False,
            "reason": "no_gig_data",
        }

    benchmarks = compute_market_benchmarks(gig_df)
    seller_df = load_seller_data_for_niche(
        niche_id=niche_id,
        run_id=run_id,
        db=db,
        seller_usernames=gig_df["seller_username"].dropna().astype(str).tolist(),
    )
    seller_distribution = compute_seller_level_distribution(seller_df) if not seller_df.empty else {}
    top_competitors = extract_top_n_competitor_gigs(gig_df, n=_resolve_top_competitor_gigs(config))
    gap_analysis = compute_new_seller_gap(benchmarks=benchmarks, config=config)

    write_competitor_profile(
        niche_id=niche_id,
        run_id=run_id,
        db=db,
        top_gig_count=len(top_competitors),
        median_price=_safe_float(benchmarks.get("median_price")),
        mean_price=_safe_float(benchmarks.get("mean_price")),
        price_std=_safe_float(benchmarks.get("price_std")),
        median_rating=_safe_float(benchmarks.get("median_rating")),
        mean_reviews=_safe_float(benchmarks.get("mean_reviews")),
        seller_level_distribution=seller_distribution or {"UNKNOWN": 1.0},
        min_delivery_days=_safe_int(benchmarks.get("min_delivery_days")),
        max_delivery_days=_safe_int(benchmarks.get("max_delivery_days")),
        video_present_rate=_safe_float(benchmarks.get("video_present_rate")),
        portfolio_present_rate=_safe_float(benchmarks.get("portfolio_present_rate")),
        new_seller_gap=gap_analysis,
    )

    result: dict[str, Any] = {
        "niche_id": niche_id,
        "run_id": run_id,
        "profiled": True,
        "top_gig_count": len(top_competitors),
        "benchmarks": benchmarks,
        "gap_flags": list(gap_analysis.get("gap_flags", [])),
        "opportunity_score": float(gap_analysis.get("opportunity_score", 0.0)),
        "top_competitor_gigs": top_competitors,
    }
    if seller_distribution:
        result["seller_level_distribution"] = seller_distribution
    return result


async def run_competitor_profiling_for_all_niches(
    run_id: str,
    db: Any,
    config: dict[str, Any],
    llm_client: Any = None,
) -> dict[str, Any]:
    """Run Stage 10 competitor profiling across all active niches."""
    results: list[dict[str, Any]] = []
    for niche_id in _extract_niche_ids(config):
        results.append(
            await run_competitor_profiling_for_niche(
                niche_id=niche_id,
                run_id=run_id,
                db=db,
                config=config,
                llm_client=llm_client,
            )
        )

    profiled_count = sum(1 for row in results if row.get("profiled") is True)
    return {
        "run_id": run_id,
        "niches_processed": len(results),
        "niches_profiled": profiled_count,
        "results": results,
    }

