"""Shared pytest fixtures for API tests."""

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from atlas_api.main import app


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing API endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def vault_fixture_dir() -> Path:
    """Provide path to test vault fixtures."""
    return Path(__file__).parent / "fixtures" / "vault"


@pytest.fixture
def sample_notes(vault_fixture_dir: Path) -> list[dict]:
    """Provide sample notes from fixtures for search/vault tests."""
    # Load fixture notes and return as structured data
    notes = []
    for note_file in sorted(vault_fixture_dir.glob("*.md")):
        # TODO: Implement frontmatter parser to load notes
        # For now, return placeholders that describe the fixtures
        if note_file.name == "research-methodologies.md":
            notes.append({
                "id": "research-methodologies-001",
                "title": "Research Methodologies in AI Systems",
                "slug": "research-methodologies",
                "type": "concept",
                "content": note_file.read_text(),
            })
        elif note_file.name == "knowledge-compilation.md":
            notes.append({
                "id": "knowledge-compilation-002",
                "title": "Knowledge Compilation and Indexing",
                "slug": "knowledge-compilation",
                "type": "concept",
                "content": note_file.read_text(),
            })
        elif note_file.name == "semantic-search.md":
            notes.append({
                "id": "semantic-search-003",
                "title": "Semantic Search and Information Retrieval",
                "slug": "semantic-search",
                "type": "concept",
                "content": note_file.read_text(),
            })
    return notes
