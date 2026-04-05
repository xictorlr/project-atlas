# Test Fixtures

This directory contains test data and fixtures for API and integration tests.

## Structure

```
fixtures/
├── vault/
│   ├── research-methodologies.md      # Concept note with references
│   ├── knowledge-compilation.md       # Concept note about vault compilation
│   └── semantic-search.md             # Concept note about search techniques
└── README.md                          # This file
```

## Vault Fixtures

The `vault/` directory contains sample Markdown notes with proper frontmatter for testing search and vault endpoints.

### Sample Notes

1. **research-methodologies.md**
   - ID: `research-methodologies-001`
   - Type: concept
   - Tags: research, methodology, ai
   - Contains: Headers, lists, internal links ([[experimental-design]], [[statistical-validation]])
   - Use for: Lexical search tests, knowledge graph tests

2. **knowledge-compilation.md**
   - ID: `knowledge-compilation-002`
   - Type: concept
   - Tags: knowledge, compilation, indexing, documentation
   - Contains: Multi-level headers, links to other concepts
   - Use for: Search ranking tests, vault API tests

3. **semantic-search.md**
   - ID: `semantic-search-003`
   - Type: concept
   - Tags: search, retrieval, ranking, nlp
   - Contains: Comprehensive content with synonyms and related concepts
   - Use for: Search quality tests, snippet extraction tests

## Using Fixtures

### In Python Tests (services/api/tests/)

Load fixture notes via the `sample_notes` fixture:

```python
@pytest.mark.asyncio
async def test_search_returns_notes(async_client: AsyncClient, sample_notes: list[dict]):
    """Test search finds indexed notes."""
    # sample_notes contains all three fixture notes
    # Can be used to populate test database or mock searches
    
    response = await async_client.get("/api/workspaces/test/search?q=research")
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0
```

### In TypeScript Tests (apps/web/)

Notes can be mocked in component tests:

```typescript
const mockNote = {
  id: 'research-methodologies-001',
  title: 'Research Methodologies in AI Systems',
  slug: 'research-methodologies',
  content: '# Research Methodologies...',
  // ... rest of note structure
}

render(<NoteReader note={mockNote} />)
```

## Adding New Fixtures

When adding new test notes:

1. Create a new `.md` file in `vault/` with proper frontmatter
2. Include frontmatter fields:
   - `id`: Unique identifier (e.g., `concept-name-001`)
   - `title`: Human-readable title
   - `type`: One of: concept, entity, source, report
   - `created_at`, `updated_at`: ISO 8601 timestamps
   - `tags`: Array of tag strings
3. Add sample note to Python conftest `sample_notes` fixture
4. Update this README with note description
5. Use in test classes that are currently blocked (see TODO comments)

## Note on Fixture Structure

Fixtures follow the frontmatter schema defined in `vault/meta/frontmatter-schema.md`. All notes include:

- **id**: Unique identifier for the note
- **title**: Display name
- **type**: Classification (concept, entity, source, report)
- **source_id**: Where the note originated
- **created_at / updated_at**: Metadata timestamps
- **tags**: Searchable tags
- **aliases**: Alternative names (Obsidian compatibility)

## Test Blocking Status

These fixtures support tests that are currently blocked by:

- **#1**: Lexical search engine implementation
- **#3**: Vault notes API endpoint
- **#4**: Dashboard layout and navigation
- **#6**: Vault browser and note reader

Once blockers are resolved, test implementations can use these fixtures to verify core functionality.
