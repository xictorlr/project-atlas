"""Inference health check — aggregates status from all backends."""

from __future__ import annotations

from atlas_worker.inference.models import InferenceHealth
from atlas_worker.inference.router import InferenceRouter


async def check_inference_health(router: InferenceRouter) -> dict:
    """Return a JSON-serializable health report for the API layer."""
    health = await router.health()
    return {
        "ollama_running": health.ollama.available,
        "ollama_models": health.ollama.models_loaded,
        "whisper_available": health.whisper.available,
        "vlm_available": health.vlm.available,
        "apple_silicon": health.apple_silicon,
        "unified_memory_gb": health.unified_memory_gb,
        "overall_status": health.overall_status,
        "errors": [
            b.error
            for b in [health.ollama, health.whisper, health.vlm]
            if b.error
        ],
    }
