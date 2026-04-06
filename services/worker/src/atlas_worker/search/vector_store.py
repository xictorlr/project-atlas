"""PgVectorStore — raw pgvector upsert, cosine-similarity search, and stats.

Uses asyncpg directly for vector operations so we can pass the pgvector
`<=>` operator through raw SQL without fighting SQLAlchemy's expression layer.

All public methods are idempotent and safe to retry.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import asyncpg

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VectorSearchResult:
    """One passage returned by a similarity search."""

    note_slug: str
    note_title: str | None
    chunk_idx: int
    chunk_text: str
    score: float  # cosine similarity in [0, 1]; higher is more similar
    model: str


@dataclass(frozen=True)
class VectorStoreStats:
    """Aggregate embedding stats for a workspace."""

    workspace_id: str
    total_chunks: int
    unique_notes: int
    model_counts: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# PgVectorStore
# ---------------------------------------------------------------------------


class PgVectorStore:
    """Async vector store backed by PostgreSQL + pgvector.

    The caller is responsible for creating the asyncpg connection pool.
    This class focuses purely on vector CRUD operations.

    Schema assumed to exist::

        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE TABLE note_embeddings (
            id              BIGSERIAL PRIMARY KEY,
            workspace_id    TEXT NOT NULL,
            note_slug       TEXT NOT NULL,
            note_title      TEXT,
            chunk_idx       INT NOT NULL,
            chunk_text      TEXT NOT NULL,
            content_hash    TEXT NOT NULL,
            embedding       vector(768) NOT NULL,
            model           TEXT NOT NULL DEFAULT 'nomic-embed-text',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(workspace_id, note_slug, chunk_idx)
        );
    """

    def __init__(self, db_url: str) -> None:
        """Initialise with a PostgreSQL DSN (asyncpg format).

        The connection pool is created lazily on first use.

        Args:
            db_url: asyncpg DSN, e.g.
                ``postgresql://atlas:pass@localhost:5432/atlas_dev``
        """
        self._db_url = db_url
        self._pool: asyncpg.Pool | None = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    async def _get_pool(self) -> asyncpg.Pool:
        """Return (or create) the asyncpg connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._db_url, min_size=1, max_size=5)
        return self._pool

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def upsert(
        self,
        workspace_id: str,
        note_slug: str,
        note_title: str | None,
        chunks: list[tuple[int, str, str]],
        embeddings: list[list[float]],
        model: str,
    ) -> int:
        """Upsert embedding chunks for a note.

        Args:
            workspace_id: Tenant identifier.
            note_slug: Stable slug of the vault note.
            note_title: Human-readable note title (nullable).
            chunks: List of ``(chunk_idx, chunk_text, content_hash)`` tuples.
            embeddings: List of embedding vectors, one per chunk.
            model: Embedding model name, e.g. ``"nomic-embed-text"``.

        Returns:
            Number of rows upserted.

        Raises:
            ValueError: If ``chunks`` and ``embeddings`` lengths differ.
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"chunks ({len(chunks)}) and embeddings ({len(embeddings)}) must have equal length"
            )
        if not chunks:
            return 0

        pool = await self._get_pool()
        sql = """
            INSERT INTO note_embeddings
                (workspace_id, note_slug, note_title, chunk_idx,
                 chunk_text, content_hash, embedding, model, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7::vector, $8, now())
            ON CONFLICT (workspace_id, note_slug, chunk_idx)
            DO UPDATE SET
                note_title   = EXCLUDED.note_title,
                chunk_text   = EXCLUDED.chunk_text,
                content_hash = EXCLUDED.content_hash,
                embedding    = EXCLUDED.embedding,
                model        = EXCLUDED.model,
                updated_at   = now()
        """
        rows = [
            (
                workspace_id,
                note_slug,
                note_title,
                chunk_idx,
                chunk_text,
                content_hash,
                str(vec),  # asyncpg accepts vector as its string repr
                model,
            )
            for (chunk_idx, chunk_text, content_hash), vec in zip(chunks, embeddings, strict=True)
        ]
        async with pool.acquire() as conn:
            await conn.executemany(sql, rows)

        logger.debug("upserted %d chunks for %s/%s", len(chunks), workspace_id, note_slug)
        return len(chunks)

    async def delete_note(self, workspace_id: str, note_slug: str) -> int:
        """Delete all embedding chunks for a note.

        Returns:
            Number of rows deleted.
        """
        pool = await self._get_pool()
        sql = "DELETE FROM note_embeddings WHERE workspace_id = $1 AND note_slug = $2"
        async with pool.acquire() as conn:
            result = await conn.execute(sql, workspace_id, note_slug)
        # result is e.g. "DELETE 5"
        try:
            count = int(result.split()[-1])
        except (ValueError, IndexError):
            count = 0
        logger.debug("deleted %d chunks for %s/%s", count, workspace_id, note_slug)
        return count

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def search(
        self,
        workspace_id: str,
        query_embedding: list[float],
        limit: int = 20,
        min_score: float = 0.3,
    ) -> list[VectorSearchResult]:
        """Return top-K passages by cosine similarity.

        Uses pgvector ``<=>`` (cosine distance); we convert to similarity
        as ``1 - distance`` so 1.0 is a perfect match.

        Args:
            workspace_id: Tenant scope.
            query_embedding: Embedded query vector (768 dims).
            limit: Maximum number of results.
            min_score: Minimum cosine similarity threshold in [0, 1].

        Returns:
            Ranked list of :class:`VectorSearchResult`, highest score first.
        """
        pool = await self._get_pool()
        sql = """
            SELECT
                note_slug,
                note_title,
                chunk_idx,
                chunk_text,
                model,
                1 - (embedding <=> $2::vector) AS score
            FROM note_embeddings
            WHERE workspace_id = $1
              AND 1 - (embedding <=> $2::vector) >= $3
            ORDER BY embedding <=> $2::vector
            LIMIT $4
        """
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                sql,
                workspace_id,
                str(query_embedding),
                min_score,
                limit,
            )

        return [
            VectorSearchResult(
                note_slug=row["note_slug"],
                note_title=row["note_title"],
                chunk_idx=row["chunk_idx"],
                chunk_text=row["chunk_text"],
                score=float(row["score"]),
                model=row["model"],
            )
            for row in rows
        ]

    async def needs_update(
        self,
        workspace_id: str,
        note_slug: str,
        content_hash: str,
    ) -> bool:
        """Return True if the note has no stored chunks or its hash has changed.

        Compares the stored ``content_hash`` for chunk 0 against the provided
        hash.  A note that has never been embedded also returns True.

        Args:
            workspace_id: Tenant scope.
            note_slug: Note to check.
            content_hash: SHA-256 of the combined note content.
        """
        pool = await self._get_pool()
        sql = """
            SELECT content_hash
            FROM note_embeddings
            WHERE workspace_id = $1
              AND note_slug = $2
              AND chunk_idx = 0
            LIMIT 1
        """
        async with pool.acquire() as conn:
            row = await conn.fetchrow(sql, workspace_id, note_slug)

        if row is None:
            return True
        return row["content_hash"] != content_hash

    async def stats(self, workspace_id: str) -> VectorStoreStats:
        """Return aggregate embedding stats for a workspace.

        Args:
            workspace_id: Tenant scope.

        Returns:
            :class:`VectorStoreStats` with counts by model.
        """
        pool = await self._get_pool()
        sql = """
            SELECT
                COUNT(*)             AS total_chunks,
                COUNT(DISTINCT note_slug) AS unique_notes,
                model,
                COUNT(*)             AS model_count
            FROM note_embeddings
            WHERE workspace_id = $1
            GROUP BY model
        """
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, workspace_id)

        total_chunks = 0
        unique_notes = 0
        model_counts: dict[str, int] = {}

        for row in rows:
            total_chunks += row["total_chunks"]
            # unique_notes is the same for all rows (full-table aggregate)
            unique_notes = max(unique_notes, row["unique_notes"])
            model_counts[row["model"]] = row["model_count"]

        return VectorStoreStats(
            workspace_id=workspace_id,
            total_chunks=total_chunks,
            unique_notes=unique_notes,
            model_counts=model_counts,
        )
