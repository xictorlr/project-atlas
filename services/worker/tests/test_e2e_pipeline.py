"""E2E integration test — full consultant pipeline with mocked InferenceRouter.

Simulates the complete workflow for a consultant use case:
  1. Create a text source (a synthetic meeting transcript written to tmp_path).
  2. Run ingest_source job → extracts text, chunks, hashes, builds manifest.
  3. Run compile_vault job  → generates source note + entities + indexes.
  4. Verify vault output: source note exists with required frontmatter fields.
  5. Verify entities were extracted from the transcript text.
  6. Verify index files were rebuilt.
  7. Run compile_vault a second time to verify idempotency.

Design constraints:
  - No real DB (db mocked via MagicMock + AsyncMock).
  - No real Ollama / LLM calls (InferenceRouter.generate mocked).
  - No real pgvector.
  - Only real I/O is tmp_path vault on disk.
  - Self-contained: all fixtures are defined in this file.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from atlas_worker.compiler.source_notes import (
    SourceProvenance,
    SourceRecord,
    make_slug,
)
from atlas_worker.compiler.vault_writer import parse_frontmatter
from atlas_worker.inference.models import GenerateResult
from atlas_worker.jobs.compile import compile_vault
from atlas_worker.jobs.ingest import ingest_source


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_TRANSCRIPT_TEXT = """\
Q3 Strategy Review — Meeting Transcript
Date: 2026-03-15
Attendees: Sarah Chen (CEO), Marcus Webb (CFO), Priya Nair (Head of Growth)

Sarah Chen opened the meeting by reviewing Q2 results.
The Acme Platform achieved 18 percent revenue growth quarter over quarter.

Marcus Webb presented the financial outlook.
Operating costs increased by 7 percent due to infrastructure expansion.
The board approved a budget increase for the AI initiatives.

Priya Nair outlined the growth strategy for Q3.
The team will focus on enterprise clients in the DACH region.
A partnership with GlobalTech Solutions is under negotiation.

Action items:
- Marcus Webb to finalise the revised budget model by 2026-03-22.
- Priya Nair to prepare the DACH market entry brief by 2026-03-29.
- Sarah Chen to schedule follow-up with GlobalTech Solutions board.

Decision: the AI roadmap will be accelerated by one quarter.
"""


def _make_provenance(**kwargs) -> SourceProvenance:
    defaults = {
        "ingest_job_id": "job_e2e_001",
        "content_hash": "sha256:" + hashlib.sha256(_TRANSCRIPT_TEXT.encode()).hexdigest(),
        "mime_type": "text/plain",
        "char_count": len(_TRANSCRIPT_TEXT),
        "ingested_by": "worker/ingest-v1",
        "url": None,
        "retrieved_at": "2026-03-15T10:00:00Z",
    }
    defaults.update(kwargs)
    return SourceProvenance(**defaults)


def _make_source_record(**kwargs) -> SourceRecord:
    defaults = {
        "source_id": "src_e2e_001",
        "workspace_id": "ws_consultant_01",
        "title": "Q3 Strategy Review Meeting Transcript",
        "extracted_text": _TRANSCRIPT_TEXT,
        "provenance": _make_provenance(),
        "tags": ["meeting", "strategy"],
        "author": "Sarah Chen",
        "published_at": "2026-03-15",
        "language": "en",
    }
    defaults.update(kwargs)
    return SourceRecord(**defaults)


def _make_db_mock(storage_key: str) -> MagicMock:
    """Return a minimal DB mock for ingest_source."""
    db = MagicMock()
    db.get_source = AsyncMock(
        return_value={
            "storage_key": storage_key,
            "mime_type": "text/plain",
            "origin_url": None,
            "title": "Q3 Strategy Review Meeting Transcript",
            "filename": "transcript.txt",
        }
    )
    db.update_source_status = AsyncMock()
    db.update_source_manifest = AsyncMock()
    return db


def _make_router_mock() -> MagicMock:
    """Return a mock InferenceRouter that returns deterministic text for generate()."""
    router = MagicMock()
    router.generate = AsyncMock(
        return_value=GenerateResult(
            text=(
                "## Summary\n\n"
                "This transcript records the Q3 strategy review. "
                "Key decisions include accelerating the AI roadmap. "
                "Action items were assigned to Sarah Chen, Marcus Webb, and Priya Nair."
            ),
            model="gemma4:26b",
            backend="ollama",
            tokens_used=120,
            duration_ms=450,
        )
    )
    router.unload_all = MagicMock()
    return router


# ---------------------------------------------------------------------------
# Full pipeline test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_consultant_pipeline(tmp_path: Path) -> None:
    """
    Simulate a consultant workflow:
    1. Create a text source (simulated meeting transcript)
    2. Run ingest job → extract text, chunk, hash
    3. Run compile job → source notes, entities, summaries (mocked LLM)
    4. Verify vault output: source note exists with frontmatter
    5. Verify entities extracted
    6. Verify indexes rebuilt
    """
    vault_root = tmp_path / "vault"
    vault_root.mkdir()

    workspace_id = "ws_consultant_01"
    source_id = "src_e2e_001"

    # ------------------------------------------------------------------
    # Step 1: write transcript file to tmp_path (simulating object storage)
    # ------------------------------------------------------------------
    transcript_file = tmp_path / "transcript.txt"
    transcript_file.write_text(_TRANSCRIPT_TEXT, encoding="utf-8")

    # ------------------------------------------------------------------
    # Step 2: run ingest_source job
    # ------------------------------------------------------------------
    db_mock = _make_db_mock(str(transcript_file))
    ingest_ctx = {"db": db_mock}

    ingest_result = await ingest_source(ingest_ctx, source_id)

    assert ingest_result["status"] == "succeeded", (
        f"ingest_source failed: {ingest_result.get('error')}"
    )
    assert ingest_result["chunk_count"] >= 1
    assert isinstance(ingest_result["content_hash"], str) and len(ingest_result["content_hash"]) == 64
    assert ingest_result["file_size_bytes"] == len(_TRANSCRIPT_TEXT.encode())

    # DB side-effects: status updated to ingesting, manifest persisted
    db_mock.update_source_status.assert_any_await(source_id, "ingesting")
    db_mock.update_source_manifest.assert_awaited_once()

    # ------------------------------------------------------------------
    # Step 3: run compile_vault job with mocked InferenceRouter
    # ------------------------------------------------------------------
    record = _make_source_record()
    router_mock = _make_router_mock()
    compile_ctx = {
        "vault_root": vault_root,
        "db": None,
        "router": router_mock,
    }

    compile_result = await compile_vault(
        compile_ctx,
        workspace_id=workspace_id,
        sources=[record],
        job_id="job_e2e_compile_001",
    )

    assert compile_result["status"] in ("ok", "partial"), (
        f"compile_vault returned unexpected status: {compile_result}"
    )
    assert compile_result["notes_created"] == 1
    assert compile_result["workspace_id"] == workspace_id
    assert isinstance(compile_result["total_time_ms"], int)

    # ------------------------------------------------------------------
    # Step 4: verify source note exists with correct frontmatter
    # ------------------------------------------------------------------
    slug = make_slug(record.title)
    note_path = vault_root / workspace_id / "sources" / f"{slug}.md"

    assert note_path.exists(), f"Source note not found at {note_path}"

    raw = note_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)

    assert fm.get("type") == "source", f"Expected type=source, got: {fm.get('type')}"
    assert fm.get("source_id") == source_id
    assert fm.get("workspace_id") == workspace_id
    assert fm.get("slug") == slug

    # Provenance block
    provenance = fm.get("provenance") or {}
    assert "content_hash" in provenance, "frontmatter missing provenance.content_hash"

    # Title heading in body
    assert f"# {record.title}" in raw, "Source note body missing title heading"

    # ------------------------------------------------------------------
    # Step 5: verify entities were extracted
    # ------------------------------------------------------------------
    # The transcript contains capitalized names (Sarah Chen, Marcus Webb, etc.)
    # and org-like phrases (Acme Platform, GlobalTech Solutions).
    # entity_extraction heuristics should find at least one entity.
    entities_dir = vault_root / workspace_id / "entities"
    entity_files = list(entities_dir.glob("*.md")) if entities_dir.exists() else []

    # We assert at least one entity was found — the heuristic extractor
    # will catch "Sarah Chen" or "Marcus Webb" as capitalized phrases.
    assert len(entity_files) >= 1, (
        f"Expected at least one entity note in {entities_dir}, found {len(entity_files)}. "
        "Transcript contains known entities: Sarah Chen, Marcus Webb, Priya Nair."
    )

    # Spot-check one entity note for required frontmatter
    entity_raw = entity_files[0].read_text(encoding="utf-8")
    entity_fm, _ = parse_frontmatter(entity_raw)
    assert entity_fm.get("type") == "entity", f"entity note type mismatch: {entity_fm.get('type')}"
    assert "provenance" in entity_fm, "entity note missing provenance block"

    # ------------------------------------------------------------------
    # Step 6: verify index files were rebuilt
    # ------------------------------------------------------------------
    ws_dir = vault_root / workspace_id
    sources_index = ws_dir / "indexes" / "sources-index.md"
    entities_index = ws_dir / "indexes" / "entities-index.md"
    tags_index = ws_dir / "indexes" / "tags-index.md"

    assert sources_index.exists(), "sources-index.md not created"
    assert entities_index.exists(), "entities-index.md not created"
    assert tags_index.exists(), "tags-index.md not created"

    # Sources index should reference our note slug
    sources_content = sources_index.read_text(encoding="utf-8")
    assert slug in sources_content, f"Slug {slug!r} not found in sources-index.md"

    # LLM steps were invoked (router.generate was called at least once for the summary)
    router_mock.generate.assert_awaited()
    router_mock.unload_all.assert_called_once()


# ---------------------------------------------------------------------------
# Idempotency test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_compile_pipeline_is_idempotent(tmp_path: Path) -> None:
    """Running compile_vault twice on the same source produces no extra notes."""
    vault_root = tmp_path / "vault"
    vault_root.mkdir()

    record = _make_source_record()
    compile_ctx = {"vault_root": vault_root, "db": None}

    r1 = await compile_vault(
        compile_ctx,
        workspace_id=record.workspace_id,
        sources=[record],
        job_id="job_idem_01",
    )
    r2 = await compile_vault(
        compile_ctx,
        workspace_id=record.workspace_id,
        sources=[record],
        job_id="job_idem_02",
    )

    assert r1["notes_created"] == 1
    assert r2["notes_created"] == 0
    assert r2["notes_updated"] + r2["notes_skipped"] >= 1


# ---------------------------------------------------------------------------
# Ingest failure paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ingest_fails_gracefully_on_missing_file(tmp_path: Path) -> None:
    """ingest_source returns status=failed when file not found."""
    db = MagicMock()
    db.get_source = AsyncMock(
        return_value={
            "storage_key": str(tmp_path / "ghost_file.txt"),
            "mime_type": "text/plain",
            "origin_url": None,
            "title": "Ghost",
            "filename": "ghost_file.txt",
        }
    )
    db.update_source_status = AsyncMock()
    db.update_source_manifest = AsyncMock()

    result = await ingest_source({"db": db}, "src_ghost")
    assert result["status"] == "failed"
    assert result["error"] == "file_not_found"
    db.update_source_status.assert_any_await("src_ghost", "failed")


@pytest.mark.asyncio
async def test_ingest_fails_gracefully_on_missing_source_record() -> None:
    """ingest_source returns status=failed when DB has no record for source_id."""
    db = MagicMock()
    db.get_source = AsyncMock(return_value=None)
    db.update_source_status = AsyncMock()

    result = await ingest_source({"db": db}, "src_missing")
    assert result["status"] == "failed"
    assert result["error"] == "source_not_found"


# ---------------------------------------------------------------------------
# Compile without LLM router
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_compile_without_router_skips_llm_steps(tmp_path: Path) -> None:
    """compile_vault runs to completion without a router in ctx (no LLM steps)."""
    vault_root = tmp_path / "vault"
    vault_root.mkdir()

    record = _make_source_record()
    compile_ctx = {"vault_root": vault_root, "db": None}  # no router

    result = await compile_vault(
        compile_ctx,
        workspace_id=record.workspace_id,
        sources=[record],
        job_id="job_no_router",
    )

    assert result["status"] in ("ok", "partial")
    assert result["notes_created"] == 1
    assert result["llm_enhanced"] is False

    slug = make_slug(record.title)
    note_path = vault_root / record.workspace_id / "sources" / f"{slug}.md"
    assert note_path.exists()
