"""Deterministic cache keying and lightweight LLM response cache."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


def build_cache_key(model: str, temperature: float, prompt_text: str) -> str:
    """Build a deterministic SHA-256 cache key for a prompt request."""
    normalized = f"{model.strip()}|{temperature:.6f}|{prompt_text}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class CacheRecord:
    """In-memory representation of a cache record."""

    key: str
    value: dict[str, Any]
    created_at: datetime
    expires_at: datetime


class LLMCache:
    """SQLite-backed cache with in-memory fallback for testability."""

    def __init__(self, db_path: str | Path | None = "data/llm_cache.sqlite") -> None:
        self._memory_store: dict[str, CacheRecord] = {}
        self._conn: sqlite3.Connection | None = None

        if db_path is None:
            return

        try:
            path = Path(db_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(path)
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )
            self._conn.commit()
        except sqlite3.Error:
            self._conn = None

    def get(self, key: str) -> dict[str, Any] | None:
        """Return cached value when present and not expired."""
        if self._conn is not None:
            row = self._conn.execute(
                "SELECT value, created_at, expires_at FROM llm_cache WHERE key = ?",
                (key,),
            ).fetchone()
            if row is None:
                return None

            record = {
                "key": key,
                "value": json.loads(str(row[0])),
                "created_at": str(row[1]),
                "expires_at": str(row[2]),
            }
            if self.is_expired(record):
                self.invalidate(key)
                return None
            return record["value"]

        memory_record = self._memory_store.get(key)
        if memory_record is None:
            return None
        if self.is_expired(memory_record):
            self.invalidate(key)
            return None
        return memory_record.value

    def set(self, key: str, value: dict[str, Any], ttl_hours: int) -> None:
        """Upsert a cache value with a TTL in hours."""
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=ttl_hours)

        if self._conn is not None:
            self._conn.execute(
                """
                INSERT INTO llm_cache(key, value, created_at, expires_at)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at
                """,
                (key, json.dumps(value), now.isoformat(), expires_at.isoformat()),
            )
            self._conn.commit()
            return

        self._memory_store[key] = CacheRecord(
            key=key,
            value=value,
            created_at=now,
            expires_at=expires_at,
        )

    def invalidate(self, key: str) -> None:
        """Delete a cached value."""
        if self._conn is not None:
            self._conn.execute("DELETE FROM llm_cache WHERE key = ?", (key,))
            self._conn.commit()
            return
        self._memory_store.pop(key, None)

    def is_expired(self, record: CacheRecord | dict[str, Any], now: datetime | None = None) -> bool:
        """Determine whether a cache record has expired."""
        reference_time = now or datetime.now(UTC)
        expires_at: datetime
        if isinstance(record, CacheRecord):
            expires_at = record.expires_at
        else:
            expires_value = record["expires_at"]
            expires_at = (
                datetime.fromisoformat(expires_value)
                if isinstance(expires_value, str)
                else expires_value
            )

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return expires_at <= reference_time
