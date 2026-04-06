"""Data contracts shared across all inference backends."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GenerateResult:
    """Result from an LLM generation call."""

    text: str
    model: str
    backend: str  # "ollama"
    tokens_used: int
    duration_ms: int


@dataclass(frozen=True)
class TranscriptSegment:
    """A timestamped segment from audio transcription."""

    start: float  # seconds
    end: float  # seconds
    text: str
    confidence: float


@dataclass(frozen=True)
class TranscribeResult:
    """Result from speech-to-text transcription."""

    text: str
    language: str
    duration_seconds: float
    segments: list[TranscriptSegment]
    confidence: float
    model: str
    backend: str  # "lightning-whisper-mlx"


@dataclass(frozen=True)
class VisionResult:
    """Result from image/OCR processing."""

    text: str
    model: str
    backend: str  # "mlx-vlm"
    has_tables: bool
    confidence: float
    duration_ms: int


@dataclass(frozen=True)
class ModelInfo:
    """Metadata for an installed model."""

    name: str
    size_gb: float
    backend: str  # "ollama", "mlx-whisper", "mlx-vlm"
    family: str
    quantization: str | None = None


@dataclass(frozen=True)
class BackendHealth:
    """Health status for a single backend."""

    name: str
    available: bool
    models_loaded: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class OllamaHealth:
    """Detailed Ollama health info."""

    running: bool
    version: str | None = None
    models_available: list[str] = field(default_factory=list)
    gpu_available: bool = False
    memory_free_gb: float = 0.0


@dataclass(frozen=True)
class InferenceHealth:
    """Aggregated health across all inference backends."""

    ollama: BackendHealth
    whisper: BackendHealth
    vlm: BackendHealth
    overall_status: str  # "healthy", "degraded", "unavailable"
    apple_silicon: bool
    unified_memory_gb: float
