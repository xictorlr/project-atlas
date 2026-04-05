"""Query execution — parse terms, score against the inverted index, return ranked
SearchResult list with contextual snippets.

Scoring: sum of TF-IDF across matched query terms for each document.
Snippet: extract a ~200-char window centred on the first matching term occurrence.
"""

from __future__ import annotations

import logging

from atlas_api.search.indexer import (
    WorkspaceIndex,
    compute_idf,
    tokenize,
)
from atlas_api.search.models import SearchResult

logger = logging.getLogger(__name__)

_SNIPPET_RADIUS = 120  # chars on each side of the first match position
_DEFAULT_LIMIT = 20


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


def execute_search(
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
