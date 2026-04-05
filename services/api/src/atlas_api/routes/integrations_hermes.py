"""Hermes memory bridge endpoints.

Endpoints:
  POST /api/v1/workspaces/{id}/integrations/hermes/context
      Store a context blob for the workspace.
  GET  /api/v1/workspaces/{id}/integrations/hermes/context
      Retrieve context by query string (query param: q).
  DELETE /api/v1/workspaces/{id}/integrations/hermes/context
      Clear all context for the workspace.

Feature flag: ATLAS_HERMES_ENABLED — routes return 503 when disabled.

Failure states:
  - Adapter disabled: 503.
  - Redis unreachable: 502.
  - Invalid payload: 422.
"""

from __future__ import annotations

import logging
from typing import Any

import redis
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from atlas_api.adapters.hermes import get_hermes_adapter
from atlas_api.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/integrations/hermes",
    tags=["integrations", "hermes"],
)


class StoreContextRequest(BaseModel):
    context: dict[str, Any]


def _require_enabled() -> None:
    if not settings.hermes_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hermes integration is not enabled. Set ATLAS_HERMES_ENABLED=true.",
        )


@router.post("/context", summary="Store Hermes context for workspace")
async def store_context(workspace_id: str, body: StoreContextRequest) -> dict[str, Any]:
    """Persist a context blob in Hermes (Redis-backed)."""
    _require_enabled()
    adapter = get_hermes_adapter()
    try:
        key = adapter.store_context(workspace_id, body.context)
    except redis.RedisError as exc:
        logger.error("Hermes Redis error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hermes storage unavailable.",
        ) from exc
    return {"success": True, "data": {"key": key}}


@router.get("/context", summary="Retrieve Hermes context for workspace")
async def retrieve_context(
    workspace_id: str,
    q: str = Query(..., description="Query string used to locate context"),
) -> dict[str, Any]:
    """Retrieve previously stored context by query string."""
    _require_enabled()
    adapter = get_hermes_adapter()
    try:
        context = adapter.retrieve_context(workspace_id, q)
    except redis.RedisError as exc:
        logger.error("Hermes Redis error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hermes storage unavailable.",
        ) from exc
    if context is None:
        return {"success": True, "data": None}
    return {"success": True, "data": context}


@router.delete("/context", summary="Clear all Hermes context for workspace")
async def clear_context(workspace_id: str) -> dict[str, Any]:
    """Delete all stored Hermes context for the workspace."""
    _require_enabled()
    adapter = get_hermes_adapter()
    try:
        deleted = adapter.clear_context(workspace_id)
    except redis.RedisError as exc:
        logger.error("Hermes Redis error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hermes storage unavailable.",
        ) from exc
    return {"success": True, "data": {"deleted": deleted}}
