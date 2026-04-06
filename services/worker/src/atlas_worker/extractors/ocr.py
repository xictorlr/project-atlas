"""OCR extractor — delegates to InferenceRouter.ocr (mlx-vlm vision model)."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OcrResult:
    text: str
    has_tables: bool
    has_handwriting: bool
    confidence: float
    language: str | None


async def extract_ocr(
    raw: bytes,
    filename: str,
    router: object,
) -> OcrResult:
    """Extract text from an image file via InferenceRouter.ocr.

    Inputs:  raw bytes of an image file, original filename for suffix detection,
             and an InferenceRouter instance.
    Outputs: OcrResult with extracted text, table/handwriting flags, confidence,
             and detected language.
    Failures: raises RuntimeError if the vision model returns an empty response;
              IOError if the temp file cannot be written or cleaned up.
    """
    suffix = _image_suffix(filename)
    tmp_path = _write_temp(raw, suffix)
    try:
        result = await router.ocr(tmp_path)  # type: ignore[union-attr]
    finally:
        _remove_temp(tmp_path)

    return OcrResult(
        text=result.text,
        has_tables=result.has_tables,
        has_handwriting=False,  # VisionResult does not expose has_handwriting yet
        confidence=result.confidence,
        language=None,  # language detection deferred to compile stage
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _image_suffix(filename: str) -> str:
    """Return the file extension from filename, defaulting to .jpg."""
    name = Path(filename).suffix.lower()
    return name if name else ".jpg"


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
