"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from atlas_api.config import settings
from atlas_api.routes import (
    evals,
    evidence,
    health,
    health_check,
    integrations_deerflow,
    integrations_hermes,
    integrations_mirofish,
    jobs,
    search,
    sources,
    sync,
    vault,
    workspaces,
)

app = FastAPI(
    title="Atlas API",
    version="0.1.0",
    description="Knowledge compiler API service",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── ops routes (no version prefix) ──────────────────────────────────────────
app.include_router(health.router)

# ── v1 API routes ────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"
app.include_router(workspaces.router, prefix=API_PREFIX)
app.include_router(sources.router, prefix=API_PREFIX)
app.include_router(jobs.router, prefix=API_PREFIX)
app.include_router(vault.router, prefix=API_PREFIX)
app.include_router(search.router, prefix=API_PREFIX)
app.include_router(evidence.router, prefix=API_PREFIX)
app.include_router(health_check.router, prefix=API_PREFIX)
app.include_router(evals.router, prefix=API_PREFIX)

# ── optional integration routes (feature-flagged) ────────────────────────────
if settings.obsidian_sync_enabled:
    app.include_router(sync.router, prefix=API_PREFIX)

if settings.deerflow_enabled:
    app.include_router(integrations_deerflow.router, prefix=API_PREFIX)

if settings.hermes_enabled:
    app.include_router(integrations_hermes.router, prefix=API_PREFIX)

if settings.mirofish_enabled:
    app.include_router(integrations_mirofish.router, prefix=API_PREFIX)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"success": False, "error": "Not found", "data": None},
    )


@app.exception_handler(422)
async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": "Validation error", "data": None},
    )
