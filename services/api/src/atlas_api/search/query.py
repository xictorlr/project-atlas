"""Query execution — parse terms, score against the inverted index, return ranked
SearchResult list with contextual snippets.

Scoring: sum of TF-IDF across matched query terms for each document.
Snippet: extract a ~200-char window centred on the first matching term occurrence.

Public API
----------
execute_search_lexical(idx, raw_query, limit) -> list[SearchResult]
    Synchronous TF-IDF search over a pre-built WorkspaceIndex.  The original
    ``execute_search`` name is kept as a backward-compatible alias.

execute_search(query, workspace_id, mode, vault_root, db_url) -> list[SearchResult]
    Async multi-mode search: "lexical", "semantic", or "hybrid" (default).
    Hybrid mode fuses lexical and semantic rankings via Reciprocal Rank Fusion.
"""

from __future__ import annotations

import logging
from pathlib import Path

from atlas_api.search.indexer import (
    WorkspaceIndex,
    compute_idf,
    get_or_build_index,
    tokenize,
)
from atlas_api.search.models import SearchResult

logger = logging.getLogger(__name__)

_SNIPPET_RADIUS = 120  # chars on each side of the first match position
_DEFAULT_LIMIT = 20
_RRF_K = 60  # RRF smoothing constant — standard value per Cormack et al.


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_snippet(body: str, positions: list[int]) -> str:
    """Return a ~240-char substring centred on the first hit position."""
    if not positions or not body:
        return body[:240] if body else ""

    anchor = positions[0]
    start = max(0, anchor - _SNIPPET_RADIUS)
    end = min(len(body), anchor + _SNIPPET_RADIUS)

    snippet = body[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(body):
        snippet = snippet + "..."
    return snippet


# ---------------------------------------------------------------------------
# Lexical (TF-IDF) search
# ---------------------------------------------------------------------------


def _lexical_search(
    idx: WorkspaceIndex,
    raw_query: str,
    limit: int = _DEFAULT_LIMIT,
) -> list[SearchResult]:
    """Run a lexical TF-IDF search and return ranked results.

    Returns an empty list when the index is empty or no terms match.
    """
    terms = tokenize(raw_query)
    if not terms:
        return []

    # Accumulate TF-IDF scores per note_path
    scores: dict[str, float] = {}
    # note_path -> earliest matching char position (for snippet)
    hit_positions: dict[str, list[int]] = {}

    for term in terms:
        if term not in idx.postings:
            continue
        idf = compute_idf(idx, term)
        for entry in idx.postings[term]:
            scores[entry.note_path] = scores.get(entry.note_path, 0.0) + entry.tf * idf
            if entry.positions:
                existing = hit_positions.get(entry.note_path, [])
                hit_positions[entry.note_path] = existing + entry.positions

    if not scores:
        return []

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    ranked = ranked[:limit]

    results: list[SearchResult] = []
    for note_path, score in ranked:
        # Find the NoteRecord by note_path
        record = None
        for r in idx.notes.values():
            if r.vault_path == note_path:
                record = r
                break

        if record is None:
            logger.warning("Index inconsistency: note_path %r has score but no record", note_path)
            continue

        positions = sorted(hit_positions.get(note_path, []))
        # Positions are relative to combined "title + body"; adjust for body offset
        title_len = len(record.title) + 1  # +1 for the space separator
        body_positions = [p - title_len for p in positions if p >= title_len]

        snippet = _extract_snippet(record.body, body_positions)

        results.append(
            SearchResult(
                note_path=note_path,
                slug=record.slug,
                title=record.title,
                note_type=record.note_type,
                tags=record.tags,
                score=round(score, 6),
                snippet=snippet,
            )
        )

    return results


# ---------------------------------------------------------------------------
# Semantic (pgvector) search
# ---------------------------------------------------------------------------


async def _semantic_search(
    query: str,
    workspace_id: str,
    db_url: str,
    limit: int = _DEFAULT_LIMIT,
) -> list[SearchResult]:
    """Embed query via Ollama, search pgvector, return SearchResults.

    Failure states:
      - Ollama unavailable: propagates ConnectionError to caller.
      - pgvector unavailable: propagates asyncpg exception to caller.
      - No results above min_score threshold: returns empty list.

    The score field is set to the cosine similarity from pgvector.
    snippet is populated from the top chunk_text of each note.
    """
    import httpx

    # -- Embed query via Ollama ------------------------------------------
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "http://localhost:11434/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": query},
        )
        resp.raise_for_status()
        data = resp.json()
        query_embedding: list[float] = data["embedding"]

    # -- Search pgvector ------------------------------------------------
    from atlas_worker.search.vector_store import PgVectorStore  # type: ignore[import]

    store = PgVectorStore(db_url)
    try:
        vector_hits = await store.search(
            workspace_id=workspace_id,
            query_embedding=query_embedding,
            limit=limit,
        )
    finally:
        await store.close()

    # -- Convert VectorSearchResult → SearchResult -----------------------
    # Group chunks by note_slug and keep the top-scoring chunk per note.
    best: dict[str, object] = {}  # slug -> VectorSearchResult
    for hit in vector_hits:
        existing = best.get(hit.note_slug)
        if existing is None or hit.score > existing.score:  # type: ignore[union-attr]
            best[hit.note_slug] = hit

    results: list[SearchResult] = []
    for slug, hit in best.items():
        results.append(
            SearchResult(
                note_path=slug,
                slug=slug,
                title=hit.note_title or slug,  # type: ignore[union-attr]
                note_type="source",
                tags=(),
                score=round(hit.score, 6),  # type: ignore[union-attr]
                snippet=hit.chunk_text[:240],  # type: ignore[union-attr]
            )
        )

    # Sort by score descending (pgvector already ordered, but grouping may unsort)
    results.sort(key=lambda r: r.score, reverse=True)
    return results


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion
# ---------------------------------------------------------------------------


def _reciprocal_rank_fusion(
    lexical: list[SearchResult],
    semantic: list[SearchResult],
    k: int = _RRF_K,
) -> list[SearchResult]:
    """Fuse two ranked lists via Reciprocal Rank Fusion (RRF).

    RRF score for document d = sum(1 / (k + rank_i(d))) across all lists.
    Documents not present in a list are treated as having infinite rank
    (i.e. contributing 0 to the sum).

    The fused list preserves all documents from both lists ranked by their
    combined RRF score.  The ``score`` field is set to the RRF score.
    The ``snippet`` and other fields are taken from whichever source had the
    document (lexical preferred when present in both, since it has richer
    positional snippets).

    Args:
        lexical:  Results from TF-IDF search, rank 1 = index 0.
        semantic: Results from vector search, rank 1 = index 0.
        k:        Smoothing constant (default 60, per standard RRF literature).

    Returns:
        Fused and re-ranked list of SearchResult, highest RRF score first.
    """
    # Map slug → SearchResult for metadata lookup
    by_slug: dict[str, SearchResult] = {}
    for r in lexical:
        by_slug[r.slug] = r
    for r in semantic:
        # Prefer lexical metadata when slug appears in both
        if r.slug not in by_slug:
            by_slug[r.slug] = r

    rrf_scores: dict[str, float] = {}

    for rank, result in enumerate(lexical, start=1):
        rrf_scores[result.slug] = rrf_scores.get(result.slug, 0.0) + 1.0 / (k + rank)

    for rank, result in enumerate(semantic, start=1):
        rrf_scores[result.slug] = rrf_scores.get(result.slug, 0.0) + 1.0 / (k + rank)

    ranked_slugs = sorted(rrf_scores.keys(), key=lambda s: rrf_scores[s], reverse=True)

    fused: list[SearchResult] = []
    for slug in ranked_slugs:
        base = by_slug[slug]
        # Replace score with the RRF score (rounded for readability)
        fused.append(
            SearchResult(
                note_path=base.note_path,
                slug=base.slug,
                title=base.title,
                note_type=base.note_type,
                tags=base.tags,
                score=round(rrf_scores[slug], 8),
                snippet=base.snippet,
            )
        )

    return fused


# ---------------------------------------------------------------------------
# Multi-mode search entrypoint (async)
# ---------------------------------------------------------------------------


async def execute_search(
    query: str,
    workspace_id: str,
    mode: str = "hybrid",
    vault_root: Path | None = None,
    db_url: str | None = None,
) -> list[SearchResult]:
    """Search vault notes with lexical, semantic, or hybrid mode.

    Args:
        query:        Raw user query string.
        workspace_id: Workspace tenant identifier.
        mode:         One of "lexical", "semantic", or "hybrid" (default).
                      Falls back to "lexical" for unknown values.
        vault_root:   Path to the vault root directory (required for lexical / hybrid).
        db_url:       asyncpg DSN for pgvector (required for semantic / hybrid).

    Returns:
        Ranked list of SearchResult.  Hybrid mode returns RRF-fused results.

    Failure states:
        - "lexical" with vault_root=None: returns empty list with a warning.
        - "semantic" with db_url=None: returns empty list with a warning.
        - "hybrid" falls back to lexical-only when db_url is absent; falls back
          to semantic-only when vault_root is absent.
        - Ollama or pgvector unavailable: exception propagates to caller.
    """
    match mode:
        case "lexical":
            if vault_root is None:
                logger.warning("execute_search mode=lexical called without vault_root")
                return []
            idx = get_or_build_index(vault_root, workspace_id)
            return _lexical_search(idx, query)

        case "semantic":
            if db_url is None:
                logger.warning("execute_search mode=semantic called without db_url")
                return []
            return await _semantic_search(query, workspace_id, db_url)

        case "hybrid":
            has_lexical = vault_root is not None
            has_semantic = db_url is not None

            if has_lexical and has_semantic:
                idx = get_or_build_index(vault_root, workspace_id)
                lexical = _lexical_search(idx, query)
                semantic = await _semantic_search(query, workspace_id, db_url)
                return _reciprocal_rank_fusion(lexical, semantic)
            elif has_lexical:
                logger.info("hybrid search: no db_url — falling back to lexical only")
                idx = get_or_build_index(vault_root, workspace_id)
                return _lexical_search(idx, query)
            elif has_semantic:
                logger.info("hybrid search: no vault_root — falling back to semantic only")
                return await _semantic_search(query, workspace_id, db_url)
            else:
                logger.warning("execute_search mode=hybrid called without vault_root or db_url")
                return []

        case _:
            logger.warning("Unknown search mode %r — falling back to lexical", mode)
            if vault_root is None:
                return []
            idx = get_or_build_index(vault_root, workspace_id)
            return _lexical_search(idx, query)


# ---------------------------------------------------------------------------
# Backward-compatible synchronous alias (used by existing route handlers)
# ---------------------------------------------------------------------------

#: Synchronous TF-IDF search over a pre-built WorkspaceIndex.
#: Signature: execute_search_lexical(idx, raw_query, limit) -> list[SearchResult]
execute_search_lexical = _lexical_search
