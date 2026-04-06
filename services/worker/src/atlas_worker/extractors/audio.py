"""Audio extractor — delegates to InferenceRouter.transcribe (lightning-whisper-mlx)."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from atlas_worker.inference.models import TranscriptSegment


@dataclass(frozen=True)
class AudioResult:
    text: str
    language: str
    duration_seconds: float
    segments: list[TranscriptSegment]
    confidence: float


async def extract_audio(
    raw: bytes,
    filename: str,
    router: object,
    *,
    language: str | None = None,
) -> AudioResult:
    """Transcribe audio bytes to text via InferenceRouter.transcribe.

    Inputs:  raw bytes of an audio file, original filename for suffix detection,
             an InferenceRouter instance, and optional ISO-639-1 language hint.
    Outputs: AudioResult with full transcript, detected language, duration,
             timestamped segments, and confidence score.
    Failures: raises RuntimeError if transcription returns no text;
              IOError if the temp file cannot be written or cleaned up.
    """
    suffix = _audio_suffix(filename)
    tmp_path = _write_temp(raw, suffix)
    try:
        result = await router.transcribe(  # type: ignore[union-attr]
            tmp_path, language=language
        )
    finally:
        _remove_temp(tmp_path)

    return AudioResult(
        text=result.text,
        language=result.language,
        duration_seconds=result.duration_seconds,
        segments=result.segments,
        confidence=result.confidence,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _audio_suffix(filename: str) -> str:
    """Return the file extension from filename, defaulting to .audio."""
    name = Path(filename).suffix.lower()
    return name if name else ".audio"


def _write_temp(raw: bytes, suffix: str) -> Path:
    """Write raw bytes to a temp file and return its path."""
    tmp_dir = Path(".local/tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    fd, path_str = tempfile.mkstemp(suffix=suffix, dir=str(tmp_dir))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(raw)
    except Exception:
        try:
            os.unlink(path_str)
        except OSError:
            pass
        raise
    return Path(path_str)


def _remove_temp(path: Path) -> None:
    """Delete a temp file, ignoring errors if it no longer exists."""
    try:
        path.unlink()
    except OSError:
        pass
