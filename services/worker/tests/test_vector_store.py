"""Tests for PgVectorStore with mocked asyncpg pool."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from atlas_worker.search.vector_store import PgVectorStore, VectorSearchResult, VectorStoreStats


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_pool_mock(fetchrow=None, fetch=None, execute=None):
    """Return a mock asyncpg pool whose acquire() context manager returns a connection."""
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value=fetchrow)
    conn.fetch = AsyncMock(return_value=fetch or [])
    conn.execute = AsyncMock(return_value=execute or "DELETE 0")
    conn.executemany = AsyncMock(return_value=None)

    # Make acquire() a context manager
    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=False)

    pool = AsyncMock()
    pool.acquire = MagicMock(return_value=acquire_cm)
    pool.close = AsyncMock()
    return pool, conn


@pytest.fixture
def store():
    return PgVectorStore(db_url="postgresql://atlas:pass@localhost:5432/atlas_test")


# ---------------------------------------------------------------------------
# upsert
# ---------------------------------------------------------------------------


class TestUpsert:
    @pytest.mark.asyncio
    async def test_upsert_returns_chunk_count(self, store: PgVectorStore) -> None:
        pool, conn = _make_pool_mock()
        store._pool = pool

        chunks = [(0, "Hello world", "abc123"), (1, "Second passage", "def456")]
        embeddings = [[0.1] * 768, [0.2] * 768]

        count = await store.upsert(
            workspace_id="ws1",
            note_slug="notes/meeting",
            note_title="Meeting Notes",
            chunks=chunks,
            embeddings=embeddings,
            model="nomic-embed-text",
        )

        assert count == 2
        conn.executemany.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_empty_chunks_returns_zero(self, store: PgVectorStore) -> None:
        pool, conn = _make_pool_mock()
        store._pool = pool

        count = await store.upsert(
            workspace_id="ws1",
            note_slug="notes/empty",
            note_title=None,
            chunks=[],
            embeddings=[],
            model="nomic-embed-text",
        )

        assert count == 0
        conn.executemany.assert_not_called()

    @pytest.mark.asyncio
    async def test_upsert_raises_on_length_mismatch(self, store: PgVectorStore) -> None:
        pool, _ = _make_pool_mock()
        store._pool = pool

        with pytest.raises(ValueError, match="equal length"):
            await store.upsert(
                workspace_id="ws1",
                note_slug="notes/mismatch",
                note_title=None,
                chunks=[(0, "text", "hash")],
                embeddings=[],  # empty — mismatch
                model="nomic-embed-text",
            )


# ---------------------------------------------------------------------------
# delete_note
# ---------------------------------------------------------------------------


class TestDeleteNote:
    @pytest.mark.asyncio
    async def test_delete_returns_count(self, store: PgVectorStore) -> None:
        pool, conn = _make_pool_mock(execute="DELETE 5")
        store._pool = pool

        count = await store.delete_note("ws1", "notes/old")

        assert count == 5
        conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_handles_zero(self, store: PgVectorStore) -> None:
        pool, conn = _make_pool_mock(execute="DELETE 0")
        store._pool = pool

        count = await store.delete_note("ws1", "notes/nonexistent")

        assert count == 0


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


class TestSearch:
    @pytest.mark.asyncio
    async def test_search_returns_ranked_results(self, store: PgVectorStore) -> None:
        row1 = {
            "note_slug": "notes/alpha",
            "note_title": "Alpha Note",
            "chunk_idx": 0,
            "chunk_text": "Alpha content",
            "model": "nomic-embed-text",
            "score": 0.92,
        }
        row2 = {
            "note_slug": "notes/beta",
            "note_title": None,
            "chunk_idx": 1,
            "chunk_text": "Beta content",
            "model": "nomic-embed-text",
            "score": 0.75,
        }
        pool, conn = _make_pool_mock(fetch=[row1, row2])
        store._pool = pool

        results = await store.search(
            workspace_id="ws1",
            query_embedding=[0.1] * 768,
            limit=10,
            min_score=0.3,
        )

        assert len(results) == 2
        assert isinstance(results[0], VectorSearchResult)
        assert results[0].note_slug == "notes/alpha"
        assert results[0].score == pytest.approx(0.92)
        assert results[1].note_title is None

    @pytest.mark.asyncio
    async def test_search_empty_returns_empty_list(self, store: PgVectorStore) -> None:
        pool, conn = _make_pool_mock(fetch=[])
        store._pool = pool

        results = await store.search("ws1", [0.0] * 768)

        assert results == []


# ---------------------------------------------------------------------------
# needs_update
# ---------------------------------------------------------------------------


class TestNeedsUpdate:
    @pytest.mark.asyncio
    async def test_needs_update_when_no_row_exists(self, store: PgVectorStore) -> None:
        pool, conn = _make_pool_mock(fetchrow=None)
        store._pool = pool

        result = await store.needs_update("ws1", "notes/new", "hash123")

        assert result is True

    @pytest.mark.asyncio
    async def test_needs_update_when_hash_changed(self, store: PgVectorStore) -> None:
        pool, conn = _make_pool_mock(fetchrow={"content_hash": "old_hash"})
        store._pool = pool

        result = await store.needs_update("ws1", "notes/existing", "new_hash")

        assert result is True

    @pytest.mark.asyncio
    async def test_no_update_when_hash_matches(self, store: PgVectorStore) -> None:
        pool, conn = _make_pool_mock(fetchrow={"content_hash": "same_hash"})
        store._pool = pool

        result = await store.needs_update("ws1", "notes/unchanged", "same_hash")

        assert result is False


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------


class TestStats:
    @pytest.mark.asyncio
    async def test_stats_aggregates_counts(self, store: PgVectorStore) -> None:
        rows = [
            {
                "total_chunks": 20,
                "unique_notes": 5,
                "model": "nomic-embed-text",
                "model_count": 20,
            }
        ]
        pool, conn = _make_pool_mock(fetch=rows)
        store._pool = pool

        stats = await store.stats("ws1")

        assert isinstance(stats, VectorStoreStats)
        assert stats.workspace_id == "ws1"
        assert stats.total_chunks == 20
        assert stats.unique_notes == 5
        assert stats.model_counts == {"nomic-embed-text": 20}

    @pytest.mark.asyncio
    async def test_stats_empty_workspace(self, store: PgVectorStore) -> None:
        pool, conn = _make_pool_mock(fetch=[])
        store._pool = pool

        stats = await store.stats("ws-empty")

        assert stats.total_chunks == 0
        assert stats.unique_notes == 0
        assert stats.model_counts == {}

    @pytest.mark.asyncio
    async def test_stats_multiple_models(self, store: PgVectorStore) -> None:
        rows = [
            {"total_chunks": 10, "unique_notes": 3, "model": "nomic-embed-text", "model_count": 10},
            {"total_chunks": 5, "unique_notes": 3, "model": "mxbai-embed-large", "model_count": 5},
        ]
        pool, conn = _make_pool_mock(fetch=rows)
        store._pool = pool

        stats = await store.stats("ws2")

        assert stats.total_chunks == 15
        assert stats.model_counts == {"nomic-embed-text": 10, "mxbai-embed-large": 5}


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------


class TestClose:
    @pytest.mark.asyncio
    async def test_close_clears_pool(self, store: PgVectorStore) -> None:
        pool, _ = _make_pool_mock()
        store._pool = pool

        await store.close()

        pool.close.assert_called_once()
        assert store._pool is None

    @pytest.mark.asyncio
    async def test_close_when_no_pool_is_noop(self, store: PgVectorStore) -> None:
        # Should not raise
        await store.close()
        assert store._pool is None
