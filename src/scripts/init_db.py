"""Database initialization script entrypoint."""

from __future__ import annotations

from src.models.database import initialize_database, list_tables, normalize_database_url


def main(database_url: str | None = None) -> int:
    normalized_url = normalize_database_url(database_url)
    engine = initialize_database(database_url=normalized_url)
    table_names = list_tables(engine)
    print(f"Initialized database at {normalized_url} with {len(table_names)} tables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
