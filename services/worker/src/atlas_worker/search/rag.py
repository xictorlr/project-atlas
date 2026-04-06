"""RAGPipeline — Retrieve-Augmented Generation shared by all Atlas tools.

Workflow
--------
query():
    1. Embed the question via InferenceRouter.
    2. Search pgvector for top-K passages.
    3. Build a context window (respect max_context_tokens).
    4. Call InferenceRouter.generate() with a citation-grounded prompt.
    5. Return RAGResult with answer, citations, and confidence.

gather_context():
    Steps 1-3 only — no generation.
    Used by output-generator, DeerFlow, and MiroFish to build grounding
    context before their own prompts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from atlas_worker.inference.router import InferenceRouter
from atlas_worker.search.vector_store import PgVectorStore, VectorSearchResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token budget helpers
# ---------------------------------------------------------------------------

_CHARS_PER_TOKEN = 4  # conservative estimate


def _estimate_tokens(text: str) -> int:
    return len(text) // _CHARS_PER_TOKEN


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceCitation:
    """A single cited passage in a RAG answer."""

    note_slug: str
    note_title: str | None
    passage: str
    relevance: float  # cosine similarity score


@dataclass(frozen=True)
class RAGResult:
    """Full result from a RAG query including generated answer and citations."""

    answer: str
    sources: list[SourceCitation]
    confidence: float  # mean relevance of top-K sources used
    model: str
    tokens_used: int


@dataclass(frozen=True)
class ContextPassage:
    """A retrieved passage for context gathering (no generation)."""

    note_slug: str
    note_title: str | None
    passage: str
    relevance: float


# ---------------------------------------------------------------------------
# RAGPipeline
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a knowledgeable assistant with access to a curated knowledge vault.
Answer the question using ONLY the provided context passages.
For every claim you make, cite the source note in the format [[note_slug]].
If the context does not contain enough information, say so clearly.
Do not fabricate facts, statistics, or citations."""

_ANSWER_PROMPT_TEMPLATE = """\
CONTEXT PASSAGES
----------------
{context}

----------------
QUESTION: {question}

Please provide a thorough, well-cited answer based exclusively on the context above.\
"""


class RAGPipeline:
    """Retrieve-Augmented Generation pipeline.

    Args:
        vector_store: :class:`PgVectorStore` for semantic retrieval.
        router: :class:`InferenceRouter` for embed + generate.
        embedding_model: Ollama model name for query embedding.
        generation_model: Ollama model name for answer generation.
        search_limit: Max passages retrieved from pgvector.
        min_score: Minimum similarity threshold for passages.
    """

    def __init__(
        self,
        vector_store: PgVectorStore,
        router: InferenceRouter,
        embedding_model: str = "nomic-embed-text",
        generation_model: str | None = None,
        search_limit: int = 20,
        min_score: float = 0.3,
    ) -> None:
        self._store = vector_store
        self._router = router
        self._embed_model = embedding_model
        self._gen_model = generation_model  # None → router default
        self._search_limit = search_limit
        self._min_score = min_score

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def query(
        self,
        question: str,
        workspace_id: str,
        max_context_tokens: int = 8000,
    ) -> RAGResult:
        """Full RAG: embed → search → generate answer with citations.

        Args:
            question: Natural language question.
            workspace_id: Tenant scope for search.
            max_context_tokens: Token budget for context passages.

        Returns:
            :class:`RAGResult` with generated answer, citations, and confidence.
        """
        passages = await self.gather_context(
            topic=question,
            workspace_id=workspace_id,
            max_tokens=max_context_tokens,
        )

        if not passages:
            return RAGResult(
                answer="No relevant passages found in the knowledge vault for this question.",
                sources=[],
                confidence=0.0,
                model=self._gen_model or "unknown",
                tokens_used=0,
            )

        context_text = _build_context_text(passages)
        prompt = _ANSWER_PROMPT_TEMPLATE.format(
            context=context_text,
            question=question,
        )

        result = await self._router.generate(
            prompt=prompt,
            model=self._gen_model,
            system=_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=2048,
        )

        sources = [
            SourceCitation(
                note_slug=p.note_slug,
                note_title=p.note_title,
                passage=p.passage,
                relevance=p.relevance,
            )
            for p in passages
        ]

        confidence = _mean_relevance(passages)

        return RAGResult(
            answer=result.text,
            sources=sources,
            confidence=round(confidence, 4),
            model=result.model,
            tokens_used=result.tokens_used,
        )

    async def gather_context(
        self,
        topic: str,
        workspace_id: str,
        max_tokens: int = 16000,
    ) -> list[ContextPassage]:
        """Retrieve context passages for a topic without generating an answer.

        Used by output-generator, DeerFlow, and MiroFish to obtain grounding
        context before their own generation prompts.

        Args:
            topic: Query or topic string.
            workspace_id: Tenant scope.
            max_tokens: Token budget for returned passages.

        Returns:
            Ranked list of :class:`ContextPassage`, highest relevance first.
            May be empty if no passages meet the minimum similarity threshold.
        """
        query_embedding = await self._router.embed(topic, model=self._embed_model)

        raw_results: list[VectorSearchResult] = await self._store.search(
            workspace_id=workspace_id,
            query_embedding=query_embedding,
            limit=self._search_limit,
            min_score=self._min_score,
        )

        passages: list[ContextPassage] = []
        budget = max_tokens

        for hit in raw_results:
            tokens = _estimate_tokens(hit.chunk_text)
            if tokens > budget:
                break
            passages.append(
                ContextPassage(
                    note_slug=hit.note_slug,
                    note_title=hit.note_title,
                    passage=hit.chunk_text,
                    relevance=hit.score,
                )
            )
            budget -= tokens

        return passages


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _build_context_text(passages: list[ContextPassage]) -> str:
    """Format passages as a numbered, cited context block."""
    parts: list[str] = []
    for i, p in enumerate(passages, start=1):
        title = p.note_title or p.note_slug
        parts.append(f"[{i}] [{p.note_slug}] {title}\n{p.passage}")
    return "\n\n".join(parts)


def _mean_relevance(passages: list[ContextPassage]) -> float:
    """Return mean relevance score over retrieved passages."""
    if not passages:
        return 0.0
    return sum(p.relevance for p in passages) / len(passages)
