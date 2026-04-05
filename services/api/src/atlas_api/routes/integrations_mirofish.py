"""MiroFish simulation gateway endpoints.

Endpoints:
  POST /api/v1/workspaces/{id}/integrations/mirofish/simulations
      Create a simulation record.
  POST /api/v1/workspaces/{id}/integrations/mirofish/simulations/{sim_id}/run
      Run a simulation — requires X-Atlas-Confirm: mirofish header.
  GET  /api/v1/workspaces/{id}/integrations/mirofish/simulations/{sim_id}
      Get simulation status / results.

Safety gates:
  1. ATLAS_MIROFISH_ENABLED must be true (routes not registered otherwise).
  2. Run endpoint requires X-Atlas-Confirm: mirofish header when
     ATLAS_MIROFISH_REQUIRE_CONFIRMATION=true (default).

Isolation guarantee:
  - All adapter calls are wrapped in try/except Exception so that any
    MiroFish failure returns a structured error and never propagates into
    the core pipeline.

Failure states:
  - Flag disabled: 503.
  - Missing confirmation header: 403.
  - sim_id not found: 404.
  - Internal adapter error: 500 with opaque message (no internal detail leaked).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, status

from atlas_api.adapters.mirofish import SimulationConfig, get_mirofish_adapter
from atlas_api.config import settings

logger = logging.getLogger(__name__)

_CONFIRMATION_VALUE = "mirofish"

router = APIRouter(
    prefix="/workspaces/{workspace_id}/integrations/mirofish",
    tags=["integrations", "mirofish"],
)


def _require_enabled() -> None:
    if not settings.mirofish_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MiroFish integration is not enabled. Set ATLAS_MIROFISH_ENABLED=true.",
        )


def _require_confirmation(x_atlas_confirm: str | None) -> None:
    if not settings.mirofish_require_confirmation:
        return
    if x_atlas_confirm != _CONFIRMATION_VALUE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Running a simulation requires explicit confirmation. "
                "Add header: X-Atlas-Confirm: mirofish"
            ),
        )


@router.post("/simulations", summary="Create a MiroFish simulation")
async def create_simulation(
    workspace_id: str,
    body: SimulationConfig,
) -> dict[str, Any]:
    """Create a new simulation record. Does not run it."""
    _require_enabled()
    try:
        adapter = get_mirofish_adapter()
        record = adapter.create_simulation(workspace_id, body)
    except Exception as exc:
        logger.error(
            "MiroFish create_simulation failed",
            extra={"workspace_id": workspace_id, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Simulation creation failed.",
        ) from exc
    return {"success": True, "data": record.model_dump()}


@router.post(
    "/simulations/{sim_id}/run",
    summary="Run a MiroFish simulation (requires confirmation)",
)
async def run_simulation(
    workspace_id: str,
    sim_id: str,
    x_atlas_confirm: str | None = Header(default=None, alias="X-Atlas-Confirm"),
) -> dict[str, Any]:
    """Execute a simulation.

    Requires X-Atlas-Confirm: mirofish header (when confirmation is enabled).
    This is a dangerous workflow: results may consume significant compute and
    have licensing implications.
    """
    _require_enabled()
    _require_confirmation(x_atlas_confirm)
    try:
        adapter = get_mirofish_adapter()
        record = adapter.run_simulation(sim_id)
    except Exception as exc:
        logger.error(
            "MiroFish run_simulation failed",
            extra={"sim_id": sim_id, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Simulation run failed.",
        ) from exc

    if record.status == "failed" and record.error == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation not found: {sim_id}",
        )

    return {"success": True, "data": record.model_dump()}


@router.get(
    "/simulations/{sim_id}",
    summary="Get MiroFish simulation results",
)
async def get_simulation_results(workspace_id: str, sim_id: str) -> dict[str, Any]:
    """Retrieve current status and results for a simulation."""
    _require_enabled()
    try:
        adapter = get_mirofish_adapter()
        record = adapter.get_results(sim_id)
    except Exception as exc:
        logger.error(
            "MiroFish get_results failed",
            extra={"sim_id": sim_id, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve simulation results.",
        ) from exc

    if record.status == "failed" and record.error == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation not found: {sim_id}",
        )

    return {"success": True, "data": record.model_dump()}
