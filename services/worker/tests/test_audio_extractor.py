"""Unit tests for the audio extractor."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from atlas_worker.extractors.audio import (
    AudioResult,
    _audio_suffix,
    _remove_temp,
    _write_temp,
    extract_audio,
)
from atlas_worker.inference.models import TranscriptSegment, TranscribeResult


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_transcribe_result(
    text: str = "Hello world",
    language: str = "en",
    duration_seconds: float = 5.0,
    confidence: float = 0.95,
) -> TranscribeResult:
    return TranscribeResult(
        text=text,
        language=language,
        duration_seconds=duration_seconds,
        segments=[
            TranscriptSegment(start=0.0, end=5.0, text=text, confidence=confidence)
        ],
        confidence=confidence,
        model="whisper-large-v3",
        backend="lightning-whisper-mlx",
    )


def _make_router(transcribe_result: TranscribeResult) -> MagicMock:
    router = MagicMock()
    router.transcribe = AsyncMock(return_value=transcribe_result)
    return router


# ---------------------------------------------------------------------------
# extract_audio
# ---------------------------------------------------------------------------

class TestExtractAudio:
    @pytest.mark.asyncio
    async def test_returns_audio_result(self):
        raw = b"\x00" * 64  # dummy bytes
        tr = _make_transcribe_result(text="Meeting notes here.")
        router = _make_router(tr)

        result = await extract_audio(raw, "meeting.m4a", router)

        assert isinstance(result, AudioResult)
        assert result.text == "Meeting notes here."
        assert result.language == "en"

    @pytest.mark.asyncio
    async def test_transcribe_called_with_path(self):
        raw = b"\x00" * 32
        tr = _make_transcribe_result()
        router = _make_router(tr)

        await extract_audio(raw, "audio.mp3", router)

        router.transcribe.assert_called_once()
        called_path = router.transcribe.call_args[0][0]
        assert isinstance(called_path, Path)
        assert called_path.suffix == ".mp3"

    @pytest.mark.asyncio
    async def test_temp_file_cleaned_up_on_success(self, tmp_path, monkeypatch):
        raw = b"\x00" * 16
        tr = _make_transcribe_result()
        router = _make_router(tr)
        created_paths: list[Path] = []

        original_write_temp = _write_temp

        def capturing_write_temp(raw_: bytes, suffix: str) -> Path:
            p = original_write_temp(raw_, suffix)
            created_paths.append(p)
            return p

        monkeypatch.setattr(
            "atlas_worker.extractors.audio._write_temp", capturing_write_temp
        )

        await extract_audio(raw, "clip.wav", router)

        # All temp files created during the call must be deleted.
        for p in created_paths:
            assert not p.exists(), f"Temp file was not cleaned up: {p}"

    @pytest.mark.asyncio
    async def test_temp_file_cleaned_up_on_failure(self, monkeypatch):
        raw = b"\x00" * 16
        router = MagicMock()
        router.transcribe = AsyncMock(side_effect=RuntimeError("backend down"))
        created_paths: list[Path] = []

        original_write_temp = _write_temp

        def capturing_write_temp(raw_: bytes, suffix: str) -> Path:
            p = original_write_temp(raw_, suffix)
            created_paths.append(p)
            return p

        monkeypatch.setattr(
            "atlas_worker.extractors.audio._write_temp", capturing_write_temp
        )

        with pytest.raises(RuntimeError):
            await extract_audio(raw, "clip.wav", router)

        for p in created_paths:
            assert not p.exists(), f"Temp file leaked on failure: {p}"

    @pytest.mark.asyncio
    async def test_duration_and_segments_propagated(self):
        raw = b"\x00" * 16
        tr = _make_transcribe_result(duration_seconds=42.5, confidence=0.88)
        router = _make_router(tr)

        result = await extract_audio(raw, "long.m4a", router)

        assert result.duration_seconds == 42.5
        assert result.confidence == 0.88
        assert len(result.segments) == 1

    @pytest.mark.asyncio
    async def test_language_hint_passed_through(self):
        raw = b"\x00" * 16
        tr = _make_transcribe_result(language="es")
        router = _make_router(tr)

        result = await extract_audio(raw, "audio.wav", router, language="es")

        _, kwargs = router.transcribe.call_args
        assert kwargs.get("language") == "es"
        assert result.language == "es"


# ---------------------------------------------------------------------------
# Helpers unit tests
# ---------------------------------------------------------------------------

class TestAudioSuffix:
    def test_extracts_known_extension(self):
        assert _audio_suffix("meeting.m4a") == ".m4a"
        assert _audio_suffix("clip.mp3") == ".mp3"
        assert _audio_suffix("recording.wav") == ".wav"

    def test_no_extension_returns_default(self):
        assert _audio_suffix("audiofile") == ".audio"

    def test_uppercase_lowercased(self):
        assert _audio_suffix("Meeting.M4A") == ".m4a"


class TestWriteAndRemoveTemp:
    def test_write_creates_file(self):
        path = _write_temp(b"test data", ".mp3")
        try:
            assert path.exists()
            assert path.read_bytes() == b"test data"
        finally:
            _remove_temp(path)

    def test_remove_temp_is_idempotent(self):
        path = _write_temp(b"x", ".wav")
        _remove_temp(path)
        _remove_temp(path)  # second call must not raise

    def test_write_uses_local_tmp_dir(self):
        path = _write_temp(b"audio", ".wav")
        try:
            assert ".local" in str(path) or "tmp" in str(path)
        finally:
            _remove_temp(path)
