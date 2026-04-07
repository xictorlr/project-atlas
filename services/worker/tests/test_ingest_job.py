"""Integration-style unit tests for ingest_source job function."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest
from atlas_worker.jobs.ingest import ingest_source


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ctx(source: dict | None = None) -> dict:
    """Build a ctx dict with a minimal db mock."""
    db = MagicMock()
    db.get_source = AsyncMock(return_value=source)
    db.update_source_status = AsyncMock()
    db.update_source_manifest = AsyncMock()
    return {"db": db}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestIngestSourceJob:
    @pytest.mark.asyncio
    async def test_returns_failed_when_source_not_found(self):
        ctx = _make_ctx(source=None)
        result = await ingest_source(ctx, "missing-id")
        assert result["status"] == "failed"
        assert result["error"] == "source_not_found"

    @pytest.mark.asyncio
    async def test_returns_failed_when_file_not_found(self):
        source = {
            "storage_key": "/nonexistent/path/file.txt",
            "mime_type": "text/plain",
            "origin_url": None,
            "title": "Test",
        }
        ctx = _make_ctx(source=source)
        result = await ingest_source(ctx, "src-1")
        assert result["status"] == "failed"
        assert result["error"] == "file_not_found"
        ctx["db"].update_source_status.assert_any_await("src-1", "failed")

    @pytest.mark.asyncio
    async def test_ingests_plain_text_file(self):
        content = b"This is a test document.\n\nIt has two paragraphs."
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as fh:
            fh.write(content)
            path = fh.name

        try:
            source = {
                "storage_key": path,
                "mime_type": "text/plain",
                "origin_url": "https://example.com/doc.txt",
                "title": "Test Doc",
            }
            ctx = _make_ctx(source=source)
            result = await ingest_source(ctx, "src-2")

            assert result["status"] == "succeeded"
            assert result["chunk_count"] >= 1
            assert isinstance(result["content_hash"], str)
            assert len(result["content_hash"]) == 64  # SHA-256 hex
            assert result["file_size_bytes"] == len(content)
            ctx["db"].update_source_manifest.assert_awaited_once()
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_ingests_html_file(self):
        html_content = (
            b"<html><head><title>My Page</title></head>"
            b"<body><p>First paragraph content here.</p>"
            b"<p>Second paragraph content here.</p></body></html>"
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as fh:
            fh.write(html_content)
            path = fh.name

        try:
            source = {
                "storage_key": path,
                "mime_type": "text/html",
                "origin_url": None,
                "title": None,
            }
            ctx = _make_ctx(source=source)
            result = await ingest_source(ctx, "src-3")

            assert result["status"] == "succeeded"
            assert result["chunk_count"] >= 1
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_sets_ingesting_status_before_processing(self):
        source = {
            "storage_key": "/nonexistent/file.txt",
            "mime_type": "text/plain",
            "origin_url": None,
            "title": "T",
        }
        ctx = _make_ctx(source=source)
        await ingest_source(ctx, "src-4")
        # Should have called update_source_status with "ingesting" before failure.
        calls = [str(c) for c in ctx["db"].update_source_status.call_args_list]
        assert any("ingesting" in c for c in calls)

    @pytest.mark.asyncio
    async def test_no_db_in_ctx_returns_source_not_found(self):
        result = await ingest_source({}, "src-5")
        assert result["status"] == "failed"
        assert result["error"] == "source_not_found"

    @pytest.mark.asyncio
    async def test_audio_without_router_falls_back_to_placeholder(self):
        """Audio uploads must succeed even when no InferenceRouter is wired in."""
        audio_bytes = b"\x00\x00\x00\x20ftypM4A "  # minimal m4a header bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as fh:
            fh.write(audio_bytes)
            path = fh.name

        try:
            source = {
                "storage_key": path,
                "mime_type": "audio/mp4",
                "origin_url": None,
                "title": "Meeting recording",
                "filename": "meeting.m4a",
            }
            ctx = _make_ctx(source=source)
            result = await ingest_source(ctx, "src-audio-1")

            assert result["status"] == "succeeded"
            assert result["chunk_count"] >= 1
            ctx["db"].update_source_manifest.assert_awaited_once()
            args = ctx["db"].update_source_manifest.call_args.args
            manifest = args[1]
            assert manifest["needs_reingest"] is True
            assert "placeholder=true" in manifest["confidence_notes"]
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_image_without_router_falls_back_to_placeholder(self):
        """Image uploads must succeed even when the vision backend is missing."""
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as fh:
            fh.write(png_bytes)
            path = fh.name

        try:
            source = {
                "storage_key": path,
                "mime_type": "image/png",
                "origin_url": None,
                "title": "Whiteboard",
                "filename": "whiteboard.png",
            }
            ctx = _make_ctx(source=source)
            result = await ingest_source(ctx, "src-img-1")

            assert result["status"] == "succeeded"
            assert result["chunk_count"] >= 1
            args = ctx["db"].update_source_manifest.call_args.args
            manifest = args[1]
            assert manifest["needs_reingest"] is True
            assert "placeholder=true" in manifest["confidence_notes"]
        finally:
            os.unlink(path)

    @pytest.mark.asyncio
    async def test_audio_with_failing_router_falls_back_to_placeholder(self):
        """If the audio backend raises (e.g., MLX lib not installed), ingest still succeeds."""
        audio_bytes = b"fakedata"
        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as fh:
            fh.write(audio_bytes)
            path = fh.name

        try:
            class _BrokenRouter:
                async def transcribe(self, *args, **kwargs):
                    raise RuntimeError("lightning-whisper-mlx not installed. Run: pip install lightning-whisper-mlx")

            source = {
                "storage_key": path,
                "mime_type": "audio/mpeg",
                "origin_url": None,
                "title": None,
                "filename": "call.mp3",
            }
            ctx = _make_ctx(source=source)
            ctx["router"] = _BrokenRouter()
            result = await ingest_source(ctx, "src-audio-broken")

            assert result["status"] == "succeeded"
            args = ctx["db"].update_source_manifest.call_args.args
            manifest = args[1]
            assert manifest["needs_reingest"] is True
        finally:
            os.unlink(path)
