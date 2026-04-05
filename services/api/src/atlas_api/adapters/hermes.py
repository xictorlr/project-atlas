"""Hermes memory/context bridge adapter.

Hermes is a memory framework for persisting and retrieving conversational and
workspace context across sessions.

Feature flag: ATLAS_HERMES_ENABLED (default false).

Redis key scheme:
  hermes:{workspace_id}:{sha256(query)[:12]}  →  JSON-encoded context entry
  hermes:{workspace_id}:index                  →  JSON list of stored context keys

Protocol
--------
HermesAdapter defines the interface. HermesMockAdapter provides an in-process
dict-backed stub for tests. RedisHermesAdapter is the production implementation.

Invariants (from rules/80-integrations-and-licensing.md):
  - replaceable: depends only on the Protocol
  - thin: no synthesis logic; pure storage/retrieval
  - documented: failure states described per method
  - optional: gated by settings.hermes_enabled
  - license-aware: no Hermes SDK bundled; communication is via Redis only
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Protocol, runtime_checkable

import redis

from atlas_api.config import settings

logger = logging.getLogger(__name__)

_KEY_PREFIX = "hermes"
_INDEX_SUFFIX = "index"


# ── Domain DTOs ────────────────────────────────────────────────────────────────


def _context_key(workspace_id: str, query: str) -> str:
    digest = hashlib.sha256(query.encode()).hexdigest()[:12]
    return f"{_KEY_PREFIX}:{workspace_id}:{digest}"


def _index_key(workspace_id: str) -> str:
    return f"{_KEY_PREFIX}:{workspace_id}:{_INDEX_SUFFIX}"


# ── Protocol ───────────────────────────────────────────────────────────────────


@runtime_checkable
class HermesAdapter(Protocol):
    """Interface that all Hermes adapter implementations must satisfy."""

    def store_context(self, workspace_id: str, context: dict[str, Any]) -> str:
        """Persist a context blob for a workspace.

        Returns the storage key.

        Failure states:
          - Redis write error: raises redis.RedisError (real impl).
          - context not serialisable: raises TypeError.
        """
        ...

    def retrieve_context(self, workspace_id: str, query: str) -> dict[str, Any] | None:
        """Retrieve context for a workspace by query string.

        Returns None if no matching entry exists.

        Failure states:
          - Redis read error: raises redis.RedisError (real impl).
        """
        ...

    def clear_context(self, workspace_id: str) -> int:
        """Delete all context entries for a workspace.

        Returns the number of keys deleted.

        Failure states:
          - Redis error: raises redis.RedisError (real impl).
        """
        ...


# ── Mock adapter ───────────────────────────────────────────────────────────────


class HermesMockAdapter:
    """In-process dict-backed stub — deterministic, no external dependencies."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def store_context(self, workspace_id: str, context: dict[str, Any]) -> str:
        key = _context_key(workspace_id, json.dumps(context, sort_keys=True))
        self._store[key] = context
        logger.debug("Hermes mock: stored context", extra={"key": key})
        return key

    def retrieve_context(self, workspace_id: str, query: str) -> dict[str, Any] | None:
        key = _context_key(workspace_id, query)
        result = self._store.get(key)
        logger.debug("Hermes mock: retrieve_context", extra={"key": key, "found": result is not None})
        return result

    def clear_context(self, workspace_id: str) -> int:
        prefix = f"{_KEY_PREFIX}:{workspace_id}:"
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        logger.debug("Hermes mock: cleared context", extra={"workspace_id": workspace_id, "count": len(keys)})
        return len(keys)


# ── Redis adapter (production) ─────────────────────────────────────────────────


class RedisHermesAdapter:
    """Production adapter that stores context in Redis.

    Uses ATLAS_REDIS_URL. Each entry TTL is controlled by
    settings.hermes_context_ttl_seconds.

    Failure states:
      - Connection refused: raises redis.ConnectionError.
      - Serialisation error: raises TypeError before any Redis call.
    """

    def __init__(self, redis_url: str, ttl_seconds: int) -> None:
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl_seconds

    def store_context(self, workspace_id: str, context: dict[str, Any]) -> str:
        serialised = json.dumps(context)
        key = _context_key(workspace_id, serialised)
        self._redis.setex(key, self._ttl, serialised)

        index_key = _index_key(workspace_id)
        self._redis.sadd(index_key, key)
        self._redis.expire(index_key, self._ttl)

        logger.info("Hermes: stored context", extra={"key": key, "workspace_id": workspace_id})
        return key

    def retrieve_context(self, workspace_id: str, query: str) -> dict[str, Any] | None:
        key = _context_key(workspace_id, query)
        raw = self._redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def clear_context(self, workspace_id: str) -> int:
        index_key = _index_key(workspace_id)
        keys: set[str] = self._redis.smembers(index_key)  # type: ignore[assignment]
        if not keys:
            return 0
        deleted = self._redis.delete(*keys, index_key)
        logger.info(
            "Hermes: cleared context",
            extra={"workspace_id": workspace_id, "deleted": deleted},
        )
        return deleted


# ── Factory ───────────────────────────────────────────────────────────────────


def get_hermes_adapter() -> HermesAdapter:
    """Return the active adapter based on feature flag and config."""
    if not settings.hermes_enabled:
        logger.debug("Hermes adapter: mock (feature disabled)")
        return HermesMockAdapter()

    logger.info("Hermes adapter: Redis (%s)", settings.redis_url)
    return RedisHermesAdapter(
        redis_url=settings.redis_url,
        ttl_seconds=settings.hermes_context_ttl_seconds,
    )
