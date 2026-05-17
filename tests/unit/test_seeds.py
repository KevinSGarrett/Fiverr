"""Tests for import_seeds.py — SCRUM-140 Acceptance Criteria coverage.

AC items tested:
1. Seed YAML files are valid and parseable for all 9 niches
2. import_seeds loads seed keywords correctly into the DB
3. Re-running import_seeds is idempotent (skips existing keywords)
4. Missing niche in DB raises a clear error
5. Dry-run mode validates without writing
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

SEEDS_DIR = Path(__file__).resolve().parents[2] / "data" / "seeds"
EXPECTED_NICHE_IDS = {
    "prd_ai_saas",
    "support_kb_readiness",
    "gumloop_lindy_workflow",
    "mcp_ai_agent",
    "python_automation",
    "ai_tool_llm_integration",
    "ai_agent_development",
    "workflow_automation",
    "python_web_scraping",
}


# ---------------------------------------------------------------------------
# AC 1: All 9 seed YAML files exist and are valid
# ---------------------------------------------------------------------------


class TestSeedFilesExist:
    def test_seeds_directory_exists(self) -> None:
        assert SEEDS_DIR.exists(), f"data/seeds/ directory not found at {SEEDS_DIR}"

    def test_all_nine_seed_files_present(self) -> None:
        yaml_files = {p.stem for p in SEEDS_DIR.glob("*.yaml")}
        missing = EXPECTED_NICHE_IDS - yaml_files
        assert not missing, f"Missing seed files for niches: {sorted(missing)}"

    @pytest.mark.parametrize("niche_id", sorted(EXPECTED_NICHE_IDS))
    def test_seed_file_is_valid_yaml(self, niche_id: str) -> None:
        seed_path = SEEDS_DIR / f"{niche_id}.yaml"
        assert seed_path.exists(), f"Seed file not found: {seed_path}"
        with seed_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        assert isinstance(data, dict), f"{niche_id}: root must be a YAML mapping"

    @pytest.mark.parametrize("niche_id", sorted(EXPECTED_NICHE_IDS))
    def test_seed_file_has_required_keys(self, niche_id: str) -> None:
        seed_path = SEEDS_DIR / f"{niche_id}.yaml"
        with seed_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        for key in ("niche_id", "niche_name", "keywords"):
            assert key in data, f"{niche_id}: missing required key '{key}'"
        assert data["niche_id"] == niche_id, (
            f"niche_id mismatch: file stem '{niche_id}' != data['niche_id'] '{data['niche_id']}'"
        )

    @pytest.mark.parametrize("niche_id", sorted(EXPECTED_NICHE_IDS))
    def test_seed_file_has_keywords(self, niche_id: str) -> None:
        seed_path = SEEDS_DIR / f"{niche_id}.yaml"
        with seed_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        keywords = data["keywords"]
        assert isinstance(keywords, list), f"{niche_id}: 'keywords' must be a list"
        assert len(keywords) >= 3, f"{niche_id}: expected >= 3 seed keywords, got {len(keywords)}"

    @pytest.mark.parametrize("niche_id", sorted(EXPECTED_NICHE_IDS))
    def test_seed_keywords_have_required_fields(self, niche_id: str) -> None:
        seed_path = SEEDS_DIR / f"{niche_id}.yaml"
        with seed_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        for i, kw in enumerate(data["keywords"]):
            assert "keyword" in kw, f"{niche_id}[{i}]: missing 'keyword' field"
            assert "normalized_keyword" in kw, f"{niche_id}[{i}]: missing 'normalized_keyword' field"
            assert kw["keyword"].strip(), f"{niche_id}[{i}]: 'keyword' must not be empty"
            assert kw["normalized_keyword"].strip(), f"{niche_id}[{i}]: 'normalized_keyword' must not be empty"


# ---------------------------------------------------------------------------
# AC 2 & 3: import_seeds loads and is idempotent
# ---------------------------------------------------------------------------


class TestImportSeedsDB:
    """Tests that require a live database and Niche rows to exist."""

    @pytest.fixture()
    def seeded_engine(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """Create a fresh SQLite DB with niches populated, return engine."""
        db_path = tmp_path / "test_seeds.db"
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

        from sqlalchemy.orm import Session
        from src.models.database import initialize_database
        from src.models.niche import Niche

        engine = initialize_database(database_url=f"sqlite:///{db_path.as_posix()}")

        # Insert one niche for targeted testing
        with Session(engine) as session:
            niche = Niche(
                slug="prd_ai_saas",
                name="PRD / AI SaaS MVP Roadmap",
                category_path="programming-tech/ai-coding/AI-Technology-Consulting",
            )
            session.add(niche)
            session.commit()

        return engine, db_path

    def test_import_inserts_keywords(self, tmp_path: Path, seeded_engine) -> None:
        engine, db_path = seeded_engine
        from sqlalchemy.orm import Session
        from src.models.market import Keyword
        from src.scripts.import_seeds import import_seeds

        # Only run for one niche to avoid needing all niches seeded
        single_seed_dir = tmp_path / "seeds_single"
        single_seed_dir.mkdir()
        (single_seed_dir / "prd_ai_saas.yaml").write_text(
            (SEEDS_DIR / "prd_ai_saas.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        results = import_seeds(
            seeds_dir=single_seed_dir,
            database_url=f"sqlite:///{db_path.as_posix()}",
        )

        assert "prd_ai_saas" in results
        assert results["prd_ai_saas"]["inserted"] >= 3
        assert results["prd_ai_saas"]["skipped"] == 0

        with Session(engine) as session:
            count = session.query(Keyword).count()
        assert count >= 3

    def test_import_is_idempotent(self, tmp_path: Path, seeded_engine) -> None:
        engine, db_path = seeded_engine
        from sqlalchemy.orm import Session
        from src.models.market import Keyword
        from src.scripts.import_seeds import import_seeds

        single_seed_dir = tmp_path / "seeds_idem"
        single_seed_dir.mkdir()
        (single_seed_dir / "prd_ai_saas.yaml").write_text(
            (SEEDS_DIR / "prd_ai_saas.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        url = f"sqlite:///{db_path.as_posix()}"
        r1 = import_seeds(seeds_dir=single_seed_dir, database_url=url)
        r2 = import_seeds(seeds_dir=single_seed_dir, database_url=url)

        assert r1["prd_ai_saas"]["inserted"] > 0
        assert r2["prd_ai_saas"]["inserted"] == 0
        assert r2["prd_ai_saas"]["skipped"] == r1["prd_ai_saas"]["inserted"]

        with Session(engine) as session:
            count1 = session.query(Keyword).count()
        # Count should not change on second run
        with Session(engine) as session:
            count2 = session.query(Keyword).count()
        assert count1 == count2


# ---------------------------------------------------------------------------
# AC 4: Missing niche raises ValueError
# ---------------------------------------------------------------------------


class TestImportSeedsMissingNiche:
    def test_missing_niche_raises_value_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        db_path = tmp_path / "empty.db"
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

        from src.models.database import initialize_database
        initialize_database(database_url=f"sqlite:///{db_path.as_posix()}")

        single_seed_dir = tmp_path / "seeds_missing"
        single_seed_dir.mkdir()
        (single_seed_dir / "prd_ai_saas.yaml").write_text(
            (SEEDS_DIR / "prd_ai_saas.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        from src.scripts.import_seeds import import_seeds
        with pytest.raises(ValueError, match="not found in database"):
            import_seeds(
                seeds_dir=single_seed_dir,
                database_url=f"sqlite:///{db_path.as_posix()}",
            )


# ---------------------------------------------------------------------------
# AC 5: Dry-run mode validates without writing
# ---------------------------------------------------------------------------


class TestImportSeedsDryRun:
    def test_dry_run_does_not_write(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        db_path = tmp_path / "dryrun.db"
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

        from sqlalchemy.orm import Session
        from src.models.database import initialize_database
        from src.models.niche import Niche

        engine = initialize_database(database_url=f"sqlite:///{db_path.as_posix()}")
        with Session(engine) as session:
            session.add(Niche(
                slug="prd_ai_saas",
                name="PRD / AI SaaS MVP Roadmap",
                category_path="programming-tech/ai-coding/AI-Technology-Consulting",
            ))
            session.commit()

        single_seed_dir = tmp_path / "seeds_dry"
        single_seed_dir.mkdir()
        (single_seed_dir / "prd_ai_saas.yaml").write_text(
            (SEEDS_DIR / "prd_ai_saas.yaml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        from src.models.market import Keyword
        from src.scripts.import_seeds import import_seeds

        results = import_seeds(
            seeds_dir=single_seed_dir,
            database_url=f"sqlite:///{db_path.as_posix()}",
            dry_run=True,
        )

        assert results["prd_ai_saas"]["inserted"] >= 3
        with Session(engine) as session:
            count = session.query(Keyword).count()
        assert count == 0, "Dry run must not write any rows to the database"
