"""DeerFlow agent-orchestration adapter.

DeerFlow is an external agent-orchestration framework. This adapter is a thin
wrapper that submits tasks, polls results, and cancels runs via the DeerFlow
HTTP API.

Feature flag: ATLAS_DEERFLOW_ENABLED (default false).
If disabled the module loads but the route returns 503 immediately.

Protocol
--------
DeerFlowAdapter defines the interface. DeerFlowMockAdapter provides a
deterministic in-process stub used in tests and when the flag is off.
HttpDeerFlowAdapter is the real implementation that calls the DeerFlow API.

Invariants (from rules/80-integrations-and-licensing.md):
  - replaceable: depends only on the Protocol, not concrete class
  - thin: no business logic beyond translating between Atlas DTOs and DeerFlow API
  - documented: failure states described per method
  - optional: gated by settings.deerflow_enabled
  - license-aware: DeerFlow is a third-party service; keep its surface minimal
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Protocol, runtime_checkable

import httpx
from pydantic import BaseModel

from atlas_api.config import settings

logger = logging.getLogger(__name__)


# ── Domain DTOs ────────────────────────────────────────────────────────────────


class DeerFlowTask(BaseModel):
    workspace_id: str
    task_type: str
    payload: dict[str, Any]


class DeerFlowTaskResult(BaseModel):
    task_id: str
    status: str  # "pending" | "running" | "completed" | "failed" | "cancelled"
    result: dict[str, Any] | None = None
    error: str | None = None


# ── Protocol ───────────────────────────────────────────────────────────────────


@runtime_checkable
class DeerFlowAdapter(Protocol):
    """Interface that all DeerFlow adapter implementations must satisfy."""

    def submit_task(self, task: DeerFlowTask) -> DeerFlowTaskResult:
        """Submit a task to DeerFlow and return an initial status record.

        Failure states:
          - DeerFlow unreachable: raises httpx.ConnectError (real impl).
          - Invalid task payload: raises ValueError.
        """
        ...

    def get_result(self, task_id: str) -> DeerFlowTaskResult:
        """Poll current status/result for a previously submitted task.

        Failure states:
          - task_id not found: returns status="failed", error="not_found".
          - DeerFlow unreachable: raises httpx.ConnectError (real impl).
        """
        ...

    def cancel(self, task_id: str) -> DeerFlowTaskResult:
        """Request cancellation of a running task.

        Failure states:
          - task_id not found: returns status="failed", error="not_found".
          - Already completed: returns current status without error.
        """
        ...


# ── Mock adapter (default / test) ─────────────────────────────────────────────


class DeerFlowMockAdapter:
    """In-process stub — returns deterministic placeholder responses.

    Used in tests and when ATLAS_DEERFLOW_ENABLED=false.
    """

    def submit_task(self, task: DeerFlowTask) -> DeerFlowTaskResult:
        task_id = str(uuid.uuid4())
        logger.info(
            "DeerFlow mock: submit_task",
            extra={"workspace_id": task.workspace_id, "task_type": task.task_type, "task_id": task_id},
        )
        return DeerFlowTaskResult(
            task_id=task_id,
            status="pending",
            result={"mock": True, "task_type": task.task_type},
        )

    def get_result(self, task_id: str) -> DeerFlowTaskResult:
        logger.info("DeerFlow mock: get_result", extra={"task_id": task_id})
        return DeerFlowTaskResult(
            task_id=task_id,
            status="completed",
            result={"mock": True, "output": "placeholder result"},
        )

    def cancel(self, task_id: str) -> DeerFlowTaskResult:
        logger.info("DeerFlow mock: cancel", extra={"task_id": task_id})
        return DeerFlowTaskResult(task_id=task_id, status="cancelled")


# ── HTTP adapter (production) ──────────────────────────────────────────────────


class HttpDeerFlowAdapter:
    """Real adapter that calls the DeerFlow HTTP API.

    Requires ATLAS_DEERFLOW_BASE_URL and ATLAS_DEERFLOW_API_KEY.

    Failure states:
      - ConnectError / TimeoutException: propagated to caller.
      - Non-2xx response: raises httpx.HTTPStatusError.
    """

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=timeout,
        )

    def submit_task(self, task: DeerFlowTask) -> DeerFlowTaskResult:
        response = self._client.post(
            "/tasks",
            json={"workspace_id": task.workspace_id, "task_type": task.task_type, "payload": task.payload},
        )
        response.raise_for_status()
        data = response.json()
        return DeerFlowTaskResult(
            task_id=data["task_id"],
            status=data.get("status", "pending"),
            result=data.get("result"),
        )

    def get_result(self, task_id: str) -> DeerFlowTaskResult:
        response = self._client.get(f"/tasks/{task_id}")
        if response.status_code == 404:
            return DeerFlowTaskResult(task_id=task_id, status="failed", error="not_found")
        response.raise_for_status()
        data = response.json()
        return DeerFlowTaskResult(
            task_id=task_id,
            status=data.get("status", "unknown"),
            result=data.get("result"),
            error=data.get("error"),
        )

    def cancel(self, task_id: str) -> DeerFlowTaskResult:
        response = self._client.post(f"/tasks/{task_id}/cancel")
        if response.status_code == 404:
            return DeerFlowTaskResult(task_id=task_id, status="failed", error="not_found")
        response.raise_for_status()
        data = response.json()
        return DeerFlowTaskResult(
            task_id=task_id,
            status=data.get("status", "cancelled"),
        )


# ── Factory ───────────────────────────────────────────────────────────────────


def get_deerflow_adapter() -> DeerFlowAdapter:
    """Return the active adapter based on feature flag and config.

    Always returns a valid DeerFlowAdapter — falls back to mock so
    calling code does not need to guard against None.
    """
    if not settings.deerflow_enabled:
        logger.debug("DeerFlow adapter: mock (feature disabled)")
        return DeerFlowMockAdapter()

    if not settings.deerflow_base_url or not settings.deerflow_api_key:
        logger.warning(
            "ATLAS_DEERFLOW_ENABLED=true but base_url or api_key not set — falling back to mock"
        )
        return DeerFlowMockAdapter()

    logger.info("DeerFlow adapter: HTTP (%s)", settings.deerflow_base_url)
    return HttpDeerFlowAdapter(
        base_url=settings.deerflow_base_url,
        api_key=settings.deerflow_api_key,
    )
