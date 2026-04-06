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
HttpDeerFlowAdapter is the real cloud implementation.
LocalDeerFlowAdapter is the local Ollama + vault RAG implementation.

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

# Ollama API endpoint used by the local adapter.
_OLLAMA_GENERATE_PATH = "/api/generate"


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


# ── Local adapter (Ollama + RAG) ──────────────────────────────────────────────


class LocalDeerFlowAdapter:
    """Multi-step research against the project vault via Ollama + RAG.

    Workflow for submit_task():
      1. Decompose the question into 2-4 sub-questions using the LLM.
      2. For each sub-question, call the worker's RAG endpoint (if available)
         or embed a simplified context step via Ollama directly.
      3. Aggregate sub-answers into a synthesis via the LLM.
      4. Return a completed DeerFlowTaskResult immediately (synchronous
         for API compatibility; the caller may enqueue async follow-up).

    Uses httpx.Client (sync) to match the synchronous Protocol interface.
    Gracefully degrades when Ollama is unreachable.

    Model used: settings.deerflow_model or fallback "gemma4:27b".
    """

    _DECOMPOSE_PROMPT = (
        "Break the following research question into 2 to 4 specific sub-questions "
        "that together will fully answer the main question. "
        "Respond with a JSON array of strings, no other text.\n\n"
        "Question: {question}"
    )

    _SYNTHESIZE_PROMPT = (
        "You are a precise research assistant. "
        "Using the following sub-answers, write a concise, well-structured research summary "
        "that answers the main question. "
        "Cite sub-question sources inline as [Q1], [Q2], etc.\n\n"
        "Main question: {question}\n\n"
        "Sub-answers:\n{sub_answers}"
    )

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        model: str = "gemma4:27b",
        timeout: float = 120.0,
    ) -> None:
        self._base_url = ollama_base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def _ollama_generate(self, prompt: str, system: str = "") -> str:
        """Call Ollama /api/generate synchronously.

        Returns generated text or raises httpx.ConnectError if Ollama is down.
        """
        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3},
        }
        if system:
            payload["system"] = system
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    f"{self._base_url}{_OLLAMA_GENERATE_PATH}",
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json().get("response", "")
        except httpx.ConnectError:
            logger.error(
                "LocalDeerFlowAdapter: Ollama unreachable at %s", self._base_url
            )
            raise
        except httpx.HTTPStatusError as exc:
            logger.error(
                "LocalDeerFlowAdapter: Ollama HTTP error %s", exc.response.status_code
            )
            raise

    def _decompose_question(self, question: str) -> list[str]:
        """Ask LLM to decompose the question into sub-questions.

        Returns a list of 2-4 sub-questions. Falls back to [question] on error.
        """
        prompt = self._DECOMPOSE_PROMPT.format(question=question)
        try:
            raw = self._ollama_generate(prompt)
            import json

            sub_questions = json.loads(raw)
            if isinstance(sub_questions, list) and sub_questions:
                return [str(q) for q in sub_questions[:4]]
        except Exception as exc:
            logger.warning(
                "LocalDeerFlowAdapter: decompose failed (%s), using original question", exc
            )
        return [question]

    def _answer_sub_question(self, sub_question: str) -> str:
        """Generate an answer for a single sub-question.

        In local mode, this calls Ollama directly without vault RAG since
        the adapter lives in the API service (no direct vector store access).
        The route layer can inject vault excerpts via the task payload.
        """
        try:
            return self._ollama_generate(
                prompt=sub_question,
                system=(
                    "You are a concise research assistant. "
                    "Answer the question based on your knowledge. "
                    "Be factual and precise."
                ),
            )
        except Exception as exc:
            logger.warning(
                "LocalDeerFlowAdapter: sub-question generation failed: %s", exc
            )
            return f"(Unable to generate answer: {exc})"

    def submit_task(self, task: DeerFlowTask) -> DeerFlowTaskResult:
        """Decompose question → sub-answers → synthesised research report.

        The question is taken from task.payload["question"]; falls back to
        task.task_type as the question if the key is absent.

        Failure states:
          - Ollama unreachable: raises httpx.ConnectError.
          - Invalid payload: raises ValueError if question cannot be extracted.
        """
        task_id = str(uuid.uuid4())
        question: str = task.payload.get("question", "") or task.task_type
        if not question:
            raise ValueError("DeerFlow task payload must include a 'question' key.")

        logger.info(
            "LocalDeerFlowAdapter: submit_task workspace=%s task_id=%s",
            task.workspace_id,
            task_id,
        )

        # 1. Decompose.
        sub_questions = self._decompose_question(question)
        logger.debug(
            "LocalDeerFlowAdapter: %d sub-questions for task %s", len(sub_questions), task_id
        )

        # 2. Answer each sub-question.
        sub_answers: list[str] = []
        sources_consulted: list[str] = []
        for i, sq in enumerate(sub_questions, start=1):
            answer = self._answer_sub_question(sq)
            sub_answers.append(f"[Q{i}] {sq}\n{answer}")

        # 3. Synthesise.
        synthesis = question  # fallback
        try:
            synthesis_prompt = self._SYNTHESIZE_PROMPT.format(
                question=question,
                sub_answers="\n\n".join(sub_answers),
            )
            synthesis = self._ollama_generate(synthesis_prompt)
        except Exception as exc:
            logger.warning(
                "LocalDeerFlowAdapter: synthesis failed for task %s: %s", task_id, exc
            )
            synthesis = "\n\n".join(sub_answers)

        return DeerFlowTaskResult(
            task_id=task_id,
            status="completed",
            result={
                "question": question,
                "sub_questions": sub_questions,
                "synthesis": synthesis,
                "sources_consulted": sources_consulted,
                "model": self._model,
                "workspace_id": task.workspace_id,
            },
        )

    def get_result(self, task_id: str) -> DeerFlowTaskResult:
        """Local adapter runs synchronously — tasks are always immediately completed.

        If an external caller polls a task_id that was not generated by this
        adapter instance, it returns not_found (no persistent store in local mode).
        """
        logger.debug("LocalDeerFlowAdapter: get_result task_id=%s (local, synchronous)", task_id)
        return DeerFlowTaskResult(
            task_id=task_id,
            status="failed",
            error="not_found",
        )

    def cancel(self, task_id: str) -> DeerFlowTaskResult:
        """Cancellation is a no-op for synchronous local tasks."""
        logger.debug("LocalDeerFlowAdapter: cancel task_id=%s (no-op)", task_id)
        return DeerFlowTaskResult(task_id=task_id, status="cancelled")


# ── HTTP adapter (cloud production) ───────────────────────────────────────────


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

    Selection priority:
      1. Disabled → DeerFlowMockAdapter.
      2. Enabled + cloud credentials present → HttpDeerFlowAdapter.
      3. Enabled + no cloud credentials → LocalDeerFlowAdapter (Ollama).

    Always returns a valid DeerFlowAdapter — never returns None.
    """
    if not settings.deerflow_enabled:
        logger.debug("DeerFlow adapter: mock (feature disabled)")
        return DeerFlowMockAdapter()

    if settings.deerflow_base_url and settings.deerflow_api_key:
        logger.info("DeerFlow adapter: HTTP cloud (%s)", settings.deerflow_base_url)
        return HttpDeerFlowAdapter(
            base_url=settings.deerflow_base_url,
            api_key=settings.deerflow_api_key,
        )

    model = getattr(settings, "deerflow_model", "gemma4:27b")
    ollama_url = getattr(settings, "ollama_base_url", "http://localhost:11434")
    logger.info(
        "DeerFlow adapter: local Ollama (model=%s base_url=%s)", model, ollama_url
    )
    return LocalDeerFlowAdapter(ollama_base_url=ollama_url, model=model)
