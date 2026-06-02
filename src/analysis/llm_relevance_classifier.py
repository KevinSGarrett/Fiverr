"""LLM relevance classification for Stage 7.5 ambiguous RSV keywords."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from src.models import Keyword, SearchResult

if TYPE_CHECKING:
    from openai import OpenAI
    from sqlalchemy import Engine

    from src.config.models import RelevanceConfig

log = logging.getLogger(__name__)

NICHE_EXPECTED_SERVICE_DESCRIPTIONS: dict[str, str] = {
    "prd_ai_saas": "AI SaaS product requirements document (PRD) writing",
    "support_kb_readiness": "Knowledge base or help center documentation setup",
    "gumloop_lindy_workflow": "Gumloop or Lindy AI workflow automation",
    "mcp_ai_agent": "Model Context Protocol (MCP) AI agent development",
    "python_automation": "Python scripting or task automation",
    "ai_tool_llm_integration": "LLM API or AI tool integration (OpenAI, Anthropic, etc.)",
    "ai_agent_development": "Autonomous AI agent development",
    "workflow_automation": "Business process or workflow automation",
    "python_web_scraping": "Python-based web scraping or data extraction",
}


@dataclass(slots=True)
class LLMRelevanceConfig:
    enabled: bool = False
    call_budget_per_run: int = 50
    model: str = "gpt-4o-mini"
    trigger_band_low: float = 0.40
    trigger_band_high: float = 0.70

    @classmethod
    def from_relevance_config(cls, relevance_cfg: RelevanceConfig | dict[str, object]) -> LLMRelevanceConfig:
        if isinstance(relevance_cfg, dict):
            llm_cfg = relevance_cfg.get("llm", {})
            llm_enabled = bool(relevance_cfg.get("llm_relevance_enabled", False))
            if not isinstance(llm_cfg, dict):
                llm_cfg = {}
            return cls(
                enabled=llm_enabled and bool(llm_cfg.get("enabled", False)),
                call_budget_per_run=int(llm_cfg.get("call_budget_per_run", 50)),
                model=str(llm_cfg.get("model", "gpt-4o-mini")),
                trigger_band_low=float(llm_cfg.get("trigger_band_low", 0.40)),
                trigger_band_high=float(llm_cfg.get("trigger_band_high", 0.70)),
            )

        llm_cfg_obj = relevance_cfg.llm
        return cls(
            enabled=bool(relevance_cfg.llm_relevance_enabled and llm_cfg_obj.enabled),
            call_budget_per_run=int(llm_cfg_obj.call_budget_per_run),
            model=str(llm_cfg_obj.model),
            trigger_band_low=float(llm_cfg_obj.trigger_band_low),
            trigger_band_high=float(llm_cfg_obj.trigger_band_high),
        )


def _should_run_llm(rsv_score: float, band_low: float = 0.40, band_high: float = 0.70) -> bool:
    """Return True iff RSV score is in the ambiguous band [band_low, band_high)."""
    return band_low <= rsv_score < band_high


def _extract_top_gig_titles(session: Session, keyword_id: int) -> list[str]:
    rows = (
        session.query(SearchResult)
        .filter(SearchResult.keyword_id == keyword_id)
        .order_by(SearchResult.collected_at.desc(), SearchResult.id.desc())
        .all()
    )
    titles: list[str] = []
    for row in rows:
        cards = row.gig_cards if isinstance(row.gig_cards, list) else []
        for card in cards:
            if not isinstance(card, dict):
                continue
            title = card.get("gig_title")
            if isinstance(title, str) and title.strip():
                titles.append(title.strip())
            if len(titles) >= 10:
                return titles
    return titles


def _build_openai_client() -> OpenAI | None:
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key.startswith("sk-"):
        log.warning("OPENAI_API_KEY missing/invalid for Stage 7.5, defaulting to RELEVANT.")
        return None
    return OpenAI(api_key=api_key)


def classify_gig_relevance(
    gig_titles: list[str],
    niche_id: str,
    keyword_text: str,
    client: OpenAI,
    model: str = "gpt-4o-mini",
) -> str:
    """Classify whether the titles are relevant; degrade safely to RELEVANT on failure."""
    expected = NICHE_EXPECTED_SERVICE_DESCRIPTIONS.get(niche_id, "the described service")
    titles_text = "\n".join(f"- {t}" for t in gig_titles[:10]) if gig_titles else "- (no titles available)"
    prompt = (
        f"Keyword: {keyword_text}\n"
        f"Expected service: {expected}\n"
        f"Top gig titles:\n{titles_text}"
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Fiverr gig relevance classifier. Determine if the listed gigs provide "
                        "the expected service or are incidental hits from a tangential market. "
                        "Reply with exactly one word: RELEVANT or NOT_RELEVANT."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=10,
            temperature=0.0,
        )
        verdict = (response.choices[0].message.content or "").strip().upper()
        return verdict if verdict in {"RELEVANT", "NOT_RELEVANT"} else "RELEVANT"
    except Exception as exc:  # noqa: BLE001
        log.warning("LLM classify_gig_relevance failed for %s/%s: %s", niche_id, keyword_text, exc)
        return "RELEVANT"


class LLMRelevanceClassifier:
    """Stateful classifier that enforces per-run call budget."""

    def __init__(self, config: LLMRelevanceConfig, client: OpenAI | None = None) -> None:
        self.config = config
        self.client = client if client is not None else _build_openai_client()
        self.calls_used = 0
        self._budget_exhausted_logged = False

    def classify_with_budget(self, gig_titles: list[str], niche_id: str, keyword_text: str) -> str:
        if self.calls_used >= self.config.call_budget_per_run:
            if not self._budget_exhausted_logged:
                log.warning("LLM call budget exhausted — remaining keywords treated as RELEVANT")
                self._budget_exhausted_logged = True
            return "RELEVANT"
        if self.client is None:
            return "RELEVANT"
        self.calls_used += 1
        return classify_gig_relevance(
            gig_titles=gig_titles,
            niche_id=niche_id,
            keyword_text=keyword_text,
            client=self.client,
            model=self.config.model,
        )

    def classify_keyword(self, session: Session, keyword_id: int) -> str | None:
        from src.scoring.result_set_relevance import get_result_set_validation

        rsv = get_result_set_validation(keyword_id, session)
        if rsv is None or rsv.result_set_relevance_score is None:
            return None
        if not _should_run_llm(
            float(rsv.result_set_relevance_score),
            band_low=self.config.trigger_band_low,
            band_high=self.config.trigger_band_high,
        ):
            return None

        keyword = session.query(Keyword).filter(Keyword.id == keyword_id).first()
        if keyword is None:
            return None
        verdict = self.classify_with_budget(
            gig_titles=_extract_top_gig_titles(session, keyword_id=keyword_id),
            niche_id=str(keyword.niche_id),
            keyword_text=keyword.keyword,
        )
        if verdict == "NOT_RELEVANT":
            rsv.ghost_market_flag = True
            rsv.relevance_deduction = min(float(rsv.relevance_deduction or 0.0), -0.50)
            keyword.ghost_market_flag = True
            log.warning("Stage 7.5 marked keyword_id=%s as NOT_RELEVANT (ghost-block path).", keyword_id)
        session.flush()
        return verdict


def run_stage_7_5(keyword_id: int, engine: Engine, config: LLMRelevanceConfig) -> str | None:
    """Run Stage 7.5 for a single keyword using a standalone DB session."""
    if not config.enabled:
        return None
    with Session(engine) as session:
        classifier = LLMRelevanceClassifier(config=config)
        verdict = classifier.classify_keyword(session=session, keyword_id=keyword_id)
        session.commit()
        return verdict

