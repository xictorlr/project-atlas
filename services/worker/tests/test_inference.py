"""Tests for the inference layer — OllamaClient, Router, health checks."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from atlas_worker.inference.backends.ollama import OllamaClient
from atlas_worker.inference.backends.whisper_mlx import WhisperMLXBackend
from atlas_worker.inference.backends.vision_mlx import VisionMLXBackend
from atlas_worker.inference.models import (
    BackendHealth,
    GenerateResult,
    InferenceHealth,
    TranscribeResult,
    TranscriptSegment,
)
from atlas_worker.inference.router import InferenceRouter


# ---------------------------------------------------------------------------
# OllamaClient
# ---------------------------------------------------------------------------


class TestOllamaClient:
    """Tests for the Ollama HTTP client with mocked responses."""

    @pytest.fixture
    def client(self) -> OllamaClient:
        return OllamaClient(base_url="http://localhost:11434", timeout_s=10)

    @pytest.mark.asyncio
    async def test_generate_success(self, client: OllamaClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "response": "Hello world",
            "model": "gemma4:26b",
            "eval_count": 5,
            "total_duration": 1_000_000_000,
        }

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
            result = await client.generate("gemma4:26b", "Say hello")

        assert isinstance(result, GenerateResult)
        assert result.text == "Hello world"
        assert result.model == "gemma4:26b"
        assert result.backend == "ollama"
        assert result.tokens_used == 5

    @pytest.mark.asyncio
    async def test_embed_success(self, client: OllamaClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "embeddings": [[0.1, 0.2, 0.3, 0.4]],
        }

        with patch.object(client._client, "post", new_callable=AsyncMock, return_value=mock_response):
            result = await client.embed("nomic-embed-text", "test query")

        assert isinstance(result, list)
        assert len(result) == 4
        assert result[0] == 0.1

    @pytest.mark.asyncio
    async def test_health_when_running(self, client: OllamaClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "gemma4:26b"}, {"name": "nomic-embed-text"}],
        }

        with patch.object(client._client, "get", new_callable=AsyncMock, return_value=mock_response):
            health = await client.health()

        assert health.available is True
        assert "gemma4:26b" in health.models_loaded

    @pytest.mark.asyncio
    async def test_health_when_down(self, client: OllamaClient) -> None:
        import httpx

        with patch.object(
            client._client, "get", new_callable=AsyncMock,
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            health = await client.health()

        assert health.available is False
        assert health.error is not None

    @pytest.mark.asyncio
    async def test_list_models(self, client: OllamaClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "models": [
                {
                    "name": "gemma4:26b",
                    "size": 18_000_000_000,
                    "details": {"family": "gemma", "quantization_level": "Q4_K_M"},
                },
            ],
        }

        with patch.object(client._client, "get", new_callable=AsyncMock, return_value=mock_response):
            models = await client.list_models()

        assert len(models) == 1
        assert models[0].name == "gemma4:26b"
        assert models[0].size_gb == 18.0
        assert models[0].backend == "ollama"


# ---------------------------------------------------------------------------
# WhisperMLXBackend
# ---------------------------------------------------------------------------


class TestWhisperMLXBackend:
    """Tests for the Whisper backend with mocked model."""

    def test_is_available_when_not_installed(self) -> None:
        backend = WhisperMLXBackend(model_dir=Path("/tmp/test"), model_size="large-v3")
        # Don't assert True/False — depends on environment.
        # Just verify it doesn't crash.
        result = backend.is_available()
        assert isinstance(result, bool)

    def test_health_returns_backend_health(self) -> None:
        backend = WhisperMLXBackend(model_dir=Path("/tmp/test"), model_size="large-v3")
        health = backend.health()
        assert isinstance(health, BackendHealth)
        assert health.name == "lightning-whisper-mlx"

    def test_unload_clears_model(self) -> None:
        backend = WhisperMLXBackend(model_dir=Path("/tmp/test"), model_size="large-v3")
        backend._model = "fake_model"
        backend.unload()
        assert backend._model is None


# ---------------------------------------------------------------------------
# VisionMLXBackend
# ---------------------------------------------------------------------------


class TestVisionMLXBackend:
    """Tests for the Vision backend with mocked model."""

    def test_is_available_when_not_installed(self) -> None:
        backend = VisionMLXBackend(model_dir=Path("/tmp/test"))
        result = backend.is_available()
        assert isinstance(result, bool)

    def test_health_returns_backend_health(self) -> None:
        backend = VisionMLXBackend(model_dir=Path("/tmp/test"))
        health = backend.health()
        assert isinstance(health, BackendHealth)
        assert health.name == "mlx-vlm"

    def test_unload_clears_model(self) -> None:
        backend = VisionMLXBackend(model_dir=Path("/tmp/test"))
        backend._model = "fake_model"
        backend._processor = "fake_processor"
        backend.unload()
        assert backend._model is None
        assert backend._processor is None


# ---------------------------------------------------------------------------
# InferenceRouter
# ---------------------------------------------------------------------------


class TestInferenceRouter:
    """Tests for the router with mocked backends."""

    @pytest.fixture
    def router(self) -> InferenceRouter:
        ollama = OllamaClient(base_url="http://localhost:11434", timeout_s=5)
        whisper = WhisperMLXBackend(model_dir=Path("/tmp/test"), model_size="large-v3")
        vlm = VisionMLXBackend(model_dir=Path("/tmp/test"))
        return InferenceRouter(
            ollama=ollama,
            whisper=whisper,
            vlm=vlm,
            default_model="gemma4:26b",
            embedding_model="nomic-embed-text",
        )

    @pytest.mark.asyncio
    async def test_generate_delegates_to_ollama(self, router: InferenceRouter) -> None:
        expected = GenerateResult(
            text="test output",
            model="gemma4:26b",
            backend="ollama",
            tokens_used=10,
            duration_ms=100,
        )
        router._ollama.generate = AsyncMock(return_value=expected)

        result = await router.generate("test prompt")
        assert result.text == "test output"
        assert result.backend == "ollama"

    @pytest.mark.asyncio
    async def test_embed_delegates_to_ollama(self, router: InferenceRouter) -> None:
        router._ollama.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])

        result = await router.embed("test text")
        assert result == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_health_aggregation(self, router: InferenceRouter) -> None:
        router._ollama.health = AsyncMock(
            return_value=BackendHealth(name="ollama", available=True, models_loaded=["gemma4:26b"])
        )

        health = await router.health()
        assert isinstance(health, InferenceHealth)
        assert health.ollama.available is True
        assert health.overall_status in ("healthy", "degraded", "unavailable")

    def test_unload_all(self, router: InferenceRouter) -> None:
        router._whisper._model = "fake"
        router._vlm._model = "fake"
        router._vlm._processor = "fake"
        router.unload_all()
        assert router._whisper._model is None
        assert router._vlm._model is None

    @pytest.mark.asyncio
    async def test_list_models(self, router: InferenceRouter) -> None:
        router._ollama.list_models = AsyncMock(return_value=[])
        models = await router.list_models()
        assert "ollama" in models
        assert "whisper" in models
        assert "vlm" in models
