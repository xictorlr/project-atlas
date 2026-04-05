# Integration and Adapter Test Guide

This guide covers the test skeletons and fixtures for integration and adapter tests (Task #7).

## Test Files Overview

### `test_adapters.py` — External Adapter Integration Tests
Tests for DeerFlow, Hermes, and MiroFish adapter integrations.

**Key test classes:**
- `TestDeerFlowAdapter` — Workflow orchestration (10 tests)
- `TestHermesAdapter` — Memory bridge (9 tests)
- `TestMiroFishAdapter` — Simulation gateway (10 tests)
- `TestAdapterIntegration` — Cross-adapter behavior (3 tests)

**Critical paths to implement:**
1. Mock HTTP client (`httpx.AsyncClient`)
2. Feature flag system (all adapters must support enable/disable)
3. Protocol conformance (all adapters implement `ExternalAdapter` protocol)
4. Error handling (connection failures, timeouts, auth errors)

### `test_health_check.py` — Vault Health Verification
Tests for health check service covering vault integrity.

**Key test classes:**
- `TestHealthCheckEndpoint` — API endpoint tests (2 tests)
- `TestBrokenLinkDetection` — Broken [[note]] references (3 tests)
- `TestMissingFrontmatter` — Frontmatter validation (3 tests)
- `TestOrphanDetection` — Unreferenced notes (3 tests)
- `TestCycleDetection` — Circular backlinks (4 tests)
- `TestIntegrityMetrics` — Coverage & completeness (3 tests)
- `TestHealthStatusDetermination` — Health aggregation (3 tests)
- `TestHealthCheckIntegration` — Integration paths (3 tests)

**Critical paths to implement:**
1. Broken link detection (parse [[ref]] and validate against vault)
2. Frontmatter validation (required fields: id, title, type, created_at, updated_at)
3. Orphan detection (notes with no backlinks)
4. Cycle detection (DFS/BFS for circular references)
5. Integrity metrics (coverage %, completeness %)

### `test_evals.py` — Quality Evaluation Framework
Tests for eval framework and quality metrics.

**Key test classes:**
- `TestSearchRankingEval` — Search quality (5 tests)
  - Precision@K, recall, NDCG, MRR
- `TestCompilerEval` — Compiler output quality (6 tests)
  - Frontmatter validity, link validity, source coverage
- `TestInformationRetrievalEval` — Citation quality (3 tests)
  - Citation coverage, accuracy, completeness
- `TestEvalFramework` — Framework integration (6 tests)
- `TestEvalEdgeCases` — Edge cases (4 tests)

**Critical paths to implement:**
1. Precision@K computation
2. Recall computation
3. NDCG (Normalized Discounted Cumulative Gain)
4. MRR (Mean Reciprocal Rank)
5. Compiler quality metrics (frontmatter, links, source coverage)
6. Citation assessment and scoring

### `test_sync.py` (worker) — Obsidian Sync and Export
Tests for Obsidian vault synchronization and ZIP export.

**Key test classes:**
- `TestFileSyncOperations` — Basic file ops (5 tests)
- `TestConflictDetection` — Conflict detection (4 tests)
- `TestConflictResolution` — Conflict resolution (3 tests)
- `TestZipExport` — ZIP export (7 tests)
- `TestBidirectionalSync` — Pull/push sync (4 tests)
- `TestSyncIdempotency` — Idempotent operations (3 tests)
- `TestSyncEdgeCases` — Special cases (4 tests)

**Critical paths to implement:**
1. File creation/update in local vault
2. Conflict detection (local modified, remote modified, concurrent)
3. Conflict resolution strategies (remote_wins, local_wins, manual_merge)
4. ZIP export with metadata
5. Bidirectional sync (pull from remote, push to remote)
6. Idempotent operations (sync twice = same result)

## Fixture Files

### Vault Fixtures (`/tests/fixtures/vault/`)

**Existing fixtures:**
- `research-methodologies.md` — Sample research note
- `knowledge-compilation.md` — Sample concept note
- `semantic-search.md` — Sample search note

**Health check fixtures:**
- `health-check-issue-note.md` — Note with broken links
- `orphan-note.md` — Note with no backlinks

**To create during implementation:**
- Notes with missing frontmatter
- Notes with incomplete frontmatter
- Circular reference examples (A → B → A)
- Large vault fixture (50+ notes) for performance testing

### Adapter Fixtures (`/tests/fixtures/adapters.py`)

Provides mock HTTP responses for:
- **DeerFlow:** health, connect, submit_workflow, workflow_status
- **Hermes:** health, init, store_memory, retrieve_memory
- **MiroFish:** health, init, submit_simulation, simulation_status, license
- **Feature flags:** all_enabled, all_disabled, partial configurations
- **Errors:** connection_error, auth_error, timeout_error, service_unavailable

## Testing Strategy

### Mocking HTTP Clients

All adapter tests mock `httpx.AsyncClient` to avoid external service dependencies:

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_deerflow_connect():
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value.json.return_value = {
            "connection_id": "conn_001",
            "token": "token_xyz"
        }
        # Test adapter connection
```

### Feature Flag Mocking

All adapters must support feature flags. Tests mock the feature flag system:

```python
@pytest.mark.asyncio
async def test_adapter_disabled():
    with patch("features.is_enabled", return_value=False) as mock_flag:
        # Verify adapter operations are skipped
```

### Protocol Conformance

All adapters implement the `ExternalAdapter` protocol with:
- `async def connect() -> bool`
- `async def health_check() -> dict`
- `async def is_enabled() -> bool`

Tests verify Protocol implementation:

```python
def test_protocol_conformance():
    # Verify adapter implements ExternalAdapter protocol
    assert hasattr(adapter, "connect")
    assert hasattr(adapter, "health_check")
    assert hasattr(adapter, "is_enabled")
```

## Common Test Patterns

### Async Test Pattern

```python
@pytest.mark.asyncio
async def test_something():
    # Setup
    # Execute
    # Assert
    pass
```

### Fixture-Based Testing

```python
def test_with_fixture(async_client: AsyncClient, health_check_vault: Path):
    # Use injected fixtures
    pass
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
])
def test_parametrized(input, expected):
    pass
```

## Running the Tests

### Run all integration tests:
```bash
pytest services/api/tests/test_adapters.py
pytest services/api/tests/test_health_check.py
pytest services/api/tests/test_evals.py
pytest services/worker/tests/test_sync.py
```

### Run specific test class:
```bash
pytest services/api/tests/test_adapters.py::TestDeerFlowAdapter -v
```

### Run with coverage:
```bash
pytest --cov=src --cov-report=term-missing services/api/tests/test_*.py
```

### Run async tests only:
```bash
pytest -m asyncio services/api/tests/test_adapters.py
```

## Test Coverage Goals

Each test file should achieve **80%+ code coverage**:
- `test_adapters.py` — 32 tests covering 3 adapters
- `test_health_check.py` — 28 tests covering vault integrity
- `test_evals.py` — 24 tests covering eval framework
- `test_sync.py` — 30 tests covering sync operations

**Total: 114 tests** with mocked external dependencies.

## Dependencies for Implementation

All tests are **unblocked by upstream tasks** once these are complete:

1. **Task #1** (Obsidian sync) — For `test_sync.py`
2. **Task #2** (DeerFlow adapter) — For `test_adapters.py` DeerFlow tests
3. **Task #3** (Hermes adapter) — For `test_adapters.py` Hermes tests
4. **Task #4** (MiroFish adapter) — For `test_adapters.py` MiroFish tests
5. **Task #5** (Health checks) — For `test_health_check.py`
6. **Task #6** (Evals framework) — For `test_evals.py`

### Preparation Phase (Current)
- Create test skeletons with all test methods as `pass`
- Create fixture data and mock response libraries
- Document test expectations and critical paths

### Implementation Phase (After #1-6)
- Implement test bodies (replace `pass` with actual test code)
- Ensure all mocks work with actual implementations
- Verify 80%+ coverage

## Key Testing Principles

1. **No External Services** — All tests mock HTTP, files, and external APIs
2. **Deterministic** — Tests produce same results every run
3. **Fast** — All tests complete in < 2 seconds
4. **Isolated** — Tests don't depend on execution order
5. **Reviewable** — Test code mirrors expected behavior
6. **Comprehensive** — Cover happy paths, error cases, edge cases

## Notes for Implementers

- Use `pytest.mark.asyncio` for all async tests
- Use `AsyncMock` for async mocks
- Use `tmp_path` fixture for temporary file operations
- Use `vault_fixture_dir` for vault fixture access
- Use `async_client` for API endpoint testing
- Mock HTTP with `patch("httpx.AsyncClient.*")`
- Mock feature flags with `patch("features.is_enabled")`
- Verify protocol conformance before implementation
