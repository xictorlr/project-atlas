# Search and UI Test Infrastructure

This document describes the test setup for search engine and UI components. All test skeletons are in place and ready for implementation once blockers (#1, #3, #4, #6) are resolved.

## Backend Tests (services/api/tests/)

### test_search.py
Tests for lexical search, ranking, and snippet generation.

**Classes and Methods** (all marked TODO, blocked by #1):
- **TestSearchIndexing**
  - `test_index_notes_basic`: Index creation and basic retrieval
  - `test_index_notes_incremental`: Single-note index updates

- **TestLexicalSearch**
  - `test_search_exact_phrase`: Exact phrase matching
  - `test_search_fuzzy_matching`: Typo tolerance and stemming
  - `test_search_case_insensitive`: Case handling
  - `test_search_boolean_operators`: AND, OR, NOT operators

- **TestRankingAndRelevance**
  - `test_ranking_relevance_score`: BM25-style scoring
  - `test_ranking_by_recency`: Freshness factor
  - `test_ranking_by_authority`: Citation/backlink factor

- **TestSearchSnippets**
  - `test_snippet_context_extraction`: Context around match
  - `test_snippet_highlighting`: Term highlighting in results
  - `test_snippet_truncation`: Long note handling

- **TestEdgeCases**
  - `test_search_empty_results`: No match handling
  - `test_search_empty_vault`: Empty vault handling
  - `test_search_special_characters`: Punctuation, unicode
  - `test_search_pagination`: Result pagination
  - `test_search_performance`: <500ms SLA

**Fixtures Used**: `sample_notes` (from conftest.py)

### test_vault_routes.py
Tests for vault API endpoints (notes listing, single read, graph).

**Classes and Methods** (all marked TODO, blocked by #3):
- **TestListNotes**
  - `test_list_notes_returns_array`: GET /notes
  - `test_list_notes_includes_frontmatter`: Frontmatter fields
  - `test_list_notes_pagination`: page, limit parameters
  - `test_list_notes_filtering_by_tag`: tag filter
  - `test_list_notes_filtering_by_type`: type filter
  - `test_list_notes_sorting`: sort, order parameters

- **TestGetNote**
  - `test_get_note_by_id`: GET /notes/{id}
  - `test_get_note_includes_backlinks`: Incoming links
  - `test_get_note_includes_outbound_links`: Outgoing links
  - `test_get_note_404_not_found`: Missing note handling
  - `test_get_note_by_slug`: GET /notes/by-slug/{slug}

- **TestNoteGraph**
  - `test_graph_relationships`: Full relationship graph
  - `test_graph_local_neighborhood`: Graph around single note
  - `test_graph_path_finding`: Connections between notes

- **TestVaultMetadata**
  - `test_vault_metadata_statistics`: Total notes, links, size
  - `test_vault_metadata_schema`: Frontmatter schema info
  - `test_vault_metadata_health`: Broken links, orphans

- **TestEdgeCases**
  - `test_note_with_special_characters_in_title`: Special char handling
  - `test_note_with_circular_links`: Graph cycle handling
  - `test_very_large_note`: Performance with large notes

**Fixtures Used**: `sample_notes`, `vault_fixture_dir`

## Frontend Tests (apps/web/src/components/__tests__/)

### SearchBar.test.tsx
Tests for search input component (search query, debouncing, keyboard navigation).

**Classes and Methods** (all marked TODO, blocked by #4):
- **Rendering**
  - `should render search input`
  - `should have accessible label`

- **Input Handling**
  - `should update input value on change`
  - `should debounce input` (300ms)
  - `should clear input on clear button click`

- **Keyboard Navigation**
  - `should submit on Enter key`
  - `should navigate results with arrow keys`
  - `should close dropdown on Escape`

- **Search Execution**
  - `should call onSearch with query`
  - `should show loading state during search`
  - `should handle search errors`

- **Results Display**
  - `should display search results dropdown`
  - `should highlight matched terms`
  - `should paginate results`

- **Accessibility**
  - `should announce search results to screen readers`
  - `should support keyboard-only navigation`

### SourceTable.test.tsx
Tests for sources list component (rows, sorting, filtering, selection, bulk actions).

**Classes and Methods** (all marked TODO, blocked by #5 and #4):
- **Rendering**
  - `should render table with headers`
  - `should render source rows`
  - `should display status badge with color`
  - `should show type icon`

- **Sorting**
  - `should sort by name`
  - `should sort by created date`
  - `should sort by notes count`
  - `should show sort indicator`

- **Filtering**
  - `should filter by status`
  - `should filter by type`
  - `should combine multiple filters`

- **Selection**
  - `should select individual row`
  - `should select all rows with header checkbox`
  - `should deselect rows`

- **Bulk Actions**
  - `should show bulk action toolbar when rows selected`
  - `should execute bulk delete`

- **Pagination**
  - `should paginate rows`
  - `should change page size`

- **Row Actions**
  - `should open source detail on row click`
  - `should show context menu on right-click`

- **Accessibility**
  - `should be keyboard navigable`
  - `should have proper ARIA attributes`
  - `should announce selection changes`

### NoteReader.test.tsx
Tests for note display component (Markdown rendering, links, sidebar, TOC, edit mode).

**Classes and Methods** (all marked TODO, blocked by #6):
- **Rendering**
  - `should render note title`
  - `should render note content as Markdown`
  - `should render frontmatter metadata`

- **Markdown Rendering**
  - `should render headers at correct levels`
  - `should render lists`
  - `should render code blocks with syntax highlighting`
  - `should render blockquotes`
  - `should render tables`

- **Internal Links**
  - `should render internal links as clickable`
  - `should navigate on link click`
  - `should show link preview on hover`
  - `should handle broken links`

- **External Links**
  - `should render external links`
  - `should open external links in new tab`

- **Sidebar - Backlinks**
  - `should display backlinks section`
  - `should navigate on backlink click`
  - `should show empty state for no backlinks`

- **Sidebar - Outbound Links**
  - `should display outbound links section`
  - `should navigate on outbound link click`

- **Breadcrumb Navigation**
  - `should show breadcrumb path`
  - `should navigate via breadcrumb`

- **Table of Contents**
  - `should generate table of contents`
  - `should scroll to section on TOC click`
  - `should highlight active section in TOC`

- **Copy and Citation**
  - `should copy text on select`
  - `should copy citation on button click`

- **Edit Mode**
  - `should switch to edit mode on button click`
  - `should save edits`
  - `should discard edits on cancel`

- **Accessibility**
  - `should be readable by screen reader`
  - `should be keyboard navigable`
  - `should support dark mode`

## Test Fixtures

Located in `services/api/tests/fixtures/vault/`:

1. **research-methodologies.md**
   - Demonstrates concept notes with references
   - Used for search, ranking, and graph tests

2. **knowledge-compilation.md**
   - Shows compilation pipeline and vault concepts
   - Used for semantic search and vault API tests

3. **semantic-search.md**
   - Comprehensive content for search quality tests
   - Includes lexical vs semantic comparison

See `fixtures/README.md` for details on fixture structure and usage.

## Test Configuration

### Python (Pytest)
- Framework: `pytest` + `pytest-asyncio`
- HTTP Client: `httpx.AsyncClient`
- Location: `services/api/tests/conftest.py`
- Markers: `@pytest.mark.asyncio` for async tests

### TypeScript (Vitest)
- Framework: `vitest`
- Test Utilities: `@testing-library/react`, `@testing-library/user-event`
- Location: `apps/web/vitest.config.ts`
- Render: `vitest` + `testing-library` DOM rendering

## Running Tests

### Backend Tests
```bash
cd services/api
pytest tests/test_search.py -v
pytest tests/test_vault_routes.py -v
```

### Frontend Tests
```bash
cd apps/web
npm run test:ui  # or vitest run
```

## Test Status and Blockers

| Task | Status | Tests Ready | Blocker |
|------|--------|-------------|---------|
| Lexical search engine | pending | Yes (test_search.py) | #1 |
| Vault notes API | pending | Yes (test_vault_routes.py) | #3 |
| Dashboard/navigation | in_progress | Yes (SearchBar, SourceTable) | #4 |
| Vault browser/reader | pending | Yes (NoteReader.test.tsx) | #6 |

Once blockers are cleared, implement tests by:
1. Removing `# TODO: Implement` comment
2. Replacing `pass` with actual test code
3. Using fixtures (`sample_notes`, `async_client`, mock components)
4. Following existing test patterns in codebase

## Quality Gates

All tests must achieve:
- **Coverage**: 80%+ of new code
- **Performance**: <100ms per unit test, <500ms per integration test
- **Isolation**: No test depends on another test's state
- **Clarity**: Test name clearly describes what is being tested

## Next Steps

1. **When #1 is done**: Implement `test_search.py` tests
2. **When #3 is done**: Implement `test_vault_routes.py` tests
3. **When #4 is done**: Implement `SearchBar.test.tsx` and `SourceTable.test.tsx`
4. **When #6 is done**: Implement `NoteReader.test.tsx`
5. **Run full suite**: `pytest && npm run test:ui`
6. **Achieve 80% coverage**: Adjust tests as needed
