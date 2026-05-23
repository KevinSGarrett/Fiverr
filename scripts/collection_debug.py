"""Quick post-run DB summary for collection debugging."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv


def _resolve_sqlite_path(database_url: str) -> Path | None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    raw_path = database_url[len(prefix) :]
    db_path = Path(raw_path)
    if db_path.is_absolute():
        return db_path
    return Path(__file__).resolve().parents[1] / db_path


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    ).fetchone()
    return row is not None


def _count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    if not _table_exists(conn, table_name):
        return 0
    row = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    return int(row[0]) if row else 0


def _latest_keywords(conn: sqlite3.Connection, limit: int = 5) -> list[str]:
    if not _table_exists(conn, "keywords"):
        return []
    rows = conn.execute(
        "SELECT keyword FROM keywords ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [str(row[0]) for row in rows if row and row[0]]


def _latest_run_id(conn: sqlite3.Connection) -> str:
    if _table_exists(conn, "jobs"):
        row = conn.execute("SELECT run_id FROM jobs ORDER BY id DESC LIMIT 1").fetchone()
        if row and row[0]:
            return str(row[0])
    if _table_exists(conn, "run_logs"):
        row = conn.execute("SELECT run_id FROM run_logs ORDER BY id DESC LIMIT 1").fetchone()
        if row and row[0]:
            return str(row[0])
    return "N/A"


def _error_entries(conn: sqlite3.Connection, limit: int = 10) -> list[str]:
    entries: list[str] = []
    if _table_exists(conn, "jobs"):
        rows = conn.execute(
            """
            SELECT id, job_id, stage, status, error_log
            FROM jobs
            WHERE status IN ('FAILED', 'DEAD_LETTER')
               OR (error_log IS NOT NULL AND error_log != '[]')
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        for row in rows:
            error_payload = row[4]
            if isinstance(error_payload, str):
                try:
                    parsed = json.loads(error_payload)
                    error_payload = parsed
                except json.JSONDecodeError:
                    pass
            entries.append(
                f"jobs.id={row[0]} job_id={row[1]} stage={row[2]} status={row[3]} error_log={error_payload}"
            )

    if _table_exists(conn, "run_logs"):
        rows = conn.execute(
            """
            SELECT id, stage, message
            FROM run_logs
            WHERE lower(message) LIKE '%error%'
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        for row in rows:
            entries.append(f"run_logs.id={row[0]} stage={row[1]} message={row[2]}")

    return entries[:limit]


def main() -> int:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL", "sqlite:///data/fiverr_research.db")
    db_path = _resolve_sqlite_path(database_url)

    if db_path is None:
        print(f"Unsupported DATABASE_URL for this helper: {database_url}")
        print("Only sqlite:///... URLs are supported.")
        return 0

    if not db_path.exists():
        print(f"Database file not found: {db_path}")
        print("Run `python run.py init-db` or a collection command first.")
        return 0

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        table_counts = {
            "search_results": _count_rows(conn, "search_results"),
            "gigs": _count_rows(conn, "gigs"),
            "sellers": _count_rows(conn, "sellers"),
            "keywords": _count_rows(conn, "keywords"),
            "external_signals": _count_rows(conn, "external_signals"),
        }
        run_id = _latest_run_id(conn)
        recent_keywords = _latest_keywords(conn, limit=5)
        errors = _error_entries(conn, limit=10)
    finally:
        conn.close()

    print(f"Database: {db_path}")
    print("Row counts:")
    for table_name, count in table_counts.items():
        print(f"  - {table_name}: {count}")

    print("Most recent 5 keywords:")
    if recent_keywords:
        for keyword in recent_keywords:
            print(f"  - {keyword}")
    else:
        print("  - (none)")

    print("Recent error log entries:")
    if errors:
        for entry in errors:
            print(f"  - {entry}")
    else:
        print("  - (none)")

    print(
        "Collection produced "
        f"{table_counts['keywords']} keywords, "
        f"{table_counts['gigs']} gigs, "
        f"{table_counts['sellers']} sellers "
        f"for run {run_id}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
