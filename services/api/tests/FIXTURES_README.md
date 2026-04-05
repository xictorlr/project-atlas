# Test Fixtures Reference

This document describes all test fixtures available for integration and adapter tests.

## Vault Fixtures

Location: `/services/api/tests/fixtures/vault/`

### Core Vault Notes

These fixtures provide a consistent test vault for search, compilation, and health check testing.

#### `research-methodologies.md`
- **ID:** research-methodologies-001
- **Type:** concept
- **Purpose:** Sample research methodology documentation
- **Contains:** Valid frontmatter, links to other notes
- **Use cases:** Search ranking tests, compiler output validation, health checks

#### `knowledge-compilation.md`
- **ID:** knowledge-compilation-002
- **Type:** concept
- **Purpose:** Sample knowledge compilation process documentation
- **Contains:** Valid frontmatter, backlinks to research-methodologies
- **Use cases:** Search ranking tests, citation accuracy tests

#### `semantic-search.md`
- **ID:** semantic-search-003
- **Type:** concept
- **Purpose:** Sample semantic search explanation
- **Contains:** Valid frontmatter, no external links
- **Use cases:** Orphan detection tests, orphan should not include this

### Health Check Specific Fixtures

#### `health-check-issue-note.md`
- **ID:** health-issue-001
- **Type:** concept
- **Purpose:** Note with known health issues
- **Issues:**
  - Broken link: `[[nonexistent-note]]`
  - Broken link: `[[another-missing-file]]`
  - Valid frontmatter otherwise
- **Use cases:** Broken link detection tests
- **Expected behavior:** Should be flagged with 2 broken links

#### `orphan-note.md`
- **ID:** orphan-001
- **Type:** concept
- **Purpose:** Note with no incoming references
- **Characteristics:**
  - Valid frontmatter
  - No links to other notes
  - Not referenced by any other note
- **Use cases:** Orphan detection tests
- **Expected behavior:** Should be flagged as orphan

## Python Fixtures

Location: `/services/api/tests/fixtures/adapters.py`

### Mock Response Classes

All mock responses are grouped by adapter for easy testing.

#### `DeerFlowMockResponses`
Mock HTTP responses for DeerFlow adapter.

**Methods:**
- `health_response()` — GET /health response
  ```python
  {
    "status": "healthy",
    "version": "1.0.0",
    "capabilities": ["workflows", "monitoring", "logging"],
    "uptime_seconds": 3600
  }
  ```

- `connect_response()` — POST /session/init response
  ```python
  {
    "connection_id": "conn_test_001",
    "token": "token_test_xyz123",
    "expires_at": "2026-04-05T12:00:00Z"
  }
  ```

- `submit_workflow_response()` — POST /workflows response
  ```python
  {
    "workflow_id": "wf_test_001",
    "status": "submitted",
    "created_at": "2026-04-05T10:00:00Z"
  }
  ```

- `workflow_status_response(status="completed")` — GET /workflows/{id} response

#### `HermesMockResponses`
Mock HTTP responses for Hermes memory bridge.

**Methods:**
- `health_response()` — Service health
- `init_response()` — Session initialization
- `store_memory_response()` — Store observation
- `retrieve_memory_response()` — Retrieve observation

#### `MiroFishMockResponses`
Mock HTTP responses for MiroFish simulation gateway.

**Methods:**
- `health_response()` — Service health and license status
- `init_response()` — Sandbox initialization
- `submit_simulation_response()` — Submit simulation
- `simulation_status_response(status="complete")` — Get simulation status
- `license_response()` — Retrieve license information

### Feature Flag Mocks

#### `FeatureFlagMocks`
Mock feature flag values.

**Methods:**
- `flags_all_enabled()` — All adapters enabled
- `flags_all_disabled()` — All adapters disabled
- `flags_partial(deerflow=True, hermes=False, mirofish=True)` — Custom combination

### Error Mocks

#### `ErrorMockResponses`
Mock error responses for failure scenario testing.

**Methods:**
- `connection_error()` — Connection failure
- `auth_error()` — Authentication failure (401)
- `timeout_error()` — Request timeout
- `service_unavailable()` — Service down (503)

## Pytest Fixtures

Location: `/services/api/tests/conftest.py` and `/services/worker/tests/conftest.py`

### Shared Fixtures (API)

#### `async_client: AsyncClient`
HTTP client for testing API endpoints.

**Usage:**
```python
@pytest.mark.asyncio
async def test_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/health")
```

#### `vault_fixture_dir: Path`
Path to vault fixtures directory.

**Usage:**
```python
def test_vault(vault_fixture_dir: Path):
    notes = list(vault_fixture_dir.glob("*.md"))
```

#### `sample_notes: list[dict]`
Pre-parsed sample notes from fixtures.

**Structure:**
```python
[
    {
        "id": "research-methodologies-001",
        "title": "Research Methodologies in AI Systems",
        "slug": "research-methodologies",
        "type": "concept",
        "content": "..."
    }
]
```

### Test-Specific Fixtures (Defined in Test Files)

#### `health_check_vault: Path` (test_health_check.py)
Complete vault fixture with health issues.

**Contains:**
- `good-note.md` — Valid note
- `another-good-note.md` — Valid note with backlinks
- `broken-link.md` — Note with broken links
- `missing-frontmatter.md` — Note without YAML frontmatter
- `incomplete-fm.md` — Note with incomplete frontmatter
- `orphan-note.md` — Note not referenced by others
- `circular-a.md` — Part of A → B → A cycle
- `circular-b.md` — Part of A → B → A cycle

#### `local_vault: Path` (test_sync.py)
Local Obsidian vault for sync testing.

**Contains:**
- `.obsidian/vault.json` — Obsidian configuration
- `note1.md` — Test note with links
- `note2.md` — Test note

#### `remote_vault_state: dict` (test_sync.py)
Mock remote vault state as API response.

**Structure:**
```python
{
    "workspace_id": "ws-001",
    "vault_id": "vault-001",
    "notes": [...]
}
```

## Creating New Fixtures

### Adding Vault Notes

1. Create `.md` file in `/services/api/tests/fixtures/vault/`
2. Include valid YAML frontmatter:
   ```yaml
   ---
   id: unique-id
   title: Note Title
   type: concept  # or concept, entity, report, etc.
   created_at: 2026-04-05T00:00:00Z
   updated_at: 2026-04-05T00:00:00Z
   ---
   ```
3. Add to `conftest.py` sample_notes if needed
4. Document in this file

### Adding Mock Responses

1. Add method to appropriate `MockResponses` class in `adapters.py`
2. Return realistic JSON matching actual API
3. Include metadata (timestamps, IDs, status)
4. Document return structure as docstring

### Adding Python Fixtures

1. Define in test file with `@pytest.fixture` decorator
2. Use `tmp_path` for temporary files
3. Use `AsyncMock` for async operations
4. Include docstring explaining purpose and contents

## Fixture Best Practices

1. **Deterministic** — Same fixture = same content every time
2. **Isolated** — Fixtures don't depend on execution order
3. **Clean** — Temp files are automatically cleaned up
4. **Documented** — All fixtures have clear docstrings
5. **Reusable** — Fixtures are shared across multiple tests
6. **Realistic** — Mock data matches production format

## Fixture Size Guidelines

- **Small fixtures:** < 1 KB (single note)
- **Medium fixtures:** 1–10 KB (complete vault)
- **Large fixtures:** 10–100 KB (performance testing)
- **Mock responses:** < 5 KB (HTTP responses)

## Using Fixtures in Tests

### Inject via function parameters
```python
def test_something(async_client: AsyncClient, vault_fixture_dir: Path):
    pass
```

### Reference class-level fixtures
```python
class TestAdapter:
    @pytest.mark.asyncio
    async def test_health(self, async_client: AsyncClient):
        pass
```

### Create temporary fixtures in test
```python
def test_creates_temp(tmp_path: Path):
    temp_vault = tmp_path / "vault"
    temp_vault.mkdir()
    # Use temp_vault for test
```

## Fixture Documentation Standards

Each fixture should include:
1. **Purpose** — What is this fixture for?
2. **Contents** — What data does it contain?
3. **Structure** — How is it organized?
4. **Use cases** — Which tests use it?
5. **Characteristics** — Size, encoding, special properties
6. **Example** — How to use it in a test

## Maintenance

### Updating Fixtures

- Keep vault notes realistic and relevant
- Update timestamps when modifying content
- Preserve backward compatibility when possible
- Document changes in git commit message

### Adding Fixtures for New Tests

- Create fixture first (before writing test)
- Name fixtures clearly (e.g., `health_check_vault`)
- Add to this documentation
- Keep related fixtures together

### Removing Fixtures

- Search codebase for all uses
- Update dependent tests
- Remove from documentation
- Clean up temporary files
