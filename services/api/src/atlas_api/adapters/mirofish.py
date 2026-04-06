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
deterministic stub. LocalMiroFishAdapter provides Ollama chain-of-thought
reasoning for local simulation.

Invariants (from rules/80-integrations-and-licensing.md):
  - replaceable: Protocol-based
  - thin: no simulation logic; only gateway translation
  - documented: failure states per method
  - optional: gated by settings.mirofish_enabled
  - license-aware: MiroFish may require separate licensing; keep surface minimal
  - isolated: failure must not affect core pipeline

IMPORTANT: MiroFish is off by default. Every run REQUIRES user confirmation
(X-Atlas-Confirm: mirofish header). The LocalMiroFishAdapter logs a WARNING
at run time to make this explicit in audit logs.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Protocol, runtime_checkable

import httpx
from pydantic import BaseModel

from atlas_api.config import settings

logger = logging.getLogger(__name__)

# Ollama API endpoint used by the local adapter.
_OLLAMA_GENERATE_PATH = "/api/generate"


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


# ── Local adapter (Ollama chain-of-thought reasoning) ─────────────────────────


class LocalMiroFishAdapter:
    """What-if scenario simulation via Ollama chain-of-thought reasoning.

    Every run REQUIRES prior user confirmation (enforced at the route layer via
    X-Atlas-Confirm: mirofish header). This adapter additionally logs a WARNING
    at run time to ensure the operation is visible in audit logs.

    Simulation records are held in memory for the lifetime of this adapter
    instance. In production, the route layer creates a new adapter per request
    from the factory, so records are not persisted. This is intentional:
    simulation artefacts should be retrieved from vault/outputs/, not from
    the adapter's in-process store.

    Workflow for run_simulation():
      1. Log WARNING: user confirmation has been received (audit trail).
      2. Build a chain-of-thought prompt from the stored scenario.
      3. Call Ollama with the reasoning model.
      4. Parse the response into a structured impact assessment.
      5. Return SimulationRecord with results.

    Model used: settings.mirofish_model or fallback "qwen3.5-27b-claude-distilled".
    Gracefully degrades when Ollama is unreachable.
    """

    _COT_SYSTEM = (
        "You are a strategic analyst performing a what-if scenario simulation. "
        "Think step by step. Reason carefully through impacts, risks, and timeline effects. "
        "Base your analysis ONLY on the provided scenario and parameters. "
        "Do NOT fabricate statistics or invent external factors. "
        "Structure your response as:\n"
        "## Reasoning\n<step-by-step chain of thought>\n\n"
        "## Impact Assessment\n<structured bullet points per affected area>\n\n"
        "## Risks\n<likelihood and severity of identified risks>\n\n"
        "## Timeline Effects\n<how the scenario changes the expected timeline>\n\n"
        "## Recommendation\n<one clear recommendation>"
    )

    _COT_PROMPT = (
        "Scenario: {scenario}\n\n"
        "Parameters:\n{parameters}\n\n"
        "Workspace context: {workspace_id}\n\n"
        "Please reason through this scenario step by step and provide a structured impact assessment."
    )

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "qwen3.5-27b-claude-distilled",
        timeout: float = 180.0,
    ) -> None:
        self._base_url = ollama_base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._records: dict[str, SimulationRecord] = {}

    def _ollama_generate(self, prompt: str, system: str = "") -> str:
        """Call Ollama /api/generate synchronously.

        Returns generated text.
        Raises httpx.ConnectError if Ollama is unreachable.
        """
        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},  # low temperature for reasoning
        }
        if system:
            payload["system"] = system
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(
                f"{self._base_url}{_OLLAMA_GENERATE_PATH}",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json().get("response", "")

    def create_simulation(
        self, workspace_id: str, config: SimulationConfig
    ) -> SimulationRecord:
        """Create a simulation record without running it.

        Failure states:
          - Invalid config (empty name): raises ValueError.
        """
        if not config.name:
            raise ValueError("SimulationConfig.name must not be empty.")
        sim_id = str(uuid.uuid4())
        record = SimulationRecord(
            sim_id=sim_id,
            workspace_id=workspace_id,
            status="created",
            config=config,
        )
        self._records[sim_id] = record
        logger.info(
            "LocalMiroFishAdapter: create_simulation sim_id=%s workspace=%s scenario=%s",
            sim_id,
            workspace_id,
            config.scenario,
        )
        return record

    def run_simulation(self, sim_id: str) -> SimulationRecord:
        """Execute the simulation using Ollama chain-of-thought reasoning.

        REQUIRES prior user confirmation at the route layer.
        Logs a WARNING as an audit record for every run.

        Failure states:
          - sim_id not found: returns status="failed", error="not_found".
          - Ollama unreachable: returns status="failed", error describes cause.
          - Ollama HTTP error: returns status="failed", error describes cause.
        """
        record = self._records.get(sim_id)
        if record is None:
            logger.error(
                "LocalMiroFishAdapter: run_simulation sim_id=%s not found", sim_id
            )
            return SimulationRecord(
                sim_id=sim_id,
                workspace_id="unknown",
                status="failed",
                config=SimulationConfig(name="unknown"),
                error="not_found",
            )

        # Mandatory audit warning — every simulation run must be visible in logs.
        logger.warning(
            "LocalMiroFishAdapter: SIMULATION RUN — user confirmation received. "
            "sim_id=%s workspace=%s scenario=%r model=%s. "
            "This is a premium workflow. Ensure licensing compliance.",
            sim_id,
            record.workspace_id,
            record.config.scenario,
            self._model,
        )

        # Mark as running.
        running_record = SimulationRecord(
            sim_id=record.sim_id,
            workspace_id=record.workspace_id,
            status="running",
            config=record.config,
        )
        self._records[sim_id] = running_record

        params_text = "\n".join(
            f"  - {k}: {v}" for k, v in record.config.parameters.items()
        ) or "  (no parameters)"
        prompt = self._COT_PROMPT.format(
            scenario=record.config.scenario,
            parameters=params_text,
            workspace_id=record.workspace_id,
        )

        try:
            reasoning_output = self._ollama_generate(prompt, system=self._COT_SYSTEM)
        except httpx.ConnectError as exc:
            logger.error(
                "LocalMiroFishAdapter: Ollama unreachable during simulation sim_id=%s: %s",
                sim_id,
                exc,
            )
            failed = SimulationRecord(
                sim_id=sim_id,
                workspace_id=record.workspace_id,
                status="failed",
                config=record.config,
                error=f"Ollama unreachable: {exc}",
            )
            self._records[sim_id] = failed
            return failed
        except Exception as exc:
            logger.error(
                "LocalMiroFishAdapter: simulation failed sim_id=%s: %s", sim_id, exc
            )
            failed = SimulationRecord(
                sim_id=sim_id,
                workspace_id=record.workspace_id,
                status="failed",
                config=record.config,
                error=str(exc),
            )
            self._records[sim_id] = failed
            return failed

        # Package the output into a structured result dict.
        completed = SimulationRecord(
            sim_id=sim_id,
            workspace_id=record.workspace_id,
            status="completed",
            config=record.config,
            results={
                "scenario": record.config.scenario,
                "reasoning_output": reasoning_output,
                "model": self._model,
                "parameters": record.config.parameters,
                "workspace_id": record.workspace_id,
            },
        )
        self._records[sim_id] = completed
        logger.info(
            "LocalMiroFishAdapter: simulation complete sim_id=%s workspace=%s",
            sim_id,
            record.workspace_id,
        )
        return completed

    def get_results(self, sim_id: str) -> SimulationRecord:
        """Retrieve current status and results for a simulation.

        Failure states:
          - sim_id not found: returns status="failed", error="not_found".
        """
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

    Selection priority:
      1. Disabled → MiroFishMockAdapter (safe default).
      2. Enabled → LocalMiroFishAdapter (Ollama chain-of-thought).

    MiroFish is disabled by default (settings.mirofish_enabled = False).
    The route layer enforces the X-Atlas-Confirm header separately.
    """
    if not settings.mirofish_enabled:
        logger.debug("MiroFish adapter: mock (feature disabled)")
        return MiroFishMockAdapter()

    model = getattr(settings, "mirofish_model", "qwen3.5-27b-claude-distilled")
    ollama_url = getattr(settings, "ollama_base_url", "http://localhost:11434")
    logger.info(
        "MiroFish adapter: local Ollama chain-of-thought (model=%s base_url=%s)",
        model,
        ollama_url,
    )
    return LocalMiroFishAdapter(ollama_base_url=ollama_url, model=model)
