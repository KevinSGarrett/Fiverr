"""Stage 11 gig-quality rubric analysis for top competitor gigs."""

from __future__ import annotations

from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.models.gig import Gig
from src.models.gig_quality_score import GigQualityScore
from src.models.market import Keyword, write_gig_quality_analysis
from src.models.niche import Niche
from src.models.search_result import SearchResult

_TOP_GIGS_PER_KEYWORD = 10
_RUBRIC_PENALTIES = {
    "video_absent": 25.0,
    "portfolio_absent": 20.0,
    "description_thin": 35.0,
    "faq_absent": 20.0,
}


def _is_session(db: Any) -> bool:
    return isinstance(db, Session)


def _resolve_niche_pk(niche_id: str, db: Any) -> int | None:
    if niche_id.isdigit():
        return int(niche_id)
    if not _is_session(db):
        return None
    row = db.query(Niche).filter(Niche.slug == niche_id).one_or_none()
    return None if row is None else int(row.id)


def _safe_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        normalized = value.strip().replace(",", "")
        if not normalized:
            return None
        try:
            return int(float(normalized))
        except ValueError:
            return None
    return None


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


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load_gig_quality_scores_for_niche(niche_id: str, run_id: str, db: Any) -> list[dict[str, Any]]:
    """
    Load run-scoped top-10 gig quality rows for one niche.

    Query contract:
    - joins `gig_quality_scores` to `gigs` via `gig_url`
    - scopes to current run_id and top-10 search ranks per keyword
    """
    if not _is_session(db):
        return []

    niche_pk = _resolve_niche_pk(niche_id, db)
    if niche_pk is None:
        return []

    rows = (
        db.query(
            Gig.gig_url.label("gig_url"),
            Gig.keyword_id.label("keyword_id"),
            Gig.gig_title_full.label("gig_title_full"),
            Gig.description_text.label("description_text"),
            Gig.faq_text.label("faq_text"),
            Gig.video_present.label("gig_video_present"),
            Gig.portfolio_count.label("gig_portfolio_count"),
            Gig.thumbnail_url.label("thumbnail_url"),
            SearchResult.rank.label("search_rank"),
            GigQualityScore.video_present.label("quality_video_present"),
            GigQualityScore.portfolio_count.label("quality_portfolio_count"),
            GigQualityScore.description_quality_score.label("description_quality_score"),
            GigQualityScore.faq_completeness_score.label("faq_completeness_score"),
            GigQualityScore.thumbnail_quality_score.label("thumbnail_quality_score"),
        )
        .join(Keyword, Keyword.id == Gig.keyword_id)
        .join(
            SearchResult,
            and_(
                SearchResult.gig_id == Gig.id,
                SearchResult.keyword_id == Gig.keyword_id,
                SearchResult.run_id == run_id,
            ),
        )
        .join(
            GigQualityScore,
            and_(
                GigQualityScore.gig_url == Gig.gig_url,
                GigQualityScore.run_id == run_id,
            ),
        )
        .filter(
            Keyword.niche_id == niche_pk,
            SearchResult.rank <= _TOP_GIGS_PER_KEYWORD,
        )
        .order_by(
            Keyword.id.asc(),
            SearchResult.rank.asc(),
            Gig.id.asc(),
        )
        .all()
    )

    if not rows:
        return []

    records: list[dict[str, Any]] = []
    keyword_counts: dict[int, int] = {}
    seen_per_keyword: dict[int, set[str]] = {}
    for row in rows:
        if row.keyword_id is None:
            continue
        keyword_id = int(row.keyword_id)
        gig_url = str(row.gig_url)
        seen = seen_per_keyword.setdefault(keyword_id, set())
        if gig_url in seen:
            continue
        if keyword_counts.get(keyword_id, 0) >= _TOP_GIGS_PER_KEYWORD:
            continue
        seen.add(gig_url)
        keyword_counts[keyword_id] = keyword_counts.get(keyword_id, 0) + 1
        records.append(
            {
                "gig_url": gig_url,
                "keyword_id": keyword_id,
                "gig_title_full": row.gig_title_full,
                "description_text": row.description_text,
                "faq_text": row.faq_text,
                "video_present": row.quality_video_present
                if row.quality_video_present is not None
                else row.gig_video_present,
                "portfolio_count": row.quality_portfolio_count
                if row.quality_portfolio_count is not None
                else row.gig_portfolio_count,
                "description_quality_score": row.description_quality_score,
                "faq_completeness_score": row.faq_completeness_score,
                "thumbnail_quality_score": row.thumbnail_quality_score,
                "thumbnail_url": row.thumbnail_url,
                "search_rank": row.search_rank,
            }
        )
    return records


def compute_rubric_score(gig_row: dict[str, Any], gig_quality_score_row: dict[str, Any]) -> dict[str, Any]:
    """Compute Stage 11 structural rubric score and weakness flags."""
    video_present = gig_quality_score_row.get("video_present")
    portfolio_count = _safe_int(gig_quality_score_row.get("portfolio_count"))
    description_text = gig_row.get("description_text")
    faq_text = gig_row.get("faq_text")
    thumbnail_quality_score = _safe_float(gig_quality_score_row.get("thumbnail_quality_score"))
    thumbnail_url = gig_row.get("thumbnail_url")
    description_quality_score = _safe_float(gig_quality_score_row.get("description_quality_score"))
    faq_completeness_score = _safe_float(gig_quality_score_row.get("faq_completeness_score"))

    video_absent = video_present is not True
    portfolio_absent = portfolio_count is None or portfolio_count <= 0

    # Blend text-length and quality score fallback to keep legacy rows scoreable.
    description_thin = not _has_text(description_text) or len(str(description_text).strip()) < 120
    if description_quality_score is not None and description_quality_score <= 3.0:
        description_thin = True

    faq_absent = not _has_text(faq_text)
    if faq_completeness_score is not None and faq_completeness_score <= 2.0:
        faq_absent = True

    thumbnail_quality_flag = (thumbnail_quality_score is not None and thumbnail_quality_score < 4.0) or (
        not _has_text(thumbnail_url)
    )

    flags: list[str] = []
    if video_absent:
        flags.append("video_absent")
    if portfolio_absent:
        flags.append("portfolio_absent")
    if description_thin:
        flags.append("description_thin")
    if faq_absent:
        flags.append("faq_absent")
    if thumbnail_quality_flag:
        flags.append("thumbnail_quality_flag")

    penalty = 0.0
    if video_absent:
        penalty += _RUBRIC_PENALTIES["video_absent"]
    if portfolio_absent:
        penalty += _RUBRIC_PENALTIES["portfolio_absent"]
    if description_thin:
        penalty += _RUBRIC_PENALTIES["description_thin"]
    if faq_absent:
        penalty += _RUBRIC_PENALTIES["faq_absent"]

    rubric_score = round(max(0.0, min(100.0, 100.0 - penalty)), 2)
    return {
        "rubric_score": rubric_score,
        "weakness_flags": flags,
        "video_absent": video_absent,
        "portfolio_absent": portfolio_absent,
        "description_thin": description_thin,
        "faq_absent": faq_absent,
        "thumbnail_quality_flag": thumbnail_quality_flag,
    }


async def run_gig_quality_analysis_for_niche(
    niche_id: str,
    run_id: str,
    db: Any,
    config: dict[str, Any],
    llm_client: Any = None,
) -> dict[str, Any]:
    """Run Stage 11 rubric analysis for one niche."""
    _ = (config, llm_client)
    rows = load_gig_quality_scores_for_niche(niche_id=niche_id, run_id=run_id, db=db)
    if not rows:
        return {
            "niche_id": niche_id,
            "run_id": run_id,
            "analyzed": False,
            "reason": "no_gig_quality_scores",
            "gigs_analyzed": 0,
        }

    for row in rows:
        score_payload = compute_rubric_score(gig_row=row, gig_quality_score_row=row)
        write_gig_quality_analysis(
            gig_url=str(row["gig_url"]),
            niche_id=niche_id,
            run_id=run_id,
            rubric_score=float(score_payload["rubric_score"]),
            video_absent=bool(score_payload["video_absent"]),
            portfolio_absent=bool(score_payload["portfolio_absent"]),
            description_thin=bool(score_payload["description_thin"]),
            faq_absent=bool(score_payload["faq_absent"]),
            thumbnail_quality_flag=bool(score_payload["thumbnail_quality_flag"]),
            weakness_flags=list(score_payload["weakness_flags"]),
            db=db,
            commit=False,
        )

    if _is_session(db):
        db.commit()

    return {
        "niche_id": niche_id,
        "run_id": run_id,
        "analyzed": True,
        "gigs_analyzed": len(rows),
    }


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


async def run_gig_quality_analysis_for_all_niches(
    run_id: str,
    db: Any,
    config: dict[str, Any],
    llm_client: Any = None,
) -> dict[str, Any]:
    """Run Stage 11 rubric analysis across all active niches."""
    results: list[dict[str, Any]] = []
    for niche_id in _extract_niche_ids(config):
        results.append(
            await run_gig_quality_analysis_for_niche(
                niche_id=niche_id,
                run_id=run_id,
                db=db,
                config=config,
                llm_client=llm_client,
            )
        )

    analyzed_count = sum(1 for result in results if result.get("analyzed") is True)
    return {
        "run_id": run_id,
        "niches_processed": len(results),
        "niches_analyzed": analyzed_count,
        "results": results,
    }

