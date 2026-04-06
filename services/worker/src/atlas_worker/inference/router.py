"""Inference Router — single entry point for all local ML inference.

Routes each task to the optimal backend:
- LLM generation/chat → Ollama 0.19+ (MLX backend on Mac)
- Embeddings          → Ollama
- Speech-to-text      → lightning-whisper-mlx
- Vision/OCR          → mlx-vlm

Models load sequentially: load → run → unload → load next.
All models stored in .local/ — nothing leaves the project directory.
"""

from __future__ import annotations

import logging
import platform
import struct
from pathlib import Path

from atlas_worker.inference.backends.ollama import OllamaClient
from atlas_worker.inference.backends.vision_mlx import VisionMLXBackend
from atlas_worker.inference.backends.whisper_mlx import WhisperMLXBackend
from atlas_worker.inference.models import (
    BackendHealth,
    GenerateResult,
    InferenceHealth,
    ModelInfo,
    TranscribeResult,
    VisionResult,
)

logger = logging.getLogger(__name__)


class InferenceRouter:
    """Routes inference requests to the optimal local backend.

    Usage::

        router = InferenceRouter.from_config(settings)
        result = await router.generate("Summarize this text...", model="gemma4:27b")
        transcript = await router.transcribe(Path("meeting.m4a"), language="en")
        ocr = await router.ocr(Path("whiteboard.jpg"))
        embedding = await router.embed("search query text")
    """

    def __init__(
        self,
        ollama: OllamaClient,
        whisper: WhisperMLXBackend,
        vlm: VisionMLXBackend,
        default_model: str = "gemma4:27b",
        embedding_model: str = "nomic-embed-text",
    ) -> None:
        self._ollama = ollama
        self._whisper = whisper
        self._vlm = vlm
        self._default_model = default_model
        self._embedding_model = embedding_model

    @classmethod
    def from_config(cls, settings: object) -> InferenceRouter:
        """Build router from WorkerSettings.

        Expects settings to have:
        - ollama_base_url, ollama_timeout_s
        - mlx_dir (Path to .local/mlx/)
        - whisper_model_size, vlm_model
        - ollama_default_model, ollama_embedding_model
        """
        ollama_base_url = getattr(settings, "ollama_base_url", "http://localhost:11434")
        ollama_timeout = getattr(settings, "ollama_timeout_s", 120)
        mlx_dir = Path(getattr(settings, "mlx_dir", ".local/mlx"))
        whisper_size = getattr(settings, "whisper_model_size", "large-v3")
        vlm_model = getattr(settings, "vlm_model", "mlx-community/gemma-4-12b-vision-4bit")
        default_model = getattr(settings, "ollama_default_model", "gemma4:27b")
        embed_model = getattr(settings, "ollama_embedding_model", "nomic-embed-text")

        return cls(
            ollama=OllamaClient(base_url=ollama_base_url, timeout_s=ollama_timeout),
            whisper=WhisperMLXBackend(model_dir=mlx_dir / "whisper", model_size=whisper_size),
            vlm=VisionMLXBackend(model_dir=mlx_dir / "vlm", model=vlm_model),
            default_model=default_model,
            embedding_model=embed_model,
        )

    # -- LLM (via Ollama) -----------------------------------------------------

    async def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        format_json: bool = False,
    ) -> GenerateResult:
        """Generate text via Ollama. Uses default model if none specified."""
        return await self._ollama.generate(
            model=model or self._default_model,
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            format_json=format_json,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> GenerateResult:
        """Multi-turn chat via Ollama."""
        return await self._ollama.chat(
            model=model or self._default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # -- Embeddings (via Ollama) -----------------------------------------------

    async def embed(self, text: str, *, model: str | None = None) -> list[float]:
        """Generate embedding vector via Ollama."""
        return await self._ollama.embed(
            model=model or self._embedding_model,
            text=text,
        )

    # -- Speech-to-text (via lightning-whisper-mlx) ----------------------------

    async def transcribe(
        self,
        audio_path: Path,
        *,
        language: str | None = None,
        task: str = "transcribe",
    ) -> TranscribeResult:
        """Transcribe audio to text with timestamps.

        Args:
            audio_path: Path to audio file.
            language: ISO-639-1 code ("en", "es"). None = auto-detect.
            task: "transcribe" (same language) or "translate" (to English).
        """
        return await self._whisper.transcribe(
            audio_path, language=language, task=task,
        )

    # -- Vision/OCR (via mlx-vlm) ---------------------------------------------

    async def ocr(
        self,
        image_path: Path,
        prompt: str = "",
    ) -> VisionResult:
        """Extract text from an image using a vision-language model."""
        return await self._vlm.process(
            image_path, prompt=prompt if prompt else None,  # type: ignore[arg-type]
        )

    # -- Model management ------------------------------------------------------

    async def list_models(self) -> dict[str, list[ModelInfo]]:
        """List all available models grouped by backend."""
        ollama_models = await self._ollama.list_models()
        return {
            "ollama": ollama_models,
            "whisper": [
                ModelInfo(
                    name=f"whisper-{self._whisper._model_size}",
                    size_gb=3.0,
                    backend="lightning-whisper-mlx",
                    family="whisper",
                ),
            ],
            "vlm": [
                ModelInfo(
                    name=self._vlm._model_name,
                    size_gb=8.0,
                    backend="mlx-vlm",
                    family="gemma-vision",
                ),
            ],
        }

    def unload_all(self) -> None:
        """Release all MLX models from memory."""
        self._whisper.unload()
        self._vlm.unload()
        logger.info("All MLX models unloaded")

    # -- Health ----------------------------------------------------------------

    async def health(self) -> InferenceHealth:
        """Aggregate health status across all backends."""
        ollama_health = await self._ollama.health()
        whisper_health = self._whisper.health()
        vlm_health = self._vlm.health()

        all_available = ollama_health.available and whisper_health.available and vlm_health.available
        any_available = ollama_health.available or whisper_health.available or vlm_health.available

        if all_available:
            status = "healthy"
        elif any_available:
            status = "degraded"
        else:
            status = "unavailable"

        return InferenceHealth(
            ollama=ollama_health,
            whisper=whisper_health,
            vlm=vlm_health,
            overall_status=status,
            apple_silicon=_is_apple_silicon(),
            unified_memory_gb=_get_system_memory_gb(),
        )

    async def close(self) -> None:
        """Clean up HTTP clients."""
        await self._ollama.close()


# ---------------------------------------------------------------------------
# System helpers
# ---------------------------------------------------------------------------

def _is_apple_silicon() -> bool:
    """Check if running on Apple Silicon (arm64 macOS)."""
    return platform.system() == "Darwin" and platform.machine() == "arm64"


def _get_system_memory_gb() -> float:
    """Get total system memory in GB."""
    try:
        import os

        if hasattr(os, "sysconf"):
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            if pages > 0 and page_size > 0:
                return round(pages * page_size / (1024**3), 1)
    except (ValueError, OSError):
        pass
    return 0.0
