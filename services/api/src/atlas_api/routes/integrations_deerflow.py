"""DeerFlow integration endpoints.

Endpoints:
  POST /api/v1/workspaces/{id}/integrations/deerflow/submit
      Submit an agent orchestration task to DeerFlow.
  GET  /api/v1/workspaces/{id}/integrations/deerflow/tasks/{task_id}
      Poll task result.
  POST /api/v1/workspaces/{id}/integrations/deerflow/tasks/{task_id}/cancel
      Request task cancellation.

Feature flag: ATLAS_DEERFLOW_ENABLED — routes return 503 when disabled.

Failure states:
  - Adapter disabled: 503.
  - DeerFlow unreachable (HTTP adapter): 502.
  - Invalid payload: 422.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from atlas_api.adapters.deerflow import DeerFlowTask, get_deerflow_adapter
from atlas_api.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/integrations/deerflow",
    tags=["integrations", "deerflow"],
)


class SubmitTaskRequest(BaseModel):
    task_type: str
    payload: dict[str, Any] = {}


def _require_enabled() -> None:
    if not settings.deerflow_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DeerFlow integration is not enabled. Set ATLAS_DEERFLOW_ENABLED=true.",
        )


@router.post("/submit", summary="Submit a DeerFlow task")
async def submit_task(workspace_id: str, body: SubmitTaskRequest) -> dict[str, Any]:
    """Submit an agent orchestration task to DeerFlow."""
    _require_enabled()
    adapter = get_deerflow_adapter()
    task = DeerFlowTask(
        workspace_id=workspace_id,
        task_type=body.task_type,
        payload=body.payload,
    )
    try:
        result = adapter.submit_task(task)
    except httpx.ConnectError as exc:
        logger.error("DeerFlow unreachable", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="DeerFlow service unreachable.",
        ) from exc
    return {"success": True, "data": result.model_dump()}


@router.get("/tasks/{task_id}", summary="Get DeerFlow task result")
async def get_task_result(workspace_id: str, task_id: str) -> dict[str, Any]:
    """Poll the status and result of a DeerFlow task."""
    _require_enabled()
    adapter = get_deerflow_adapter()
    try:
        result = adapter.get_result(task_id)
    except httpx.ConnectError as exc:
        logger.error("DeerFlow unreachable", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="DeerFlow service unreachable.",
        ) from exc
    return {"success": True, "data": result.model_dump()}


@router.post("/tasks/{task_id}/cancel", summary="Cancel a DeerFlow task")
async def cancel_task(workspace_id: str, task_id: str) -> dict[str, Any]:
    """Request cancellation of a running DeerFlow task."""
    _require_enabled()
    adapter = get_deerflow_adapter()
    try:
        result = adapter.cancel(task_id)
    except httpx.ConnectError as exc:
        logger.error("DeerFlow unreachable", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="DeerFlow service unreachable.",
        ) from exc
    return {"success": True, "data": result.model_dump()}
