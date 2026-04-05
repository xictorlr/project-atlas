"""Shared pytest fixtures for worker tests."""

import pytest


@pytest.fixture
def worker_ctx() -> dict:
    """Minimal arq context stub for unit-testing job functions."""
    return {}
