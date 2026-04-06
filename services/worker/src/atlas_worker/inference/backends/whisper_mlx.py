"""Whisper MLX backend — speech-to-text via lightning-whisper-mlx.

10x faster than whisper.cpp on Apple Silicon. Native MLX, zero-copy memory.
Models cached in .local/mlx/whisper/ — never ~/.cache/.

Handles:
- 20-minute meeting audios with near-perfect accuracy
- EN and ES transcription (Whisper large-v3 supports 99 languages)
- Timestamped segments for meeting minutes generation
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from atlas_worker.inference.models import (
    BackendHealth,
    TranscribeResult,
    TranscriptSegment,
)

logger = logging.getLogger(__name__)

_BACKEND_NAME = "lightning-whisper-mlx"


class WhisperMLXBackend:
    """Speech-to-text backend using lightning-whisper-mlx.

    Models are downloaded on first use and cached in ``model_dir``.
    Set HF_HOME to the same directory to keep everything project-local.
    """

    def __init__(self, model_dir: Path, model_size: str = "large-v3") -> None:
        self._model_dir = model_dir
        self._model_size = model_size
        self._model: object | None = None

    def _ensure_model(self) -> object:
        """Lazy-load the Whisper model on first call."""
        if self._model is not None:
            return self._model

        import os

        os.environ["HF_HOME"] = str(self._model_dir)

        try:
            from lightning_whisper_mlx import LightningWhisperMLX

            logger.info("Loading Whisper %s from %s", self._model_size, self._model_dir)
            self._model = LightningWhisperMLX(
                model=self._model_size,
                batch_size=12,
                quant=None,
            )
            return self._model
        except ImportError:
            raise RuntimeError(
                "lightning-whisper-mlx not installed. "
                "Run: pip install lightning-whisper-mlx"
            )

    async def transcribe(
        self,
        audio_path: Path,
        *,
        language: str | None = None,
        task: str = "transcribe",
    ) -> TranscribeResult:
        """Transcribe an audio file to text with timestamps.

        Args:
            audio_path: Path to audio file (wav, mp3, m4a, etc.)
            language: ISO-639-1 code (e.g. "en", "es"). None = auto-detect.
            task: "transcribe" = same language output, "translate" = English output.

        Returns:
            TranscribeResult with full text, segments, and metadata.
        """
        model = self._ensure_model()

        start = time.monotonic()
        result = model.transcribe(  # type: ignore[union-attr]
            str(audio_path),
            language=language,
            task=task,
        )
        elapsed = time.monotonic() - start

        raw_segments = result.get("segments", [])
        segments = [
            TranscriptSegment(
                start=seg.get("start", 0.0),
                end=seg.get("end", 0.0),
                text=seg.get("text", "").strip(),
                confidence=seg.get("avg_logprob", 0.0),
            )
            for seg in raw_segments
        ]

        full_text = result.get("text", "").strip()
        detected_lang = result.get("language", language or "unknown")

        duration_seconds = 0.0
        if segments:
            duration_seconds = segments[-1].end

        avg_confidence = 0.0
        if segments:
            avg_confidence = sum(s.confidence for s in segments) / len(segments)

        return TranscribeResult(
            text=full_text,
            language=detected_lang,
            duration_seconds=duration_seconds,
            segments=segments,
            confidence=avg_confidence,
            model=f"whisper-{self._model_size}",
            backend=_BACKEND_NAME,
        )

    def unload(self) -> None:
        """Release model from memory to free RAM for next pipeline stage."""
        self._model = None
        logger.info("Whisper model unloaded")

    def is_available(self) -> bool:
        """Check if lightning-whisper-mlx is importable."""
        try:
            import lightning_whisper_mlx  # noqa: F401

            return True
        except ImportError:
            return False

    def health(self) -> BackendHealth:
        """Return health status for this backend."""
        available = self.is_available()
        models = [f"whisper-{self._model_size}"] if self._model is not None else []
        return BackendHealth(
            name=_BACKEND_NAME,
            available=available,
            models_loaded=models,
            error=None if available else "lightning-whisper-mlx not installed",
        )
