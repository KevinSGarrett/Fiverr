"""Recommendation export helpers for Stage 13 outputs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.models import Keyword, Niche, Recommendation
from src.recommendations.schemas import RecommendationOutput
from src.recommendations.storage import get_recommendation

_ERROR_MARKDOWN_TITLE = "# Recommendation Export Error"


@dataclass(slots=True)
class RecommendationExportMetadata:
    keyword_text: str
    tag: str
    final_score: float
    niche_name: str
    generated_at: datetime | None
    llm_cost_usd: float
    generation_complete: bool


async def export_recommendation_markdown(recommendation_id: str, db: Any) -> str:
    """Exports a recommendation as formatted Markdown per RECOMMENDATION_OUTPUT_FORMAT.md spec."""
    keyword_id = _parse_keyword_id(recommendation_id)
    if keyword_id is None:
        return _error_markdown(f"Invalid recommendation id '{recommendation_id}'. Expected keyword id.")

    metadata = _load_export_metadata(keyword_id=keyword_id, db=db)
    if metadata is None:
        return _error_markdown(f"Recommendation not found for keyword_id={keyword_id}.")
    if not metadata.generation_complete:
        return _error_markdown(f"Recommendation for keyword_id={keyword_id} is not generation_complete.")

    recommendation = get_recommendation(keyword_id=keyword_id, db=db)
    if recommendation is None:
        return _error_markdown(f"Recommendation payload unavailable for keyword_id={keyword_id}.")

    return _render_markdown(recommendation=recommendation, metadata=metadata)


async def export_recommendation_by_keyword(
    keyword_id: int,
    niche_id: str,
    run_id: str,
    db: Any,
) -> tuple[str, str | None]:
    """Returns (markdown_string, error_message_or_none)."""
    del niche_id, run_id
    markdown = await export_recommendation_markdown(recommendation_id=str(keyword_id), db=db)
    if _is_error_markdown(markdown):
        return "", _extract_error_message(markdown)
    return markdown, None


async def export_recommendation_json(recommendation_id: str, db: Any) -> dict[str, Any]:
    """Exports recommendation as JSON dict. Stub returns {}."""
    del recommendation_id, db
    return {}


def _render_markdown(recommendation: RecommendationOutput, metadata: RecommendationExportMetadata) -> str:
    output_sections: list[str] = [
        f"# Recommendation: {metadata.keyword_text}",
        f"**Tag:** {metadata.tag} | **Score:** {metadata.final_score:.1f} | **Niche:** {metadata.niche_name}",
        "## Viability Assessment\n" + _render_viability_section(recommendation),
        "## Gig Title Options\n" + _render_gig_titles_section(recommendation),
        "## Packages\n" + _render_packages_section(recommendation),
        "## Differentiation Angle\n" + _render_differentiation_section(recommendation),
        "## FAQ\n" + _render_faq_section(recommendation),
        "## Buyer Persona\n" + _render_buyer_persona_section(recommendation),
        "## Thumbnail Direction\n" + _render_thumbnail_direction_section(recommendation),
        "## Red Flags\n" + _render_red_flags_section(recommendation),
    ]

    llm_cost_usd = metadata.llm_cost_usd if metadata.llm_cost_usd > 0 else float(recommendation.total_llm_cost_usd)
    generated_label = metadata.generated_at.strftime("%Y-%m-%d %H:%M") if metadata.generated_at is not None else "N/A"
    output_sections.append("---")
    output_sections.append(
        f"_Generated: {generated_label} | Estimated LLM Cost: ${llm_cost_usd:.4f} | "
        f"Completeness: {_safe_completeness_ratio(recommendation):.0%}_"
    )
    return "\n\n".join(output_sections)


def _render_viability_section(recommendation: RecommendationOutput) -> str:
    viability = recommendation.niche_viability
    if viability is None:
        return _missing_section_message("Viability Assessment")
    return viability.viability_assessment


def _render_gig_titles_section(recommendation: RecommendationOutput) -> str:
    gig_titles = recommendation.gig_titles
    if gig_titles is None or not gig_titles.titles:
        return _missing_section_message("Gig Title Options")
    return "\n".join(f"{index}. {title.title}" for index, title in enumerate(gig_titles.titles, start=1))


def _render_packages_section(recommendation: RecommendationOutput) -> str:
    package_structure = recommendation.package_structure
    if package_structure is None:
        return _missing_section_message("Packages")

    lines = [
        "| Tier | Price | Deliverables | Delivery | Revisions |",
        "|---|---|---|---|---|",
        _package_tier_row("Basic", package_structure.basic),
        _package_tier_row("Standard", package_structure.standard),
        _package_tier_row("Premium", package_structure.premium),
    ]
    return "\n".join(lines)


def _render_differentiation_section(recommendation: RecommendationOutput) -> str:
    differentiation = recommendation.differentiation_angle
    if differentiation is None:
        return _missing_section_message("Differentiation Angle")

    lines = [differentiation.positioning_statement, "", "**Tactical Actions:**"]
    if not differentiation.differentiators:
        lines.append("- No tactical actions were generated.")
        return "\n".join(lines)

    lines.extend(f"- {differentiator.action}" for differentiator in differentiation.differentiators)
    return "\n".join(lines)


def _render_faq_section(recommendation: RecommendationOutput) -> str:
    faq_entries = recommendation.faq_entries
    if faq_entries is None or not faq_entries.faq_entries:
        return _missing_section_message("FAQ")

    lines: list[str] = []
    for entry in faq_entries.faq_entries:
        lines.append(f"**Q: {entry.question}**")
        lines.append(f"A: {entry.answer}")
        lines.append("")

    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def _render_buyer_persona_section(recommendation: RecommendationOutput) -> str:
    persona = recommendation.buyer_persona
    if persona is None:
        return _missing_section_message("Buyer Persona")

    lines = [
        f"{persona.name} — {persona.role}, {persona.company_stage}",
        "",
        "**Pain Points:**",
    ]
    lines.extend(f"- {pain_point}" for pain_point in persona.pain_points)
    lines.append(f"**Budget:** {persona.budget_range}")
    lines.append(f"**Decision Trigger:** {persona.decision_trigger}")
    return "\n".join(lines)


def _render_thumbnail_direction_section(recommendation: RecommendationOutput) -> str:
    thumbnail_direction = recommendation.thumbnail_direction
    if thumbnail_direction is None:
        return _missing_section_message("Thumbnail Direction")

    include = ", ".join(thumbnail_direction.elements_to_include)
    avoid = ", ".join(thumbnail_direction.elements_to_avoid)
    lines = [
        thumbnail_direction.concept,
        f"**Style:** {thumbnail_direction.style}",
        f"**Elements to Include:** {include}",
        f"**Elements to Avoid:** {avoid}",
        f"**Differentiation Note:** {thumbnail_direction.differentiation_note}",
    ]
    return "\n".join(lines)


def _render_red_flags_section(recommendation: RecommendationOutput) -> str:
    red_flags = recommendation.red_flags
    if red_flags is None:
        return _missing_section_message("Red Flags")

    if not red_flags.red_flags:
        return "No critical red flags were generated."

    lines: list[str] = []
    for red_flag in red_flags.red_flags:
        lines.append(f"- ⚠ {red_flag.severity}: {red_flag.description}")
        lines.append(f"  → {red_flag.mitigation}")
    return "\n".join(lines)


def _package_tier_row(label: str, tier: Any) -> str:
    deliverables = ", ".join(str(item) for item in getattr(tier, "deliverables", []))
    price_text = _format_price(getattr(tier, "price", 0))
    delivery_days = int(getattr(tier, "delivery_days", 0))
    revisions = int(getattr(tier, "revisions", 0))
    return f"| {label} | {price_text} | {deliverables} | {delivery_days} days | {revisions} |"


def _format_price(value: Any) -> str:
    numeric_price = _to_float(value, 0.0)
    if numeric_price.is_integer():
        return f"${int(numeric_price)}"
    return f"${numeric_price:.2f}"


def _missing_section_message(section_name: str) -> str:
    return f"_{section_name} not available — task failed or data insufficient._"


def _parse_keyword_id(recommendation_id: str) -> int | None:
    try:
        keyword_id = int(str(recommendation_id).strip())
    except (TypeError, ValueError):
        return None
    if keyword_id <= 0:
        return None
    return keyword_id


def _load_export_metadata(keyword_id: int, db: Any) -> RecommendationExportMetadata | None:
    query = _safe_query(db, Recommendation)
    if query is None:
        return None

    row = query.filter(Recommendation.keyword_id == keyword_id).order_by(Recommendation.created_at.desc()).first()
    if row is None:
        return None

    raw_json = getattr(row, "raw_json", {})
    generation_complete = bool(getattr(row, "generation_complete", False))
    if not generation_complete and isinstance(raw_json, Mapping):
        generation_complete = bool(raw_json.get("generation_complete", False))

    keyword_text = (
        _as_non_empty_text(getattr(row, "recommendation_text", None))
        or _as_non_empty_text(_mapping_value(raw_json, "keyword_text"))
        or _lookup_keyword_text(keyword_id=keyword_id, db=db)
        or f"keyword-{keyword_id}"
    )
    niche_name = (
        _as_non_empty_text(_mapping_value(raw_json, "niche_name"))
        or _lookup_niche_name(row=row, keyword_id=keyword_id, db=db)
        or "Unknown Niche"
    )
    tag = _as_non_empty_text(getattr(row, "tag", None)) or _as_non_empty_text(_mapping_value(raw_json, "tag")) or "UNKNOWN"
    final_score = _to_float(getattr(row, "final_score", None), _to_float(_mapping_value(raw_json, "final_score"), 0.0))
    llm_cost_usd = _to_float(
        getattr(row, "llm_cost_usd", None),
        _to_float(_mapping_value(raw_json, "total_llm_cost_usd"), _to_float(_mapping_value(raw_json, "llm_cost_usd"), 0.0)),
    )
    generated_at = _coerce_datetime(getattr(row, "generated_at", None))
    if generated_at is None:
        generated_at = _coerce_datetime(_mapping_value(raw_json, "generated_at"))

    return RecommendationExportMetadata(
        keyword_text=keyword_text,
        tag=tag,
        final_score=final_score,
        niche_name=niche_name,
        generated_at=generated_at,
        llm_cost_usd=llm_cost_usd,
        generation_complete=generation_complete,
    )


def _safe_query(db: Any, model: Any) -> Any | None:
    query_fn = getattr(db, "query", None)
    if query_fn is None:
        return None
    try:
        return query_fn(model)
    except Exception:
        return None


def _lookup_keyword_text(keyword_id: int, db: Any) -> str | None:
    query = _safe_query(db, Keyword)
    if query is None:
        return None
    row = query.filter(Keyword.id == keyword_id).first()
    if row is None:
        return None
    return _as_non_empty_text(getattr(row, "keyword", None))


def _lookup_niche_name(row: Any, keyword_id: int, db: Any) -> str | None:
    raw_niche_id = getattr(row, "niche_id", None)
    niche_id = _to_optional_int(raw_niche_id)
    if niche_id is None:
        keyword_query = _safe_query(db, Keyword)
        if keyword_query is not None:
            keyword_row = keyword_query.filter(Keyword.id == keyword_id).first()
            if keyword_row is not None:
                niche_id = _to_optional_int(getattr(keyword_row, "niche_id", None))
    if niche_id is None:
        return _as_non_empty_text(raw_niche_id)

    niche_query = _safe_query(db, Niche)
    if niche_query is None:
        return str(niche_id)
    niche_row = niche_query.filter(Niche.id == niche_id).first()
    if niche_row is None:
        return str(niche_id)
    return _as_non_empty_text(getattr(niche_row, "name", None)) or str(niche_id)


def _to_optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_non_empty_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    return text


def _coerce_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _mapping_value(value: Any, key: str) -> Any:
    if not isinstance(value, Mapping):
        return None
    return value.get(key)


def _safe_completeness_ratio(recommendation: RecommendationOutput) -> float:
    ratio = recommendation.completeness_ratio()
    if ratio < 0:
        return 0.0
    if ratio > 1:
        return 1.0
    return ratio


def _error_markdown(message: str) -> str:
    return f"{_ERROR_MARKDOWN_TITLE}\n\n{message}"


def _is_error_markdown(markdown: str) -> bool:
    return markdown.startswith(_ERROR_MARKDOWN_TITLE)


def _extract_error_message(markdown: str) -> str:
    lines = [line.strip() for line in markdown.splitlines() if line.strip()]
    if len(lines) >= 2:
        return lines[1]
    if lines:
        return lines[0]
    return "Recommendation export failed."


__all__ = [
    "export_recommendation_markdown",
    "export_recommendation_by_keyword",
    "export_recommendation_json",
]
