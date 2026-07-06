"""Rank-2 (PROD-2): initialize_database must auto-run the SRDI R8 migration set so a
production DB gets the FULL schema — not just create_all().

Before this fix, initialize_database() only called create_all()+_ensure_* helpers and
never invoked run_srdi_r8_migrations(), and migration_14 (S7.6 discovery feedback) was
orphaned (unregistered) — so the discovery-feedback tables never existed in production
even though discovery code depends on them.
"""
from __future__ import annotations

import inspect

from src.models.base import Base
from src.models.database import build_engine, initialize_database, list_tables


def test_initialize_database_creates_migration14_discovery_tables() -> None:
    eng = initialize_database("sqlite:///:memory:")
    tables = set(list_tables(eng))
    # migration_14 tables — previously never created because migrations weren't auto-run
    for t in ("discovery_cycle_logs", "discovery_outcomes"):
        assert t in tables, f"{t} missing — migrations are not auto-run on init"


def test_runner_registers_migration_14() -> None:
    """The orphaned migration_14 must be registered + applied by the orchestrator."""
    from src.migrations.srdi_r8 import run_srdi_r8_migrations as mod
    src = inspect.getsource(mod)
    assert "migration_14_s76_discovery_feedback" in src
    assert "migration_14_s76_discovery_feedback.apply(" in src


def test_runner_is_idempotent() -> None:
    """Running the full migration set twice must not error (add-if-missing)."""
    from src.migrations.srdi_r8.run_srdi_r8_migrations import run_srdi_r8_migrations
    eng = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    run_srdi_r8_migrations(engine=eng)
    run_srdi_r8_migrations(engine=eng)  # second apply is a no-op, not an error
    assert "discovery_cycle_logs" in set(list_tables(eng))


def test_initialize_database_migration_failure_is_non_fatal(monkeypatch) -> None:
    """A migration hiccup must degrade (log) rather than brick DB init — the create_all
    schema must still come up."""
    import sys
    modname = "src.migrations.srdi_r8.run_srdi_r8_migrations"
    __import__(modname)

    def _boom(*_a, **_k):
        raise RuntimeError("simulated migration failure")

    # patch the submodule attribute the lazy `from <modname> import run_srdi_r8_migrations`
    # inside initialize_database resolves to
    monkeypatch.setattr(sys.modules[modname], "run_srdi_r8_migrations", _boom)
    eng = initialize_database("sqlite:///:memory:")  # must NOT raise
    assert len(list_tables(eng)) > 0  # create_all schema still came up
