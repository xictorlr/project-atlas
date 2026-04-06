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
        # Step 3: extract text (try async extractors first, then sync)
        # ------------------------------------------------------------------
        filename = source.get("filename", source_id)
        extracted = await _extract_async(raw_bytes, mime_type, filename, ctx)
        if extracted is None:
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
    """Load source record from DB. Returns None if not found.

    Uses ctx["pg_pool"] (asyncpg pool) injected at worker startup.
    Falls back to ctx["db"] (test injection) for unit tests.
    """
    db = ctx.get("db")
    if db is not None:
        return await db.get_source(source_id)  # type: ignore[return-value]

    pool = ctx.get("pg_pool")
    if pool is None:
        return None

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, workspace_id, kind, status, title,
                      description, storage_key, manifest::text AS manifest
               FROM sources WHERE id = $1""",
            source_id,
        )
    if row is None:
        return None

    record = dict(row)
    # Extract mime_type and origin_url from JSON manifest
    import json as _json
    manifest_raw = record.pop("manifest", None)
    manifest = _json.loads(manifest_raw) if manifest_raw else {}
    record["mime_type"] = manifest.get("mime_type")
    record["origin_url"] = manifest.get("origin_url")
    record["filename"] = (record["storage_key"] or "").rsplit("/", 1)[-1]
    return record


async def _update_source_status(
    ctx: dict[str, Any], source_id: str, status: str
) -> None:
    db = ctx.get("db")
    if db is not None:
        await db.update_source_status(source_id, status)  # type: ignore[misc]
        return

    pool = ctx.get("pg_pool")
    if pool is None:
        return
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE sources SET status = $1, updated_at = now() WHERE id = $2",
            status, source_id,
        )


async def _persist_manifest(
    ctx: dict[str, Any],
    source_id: str,
    manifest: dict[str, object],
    title: str | None,
) -> None:
    db = ctx.get("db")
    if db is not None:
        await db.update_source_manifest(source_id, manifest, title, "ready")  # type: ignore[misc]
        return

    pool = ctx.get("pg_pool")
    if pool is None:
        return
    import json as _json
    async with pool.acquire() as conn:
        await conn.execute(
            """UPDATE sources
               SET manifest = $1::json, title = COALESCE($2, title),
                   status = 'ready', updated_at = now()
               WHERE id = $3""",
            _json.dumps(manifest), title, source_id,
        )


def _read_file(storage_key: str) -> bytes:
    """Read raw bytes by storage key.

    The API saves files at <api-cwd>/storage/{workspace_id}/{source_id}/{filename}
    Currently the API runs from services/api/, so storage is at
    services/api/storage/. Worker can override via ATLAS_STORAGE_ROOT env var.
    """
    from pathlib import Path
    import os

    p = Path(storage_key)
    if p.is_absolute():
        return p.read_bytes()

    # Try ATLAS_STORAGE_ROOT first, then default to <atlas_root>/services/api/storage
    storage_root_env = os.environ.get("ATLAS_STORAGE_ROOT")
    if storage_root_env:
        storage_root = Path(storage_root_env)
    else:
        from atlas_worker.config import worker_settings
        storage_root = worker_settings.root / "services" / "api" / "storage"

    full_path = storage_root.resolve() / storage_key
    return full_path.read_bytes()


# ---------------------------------------------------------------------------
# Extraction dispatcher
# ---------------------------------------------------------------------------

def _extract(raw: bytes, mime_type: str | None) -> dict[str, Any]:
    """Route to extractor by mime_type. Returns dict with full_text + optional fields.

    Sync extractors (PDF, HTML, text, Office) return immediately.
    Async extractors (audio, image/OCR) require the InferenceRouter and must
    be called via _extract_async() instead.
    """
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

    # Word .docx
    if "wordprocessingml" in mime or mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        from atlas_worker.extractors.docx import extract_docx
        result = extract_docx(raw)
        return {
            "full_text": result.full_text,
            "title": result.title,
            "language": result.language,
        }

    # Excel .xlsx / .csv
    if "spreadsheetml" in mime or "csv" in mime or mime == "text/csv":
        from atlas_worker.extractors.xlsx import extract_xlsx
        result = extract_xlsx(raw)
        return {
            "full_text": result.full_text,
            "title": None,
            "language": result.language,
        }

    # PowerPoint .pptx
    if "presentationml" in mime:
        from atlas_worker.extractors.pptx import extract_pptx
        result = extract_pptx(raw)
        return {
            "full_text": result.full_text,
            "title": result.title,
            "language": result.language,
        }

    # Default: plain text passthrough
    from atlas_worker.extractors.text import extract_text
    result = extract_text(raw)
    return {
        "full_text": result.full_text,
        "title": result.title,
    }


async def _extract_async(
    raw: bytes, mime_type: str | None, filename: str, ctx: dict[str, Any]
) -> dict[str, Any] | None:
    """Handle async extractors that need the InferenceRouter (audio, images).

    Returns None if mime_type is not an async type (caller should fall through to _extract).
    """
    mime = (mime_type or "").lower()
    router = ctx.get("router")

    # Audio files → Whisper transcription
    if mime.startswith("audio/") and router is not None:
        from atlas_worker.extractors.audio import extract_audio
        result = await extract_audio(raw, filename, router)
        return {
            "full_text": result.text,
            "title": None,
            "language": result.language,
            "duration_seconds": result.duration_seconds,
            "confidence": result.confidence,
        }

    # Image files → Vision OCR
    if mime.startswith("image/") and router is not None:
        from atlas_worker.extractors.ocr import extract_ocr
        result = await extract_ocr(raw, filename, router)
        return {
            "full_text": result.text,
            "title": None,
            "language": result.language,
            "has_tables": result.has_tables,
        }

    return None


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
