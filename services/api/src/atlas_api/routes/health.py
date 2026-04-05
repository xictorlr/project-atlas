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
