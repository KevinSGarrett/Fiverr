"""Template rendering and contract checks for Stage 13 recommendation prompts."""

from __future__ import annotations

from pathlib import Path

from src.recommendations.contracts import RecommendationContext
from src.recommendations.llm_tasks import context_to_dict, load_template
from src.recommendations.template_validation import validate_template_has_json_instruction

TEMPLATE_NAMES = [
    "gig_titles.j2",
    "tag_sets.j2",
    "package_structure.j2",
    "description_outline.j2",
    "faq_entries.j2",
    "differentiation_angle.j2",
    "buyer_persona.j2",
    "thumbnail_direction.j2",
    "upsell_structure.j2",
    "red_flags.j2",
    "niche_viability.j2",
]


def _template_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "src" / "llm" / "templates" / "stage13_recommendations"


def _minimal_context() -> dict[str, object]:
    context = RecommendationContext(
        keyword_id=101,
        keyword_text="python automation",
        niche_id="1",
        niche_name="Automation",
        run_id="run-tpl-1",
        tag="STRONG GO",
        final_score=82.0,
        confidence_modifier=0.82,
        top_competitor_weaknesses=[],
    )
    return context_to_dict(context)


def _render(template_name: str, context: dict[str, object] | None = None) -> str:
    rendered = load_template(f"stage13_recommendations/{template_name}").render(**(context or _minimal_context()))
    assert rendered.strip()
    return rendered


def _assert_template_renders(template_name: str) -> None:
    rendered = _render(template_name)
    assert "Return JSON only. No preamble." in rendered


def test_gig_titles_renders_without_error() -> None:
    _assert_template_renders("gig_titles.j2")


def test_tag_sets_renders_without_error() -> None:
    _assert_template_renders("tag_sets.j2")


def test_package_structure_renders_without_error() -> None:
    _assert_template_renders("package_structure.j2")


def test_description_outline_renders_without_error() -> None:
    _assert_template_renders("description_outline.j2")


def test_faq_entries_renders_without_error() -> None:
    _assert_template_renders("faq_entries.j2")


def test_differentiation_angle_renders_without_error() -> None:
    _assert_template_renders("differentiation_angle.j2")


def test_buyer_persona_renders_without_error() -> None:
    _assert_template_renders("buyer_persona.j2")


def test_thumbnail_direction_renders_without_error() -> None:
    _assert_template_renders("thumbnail_direction.j2")


def test_upsell_structure_renders_without_error() -> None:
    _assert_template_renders("upsell_structure.j2")


def test_red_flags_renders_without_error() -> None:
    _assert_template_renders("red_flags.j2")


def test_niche_viability_renders_without_error() -> None:
    _assert_template_renders("niche_viability.j2")


def test_all_templates_present_on_disk() -> None:
    template_files = sorted(path.name for path in _template_dir().glob("*.j2"))
    assert template_files == sorted(TEMPLATE_NAMES)


def test_template_outputs_contain_json_instruction() -> None:
    for template_name in TEMPLATE_NAMES:
        rendered = _render(template_name)
        assert "Return JSON only. No preamble." in rendered


def test_all_templates_have_json_only_instruction() -> None:
    for template_name in TEMPLATE_NAMES:
        content = (_template_dir() / template_name).read_text(encoding="utf-8")
        assert validate_template_has_json_instruction(content) is True


def test_context_to_dict_provides_all_template_variables() -> None:
    mapped = _minimal_context()
    required = {
        "niche_name",
        "keyword_text",
        "cluster_label",
        "cluster_size",
        "total_result_count",
        "competition_score",
        "demand_score",
        "tag",
        "final_score",
        "top_competitor_weaknesses",
        "top_buyer_complaints",
        "hard_exclusions",
        "positioning_gaps",
        "cluster_synthesis_narrative",
        "top_buyer_praise",
        "trends_slope",
        "reddit_intent_score",
        "thumbnail_class_distribution",
        "competitor_extras",
        "starter_price_basic",
        "starter_price_standard",
        "starter_price_premium",
        "opportunity_score",
        "feasibility_score",
        "confidence_modifier",
        "trend_score",
        "saturation_score",
        "profitability_score",
        "weakness_score",
        "opportunity_narrative",
    }
    assert required.issubset(mapped.keys())


def test_gig_titles_template_handles_null_cluster() -> None:
    context = RecommendationContext(
        keyword_id=101,
        keyword_text="python automation",
        niche_id="1",
        niche_name="Automation",
        run_id="run-tpl-cluster-null",
        cluster_label=None,
        top_competitor_weaknesses=[],
    )
    rendered = _render("gig_titles.j2", context_to_dict(context))
    assert "unknown topic cluster" in rendered


def test_niche_viability_template_handles_missing_scores() -> None:
    context = RecommendationContext(
        keyword_id=101,
        keyword_text="python automation",
        niche_id="1",
        niche_name="Automation",
        run_id="run-tpl-no-scores",
        top_competitor_weaknesses=[],
    )
    rendered = _render("niche_viability.j2", context_to_dict(context))
    assert "N/A" in rendered
