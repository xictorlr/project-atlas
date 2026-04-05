"""Mock adapter responses for testing.

This module provides reusable mock responses and fixtures for testing
DeerFlow, Hermes, and MiroFish adapter integrations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# DeerFlow Mock Responses
# ---------------------------------------------------------------------------


@dataclass
class DeerFlowMockResponses:
    """Mock HTTP responses for DeerFlow adapter testing."""

    @staticmethod
    def health_response() -> dict[str, Any]:
        """Mock response from GET /health."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "capabilities": ["workflows", "monitoring", "logging"],
            "uptime_seconds": 3600,
        }

    @staticmethod
    def connect_response() -> dict[str, Any]:
        """Mock response from POST /session/init."""
        return {
            "connection_id": "conn_test_001",
            "token": "token_test_xyz123",
            "expires_at": "2026-04-05T12:00:00Z",
        }

    @staticmethod
    def submit_workflow_response() -> dict[str, Any]:
        """Mock response from POST /workflows."""
        return {
            "workflow_id": "wf_test_001",
            "status": "submitted",
            "created_at": "2026-04-05T10:00:00Z",
        }

    @staticmethod
    def workflow_status_response(status: str = "completed") -> dict[str, Any]:
        """Mock response from GET /workflows/{workflow_id}."""
        return {
            "workflow_id": "wf_test_001",
            "status": status,
            "progress": 100 if status == "completed" else 50,
            "result": {
                "output": "Workflow completed successfully",
                "duration_seconds": 42,
            },
        }


# ---------------------------------------------------------------------------
# Hermes Mock Responses
# ---------------------------------------------------------------------------


@dataclass
class HermesMockResponses:
    """Mock HTTP responses for Hermes adapter testing."""

    @staticmethod
    def health_response() -> dict[str, Any]:
        """Mock response from GET /health."""
        return {
            "status": "ok",
            "queue_depth": 5,
            "latency_ms": 42,
            "memory_gb": 2.5,
        }

    @staticmethod
    def init_response() -> dict[str, Any]:
        """Mock response from POST /memory/init."""
        return {
            "session_id": "session_test_001",
            "token": "token_test_abc123",
            "max_memory_kb": 10000,
        }

    @staticmethod
    def store_memory_response() -> dict[str, Any]:
        """Mock response from POST /memory/store."""
        return {
            "memory_id": "mem_test_001",
            "stored_at": "2026-04-05T10:00:00Z",
            "expires_at": "2026-04-05T11:00:00Z",
        }

    @staticmethod
    def retrieve_memory_response() -> dict[str, Any]:
        """Mock response from GET /memory/{memory_id}."""
        return {
            "memory_id": "mem_test_001",
            "key": "observation_key",
            "value": {"data": "stored observation"},
            "created_at": "2026-04-05T10:00:00Z",
            "expires_at": "2026-04-05T11:00:00Z",
        }


# ---------------------------------------------------------------------------
# MiroFish Mock Responses
# ---------------------------------------------------------------------------


@dataclass
class MiroFishMockResponses:
    """Mock HTTP responses for MiroFish adapter testing."""

    @staticmethod
    def health_response() -> dict[str, Any]:
        """Mock response from GET /health."""
        return {
            "status": "ok",
            "sandbox_count": 3,
            "license_status": "valid",
            "license_expires_at": "2027-04-05T00:00:00Z",
        }

    @staticmethod
    def init_response() -> dict[str, Any]:
        """Mock response from POST /simulate/init."""
        return {
            "sandbox_id": "sbx_test_001",
            "token": "token_test_mf123",
            "max_duration_seconds": 300,
        }

    @staticmethod
    def submit_simulation_response() -> dict[str, Any]:
        """Mock response from POST /simulate."""
        return {
            "simulation_id": "sim_test_001",
            "sandbox_id": "sbx_test_001",
            "status": "pending",
            "created_at": "2026-04-05T10:00:00Z",
        }

    @staticmethod
    def simulation_status_response(status: str = "complete") -> dict[str, Any]:
        """Mock response from GET /simulate/{simulation_id}."""
        return {
            "simulation_id": "sim_test_001",
            "status": status,
            "progress": 100 if status == "complete" else 50,
            "result": {
                "output": "Simulation completed",
                "metrics": {"success_rate": 0.95},
                "duration_ms": 2500,
            },
        }

    @staticmethod
    def license_response() -> dict[str, Any]:
        """Mock response from GET /license."""
        return {
            "status": "valid",
            "license_type": "enterprise",
            "expires_at": "2027-04-05T00:00:00Z",
            "simulations_remaining": 9999,
        }


# ---------------------------------------------------------------------------
# Feature Flag Mock Values
# ---------------------------------------------------------------------------


@dataclass
class FeatureFlagMocks:
    """Mock feature flag values for adapter testing."""

    @staticmethod
    def flags_all_enabled() -> dict[str, bool]:
        """All adapters enabled."""
        return {
            "deerflow_enabled": True,
            "hermes_enabled": True,
            "mirofish_enabled": True,
        }

    @staticmethod
    def flags_all_disabled() -> dict[str, bool]:
        """All adapters disabled."""
        return {
            "deerflow_enabled": False,
            "hermes_enabled": False,
            "mirofish_enabled": False,
        }

    @staticmethod
    def flags_partial(deerflow: bool = True, hermes: bool = False, mirofish: bool = True) -> dict[str, bool]:
        """Partial adapter enablement."""
        return {
            "deerflow_enabled": deerflow,
            "hermes_enabled": hermes,
            "mirofish_enabled": mirofish,
        }


# ---------------------------------------------------------------------------
# Error Response Mocks
# ---------------------------------------------------------------------------


@dataclass
class ErrorMockResponses:
    """Mock error responses for failure scenario testing."""

    @staticmethod
    def connection_error() -> dict[str, Any]:
        """Mock connection error response."""
        return {
            "error": "Connection failed",
            "code": "CONN_ERR",
            "details": "Unable to connect to service",
        }

    @staticmethod
    def auth_error() -> dict[str, Any]:
        """Mock authentication error (401)."""
        return {
            "error": "Unauthorized",
            "code": "AUTH_ERR",
            "details": "Invalid credentials",
        }

    @staticmethod
    def timeout_error() -> dict[str, Any]:
        """Mock timeout error."""
        return {
            "error": "Request timeout",
            "code": "TIMEOUT",
            "details": "Operation exceeded time limit",
        }

    @staticmethod
    def service_unavailable() -> dict[str, Any]:
        """Mock service unavailable (503)."""
        return {
            "error": "Service unavailable",
            "code": "SERVICE_DOWN",
            "details": "Service is temporarily unavailable",
        }
