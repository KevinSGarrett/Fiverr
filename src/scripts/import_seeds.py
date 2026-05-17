"""Import seed keywords from data/seeds/ YAML files into the database.

Usage:
    python -m src.scripts.import_seeds
    python -m src.scripts.import_seeds --seeds-dir data/seeds --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.database import initialize_database, normalize_database_url  # noqa: E402
from src.models.market import Keyword  # noqa: E402
from src.models.niche import Niche  # noqa: E402

_DEFAULT_SEEDS_DIR = PROJECT_ROOT / "data" / "seeds"


def _load_seed_file(path: Path) -> dict:
    """Load and validate a single seed YAML file."""
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Seed file {path} must be a YAML mapping, got {type(data)}")
    required_keys = {"niche_id", "niche_name", "keywords"}
    missing = required_keys - set(data.keys())
    if missing:
        raise ValueError(f"Seed file {path} missing required keys: {missing}")
    if not isinstance(data["keywords"], list) or len(data["keywords"]) == 0:
        raise ValueError(f"Seed file {path} 'keywords' must be a non-empty list")
    return data


def _upsert_seed_keywords(
    session: Session,
    niche_id_str: str,
    keywords: list[dict],
    dry_run: bool = False,
) -> tuple[int, int]:
    """Upsert seed keywords for a niche. Returns (inserted, skipped) counts."""
    # Look up the Niche by slug (niche_id in config = slug in model)
    niche = session.query(Niche).filter_by(slug=niche_id_str).first()
    if niche is None:
        raise ValueError(
            f"Niche with slug '{niche_id_str}' not found in database. "
            "Run `python run.py init-db` first to create the schema and seed niches."
        )

    inserted = 0
    skipped = 0

    for kw_data in keywords:
        keyword_text = str(kw_data.get("keyword", "")).strip()
        normalized = str(kw_data.get("normalized_keyword", keyword_text.lower())).strip()
        language = str(kw_data.get("language", "en")).strip()
        source = str(kw_data.get("source", "seed")).strip()

        if not keyword_text:
            continue

        # Check for existing keyword (upsert by niche_id + keyword)
        existing = (
            session.query(Keyword)
            .filter_by(niche_id=niche.id, keyword=keyword_text)
            .first()
        )

        if existing is not None:
            skipped += 1
            continue

        if not dry_run:
            kw = Keyword(
                niche_id=niche.id,
                keyword=keyword_text,
                normalized_keyword=normalized,
                language=language,
                external_source=source,
            )
            session.add(kw)
        inserted += 1

    if not dry_run:
        session.flush()

    return inserted, skipped


def import_seeds(
    seeds_dir: Path | None = None,
    database_url: str | None = None,
    dry_run: bool = False,
) -> dict[str, dict[str, int]]:
    """Import all seed YAML files from seeds_dir.

    Returns a summary dict: {niche_id: {"inserted": N, "skipped": N}}.
    Raises ValueError if any seed file is malformed or its niche is missing.
    """
    seeds_dir = seeds_dir or _DEFAULT_SEEDS_DIR
    if not seeds_dir.exists():
        raise FileNotFoundError(f"Seeds directory not found: {seeds_dir}")

    yaml_files = sorted(seeds_dir.glob("*.yaml"))
    if not yaml_files:
        raise FileNotFoundError(f"No .yaml seed files found in {seeds_dir}")

    url = normalize_database_url(database_url)
    engine = initialize_database(database_url=url)

    results: dict[str, dict[str, int]] = {}

    with Session(engine) as session:
        for seed_file in yaml_files:
            data = _load_seed_file(seed_file)
            niche_id = data["niche_id"]
            inserted, skipped = _upsert_seed_keywords(
                session=session,
                niche_id_str=niche_id,
                keywords=data["keywords"],
                dry_run=dry_run,
            )
            results[niche_id] = {"inserted": inserted, "skipped": skipped}

        if not dry_run:
            session.commit()

    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Import seed keywords from data/seeds/*.yaml into the database."
    )
    parser.add_argument(
        "--seeds-dir",
        type=Path,
        default=_DEFAULT_SEEDS_DIR,
        help="Directory containing seed YAML files (default: data/seeds)",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Database URL override (default: DATABASE_URL env var or SQLite data/fiverr.db)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Parse and validate seeds without writing to the database",
    )
    args = parser.parse_args(argv)

    mode = "DRY RUN" if args.dry_run else "IMPORT"
    print(f"[import_seeds] {mode} from {args.seeds_dir}")

    try:
        results = import_seeds(
            seeds_dir=args.seeds_dir,
            database_url=args.database_url,
            dry_run=args.dry_run,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"[import_seeds] ERROR: {exc}", file=sys.stderr)
        return 1

    total_inserted = sum(v["inserted"] for v in results.values())
    total_skipped = sum(v["skipped"] for v in results.values())

    for niche_id, counts in sorted(results.items()):
        print(
            f"  {niche_id}: inserted={counts['inserted']} skipped={counts['skipped']}"
        )

    print(
        f"[import_seeds] Done — {len(results)} niches, "
        f"{total_inserted} keywords inserted, {total_skipped} skipped"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
