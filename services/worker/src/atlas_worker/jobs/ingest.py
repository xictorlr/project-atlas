"""Source ingestion job — read raw file, extract text, chunk, build manifest."""

from __future__ import annotations

import hashlib
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Chunk target size in characters (split on paragraph boundaries).
_CHUNK_TARGET = 1500
_CHUNK_MAX = 2000


async def ingest_source(ctx: dict[str, Any], source_id: str) -> dict[str, object]:
    """Ingest a raw source file and write a SourceManifest to the DB.

    Workflow:
      1. Load source record from DB (storage_key, mime_type, origin_url).
      2. Read raw bytes from disk via storage_key.
      3. Dispatch to correct extractor based on mime_type.
      4. Chunk extracted text on paragraph boundaries.
      5. Compute SHA-256 content hash.
      6. Build SourceManifest.
      7. Persist manifest + status=ready to DB.
      8. Return job result dict.

    Failure states:
      - File not found: status → failed, error recorded.
      - Extractor error: status → failed, error recorded.
      - DB write error: propagates to arq for retry.
    """
    logger.info("ingest_source started", extra={"source_id": source_id})

    # ------------------------------------------------------------------
    # Step 1: load source record
    # ------------------------------------------------------------------
    source = await _load_source(ctx, source_id)
    if source is None:
        logger.error("source not found", extra={"source_id": source_id})
        return {"job": "ingest_source", "source_id": source_id, "status": "failed",
                "error": "source_not_found"}

    storage_key: str = source["storage_key"]
    mime_type: str | None = source.get("mime_type")
    origin_url: str | None = source.get("origin_url")

    await _update_source_status(ctx, source_id, "ingesting")

    try:
        # ------------------------------------------------------------------
        # Step 2: read raw file
        # ------------------------------------------------------------------
        raw_bytes = _read_file(storage_key)
        file_size_bytes = len(raw_bytes)

        # ------------------------------------------------------------------
        # Step 3: extract text
        # ------------------------------------------------------------------
        extracted = _extract(raw_bytes, mime_type)
        full_text: str = extracted["full_text"]
        title: str | None = extracted.get("title") or source.get("title")

        # ------------------------------------------------------------------
        # Step 4: chunk
        # ------------------------------------------------------------------
        chunks = _chunk_text(full_text)

        # ------------------------------------------------------------------
        # Step 5: content hash
        # ------------------------------------------------------------------
        content_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()

        # ------------------------------------------------------------------
        # Step 6: build manifest
        # ------------------------------------------------------------------
        ingested_at = datetime.now(timezone.utc).isoformat()
        manifest: dict[str, object] = {
            "ingested_at": ingested_at,
            "normalized_at": None,
            "origin_url": origin_url,
            "mime_type": mime_type,
            "file_size_bytes": file_size_bytes,
            "chunk_count": len(chunks),
            "model": None,
            "confidence_notes": f"content_hash={content_hash}",
        }

        # ------------------------------------------------------------------
        # Step 7: persist
        # ------------------------------------------------------------------
        await _persist_manifest(ctx, source_id, manifest, title)

        logger.info(
            "ingest_source completed",
            extra={"source_id": source_id, "chunks": len(chunks),
                   "bytes": file_size_bytes},
        )
        return {
            "job": "ingest_source",
            "source_id": source_id,
            "status": "succeeded",
            "chunk_count": len(chunks),
            "content_hash": content_hash,
            "file_size_bytes": file_size_bytes,
        }

    except FileNotFoundError:
        logger.exception("file not found", extra={"source_id": source_id,
                                                   "storage_key": storage_key})
        await _update_source_status(ctx, source_id, "failed")
        return {"job": "ingest_source", "source_id": source_id, "status": "failed",
                "error": "file_not_found"}
    except Exception as exc:
        logger.exception("extraction failed", extra={"source_id": source_id})
        await _update_source_status(ctx, source_id, "failed")
        return {"job": "ingest_source", "source_id": source_id, "status": "failed",
                "error": str(exc)}


# ---------------------------------------------------------------------------
# I/O helpers — thin wrappers so tests can patch them
# ---------------------------------------------------------------------------

async def _load_source(ctx: dict[str, Any], source_id: str) -> dict[str, Any] | None:
    """Return source record dict from DB, or None if not found.

    When a real DB session is in ctx["db"], this should query it.
    Currently returns a minimal stub so the job can run end-to-end in tests.
    """
    db = ctx.get("db")
    if db is not None:
        # Real DB path — delegated to caller-injected session.
        return await db.get_source(source_id)  # type: ignore[return-value]
    return None


async def _update_source_status(
    ctx: dict[str, Any], source_id: str, status: str
) -> None:
    db = ctx.get("db")
    if db is not None:
        await db.update_source_status(source_id, status)  # type: ignore[misc]


async def _persist_manifest(
    ctx: dict[str, Any],
    source_id: str,
    manifest: dict[str, object],
    title: str | None,
) -> None:
    db = ctx.get("db")
    if db is not None:
        await db.update_source_manifest(source_id, manifest, title, "ready")  # type: ignore[misc]


def _read_file(storage_key: str) -> bytes:
    """Read raw bytes from a local path (storage_key is an absolute path for now)."""
    with open(storage_key, "rb") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Extraction dispatcher
# ---------------------------------------------------------------------------

def _extract(raw: bytes, mime_type: str | None) -> dict[str, Any]:
    """Route to extractor by mime_type. Returns dict with full_text + optional fields."""
    mime = (mime_type or "text/plain").lower()

    if "pdf" in mime:
        from atlas_worker.extractors.pdf import extract_pdf
        result = extract_pdf(raw)
        return {
            "full_text": result.full_text,
            "title": result.title,
            "author": result.author,
        }

    if "html" in mime or "xml" in mime:
        from atlas_worker.extractors.html import extract_html
        result = extract_html(raw)
        return {
            "full_text": result.full_text,
            "title": result.title,
            "author": result.author,
        }

    # Default: plain text passthrough
    from atlas_worker.extractors.text import extract_text
    result = extract_text(raw)
    return {
        "full_text": result.full_text,
        "title": result.title,
    }


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def _chunk_text(text: str, target: int = _CHUNK_TARGET, max_size: int = _CHUNK_MAX) -> list[str]:
    """Split text into chunks of ~target chars on paragraph boundaries.

    Strategy:
      1. Split on double-newline paragraphs.
      2. Accumulate paragraphs until the chunk would exceed target.
      3. If a single paragraph exceeds max_size, split it on sentence boundaries.
    """
    if not text.strip():
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current_parts: list[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)
        if para_len > max_size:
            # Flush current buffer first.
            if current_parts:
                chunks.append("\n\n".join(current_parts))
                current_parts = []
                current_len = 0
            # Split oversized paragraph on sentence boundaries.
            chunks.extend(_split_sentences(para, target))
            continue

        if current_len + para_len > target and current_parts:
            chunks.append("\n\n".join(current_parts))
            current_parts = []
            current_len = 0

        current_parts.append(para)
        current_len += para_len

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return chunks


def _split_sentences(text: str, target: int) -> list[str]:
    """Split text into sentence-boundary chunks of ~target chars."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        s_len = len(sentence)
        if current_len + s_len > target and current:
            chunks.append(" ".join(current))
            current = []
            current_len = 0
        current.append(sentence)
        current_len += s_len

    if current:
        chunks.append(" ".join(current))

    return chunks
