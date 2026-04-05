"""Tests for API health check endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(async_client: AsyncClient):
    """Test that GET /health returns 200 with status ok."""
    response = await async_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "atlas-api"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_health_ready_endpoint_exists(async_client: AsyncClient):
    """Test that readiness probe endpoint is available."""
    response = await async_client.get("/health/ready")
    assert response.status_code in (200, 503)  # May be 503 if database unavailable

    data = response.json()
    assert "status" in data
    assert "checks" in data
