"""Vision MLX backend — OCR and image understanding via mlx-vlm.

Handles: documents, whiteboards, screenshots, tables, handwriting.
Models cached in .local/mlx/vlm/ — never ~/.cache/.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from atlas_worker.inference.models import BackendHealth, VisionResult

logger = logging.getLogger(__name__)

_BACKEND_NAME = "mlx-vlm"

_DEFAULT_OCR_PROMPT = (
    "Extract all text from this image. Preserve the structure: "
    "headings, paragraphs, tables (as markdown), lists. "
    "If there is handwriting, transcribe it as accurately as possible."
)


class VisionMLXBackend:
    """Image understanding backend using mlx-vlm.

    Supports 50+ vision-language models via the mlx-community HuggingFace hub.
    """

    def __init__(
        self,
        model_dir: Path,
        model: str = "mlx-community/gemma-4-12b-vision-4bit",
    ) -> None:
        self._model_dir = model_dir
        self._model_name = model
        self._model: object | None = None
        self._processor: object | None = None

    def _ensure_model(self) -> tuple[object, object]:
        """Lazy-load the vision model on first call."""
        if self._model is not None and self._processor is not None:
            return self._model, self._processor

        import os

        os.environ["HF_HOME"] = str(self._model_dir)

        try:
            from mlx_vlm import load

            logger.info("Loading vision model %s from %s", self._model_name, self._model_dir)
            self._model, self._processor = load(self._model_name)
            return self._model, self._processor
        except ImportError:
            raise RuntimeError(
                "mlx-vlm not installed. Run: pip install mlx-vlm"
            )

    async def process(
        self,
        image_path: Path,
        prompt: str = _DEFAULT_OCR_PROMPT,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> VisionResult:
        """Process an image with a vision-language model.

        Args:
            image_path: Path to image file (jpg, png, webp, tiff).
            prompt: Instruction for the model (default: OCR extraction).
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            VisionResult with extracted text and metadata.
        """
        model, processor = self._ensure_model()

        try:
            from mlx_vlm import generate
        except ImportError:
            raise RuntimeError("mlx-vlm not installed. Run: pip install mlx-vlm")

        start = time.monotonic()
        output = generate(
            model,
            processor,
            str(image_path),
            prompt,
            max_tokens=max_tokens,
            temp=temperature,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)

        text = output if isinstance(output, str) else str(output)
        has_tables = "|" in text and "---" in text  # markdown table heuristic

        return VisionResult(
            text=text.strip(),
            model=self._model_name,
            backend=_BACKEND_NAME,
            has_tables=has_tables,
            confidence=0.8,  # vlm doesn't provide confidence; default high
            duration_ms=elapsed_ms,
        )

    def unload(self) -> None:
        """Release model from memory to free RAM for next pipeline stage."""
        self._model = None
        self._processor = None
        logger.info("Vision model unloaded")

    def is_available(self) -> bool:
        """Check if mlx-vlm is importable."""
        try:
            import mlx_vlm  # noqa: F401

            return True
        except ImportError:
            return False

    def health(self) -> BackendHealth:
        """Return health status for this backend."""
        available = self.is_available()
        models = [self._model_name] if self._model is not None else []
        return BackendHealth(
            name=_BACKEND_NAME,
            available=available,
            models_loaded=models,
            error=None if available else "mlx-vlm not installed",
        )
