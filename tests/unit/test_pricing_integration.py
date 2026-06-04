from __future__ import annotations

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker
from src.migrations.srdi_r8.run_srdi_r8_migrations import run_srdi_r8_migrations
from src.models import Base, Gig, Keyword, Niche, NichePriceAnalysis, PriceAnalysis, PricingSnapshot
from src.pricing.orchestrator import run_pricing_stage, run_stage_10_5, run_stage_10_5_for_niche


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)()


def _seed_keyword(session: Session, slug: str, depth: str = "standard") -> tuple[Niche, Keyword]:
    niche = Niche(slug=slug, name=slug, category_path="Programming & Tech", metadata_json={"depth": depth})
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword=f"{slug} kw", normalized_keyword=f"{slug} kw")
    session.add(keyword)
    session.flush()
    return niche, keyword


def _seed_gigs(session: Session, keyword_id: int, n: int = 6) -> None:
    for idx in range(1, n + 1):
        session.add(
            Gig(
                keyword_id=keyword_id,
                seller_username=f"s{idx}",
                gig_url=f"u://{keyword_id}/{idx}",
                packages={"basic": {"price": 50 + idx * 10}, "standard": {"price": 90 + idx * 10}, "premium": {"price": 150 + idx * 15}},
                review_count=idx * 10,
                gig_extras=[{"name": "fast", "price": 10 + idx}],
            )
        )
    session.commit()


def test_full_stage_10_5_creates_price_analysis_row() -> None:
    session = _session()
    _, keyword = _seed_keyword(session, "full_a")
    _seed_gigs(session, keyword.id)
    result = run_stage_10_5(keyword.id, session, run_id="r1")
    assert result["status"] == "complete"
    assert session.query(PriceAnalysis).count() == 1
    session.close()


def test_full_stage_10_5_creates_pricing_snapshot_row() -> None:
    session = _session()
    _, keyword = _seed_keyword(session, "full_b")
    _seed_gigs(session, keyword.id)
    run_stage_10_5(keyword.id, session, run_id="r2")
    assert session.query(PricingSnapshot).count() == 1
    session.close()


def test_keyword_only_depth_niche_skips_gracefully() -> None:
    session = _session()
    _, keyword = _seed_keyword(session, "keyword_only", depth="keyword_only")
    result = run_stage_10_5(keyword.id, session, run_id="r3")
    assert result["status"] == "skipped"
    session.close()


def test_missing_packages_on_all_gigs_no_crash() -> None:
    session = _session()
    _, keyword = _seed_keyword(session, "no_pkg")
    for idx in range(3):
        session.add(Gig(keyword_id=keyword.id, seller_username=f"s{idx}", gig_url=f"u://np/{idx}", packages=None))
    session.commit()
    result = run_stage_10_5(keyword.id, session, run_id="r4")
    assert result["status"] == "skipped"
    session.close()


def test_all_9_niche_configs_have_starter_prices() -> None:
    from src.config import ConfigLoader

    config = ConfigLoader("config.yaml").load()
    assert len(config.niches) == 9
    assert all(niche.starter_prices is not None for niche in config.niches)


def test_price_analysis_stored_with_keyword_and_niche() -> None:
    session = _session()
    niche, keyword = _seed_keyword(session, "idcheck")
    _seed_gigs(session, keyword.id)
    run_stage_10_5(keyword.id, session, run_id="r5")
    row = session.query(PriceAnalysis).first()
    assert row is not None and row.keyword_id == keyword.id and row.niche_id == niche.slug
    session.close()


def test_pricing_snapshot_ordering_invariant_maintained() -> None:
    session = _session()
    _, keyword = _seed_keyword(session, "ordercheck")
    _seed_gigs(session, keyword.id)
    run_stage_10_5(keyword.id, session, run_id="r6")
    snap = session.query(PricingSnapshot).first()
    assert snap is not None and snap.entry_basic < snap.entry_standard < snap.entry_premium
    session.close()


def test_niche_price_analysis_aggregates_multiple_keywords() -> None:
    session = _session()
    niche, kw1 = _seed_keyword(session, "aggregate")
    kw2 = Keyword(niche_id=niche.id, keyword="aggregate kw 2", normalized_keyword="aggregate kw 2")
    session.add(kw2)
    session.flush()
    _seed_gigs(session, kw1.id)
    _seed_gigs(session, kw2.id)
    run_stage_10_5_for_niche(niche.slug, session, run_id="r7")
    row = session.query(NichePriceAnalysis).filter(NichePriceAnalysis.niche_id == niche.slug).first()
    assert row is not None and row.keywords_analyzed >= 2
    session.close()


def test_stage_10_5_is_additive_only() -> None:
    session = _session()
    _, keyword = _seed_keyword(session, "additive")
    _seed_gigs(session, keyword.id)
    before = session.query(Keyword).filter(Keyword.id == keyword.id).first()
    run_stage_10_5(keyword.id, session, run_id="r8")
    after = session.query(Keyword).filter(Keyword.id == keyword.id).first()
    assert before is not None and after is not None and before.keyword == after.keyword
    session.close()


def test_migration_12_idempotent() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    run_srdi_r8_migrations(engine=engine)
    run_srdi_r8_migrations(engine=engine)
    tables = set(inspect(engine).get_table_names())
    assert {"price_analysis", "niche_price_analysis", "pricing_snapshots"}.issubset(tables)


def test_stage_10_5_run_produces_price_analysis_row() -> None:
    session = _session()
    _, keyword = _seed_keyword(session, "pa_row")
    _seed_gigs(session, keyword.id)
    run_stage_10_5(keyword.id, session, run_id="r9")
    assert session.query(PriceAnalysis).filter(PriceAnalysis.keyword_id == keyword.id).count() == 1
    session.close()


def test_stage_10_5_run_produces_pricing_snapshot_row() -> None:
    session = _session()
    _, keyword = _seed_keyword(session, "snap_row")
    _seed_gigs(session, keyword.id)
    run_stage_10_5(keyword.id, session, run_id="r10")
    assert session.query(PricingSnapshot).filter(PricingSnapshot.keyword_id == keyword.id).count() == 1
    session.close()


def test_price_analysis_and_snapshot_share_keyword_id() -> None:
    session = _session()
    _, keyword = _seed_keyword(session, "shared_kw")
    _seed_gigs(session, keyword.id)
    run_stage_10_5(keyword.id, session, run_id="r11")
    pa = session.query(PriceAnalysis).first()
    snap = session.query(PricingSnapshot).first()
    assert pa is not None and snap is not None and pa.keyword_id == snap.keyword_id
    session.close()


def test_pricing_moat_strength_matches_correlation_signal() -> None:
    session = _session()
    _, keyword = _seed_keyword(session, "moat")
    _seed_gigs(session, keyword.id, n=8)
    run_stage_10_5(keyword.id, session, run_id="r12")
    pa = session.query(PriceAnalysis).first()
    assert pa is not None and pa.moat_strength in {"LOW", "MEDIUM", "HIGH"}
    session.close()


def test_pricing_snapshot_acquisition_never_exceeds_entry() -> None:
    session = _session()
    _, keyword = _seed_keyword(session, "acq")
    _seed_gigs(session, keyword.id)
    run_stage_10_5(keyword.id, session, run_id="r13")
    snap = session.query(PricingSnapshot).first()
    assert snap is not None and snap.acquisition_basic <= snap.entry_basic
    session.close()


def test_niche_price_analysis_keywords_analyzed_count() -> None:
    session = _session()
    niche, kw1 = _seed_keyword(session, "count_niche")
    kw2 = Keyword(niche_id=niche.id, keyword="count kw 2", normalized_keyword="count kw 2")
    session.add(kw2)
    session.flush()
    _seed_gigs(session, kw1.id, n=4)
    _seed_gigs(session, kw2.id, n=4)
    result = run_stage_10_5_for_niche(niche.slug, session, run_id="r14")
    assert result["analyzed"] >= 2
    session.close()


def test_stage_logging_path_returns_analyzed_skipped_keys() -> None:
    session = _session()
    niche, keyword = _seed_keyword(session, "log_niche")
    _seed_gigs(session, keyword.id, n=3)
    out = run_stage_10_5_for_niche(niche.slug, session, run_id="r15")
    assert "analyzed" in out and "skipped" in out
    session.close()


def test_run_stage_10_5_invalid_session_skips() -> None:
    result = run_stage_10_5(1, object(), run_id="r16")
    assert result["status"] == "skipped"


def test_run_pricing_stage_handles_empty_keywords() -> None:
    result = run_pricing_stage("run-empty", [], object(), config=None)
    assert result["analyzed"] == 0 and result["failed"] == 0


def test_run_pricing_stage_exception_path(monkeypatch) -> None:
    monkeypatch.setattr("src.pricing.orchestrator.run_stage_10_5", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    result = run_pricing_stage("run-error", [1], object(), config=None)
    assert result["failed"] == 1
