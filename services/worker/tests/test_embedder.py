"""Tests for IncrementalEmbedder with mocked vector_store and router."""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from atlas_worker.search.embedder import (
    EmbedSyncResult,
    IncrementalEmbedder,
    _chunk_text,
    _compute_content_hash,
    _extract_title,
    _path_to_slug,
    _prepare_chunks,
    _split_frontmatter,
)
from atlas_worker.search.vector_store import VectorStoreStats


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_store_mock(
    needs_update: bool = True,
    upsert_count: int = 3,
    stats_total: int = 0,
    slugs: set[str] | None = None,
) -> MagicMock:
    store = AsyncMock()
    store.needs_update = AsyncMock(return_value=needs_update)
    store.upsert = AsyncMock(return_value=upsert_count)
    store.stats = AsyncMock(
        return_value=VectorStoreStats(
            workspace_id="ws1",
            total_chunks=stats_total,
            unique_notes=len(slugs) if slugs else 0,
            model_counts={},
        )
    )
    # _get_pool is used internally by _get_note_slugs
    pool = AsyncMock()
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[{"note_slug": s} for s in (slugs or [])])
    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=False)
    pool.acquire = MagicMock(return_value=acquire_cm)
    store._get_pool = AsyncMock(return_value=pool)
    return store


def _make_router_mock(embedding: list[float] | None = None) -> MagicMock:
    router = AsyncMock()
    router.embed = AsyncMock(return_value=embedding or [0.1] * 768)
    return router


# ---------------------------------------------------------------------------
# Unit tests for helpers
# ---------------------------------------------------------------------------


class TestComputeContentHash:
    def test_is_deterministic(self) -> None:
        h1 = _compute_content_hash("slug/a", 0, "text here")
        h2 = _compute_content_hash("slug/a", 0, "text here")
        assert h1 == h2

    def test_different_slug_gives_different_hash(self) -> None:
        h1 = _compute_content_hash("slug/a", 0, "same text")
        h2 = _compute_content_hash("slug/b", 0, "same text")
        assert h1 != h2

    def test_different_chunk_idx_gives_different_hash(self) -> None:
        h1 = _compute_content_hash("slug", 0, "text")
        h2 = _compute_content_hash("slug", 1, "text")
        assert h1 != h2

    def test_returns_sha256_hex(self) -> None:
        h = _compute_content_hash("slug", 0, "hello")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestSplitFrontmatter:
    def test_extracts_frontmatter(self) -> None:
        content = "---\ntitle: Test\ntags: [a, b]\n---\n\nBody text."
        fm, body = _split_frontmatter(content)
        assert fm is not None
        assert "title: Test" in fm
        assert "Body text." in body

    def test_no_frontmatter_returns_none(self) -> None:
        content = "# Just a heading\nBody text."
        fm, body = _split_frontmatter(content)
        assert fm is None
        assert body == content

    def test_incomplete_frontmatter_returns_none(self) -> None:
        content = "---\ntitle: Incomplete"
        fm, body = _split_frontmatter(content)
        assert fm is None


class TestChunkText:
    def test_short_text_produces_single_chunk(self) -> None:
        text = "Short text that fits in one chunk easily."
        chunks = _chunk_text(text)
        assert len(chunks) == 1

    def test_long_text_produces_multiple_chunks(self) -> None:
        # Create text longer than _CHUNK_TARGET_CHARS
        text = "This is a sentence. " * 200
        chunks = _chunk_text(text)
        assert len(chunks) > 1

    def test_empty_text_returns_empty_list(self) -> None:
        assert _chunk_text("") == []
        assert _chunk_text("   ") == []

    def test_chunks_overlap(self) -> None:
        # With overlap, adjacent chunks should share some words
        text = "Sentence one. Sentence two. Sentence three. " * 100
        chunks = _chunk_text(text, target=200, overlap=50)
        assert len(chunks) > 1
        # At least some consecutive chunks should share content
        shared = any(
            any(word in chunks[i + 1] for word in chunks[i].split()[:5])
            for i in range(len(chunks) - 1)
        )
        assert shared


class TestExtractTitle:
    def test_extracts_from_frontmatter(self, tmp_path: Path) -> None:
        content = '---\ntitle: "My Note Title"\n---\n\nBody'
        path = tmp_path / "note.md"
        assert _extract_title(content, path) == "My Note Title"

    def test_extracts_from_h1(self, tmp_path: Path) -> None:
        content = "# Great Heading\n\nBody text."
        path = tmp_path / "note.md"
        assert _extract_title(content, path) == "Great Heading"

    def test_fallback_to_filename(self, tmp_path: Path) -> None:
        content = "No headings or frontmatter."
        path = tmp_path / "my-cool-note.md"
        title = _extract_title(content, path)
        assert "My" in title or "my" in title.lower()


class TestPathToSlug:
    def test_relative_slug(self, tmp_path: Path) -> None:
        vault = tmp_path / "vault"
        vault.mkdir()
        note = vault / "sources" / "meeting-2024.md"
        slug = _path_to_slug(note, vault)
        assert slug == "sources/meeting-2024"

    def test_top_level_note(self, tmp_path: Path) -> None:
        vault = tmp_path / "vault"
        vault.mkdir()
        note = vault / "index.md"
        slug = _path_to_slug(note, vault)
        assert slug == "index"


class TestPrepareChunks:
    def test_returns_tuples(self) -> None:
        content = "# Title\n\nSome content here for the note."
        chunks = _prepare_chunks(content, "notes/test")
        assert all(isinstance(c, tuple) and len(c) == 3 for c in chunks)

    def test_frontmatter_is_chunk_zero(self) -> None:
        content = "---\ntitle: Test\n---\n\nBody content."
        chunks = _prepare_chunks(content, "notes/fm")
        assert chunks[0][0] == 0
        assert "title: Test" in chunks[0][1]

    def test_chunk_indices_are_sequential(self) -> None:
        content = "---\ntitle: T\n---\n\nFirst body. " * 5
        chunks = _prepare_chunks(content, "notes/seq")
        indices = [c[0] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_hashes_are_unique(self) -> None:
        content = "Passage one. Passage two. Passage three. "
        chunks = _prepare_chunks(content, "notes/u")
        hashes = [c[2] for c in chunks]
        assert len(hashes) == len(set(hashes))


# ---------------------------------------------------------------------------
# IncrementalEmbedder.embed_single_note
# ---------------------------------------------------------------------------


class TestEmbedSingleNote:
    @pytest.mark.asyncio
    async def test_embeds_and_returns_chunk_count(self, tmp_path: Path) -> None:
        note = tmp_path / "meeting.md"
        note.write_text("# Meeting\n\nSome content from the meeting.")

        store = _make_store_mock(upsert_count=2)
        router = _make_router_mock()
        embedder = IncrementalEmbedder(vector_store=store, router=router)

        count = await embedder.embed_single_note("ws1", note, vault_root=tmp_path)

        assert count == 2
        store.upsert.assert_called_once()
        router.embed.assert_called()

    @pytest.mark.asyncio
    async def test_empty_note_skips_upsert(self, tmp_path: Path) -> None:
        note = tmp_path / "empty.md"
        note.write_text("")

        store = _make_store_mock()
        router = _make_router_mock()
        embedder = IncrementalEmbedder(vector_store=store, router=router)

        count = await embedder.embed_single_note("ws1", note, vault_root=tmp_path)

        assert count == 0
        store.upsert.assert_not_called()


# ---------------------------------------------------------------------------
# IncrementalEmbedder.sync
# ---------------------------------------------------------------------------


class TestSync:
    @pytest.mark.asyncio
    async def test_sync_skips_unchanged_notes(self, tmp_path: Path) -> None:
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "note1.md").write_text("# Note 1\n\nContent.")
        (vault / "note2.md").write_text("# Note 2\n\nContent.")

        store = _make_store_mock(needs_update=False)
        router = _make_router_mock()
        embedder = IncrementalEmbedder(vector_store=store, router=router)

        result = await embedder.sync("ws1", vault)

        assert isinstance(result, EmbedSyncResult)
        store.upsert.assert_not_called()
        router.embed.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_embeds_changed_notes(self, tmp_path: Path) -> None:
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "note.md").write_text("# Note\n\nNew content that changed.")

        store = _make_store_mock(needs_update=True, upsert_count=2, slugs=set())
        router = _make_router_mock()
        embedder = IncrementalEmbedder(vector_store=store, router=router)

        result = await embedder.sync("ws1", vault)

        assert isinstance(result, EmbedSyncResult)
        assert result.workspace_id == "ws1"
        store.upsert.assert_called_once()
        router.embed.assert_called()

    @pytest.mark.asyncio
    async def test_sync_nonexistent_vault_returns_empty_result(self, tmp_path: Path) -> None:
        fake_vault = tmp_path / "does_not_exist"

        store = _make_store_mock()
        router = _make_router_mock()
        embedder = IncrementalEmbedder(vector_store=store, router=router)

        result = await embedder.sync("ws1", fake_vault)

        assert result.chunks_added == 0
        assert result.chunks_updated == 0
        assert result.duration_ms == 0

    @pytest.mark.asyncio
    async def test_sync_result_has_correct_timing(self, tmp_path: Path) -> None:
        vault = tmp_path / "vault"
        vault.mkdir()

        store = _make_store_mock(needs_update=False)
        router = _make_router_mock()
        embedder = IncrementalEmbedder(vector_store=store, router=router)

        result = await embedder.sync("ws1", vault)

        assert result.duration_ms >= 0
