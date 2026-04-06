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
LocalHermesAdapter extends Redis storage with LLM-powered session summarisation.

Invariants (from rules/80-integrations-and-licensing.md):
  - replaceable: depends only on the Protocol
  - thin: no synthesis logic beyond session summarisation
  - documented: failure states described per method
  - optional: gated by settings.hermes_enabled
  - license-aware: no Hermes SDK bundled; communication is via Redis only
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Protocol, runtime_checkable

import httpx
import redis

from atlas_api.config import settings

logger = logging.getLogger(__name__)

_KEY_PREFIX = "hermes"
_INDEX_SUFFIX = "index"
_SESSION_SUFFIX = "session"

# Ollama API endpoint used by the local adapter.
_OLLAMA_GENERATE_PATH = "/api/generate"


# ── Domain helpers ─────────────────────────────────────────────────────────────


def _context_key(workspace_id: str, query: str) -> str:
    digest = hashlib.sha256(query.encode()).hexdigest()[:12]
    return f"{_KEY_PREFIX}:{workspace_id}:{digest}"


def _index_key(workspace_id: str) -> str:
    return f"{_KEY_PREFIX}:{workspace_id}:{_INDEX_SUFFIX}"


def _session_key(workspace_id: str) -> str:
    """Key used to store the serialised current-session context string."""
    return f"{_KEY_PREFIX}:{workspace_id}:{_SESSION_SUFFIX}"


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
        logger.debug(
            "Hermes mock: cleared context",
            extra={"workspace_id": workspace_id, "count": len(keys)},
        )
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


# ── Local adapter (Redis + Ollama summarisation) ───────────────────────────────


class LocalHermesAdapter:
    """Session memory backed by Redis + Ollama-powered session summarisation.

    Extends RedisHermesAdapter with three additional operations:
      - store_context(workspace_id, context_str, ttl): store plain string in Redis.
      - retrieve_context(workspace_id): return last stored session string.
      - summarize_session(workspace_id): LLM condenses stored context for next session.
      - clear_context(workspace_id): delete all Redis keys for the workspace.

    These methods use string-typed context (not dict) to match the
    session-memory use case described in the adapter spec.  The Protocol's
    dict-typed methods are delegated to an inner RedisHermesAdapter.

    Model used: settings.hermes_model or fallback "gemma4:12b".
    """

    _SUMMARIZE_PROMPT = (
        "The following is context stored during a work session on workspace {workspace_id}.\n"
        "Write a concise, bullet-point summary (max 200 words) of what was worked on, "
        "any key decisions made, and any open action items. "
        "This summary will be shown at the start of the next session.\n\n"
        "Session context:\n{context}"
    )

    def __init__(
        self,
        redis_url: str,
        ttl_seconds: int,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "gemma4:12b",
        timeout: float = 60.0,
    ) -> None:
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl_seconds
        self._ollama_base_url = ollama_base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        # Delegate dict-based context ops to the standard Redis adapter.
        self._dict_adapter = RedisHermesAdapter(redis_url=redis_url, ttl_seconds=ttl_seconds)

    # -- Protocol methods (dict-typed context) ---------------------------------

    def store_context(self, workspace_id: str, context: dict[str, Any]) -> str:
        """Store dict context blob in Redis (delegates to RedisHermesAdapter)."""
        return self._dict_adapter.store_context(workspace_id, context)

    def retrieve_context(self, workspace_id: str, query: str) -> dict[str, Any] | None:
        """Retrieve dict context by query string (delegates to RedisHermesAdapter).

        Falls back to checking the session key when no dict match is found.
        """
        result = self._dict_adapter.retrieve_context(workspace_id, query)
        if result is not None:
            return result
        # Try the session string key as a last resort.
        raw = self._redis.get(_session_key(workspace_id))
        if raw:
            return {"session_context": raw, "workspace_id": workspace_id}
        return None

    def clear_context(self, workspace_id: str) -> int:
        """Delete all context keys for the workspace, including the session key."""
        dict_count = self._dict_adapter.clear_context(workspace_id)
        session_k = _session_key(workspace_id)
        session_deleted = self._redis.delete(session_k)
        total = dict_count + session_deleted
        logger.info(
            "LocalHermesAdapter: cleared %d keys for workspace=%s", total, workspace_id
        )
        return total

    # -- Session-level string context methods ----------------------------------

    def store_session_context(
        self, workspace_id: str, context: str, ttl: int = 86400
    ) -> str:
        """Store a session context string in Redis with TTL.

        Args:
            workspace_id: Workspace to store context for.
            context:      Free-form string describing session state.
            ttl:          TTL in seconds (default 24 h).

        Returns the Redis key.

        Failure states:
          - Redis unreachable: raises redis.ConnectionError.
        """
        key = _session_key(workspace_id)
        self._redis.setex(key, ttl, context)
        logger.info(
            "LocalHermesAdapter: stored session context workspace=%s key=%s ttl=%ds",
            workspace_id,
            key,
            ttl,
        )
        return key

    def retrieve_session_context(self, workspace_id: str) -> str | None:
        """Return the stored session context string, or None if expired/missing.

        Failure states:
          - Redis unreachable: raises redis.ConnectionError.
        """
        raw = self._redis.get(_session_key(workspace_id))
        if raw is None:
            logger.debug(
                "LocalHermesAdapter: no session context for workspace=%s", workspace_id
            )
            return None
        logger.debug("LocalHermesAdapter: retrieved session context workspace=%s", workspace_id)
        return raw

    def summarize_session(self, workspace_id: str) -> str:
        """LLM-powered summarisation of the stored session context.

        Calls Ollama to condense the stored context string into a brief
        bullet-point summary suitable for display at the next session start.

        Returns the summary string. If Ollama is unreachable or no context
        is stored, returns a descriptive fallback string (never raises).

        Failure states:
          - Ollama down: returns fallback, logs warning — does not raise.
          - No context found: returns "No session context stored."
        """
        raw = self.retrieve_session_context(workspace_id)
        if not raw:
            return "No session context stored for this workspace."

        prompt = self._SUMMARIZE_PROMPT.format(workspace_id=workspace_id, context=raw)
        try:
            payload = {
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2},
            }
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    f"{self._ollama_base_url}{_OLLAMA_GENERATE_PATH}",
                    json=payload,
                )
                resp.raise_for_status()
                summary = resp.json().get("response", "").strip()
                logger.info(
                    "LocalHermesAdapter: summarize_session complete workspace=%s model=%s",
                    workspace_id,
                    self._model,
                )
                return summary
        except httpx.ConnectError:
            logger.warning(
                "LocalHermesAdapter: Ollama unreachable at %s — returning raw context excerpt",
                self._ollama_base_url,
            )
            return f"(Summary unavailable — Ollama offline)\n\nRaw context:\n{raw[:500]}"
        except Exception as exc:
            logger.warning(
                "LocalHermesAdapter: summarize_session failed: %s — returning fallback", exc
            )
            return f"(Summary unavailable: {exc})\n\nRaw context:\n{raw[:500]}"


# ── Factory ───────────────────────────────────────────────────────────────────


def get_hermes_adapter() -> HermesAdapter:
    """Return the active adapter based on feature flag and config.

    Selection priority:
      1. Disabled → HermesMockAdapter.
      2. Enabled + Redis reachable → LocalHermesAdapter (Redis + Ollama).

    Always returns a valid HermesAdapter — never returns None.
    """
    if not settings.hermes_enabled:
        logger.debug("Hermes adapter: mock (feature disabled)")
        return HermesMockAdapter()

    model = getattr(settings, "hermes_model", "gemma4:12b")
    ollama_url = getattr(settings, "ollama_base_url", "http://localhost:11434")
    logger.info(
        "Hermes adapter: local Redis+Ollama (model=%s redis=%s)", model, settings.redis_url
    )
    return LocalHermesAdapter(
        redis_url=settings.redis_url,
        ttl_seconds=settings.hermes_context_ttl_seconds,
        ollama_base_url=ollama_url,
        model=model,
    )
