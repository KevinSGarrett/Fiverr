"""TierD-2 live collection pilot orchestration and guardrails."""

from __future__ import annotations

import json
import logging
import uuid
from html import unescape
from typing import Any

from src.collection.pilot_logger import PilotLogger

log = logging.getLogger(__name__)

DEFAULT_BUDGET_CREDITS = 500
PILOT_EVIDENCE_PATH = "data/live_validation_evidence.json"


async def run_live_collection_pilot(
    niche_id: str,
    budget_credits: int = DEFAULT_BUDGET_CREDITS,
    database_url: str | None = None,
    config_path: str = "config.yaml",
    log_path: str = "data/live_pilot_log.jsonl",
    evidence_path: str = PILOT_EVIDENCE_PATH,
) -> dict[str, Any]:
    """
    Run controlled one-niche live collection with runtime-only ScrapFly overrides.

    TierD-2 controls:
    - one niche scope
    - hard credit ceiling
    - persistent request logging/evidence
    - explicit stop reasons for session/budget/pipeline failures
    - isolated pilot DB path
    """
    from src.collection.orchestrator import run_collection_pipeline
    from src.collection.scrapfly_client import ScrapFlyRateLimitError
    from src.collection.session_manager import SessionManager
    from src.config import ConfigLoader
    from src.models.database import (
        create_session_factory,
        get_session,
        initialize_database,
        normalize_database_url,
    )

    db_url = database_url or f"sqlite:///data/live_pilot_{niche_id}.db"
    result: dict[str, Any] = {
        "run_id": None,
        "niche_id": niche_id,
        "db_url": db_url,
        "budget_credits": budget_credits,
        "success": False,
        "credits_used": 0,
        "gigs_collected": 0,
        "search_results": 0,
        "keywords_found": 0,
        "errors": [],
        "stop_reason": None,
        "evidence_path": evidence_path,
    }

    logger_obj: PilotLogger | None = None
    session_manager: SessionManager | None = None

    try:
        normalized_url = normalize_database_url(db_url)
        engine = initialize_database(database_url=normalized_url)
        _seed_pilot_niche(niche_id, engine)
        session_factory = create_session_factory(engine)

        config = ConfigLoader(config_path).load()
        config_payload = config.model_dump() if hasattr(config, "model_dump") else {}
        if not isinstance(config_payload, dict):
            config_payload = {}

        # Runtime-only override (config.yaml stays false in git).
        config_payload.setdefault("collection", {})
        if not isinstance(config_payload["collection"], dict):
            config_payload["collection"] = {}
        config_payload["collection"].setdefault("scrapfly", {})
        if not isinstance(config_payload["collection"]["scrapfly"], dict):
            config_payload["collection"]["scrapfly"] = {}
        config_payload["collection"]["scrapfly"]["enabled"] = True
        config_payload["collection"]["scrapfly"]["cost_budget_credits"] = budget_credits

        # One niche only.
        niches = config_payload.get("niches", [])
        if isinstance(niches, list):
            filtered_niches = [
                niche
                for niche in niches
                if isinstance(niche, dict) and niche.get("niche_id") == niche_id
            ]
            for niche in filtered_niches:
                niche["external_sources"] = {
                    "google_trends": False,
                    "reddit": False,
                    "youtube": False,
                }
            config_payload["niches"] = filtered_niches

        logger_obj = PilotLogger(log_path=log_path)
        run_id = f"pilot-{niche_id}-{uuid.uuid4().hex[:8]}"
        result["run_id"] = run_id

        session_manager = SessionManager(config)

        # SessionManager in this repo exposes is_session_valid() rather than ensure_session().
        is_valid = await session_manager.is_session_valid()
        if not is_valid:
            result["errors"].append("Session validation failed.")
            result["stop_reason"] = "session_expired"
            return result

        try:
            with get_session(session_factory) as db:
                summary = await run_collection_pipeline(
                    run_id=run_id,
                    db=db,
                    config=config_payload,
                    session_manager=session_manager,
                    dry_run=False,
                )
                gigs_backfilled = _backfill_gigs_from_search_results(db=db, run_id=run_id, max_cards=25)
            result["success"] = True
            result["errors"] = list(summary.get("errors", []))
            result["gigs_collected"] = gigs_backfilled
            result["search_results"] = int(summary.get("search_jobs_run", 0))
            result["keywords_found"] = int(summary.get("search_jobs_run", 0))
        except ScrapFlyRateLimitError as exc:
            result["errors"].append(str(exc))
            result["stop_reason"] = "budget_exceeded"
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(str(exc))
            result["stop_reason"] = "pipeline_error"
    except Exception as exc:  # noqa: BLE001
        result["errors"].append(f"Setup error: {exc}")
        result["stop_reason"] = "setup_error"
    finally:
        if session_manager is not None:
            await session_manager.close()

        try:
            evidence_logger = logger_obj if logger_obj is not None else PilotLogger(log_path=log_path)
            evidence = evidence_logger.write_evidence_bundle(evidence_path, extra=result)
            result["credits_used"] = int(evidence.get("total_credits_used", 0))
        except Exception as exc:  # noqa: BLE001
            log.warning("Failed to write pilot evidence bundle: %s", exc)

    return result


def _seed_pilot_niche(niche_id: str, engine: Any) -> None:
    """Ensure niche exists in pilot DB, seeded from config if available."""
    from src.config import ConfigLoader
    from src.models.database import create_session_factory, get_session
    from src.models.niche import Niche

    session_factory = create_session_factory(engine)
    config = ConfigLoader("config.yaml").load()
    payload = config.model_dump() if hasattr(config, "model_dump") else {}
    niche_cfg: dict[str, Any] = {}
    if isinstance(payload, dict):
        for record in payload.get("niches", []):
            if isinstance(record, dict) and record.get("niche_id") == niche_id:
                niche_cfg = record
                break

    with get_session(session_factory) as db:
        existing = db.query(Niche).filter(Niche.slug == niche_id).first()
        if existing is None:
            db.add(
                Niche(
                    slug=niche_id,
                    name=niche_cfg.get("name", niche_id.replace("_", " ").title()),
                    category_path=niche_cfg.get("category_path", "uncategorized"),
                    is_active=True,
                )
            )
            db.commit()
            log.info("Seeded pilot niche: %s", niche_id)


def _backfill_gigs_from_search_results(db: Any, run_id: str, max_cards: int = 25) -> int:
    """Persist minimal gig rows from Stage-3 search cards when Stage-4 is sparse."""
    from sqlalchemy.orm import Session

    from src.models.gig import Gig
    from src.models.search_result import SearchResult

    if not isinstance(db, Session):
        return 0

    search_rows = (
        db.query(SearchResult)
        .filter(SearchResult.run_id == run_id)
        .order_by(SearchResult.id.desc())
        .all()
    )
    upserts = 0
    for row in search_rows:
        cards_raw = row.gig_cards
        cards: list[dict[str, Any]] = []
        if isinstance(cards_raw, list):
            cards = [value for value in cards_raw if isinstance(value, dict)]
        elif isinstance(cards_raw, str):
            try:
                loaded = json.loads(cards_raw)
                if isinstance(loaded, list):
                    cards = [value for value in loaded if isinstance(value, dict)]
            except json.JSONDecodeError:
                continue

        for card in cards:
            if upserts >= max_cards:
                break
            gig_url = unescape(str(card.get("gig_url", "")).strip())
            if not gig_url:
                continue

            seller_username = str(card.get("seller_username", "")).strip() or "unknown_seller"
            existing = db.query(Gig).filter(Gig.gig_url == gig_url).one_or_none()
            if existing is None:
                existing = Gig(gig_url=gig_url, seller_username=seller_username)
                db.add(existing)

            existing.run_id = run_id
            existing.keyword_id = row.keyword_id if isinstance(row.keyword_id, int) and row.keyword_id > 0 else None
            existing.seller_username = seller_username
            existing.position = (
                int(card.get("position")) if isinstance(card.get("position"), (int, float)) else existing.position
            )
            existing.starting_price = (
                float(card.get("starting_price"))
                if isinstance(card.get("starting_price"), (int, float))
                else existing.starting_price
            )
            existing.gig_title_full = str(card.get("gig_title")) if card.get("gig_title") else existing.gig_title_full
            existing.title = existing.gig_title_full
            existing.sponsored_flag = bool(card.get("sponsored_flag", False))
            existing.detail_collected = bool(existing.detail_collected)
            upserts += 1
        if upserts >= max_cards:
            break

    db.commit()
    return int(db.query(Gig).count())
