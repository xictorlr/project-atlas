"""Health and readiness probes."""

import time

import httpx
from fastapi import APIRouter

from atlas_api.config import settings

router = APIRouter(tags=["ops"])
inference_router = APIRouter(prefix="/api/v1/health", tags=["inference"])
models_router = APIRouter(prefix="/api/v1/models", tags=["inference"])


@router.get("/health")
async def health() -> dict[str, object]:
    """Liveness probe."""
    return {
        "status": "ok",
        "service": "atlas-api",
        "version": "0.1.0",
        "environment": settings.environment,
        "timestamp": time.time(),
    }


@router.get("/health/ready")
async def health_ready() -> dict[str, object]:
    """Readiness probe — checks database connectivity."""
    checks: dict[str, str] = {}
    all_ok = True

    try:
        from atlas_api.db import engine
        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
        all_ok = False

    from fastapi.responses import JSONResponse

    status_code = 200 if all_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if all_ok else "degraded",
            "checks": checks,
            "timestamp": time.time(),
        },
    )


# ---------------------------------------------------------------------------
# Inference health and model management — proxies to local Ollama
# ---------------------------------------------------------------------------


@inference_router.get("/inference")
async def inference_health() -> dict[str, object]:
    """Check if the local Ollama instance is running and which models are loaded."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]

        required = [settings.ollama_default_model, settings.ollama_embedding_model]
        missing = [m for m in required if not any(m in name for name in models)]

        return {
            "ollama_running": True,
            "ollama_url": settings.ollama_base_url,
            "models_available": models,
            "models_required": required,
            "models_missing": missing,
            "default_model": settings.ollama_default_model,
            "embedding_model": settings.ollama_embedding_model,
            "status": "healthy" if not missing else "degraded",
        }
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as exc:
        return {
            "ollama_running": False,
            "ollama_url": settings.ollama_base_url,
            "error": str(exc),
            "status": "unavailable",
        }


@models_router.get("")
async def list_models() -> dict[str, object]:
    """List all installed Ollama models."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            models = data.get("models", [])
            return {
                "models": [
                    {
                        "name": m.get("name", ""),
                        "size_gb": round(m.get("size", 0) / 1e9, 2),
                        "family": m.get("details", {}).get("family", "unknown"),
                        "quantization": m.get("details", {}).get("quantization_level"),
                        "modified_at": m.get("modified_at", ""),
                    }
                    for m in models
                ],
                "total": len(models),
            }
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as exc:
        return {"models": [], "total": 0, "error": str(exc)}
