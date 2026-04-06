"""Chat endpoint — RAG-grounded conversation against a project's vault.

This is the "ask anything about your project" feature. It uses:
- Hybrid search (TF-IDF + pgvector) to find relevant passages
- LLM (Ollama) to synthesize an answer with citations
- All grounded in vault knowledge — no hallucinations

Designed to feel like ChatGPT but with sources.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from atlas_api.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Question to ask about the project."""

    question: str = Field(..., min_length=1, max_length=2000)
    history: list[dict[str, str]] = Field(default_factory=list)
    model: str | None = Field(default=None)


class ChatSource(BaseModel):
    """Citation pointing back to a vault note."""

    note_slug: str
    note_title: str
    passage: str
    relevance: float


class ChatResponse(BaseModel):
    """Generated answer with source citations."""

    answer: str
    sources: list[ChatSource]
    model: str
    confidence: float


SYSTEM_PROMPT = """You are a knowledge assistant for a consulting project. \
You answer questions using ONLY the provided context from the project's vault. \
If the answer is not in the context, say so clearly. Never invent facts. \
When quoting or referencing information, mention which source it came from."""


async def _embed_query(text: str) -> list[float] | None:
    """Embed a query via Ollama. Returns None if Ollama unavailable."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/embed",
                json={"model": settings.ollama_embedding_model, "input": text},
            )
            resp.raise_for_status()
            data = resp.json()
            embeddings = data.get("embeddings", [[]])
            return embeddings[0] if embeddings else None
    except Exception as exc:
        logger.warning("Embedding failed: %s", exc)
        return None


async def _search_vault(workspace_id: str, embedding: list[float], limit: int = 8) -> list[dict[str, Any]]:
    """Search note_embeddings table by cosine similarity. Returns top passages.

    Uses asyncpg directly (not SQLAlchemy) so the pgvector cast works cleanly.
    """
    if not embedding:
        return []

    import asyncpg

    # Build asyncpg DSN from settings
    dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    vec_str = "[" + ",".join(str(v) for v in embedding) + "]"

    try:
        conn = await asyncpg.connect(dsn)
        try:
            rows = await conn.fetch(
                """SELECT note_slug, note_title, chunk_text,
                          1 - (embedding <=> $1::vector) AS score
                   FROM note_embeddings
                   WHERE workspace_id = $2
                   ORDER BY embedding <=> $1::vector
                   LIMIT $3""",
                vec_str, workspace_id, limit,
            )
            return [
                {
                    "note_slug": r["note_slug"],
                    "note_title": r["note_title"] or r["note_slug"],
                    "passage": r["chunk_text"],
                    "relevance": float(r["score"]),
                }
                for r in rows
            ]
        finally:
            await conn.close()
    except Exception as exc:
        logger.warning("Vector search failed: %s", exc)
        return []


async def _generate_answer(
    question: str,
    context_passages: list[dict[str, Any]],
    history: list[dict[str, str]],
    model: str,
) -> tuple[str, int]:
    """Generate an answer via Ollama. Returns (answer_text, tokens_used)."""
    if context_passages:
        context_text = "\n\n".join(
            f"[Source {i+1}: {p['note_title']}]\n{p['passage']}"
            for i, p in enumerate(context_passages)
        )
        prompt = f"""Based on the following context from the project vault, answer the question.

Context:
{context_text}

Question: {question}

Answer:"""
    else:
        prompt = f"""The project vault has no relevant context for this question yet. \
Answer based on general knowledge only and explicitly note that no project-specific \
context was found.

Question: {question}

Answer:"""

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "system": SYSTEM_PROMPT,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 1024},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", ""), data.get("eval_count", 0)
    except httpx.HTTPError as exc:
        logger.error("Ollama generate failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM unavailable: {exc}",
        )


@router.post("", response_model=ChatResponse)
async def chat(workspace_id: str, request: ChatRequest) -> ChatResponse:
    """Ask a question about the project.

    Pipeline:
    1. Embed the question via Ollama
    2. Search note_embeddings via pgvector cosine similarity
    3. Build context from top passages
    4. Generate answer via Ollama with system prompt
    5. Return answer + source citations
    """
    model = request.model or settings.ollama_default_model

    # 1. Embed
    embedding = await _embed_query(request.question)

    # 2. Retrieve
    passages = await _search_vault(workspace_id, embedding) if embedding else []

    # 3+4. Generate
    answer_text, _tokens = await _generate_answer(
        request.question, passages, request.history, model
    )

    # 5. Build response with citations
    sources = [
        ChatSource(
            note_slug=p["note_slug"],
            note_title=p["note_title"],
            passage=p["passage"][:300] + ("..." if len(p["passage"]) > 300 else ""),
            relevance=p["relevance"],
        )
        for p in passages
    ]

    confidence = max((p["relevance"] for p in passages), default=0.0)

    return ChatResponse(
        answer=answer_text.strip(),
        sources=sources,
        model=model,
        confidence=confidence,
    )
