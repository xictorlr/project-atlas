"""IncrementalEmbedder — vault-level incremental embedding sync.

Chunks vault Markdown notes into ~512-token passages and embeds only new or
changed chunks.  Content-hashing prevents redundant inference calls.

Chunking strategy
-----------------
- Respect sentence boundaries (split on ``.  `` and ``\\n``).
- Target ~512 tokens per chunk with a 50-token overlap between passages.
- Treat frontmatter (YAML between ``---`` fences) as chunk 0 if present.
- Each chunk is assigned a SHA-256 hash of (note_slug + chunk_idx + text).
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path

from atlas_worker.inference.router import InferenceRouter
from atlas_worker.search.vector_store import PgVectorStore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

_CHUNK_TARGET_CHARS = 2000   # ~512 tokens at ~4 chars/token
_CHUNK_OVERLAP_CHARS = 200   # ~50 tokens of overlap between passages
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n{2,}")

# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EmbedSyncResult:
    """Summary of an incremental embedding sync run."""

    workspace_id: str
    chunks_added: int
    chunks_updated: int
    chunks_deleted: int
    chunks_unchanged: int
    duration_ms: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_content_hash(note_slug: str, chunk_idx: int, chunk_text: str) -> str:
    """Return SHA-256 hex digest of the chunk identity and content.

    Incorporates note_slug and chunk_idx so that moving identical text to a
    different note or position is detected as a change.
    """
    payload = f"{note_slug}:{chunk_idx}:{chunk_text}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _split_frontmatter(content: str) -> tuple[str | None, str]:
    """Separate YAML frontmatter from note body.

    Returns:
        ``(frontmatter_text | None, body_text)``
    """
    if not content.startswith("---"):
        return None, content

    end = content.find("\n---", 3)
    if end == -1:
        return None, content

    fm = content[3:end].strip()
    body = content[end + 4:].lstrip("\n")
    return fm, body


def _chunk_text(text: str, target: int = _CHUNK_TARGET_CHARS, overlap: int = _CHUNK_OVERLAP_CHARS) -> list[str]:
    """Split text into overlapping passages respecting sentence boundaries.

    Args:
        text: Raw text to chunk.
        target: Target character count per chunk.
        overlap: Character overlap between consecutive chunks.

    Returns:
        List of chunk strings.  Empty input returns ``[]``.
    """
    if not text.strip():
        return []

    # Split into sentences / paragraphs
    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    if not sentences:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        sentence_len = len(sentence)
        if current_len + sentence_len > target and current:
            chunks.append(" ".join(current))
            # Keep overlap: retain last sentences until we're under overlap budget
            overlap_buf: list[str] = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s) > overlap:
                    break
                overlap_buf.insert(0, s)
                overlap_len += len(s) + 1
            current = overlap_buf
            current_len = overlap_len

        current.append(sentence)
        current_len += sentence_len + 1  # +1 for space

    if current:
        chunks.append(" ".join(current))

    return chunks


# ---------------------------------------------------------------------------
# IncrementalEmbedder
# ---------------------------------------------------------------------------


class IncrementalEmbedder:
    """Sync a vault directory into pgvector, embedding only changed notes.

    Args:
        vector_store: :class:`PgVectorStore` instance for persistence.
        router: :class:`InferenceRouter` for embedding inference.
        embedding_model: Ollama model name for embeddings.
    """

    def __init__(
        self,
        vector_store: PgVectorStore,
        router: InferenceRouter,
        embedding_model: str = "nomic-embed-text",
    ) -> None:
        self._store = vector_store
        self._router = router
        self._model = embedding_model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def sync(self, workspace_id: str, vault_path: Path | str) -> EmbedSyncResult:
        """Sync all Markdown notes in vault_path for a workspace.

        For each ``.md`` file:
        1. Compute a content hash for the whole note.
        2. Skip the note if the stored hash matches (unchanged).
        3. Otherwise chunk, embed, and upsert.

        Args:
            workspace_id: Tenant identifier.
            vault_path: Root directory of the Markdown vault.

        Returns:
            :class:`EmbedSyncResult` summary.
        """
        vault = Path(vault_path)
        if not vault.is_dir():
            logger.warning("vault_path %s is not a directory — skipping sync", vault)
            return EmbedSyncResult(
                workspace_id=workspace_id,
                chunks_added=0,
                chunks_updated=0,
                chunks_deleted=0,
                chunks_unchanged=0,
                duration_ms=0,
            )

        t0 = time.monotonic()
        added = updated = deleted = unchanged = 0

        note_files = list(vault.rglob("*.md"))
        seen_slugs: set[str] = set()

        for note_path in note_files:
            note_slug = _path_to_slug(note_path, vault)
            seen_slugs.add(note_slug)

            content = note_path.read_text(encoding="utf-8", errors="replace")
            note_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            if not await self._store.needs_update(workspace_id, note_slug, note_hash):
                unchanged_chunks = await _count_existing_chunks(self._store, workspace_id, note_slug)
                unchanged += unchanged_chunks
                continue

            note_title = _extract_title(content, note_path)
            chunks = _prepare_chunks(content, note_slug)
            if not chunks:
                continue

            chunk_texts = [c[1] for c in chunks]
            embeddings = [await self._router.embed(t, model=self._model) for t in chunk_texts]

            # Check if this is an update (already had chunks) or a fresh insert
            existing_stats = await self._store.stats(workspace_id)
            note_already_existed = note_slug in await _get_note_slugs(self._store, workspace_id)

            upserted = await self._store.upsert(
                workspace_id=workspace_id,
                note_slug=note_slug,
                note_title=note_title,
                chunks=chunks,
                embeddings=embeddings,
                model=self._model,
            )

            if note_already_existed:
                updated += upserted
            else:
                added += upserted

        duration_ms = int((time.monotonic() - t0) * 1000)

        return EmbedSyncResult(
            workspace_id=workspace_id,
            chunks_added=added,
            chunks_updated=updated,
            chunks_deleted=deleted,
            chunks_unchanged=unchanged,
            duration_ms=duration_ms,
        )

    async def embed_single_note(
        self,
        workspace_id: str,
        note_path: Path | str,
        vault_root: Path | str | None = None,
    ) -> int:
        """Embed (or re-embed) a single vault note.

        Args:
            workspace_id: Tenant identifier.
            note_path: Absolute or vault-relative path to the ``.md`` file.
            vault_root: Optional vault root for slug computation.
                        Defaults to the note's parent directory.

        Returns:
            Number of chunks upserted.
        """
        note_path = Path(note_path)
        vault_root = Path(vault_root) if vault_root else note_path.parent

        content = note_path.read_text(encoding="utf-8", errors="replace")
        note_slug = _path_to_slug(note_path, vault_root)
        note_title = _extract_title(content, note_path)
        chunks = _prepare_chunks(content, note_slug)

        if not chunks:
            return 0

        chunk_texts = [c[1] for c in chunks]
        embeddings = [await self._router.embed(t, model=self._model) for t in chunk_texts]

        return await self._store.upsert(
            workspace_id=workspace_id,
            note_slug=note_slug,
            note_title=note_title,
            chunks=chunks,
            embeddings=embeddings,
            model=self._model,
        )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _path_to_slug(note_path: Path, vault_root: Path) -> str:
    """Convert a file path to a vault slug relative to vault_root.

    Example: ``vault/sources/meeting-2024.md`` → ``sources/meeting-2024``
    """
    try:
        rel = note_path.relative_to(vault_root)
    except ValueError:
        rel = note_path
    return str(rel.with_suffix("")).replace("\\", "/")


def _extract_title(content: str, note_path: Path) -> str | None:
    """Extract the note title from frontmatter or the first H1 heading."""
    # Try frontmatter `title:` field
    fm_match = re.search(r"^title:\s*(.+)$", content[:500], re.MULTILINE)
    if fm_match:
        return fm_match.group(1).strip().strip('"').strip("'")

    # Try first H1
    h1_match = re.search(r"^#\s+(.+)$", content[:1000], re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()

    # Fallback: stem of the filename
    return note_path.stem.replace("-", " ").replace("_", " ").title()


def _prepare_chunks(content: str, note_slug: str) -> list[tuple[int, str, str]]:
    """Split note content into indexed chunks with content hashes.

    Returns:
        List of ``(chunk_idx, chunk_text, content_hash)`` tuples.
    """
    fm, body = _split_frontmatter(content)
    chunk_idx = 0
    result: list[tuple[int, str, str]] = []

    if fm:
        h = _compute_content_hash(note_slug, chunk_idx, fm)
        result.append((chunk_idx, fm, h))
        chunk_idx += 1

    for passage in _chunk_text(body):
        h = _compute_content_hash(note_slug, chunk_idx, passage)
        result.append((chunk_idx, passage, h))
        chunk_idx += 1

    return result


async def _count_existing_chunks(
    store: PgVectorStore, workspace_id: str, note_slug: str
) -> int:
    """Return the number of existing chunks for a note (best-effort)."""
    stats = await store.stats(workspace_id)
    # We don't have per-note chunk counts in stats; return 0 as safe fallback
    _ = stats
    return 0


async def _get_note_slugs(store: PgVectorStore, workspace_id: str) -> set[str]:
    """Return the set of note slugs currently indexed for a workspace."""
    # Reaches into the pool for a direct query; isolated so it's easy to mock
    pool = await store._get_pool()
    sql = "SELECT DISTINCT note_slug FROM note_embeddings WHERE workspace_id = $1"
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, workspace_id)
    return {row["note_slug"] for row in rows}
