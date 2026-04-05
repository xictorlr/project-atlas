"""MiroFish simulation gateway adapter.

MiroFish is an optional, isolated simulation engine. This adapter is a thin
gateway that creates, runs, and retrieves simulation results.

Feature flag: ATLAS_MIROFISH_ENABLED (default false, explicitly isolated).
Safety gate: ATLAS_MIROFISH_REQUIRE_CONFIRMATION (default true) — the HTTP
  route checks for the X-Atlas-Confirm: mirofish header before running any
  simulation.

MiroFish is entirely isolated: its adapter import, route registration, and
execution are all conditional. Any unhandled exception inside this module must
not propagate beyond the route handler.

Protocol
--------
MiroFishAdapter defines the interface. MiroFishMockAdapter provides a
deterministic stub. Future: HttpMiroFishAdapter for production.

Invariants (from rules/80-integrations-and-licensing.md):
  - replaceable: Protocol-based
  - thin: no simulation logic; only gateway translation
  - documented: failure states per method
  - optional: gated by settings.mirofish_enabled
  - license-aware: MiroFish may require separate licensing; keep surface minimal
  - isolated: failure must not affect core pipeline
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from atlas_api.config import settings

logger = logging.getLogger(__name__)


# ── Domain DTOs ────────────────────────────────────────────────────────────────


class SimulationConfig(BaseModel):
    name: str
    parameters: dict[str, Any] = {}
    scenario: str = "default"


class SimulationRecord(BaseModel):
    sim_id: str
    workspace_id: str
    status: str  # "created" | "running" | "completed" | "failed"
    config: SimulationConfig
    results: dict[str, Any] | None = None
    error: str | None = None


# ── Protocol ───────────────────────────────────────────────────────────────────


@runtime_checkable
class MiroFishAdapter(Protocol):
    """Interface for all MiroFish adapter implementations."""

    def create_simulation(
        self, workspace_id: str, config: SimulationConfig
    ) -> SimulationRecord:
        """Create a new simulation record.

        Failure states:
          - Invalid config: raises ValueError.
          - MiroFish unreachable (real impl): raises httpx.ConnectError.
        """
        ...

    def run_simulation(self, sim_id: str) -> SimulationRecord:
        """Start execution of a previously created simulation.

        Failure states:
          - sim_id not found: returns status="failed", error="not_found".
          - Already running: returns current record without error.
        """
        ...

    def get_results(self, sim_id: str) -> SimulationRecord:
        """Retrieve current status and results for a simulation.

        Failure states:
          - sim_id not found: returns status="failed", error="not_found".
        """
        ...


# ── Mock adapter ───────────────────────────────────────────────────────────────


class MiroFishMockAdapter:
    """Deterministic in-process stub. Returns placeholder results.

    Used in tests and until a real MiroFish deployment is configured.
    """

    def __init__(self) -> None:
        self._records: dict[str, SimulationRecord] = {}

    def create_simulation(
        self, workspace_id: str, config: SimulationConfig
    ) -> SimulationRecord:
        sim_id = str(uuid.uuid4())
        record = SimulationRecord(
            sim_id=sim_id,
            workspace_id=workspace_id,
            status="created",
            config=config,
        )
        self._records[sim_id] = record
        logger.info(
            "MiroFish mock: create_simulation",
            extra={"sim_id": sim_id, "workspace_id": workspace_id},
        )
        return record

    def run_simulation(self, sim_id: str) -> SimulationRecord:
        record = self._records.get(sim_id)
        if record is None:
            return SimulationRecord(
                sim_id=sim_id,
                workspace_id="unknown",
                status="failed",
                config=SimulationConfig(name="unknown"),
                error="not_found",
            )
        updated = SimulationRecord(
            sim_id=record.sim_id,
            workspace_id=record.workspace_id,
            status="completed",
            config=record.config,
            results={"mock": True, "output": "placeholder simulation result"},
        )
        self._records[sim_id] = updated
        logger.info("MiroFish mock: run_simulation", extra={"sim_id": sim_id})
        return updated

    def get_results(self, sim_id: str) -> SimulationRecord:
        record = self._records.get(sim_id)
        if record is None:
            return SimulationRecord(
                sim_id=sim_id,
                workspace_id="unknown",
                status="failed",
                config=SimulationConfig(name="unknown"),
                error="not_found",
            )
        return record


# ── Factory ───────────────────────────────────────────────────────────────────


def get_mirofish_adapter() -> MiroFishAdapter:
    """Return the active MiroFish adapter.

    Currently always returns the mock. Swap to HttpMiroFishAdapter when a
    production MiroFish endpoint is configured.
    """
    if not settings.mirofish_enabled:
        logger.debug("MiroFish adapter: mock (feature disabled)")
    else:
        logger.info("MiroFish adapter: mock (production adapter not yet wired)")
    return MiroFishMockAdapter()
