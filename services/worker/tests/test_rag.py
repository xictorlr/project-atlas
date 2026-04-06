"""Tests for RAGPipeline with mocked vector_store and router."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from atlas_worker.inference.models import GenerateResult
from atlas_worker.search.rag import (
    ContextPassage,
    RAGPipeline,
    RAGResult,
    SourceCitation,
    _build_context_text,
    _mean_relevance,
)
from atlas_worker.search.vector_store import VectorSearchResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_search_results(n: int = 3) -> list[VectorSearchResult]:
    return [
        VectorSearchResult(
            note_slug=f"notes/doc-{i}",
            note_title=f"Document {i}",
            chunk_idx=0,
            chunk_text=f"Passage content for document {i}. This is relevant information.",
            score=round(0.9 - i * 0.05, 2),
            model="nomic-embed-text",
        )
        for i in range(n)
    ]


def _make_store_mock(results: list[VectorSearchResult] | None = None) -> MagicMock:
    store = AsyncMock()
    store.search = AsyncMock(return_value=results if results is not None else _make_search_results())
    return store


def _make_router_mock(
    embedding: list[float] | None = None,
    answer: str = "Based on the context, the answer is clear.",
) -> MagicMock:
    router = AsyncMock()
    router.embed = AsyncMock(return_value=embedding or [0.1] * 768)
    router.generate = AsyncMock(
        return_value=GenerateResult(
            text=answer,
            model="gemma4:27b",
            backend="ollama",
            tokens_used=150,
            duration_ms=500,
        )
    )
    return router


def _make_pipeline(
    results: list[VectorSearchResult] | None = None,
    answer: str = "The answer based on context.",
) -> RAGPipeline:
    store = _make_store_mock(results=results)
    router = _make_router_mock(answer=answer)
    return RAGPipeline(
        vector_store=store,
        router=router,
        search_limit=10,
        min_score=0.3,
    )


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestBuildContextText:
    def test_formats_passages_with_indices(self) -> None:
        passages = [
            ContextPassage(note_slug="notes/a", note_title="Alpha", passage="Content A", relevance=0.9),
            ContextPassage(note_slug="notes/b", note_title=None, passage="Content B", relevance=0.7),
        ]
        text = _build_context_text(passages)
        assert "[1]" in text
        assert "[2]" in text
        assert "notes/a" in text
        assert "Content A" in text
        assert "Content B" in text

    def test_empty_passages_returns_empty_string(self) -> None:
        assert _build_context_text([]) == ""

    def test_uses_slug_when_no_title(self) -> None:
        passages = [
            ContextPassage(note_slug="notes/untitled", note_title=None, passage="Text", relevance=0.8)
        ]
        text = _build_context_text(passages)
        assert "notes/untitled" in text


class TestMeanRelevance:
    def test_correct_average(self) -> None:
        passages = [
            ContextPassage(note_slug="a", note_title=None, passage="", relevance=0.8),
            ContextPassage(note_slug="b", note_title=None, passage="", relevance=0.6),
        ]
        assert _mean_relevance(passages) == pytest.approx(0.7)

    def test_empty_returns_zero(self) -> None:
        assert _mean_relevance([]) == 0.0

    def test_single_passage(self) -> None:
        passages = [ContextPassage(note_slug="a", note_title=None, passage="", relevance=0.95)]
        assert _mean_relevance(passages) == pytest.approx(0.95)


# ---------------------------------------------------------------------------
# gather_context
# ---------------------------------------------------------------------------


class TestGatherContext:
    @pytest.mark.asyncio
    async def test_returns_context_passages(self) -> None:
        pipeline = _make_pipeline(results=_make_search_results(3))

        passages = await pipeline.gather_context("What is Atlas?", "ws1")

        assert len(passages) > 0
        assert all(isinstance(p, ContextPassage) for p in passages)

    @pytest.mark.asyncio
    async def test_embed_called_with_topic(self) -> None:
        store = _make_store_mock()
        router = _make_router_mock()
        pipeline = RAGPipeline(vector_store=store, router=router)

        await pipeline.gather_context("my topic", "ws1")

        router.embed.assert_called_once()
        call_args = router.embed.call_args
        assert call_args[0][0] == "my topic"

    @pytest.mark.asyncio
    async def test_empty_search_results_returns_empty(self) -> None:
        pipeline = _make_pipeline(results=[])

        passages = await pipeline.gather_context("irrelevant query", "ws1")

        assert passages == []

    @pytest.mark.asyncio
    async def test_respects_max_tokens_budget(self) -> None:
        # Each passage is ~50 chars → ~12 tokens; budget of 15 should limit to 1 passage
        short_results = [
            VectorSearchResult(
                note_slug=f"notes/doc-{i}",
                note_title=f"Doc {i}",
                chunk_idx=0,
                chunk_text="A" * 60,  # ~15 tokens
                score=0.9 - i * 0.05,
                model="nomic-embed-text",
            )
            for i in range(5)
        ]
        pipeline = _make_pipeline(results=short_results)

        passages = await pipeline.gather_context("topic", "ws1", max_tokens=20)

        assert len(passages) <= 2  # budget should cut it short

    @pytest.mark.asyncio
    async def test_passages_ordered_by_relevance(self) -> None:
        results = _make_search_results(4)  # already sorted by descending score
        pipeline = _make_pipeline(results=results)

        passages = await pipeline.gather_context("topic", "ws1")

        if len(passages) > 1:
            for i in range(len(passages) - 1):
                assert passages[i].relevance >= passages[i + 1].relevance


# ---------------------------------------------------------------------------
# query
# ---------------------------------------------------------------------------


class TestQuery:
    @pytest.mark.asyncio
    async def test_returns_rag_result(self) -> None:
        pipeline = _make_pipeline()

        result = await pipeline.query("What happened in the meeting?", "ws1")

        assert isinstance(result, RAGResult)
        assert isinstance(result.answer, str)
        assert len(result.answer) > 0

    @pytest.mark.asyncio
    async def test_sources_match_retrieved_passages(self) -> None:
        search_results = _make_search_results(3)
        pipeline = _make_pipeline(results=search_results)

        result = await pipeline.query("question", "ws1")

        assert len(result.sources) == 3
        assert all(isinstance(s, SourceCitation) for s in result.sources)
        for i, source in enumerate(result.sources):
            assert source.note_slug == search_results[i].note_slug

    @pytest.mark.asyncio
    async def test_empty_search_returns_no_context_answer(self) -> None:
        pipeline = _make_pipeline(results=[])

        result = await pipeline.query("query with no matches", "ws1")

        assert isinstance(result, RAGResult)
        assert result.sources == []
        assert result.confidence == 0.0
        assert "No relevant" in result.answer or len(result.answer) > 0

    @pytest.mark.asyncio
    async def test_generate_called_with_context(self) -> None:
        store = _make_store_mock(results=_make_search_results(2))
        router = _make_router_mock()
        pipeline = RAGPipeline(vector_store=store, router=router)

        await pipeline.query("my question", "ws1")

        router.generate.assert_called_once()
        call_kwargs = router.generate.call_args.kwargs
        assert "my question" in call_kwargs.get("prompt", "")

    @pytest.mark.asyncio
    async def test_confidence_is_between_zero_and_one(self) -> None:
        pipeline = _make_pipeline(results=_make_search_results(3))

        result = await pipeline.query("question", "ws1")

        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_model_name_propagated(self) -> None:
        store = _make_store_mock()
        router = _make_router_mock(answer="answer text")
        pipeline = RAGPipeline(vector_store=store, router=router)

        result = await pipeline.query("question", "ws1")

        assert result.model == "gemma4:27b"

    @pytest.mark.asyncio
    async def test_tokens_used_propagated(self) -> None:
        store = _make_store_mock()
        router = _make_router_mock()
        pipeline = RAGPipeline(vector_store=store, router=router)

        result = await pipeline.query("question", "ws1")

        assert result.tokens_used == 150

    @pytest.mark.asyncio
    async def test_workspace_scoped_search(self) -> None:
        store = _make_store_mock()
        router = _make_router_mock()
        pipeline = RAGPipeline(vector_store=store, router=router)

        await pipeline.query("question", workspace_id="tenant-42")

        store.search.assert_called_once()
        call_kwargs = store.search.call_args
        assert call_kwargs[1].get("workspace_id") == "tenant-42" or call_kwargs[0][0] == "tenant-42"


# ---------------------------------------------------------------------------
# Incremental embed + re-query scenario (integration-style with mocks)
# ---------------------------------------------------------------------------


class TestRAGIncrementalFlow:
    @pytest.mark.asyncio
    async def test_query_after_embedding_uses_stored_results(self) -> None:
        """Simulate: embed 3 notes → query → verify results reference those notes."""
        slugs = ["notes/meeting-a", "notes/meeting-b", "notes/summary"]
        search_results = [
            VectorSearchResult(
                note_slug=s,
                note_title=s.split("/")[-1].title(),
                chunk_idx=0,
                chunk_text=f"Content from {s}",
                score=0.85 - i * 0.1,
                model="nomic-embed-text",
            )
            for i, s in enumerate(slugs)
        ]

        pipeline = _make_pipeline(results=search_results)
        result = await pipeline.query("summarise all meetings", "ws1")

        retrieved_slugs = [s.note_slug for s in result.sources]
        assert set(retrieved_slugs) == set(slugs)
