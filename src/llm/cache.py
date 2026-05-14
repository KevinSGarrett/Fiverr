"""Durable, deterministic cache for LLM requests."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

CACHE_VERSION = "v2"


@dataclass(slots=True, frozen=True)
class CachePolicy:
    """Behavior controls for cache keying and reads/writes."""

    ttl_hours: int = 72
    enabled: bool = True
    cache_namespace: str = "default"
    max_prompt_chars_for_keying: int = 4000
    store_prompt_text: bool = False


def _build_prompt_hash(prompt_text: str, max_chars: int) -> str:
    prompt_slice = prompt_text[:max_chars]
    return hashlib.sha256(prompt_slice.encode("utf-8")).hexdigest()


def build_cache_key(
    *,
    model: str,
    temperature: float,
    prompt_text: str,
    cache_namespace: str = "default",
    max_prompt_chars_for_keying: int = 4000,
    cache_version: str = CACHE_VERSION,
) -> str:
    """Build deterministic SHA-256 key from request attributes."""
    prompt_hash = _build_prompt_hash(prompt_text, max_prompt_chars_for_keying)
    normalized = (
        f"{cache_version}|{cache_namespace.strip()}|{model.strip()}|"
        f"{temperature:.6f}|{prompt_hash}"
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class CacheRecord:
    """In-memory representation of durable cache record."""

    key: str
    model: str
    temperature: float
    cache_namespace: str
    prompt_hash: str
    prompt_text: str | None
    response_payload: dict[str, Any]
    created_at: datetime
    expires_at: datetime
    cache_version: str = CACHE_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Serialize cache record to a test-friendly dictionary."""
        return {
            "key": self.key,
            "model": self.model,
            "temperature": self.temperature,
            "cache_namespace": self.cache_namespace,
            "prompt_hash": self.prompt_hash,
            "prompt_text": self.prompt_text,
            "response_payload": self.response_payload,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "cache_version": self.cache_version,
        }


class LLMCache:
    """SQLite-backed cache with lazy initialization and invalidation."""

    def __init__(self, db_path: str | Path | None = "data/llm_cache.sqlite") -> None:
        self._db_path = Path(db_path) if db_path is not None else None
        self._memory_store: dict[str, CacheRecord] = {}
        self._conn: sqlite3.Connection | None = None

    def _ensure_connection(self) -> sqlite3.Connection | None:
        if self._db_path is None:
            return None
        if self._conn is not None:
            return self._conn
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self._db_path)
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_cache (
                    key TEXT PRIMARY KEY,
                    model TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    cache_namespace TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    prompt_text TEXT,
                    response_payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    cache_version TEXT NOT NULL
                )
                """
            )
            self._conn.commit()
        except sqlite3.Error:
            self._conn = None
        return self._conn

    def get(self, key: str, policy: CachePolicy | None = None) -> dict[str, Any] | None:
        """Return cached payload when present and not expired."""
        resolved_policy = policy or CachePolicy()
        if not resolved_policy.enabled:
            return None
        record = self.get_record(key, policy=resolved_policy)
        return None if record is None else record["response_payload"]

    def get_record(self, key: str, policy: CachePolicy | None = None) -> dict[str, Any] | None:
        """Return full cache record for inspection/debugging."""
        resolved_policy = policy or CachePolicy()
        if not resolved_policy.enabled:
            return None

        conn = self._ensure_connection()
        if conn is not None:
            row = conn.execute(
                """
                SELECT
                    model,
                    temperature,
                    cache_namespace,
                    prompt_hash,
                    prompt_text,
                    response_payload,
                    created_at,
                    expires_at,
                    cache_version
                FROM llm_cache
                WHERE key = ?
                """,
                (key,),
            ).fetchone()
            if row is None:
                return None

            response_payload = json.loads(str(row[5]))
            record = CacheRecord(
                key=key,
                model=str(row[0]),
                temperature=float(row[1]),
                cache_namespace=str(row[2]),
                prompt_hash=str(row[3]),
                prompt_text=str(row[4]) if row[4] is not None else None,
                response_payload=response_payload,
                created_at=datetime.fromisoformat(str(row[6])),
                expires_at=datetime.fromisoformat(str(row[7])),
                cache_version=str(row[8]),
            ).to_dict()
            if self.is_expired(record):
                self.invalidate(key)
                return None
            return record

        memory_record = self._memory_store.get(key)
        if memory_record is None:
            return None
        if self.is_expired(memory_record):
            self.invalidate(key)
            return None
        return memory_record.to_dict()

    def set(
        self,
        key: str,
        response_payload: dict[str, Any],
        *,
        model: str,
        temperature: float,
        prompt_text: str,
        policy: CachePolicy | None = None,
    ) -> None:
        """Upsert cache value with policy metadata and TTL."""
        resolved_policy = policy or CachePolicy()
        if not resolved_policy.enabled:
            return

        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=resolved_policy.ttl_hours)
        prompt_hash = _build_prompt_hash(prompt_text, resolved_policy.max_prompt_chars_for_keying)
        prompt_to_store = prompt_text if resolved_policy.store_prompt_text else None

        conn = self._ensure_connection()
        if conn is not None:
            conn.execute(
                """
                INSERT INTO llm_cache(
                    key,
                    model,
                    temperature,
                    cache_namespace,
                    prompt_hash,
                    prompt_text,
                    response_payload,
                    created_at,
                    expires_at,
                    cache_version
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    model = excluded.model,
                    temperature = excluded.temperature,
                    cache_namespace = excluded.cache_namespace,
                    prompt_hash = excluded.prompt_hash,
                    prompt_text = excluded.prompt_text,
                    response_payload = excluded.response_payload,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at,
                    cache_version = excluded.cache_version
                """,
                (
                    key,
                    model,
                    temperature,
                    resolved_policy.cache_namespace,
                    prompt_hash,
                    prompt_to_store,
                    json.dumps(response_payload),
                    now.isoformat(),
                    expires_at.isoformat(),
                    CACHE_VERSION,
                ),
            )
            conn.commit()
            return

        self._memory_store[key] = CacheRecord(
            key=key,
            model=model,
            temperature=temperature,
            cache_namespace=resolved_policy.cache_namespace,
            prompt_hash=prompt_hash,
            prompt_text=prompt_to_store,
            response_payload=response_payload,
            created_at=now,
            expires_at=expires_at,
            cache_version=CACHE_VERSION,
        )

    def invalidate(self, key: str) -> None:
        """Delete a cached value."""
        conn = self._ensure_connection()
        if conn is not None:
            conn.execute("DELETE FROM llm_cache WHERE key = ?", (key,))
            conn.commit()
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
