"""Health and readiness probes."""

import time

from fastapi import APIRouter

from atlas_api.config import settings

router = APIRouter(tags=["ops"])


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
