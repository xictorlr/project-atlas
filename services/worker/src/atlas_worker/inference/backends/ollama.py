"""Ollama backend — async HTTP client for LLM generation and embeddings.

Ollama 0.19+ uses MLX on Apple Silicon for near-native inference speed.
Models stored in OLLAMA_MODELS (.local/ollama/) — never ~/.ollama/.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from atlas_worker.inference.models import BackendHealth, GenerateResult, ModelInfo

logger = logging.getLogger(__name__)

_BACKEND_NAME = "ollama"


@dataclass(frozen=True)
class _OllamaGenerateResponse:
    """Raw response from Ollama /api/generate."""

    response: str
    model: str
    total_duration: int  # nanoseconds
    eval_count: int


class OllamaClient:
    """Async HTTP client for the Ollama REST API at localhost:11434."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout_s: int = 120,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(timeout_s, connect=10.0),
        )

    async def close(self) -> None:
        await self._client.aclose()

    # -- Generation -----------------------------------------------------------

    async def generate(
        self,
        model: str,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        format_json: bool = False,
    ) -> GenerateResult:
        """Generate text from a prompt. Blocks until complete."""
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system
        if format_json:
            payload["format"] = "json"

        start = time.monotonic()
        resp = await self._client.post("/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()
        elapsed_ms = int((time.monotonic() - start) * 1000)

        return GenerateResult(
            text=data.get("response", ""),
            model=data.get("model", model),
            backend=_BACKEND_NAME,
            tokens_used=data.get("eval_count", 0),
            duration_ms=elapsed_ms,
        )

    # -- Chat -----------------------------------------------------------------

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> GenerateResult:
        """Multi-turn chat completion."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        start = time.monotonic()
        resp = await self._client.post("/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        elapsed_ms = int((time.monotonic() - start) * 1000)

        message = data.get("message", {})
        return GenerateResult(
            text=message.get("content", ""),
            model=data.get("model", model),
            backend=_BACKEND_NAME,
            tokens_used=data.get("eval_count", 0),
            duration_ms=elapsed_ms,
        )

    # -- Embeddings -----------------------------------------------------------

    async def embed(self, model: str, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        resp = await self._client.post(
            "/api/embed",
            json={"model": model, "input": text},
        )
        resp.raise_for_status()
        data = resp.json()
        embeddings = data.get("embeddings", [[]])
        return embeddings[0] if embeddings else []

    # -- Model management -----------------------------------------------------

    async def list_models(self) -> list[ModelInfo]:
        """List locally available Ollama models."""
        resp = await self._client.get("/api/tags")
        resp.raise_for_status()
        models = resp.json().get("models", [])
        return [
            ModelInfo(
                name=m.get("name", ""),
                size_gb=round(m.get("size", 0) / 1e9, 2),
                backend=_BACKEND_NAME,
                family=m.get("details", {}).get("family", "unknown"),
                quantization=m.get("details", {}).get("quantization_level"),
            )
            for m in models
        ]

    async def pull_model(self, name: str) -> None:
        """Pull a model from the Ollama registry. Blocks until complete."""
        async with self._client.stream(
            "POST", "/api/pull", json={"name": name, "stream": True}
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                logger.debug("pull %s: %s", name, line)

    # -- Health ---------------------------------------------------------------

    async def health(self) -> BackendHealth:
        """Check if Ollama is running and responsive."""
        try:
            resp = await self._client.get("/api/tags")
            resp.raise_for_status()
            models = [m.get("name", "") for m in resp.json().get("models", [])]
            return BackendHealth(
                name=_BACKEND_NAME,
                available=True,
                models_loaded=models,
            )
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as exc:
            return BackendHealth(
                name=_BACKEND_NAME,
                available=False,
                error=str(exc),
            )
