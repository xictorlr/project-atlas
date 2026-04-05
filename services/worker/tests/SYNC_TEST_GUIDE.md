# Obsidian Sync and Export Test Guide

This guide covers the test skeletons for Obsidian sync and vault export testing (part of Task #7).

## Overview

The `test_sync.py` file contains 33 tests across 7 test classes covering:
- File sync operations (create, update, delete)
- Conflict detection and resolution
- ZIP export functionality
- Bidirectional sync (push/pull)
- Idempotency and recovery
- Edge cases and error handling

## Test Classes

### `TestFileSyncOperations` (5 tests)
Core file synchronization operations.

**Tests:**
1. `test_create_new_file` — Create new note in local vault from remote
2. `test_update_existing_file` — Update local file from remote changes
3. `test_delete_file` — Remove file from local vault when deleted remotely
4. `test_preserve_obsidian_metadata` — Don't overwrite `.obsidian/` directory
5. `test_sync_creates_subdirectories` — Create directory structure automatically

**Critical implementation:**
- Receive note from remote (via API)
- Write to local file system with correct encoding (UTF-8)
- Preserve frontmatter during write
- Create parent directories as needed
- Never modify `.obsidian/` configuration files

### `TestConflictDetection` (4 tests)
Detect when local and remote have diverged.

**Tests:**
1. `test_detect_local_modification` — User edited local file, server updated remote
2. `test_detect_deletion_conflict` — Local deleted, remote updated
3. `test_detect_concurrent_edits` — Both sides modified (non-overlapping)
4. `test_idempotent_sync_no_conflict` — Re-syncing same version doesn't create conflict

**Critical implementation:**
- Compare timestamps: local_modified_at vs remote_modified_at
- Compute content hash to detect actual divergence
- Report conflict with: local_modified_at, remote_modified_at, conflict_type
- Support conflict types:
  - `"diverged"` — Both sides changed
  - `"local_deleted_remote_updated"` — Local deleted, remote changed
  - `"local_updated_remote_deleted"` — Local changed, remote deleted
  - `"concurrent_edits"` — Non-overlapping changes (may be mergeable)

### `TestConflictResolution` (3 tests)
Resolve detected conflicts using different strategies.

**Tests:**
1. `test_resolve_conflict_keep_remote` — Overwrite local with remote, save backup
2. `test_resolve_conflict_keep_local` — Keep local version, don't update remote
3. `test_resolve_conflict_manual_merge` — Create merge candidate with conflict markers

**Critical implementation:**
- Strategy 1: `remote_wins` — Use remote version
  - Overwrite local file
  - Save backup: `note.md.conflict.20260405T120000Z`
  - Document resolution in metadata
- Strategy 2: `local_wins` — Keep local version
  - Don't update local
  - Don't push to remote
  - Document resolution in metadata
- Strategy 3: `manual_merge` — Create merge candidate
  - Three-way merge (local, remote, common ancestor)
  - Add conflict markers to file
  - Document merge status in metadata

### `TestZipExport` (7 tests)
Export vault to portable ZIP file.

**Tests:**
1. `test_export_zip_contains_all_notes` — All notes present in ZIP
2. `test_export_zip_preserves_frontmatter` — Frontmatter not corrupted
3. `test_export_zip_excludes_obsidian_config` — `.obsidian/` not in ZIP
4. `test_export_zip_includes_metadata` — `__metadata__.json` present
5. `test_export_zip_includes_attachments` — Images and files included
6. `test_export_zip_with_subdirectories` — Directory structure preserved
7. `test_export_zip_with_large_vault` — Performance test (100+ notes, <10s)

**Critical implementation:**
- Create ZIP file with local notes
- Include all `.md` files (recursively)
- Exclude `.obsidian/` directory
- Exclude `.git/` and other control directories
- Include `__metadata__.json`:
  ```json
  {
    "export_timestamp": "2026-04-05T10:00:00Z",
    "vault_id": "vault-001",
    "note_count": 42,
    "schema_version": "1.0",
    "compression": "deflate"
  }
  ```
- Include attachments (images, PDFs, etc.)
- Preserve directory structure
- Use UTF-8 encoding

### `TestBidirectionalSync` (4 tests)
Test pull (remote → local) and push (local → remote) operations.

**Tests:**
1. `test_pull_from_remote` — Get updates from remote to local
2. `test_push_to_remote` — Send local changes to remote
3. `test_full_sync_cycle` — Pull → modify → push → pull (consistency)
4. `test_sync_incremental` — Only changed notes transmitted

**Critical implementation:**
- **Pull operation:**
  - Get list of notes from remote API
  - Compare with local versions
  - Download changed notes
  - Update local files
  - Update local metadata (timestamps)
- **Push operation:**
  - Scan local vault for changes
  - Send changed notes to remote API
  - Include frontmatter metadata
  - Wait for server confirmation
  - Update local sync state
- **Full cycle:**
  - Pull latest from remote
  - User edits local note
  - Push changes to remote
  - Pull again to verify consistency
  - Assert local == remote

### `TestSyncIdempotency` (3 tests)
Verify sync operations are safe to repeat.

**Tests:**
1. `test_sync_twice_idempotent` — Running sync twice = same result
2. `test_partial_sync_recovery` — Recover from interrupted sync
3. `test_sync_with_existing_files` — Don't re-write unchanged files

**Critical implementation:**
- **Idempotency:** Sync twice should produce identical state
  - No duplicate files
  - No extra modifications
  - Same timestamps and content hashes
- **Recovery:** Resume from interruption
  - Save sync checkpoint (last synced note)
  - Resume from checkpoint on restart
  - Verify no data loss
- **Incremental:** Don't modify unchanged files
  - Compare content hashes
  - Skip write if unchanged
  - Preserve file modification time

### `TestSyncEdgeCases` (4 tests)
Handle unusual scenarios gracefully.

**Tests:**
1. `test_sync_empty_vault` — Sync vault with no notes
2. `test_sync_with_special_characters` — Note names with special chars
3. `test_sync_with_unicode_content` — Unicode content (emoji, CJK)
4. `test_sync_respects_gitignore` — Ignore patterns from `.gitignore`

**Critical implementation:**
- **Empty vault:** Complete successfully, result is empty
- **Special chars:** Handle `"note (1) & (2).md"` correctly
  - Proper file system escaping
  - Links still resolve correctly
- **Unicode:** Preserve content exactly
  - UTF-8 encoding
  - Emoji in frontmatter and body
  - CJK characters (Chinese, Japanese, Korean)
  - RTL text (Arabic, Hebrew)
- **`.gitignore`:** Respect patterns
  - Parse `.gitignore` file
  - Apply patterns: `*.tmp`, `node_modules/`, etc.
  - Don't sync ignored files

## Fixtures

### `local_vault` (fixture)
Temporary local Obsidian vault with initial notes.

**Structure:**
```
local_vault/
├── .obsidian/
│   └── vault.json
├── note1.md
└── note2.md
```

**Contents:**
- `note1.md`: Valid note with frontmatter, links to `note2`
- `note2.md`: Valid note with frontmatter

### `remote_vault_state` (fixture)
Mock remote vault state as returned by API.

**Structure:**
```json
{
  "workspace_id": "ws-001",
  "vault_id": "vault-001",
  "notes": [
    {
      "id": "note-001",
      "title": "First Note",
      "slug": "note-1",
      "content": "...",
      "frontmatter": {...},
      "updated_at": "2026-04-05T10:00:00Z"
    }
  ]
}
```

## Fixture Extension Points

Create additional fixtures during implementation:

### Health check vault (for `test_sync_with_existing_files`)
Notes with health issues to test conflict scenarios.

### Large vault (for performance testing)
100+ notes with subdirectories and attachments.

### Attachment vault
Notes with image and file references.

## Testing Strategy

### File Operations Mocking

Don't mock file operations—use real temp directories:

```python
def test_create_new_file(self, local_vault: Path):
    # local_vault is a real temp directory from pytest
    # Write files there directly
    note_file = local_vault / "new-note.md"
    note_file.write_text("...")
    assert note_file.exists()
```

### API Mocking

Mock remote API calls with `patch`:

```python
@pytest.mark.asyncio
async def test_pull_from_remote(self, local_vault: Path, remote_vault_state: dict):
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value.json.return_value = remote_vault_state
        # Test pull operation
```

### Timestamp Comparison

Use timestamps to detect changes:

```python
# Get local file timestamp
local_mtime = local_vault.stat().st_mtime
# Get remote timestamp
remote_updated = remote_note["updated_at"]
# Compare (with timezone conversion)
if remote_timestamp > local_timestamp:
    # File needs update
```

## Critical Paths to Implement

1. **Frontmatter Parsing** — Parse YAML frontmatter from notes
   - Extract fields: id, title, type, created_at, updated_at, tags
   - Preserve custom fields

2. **Link Resolution** — Handle [[note]] references
   - Extract links from content
   - Resolve slugs to filenames
   - Handle cross-directory links

3. **Conflict Detection** — Compare timestamps and content
   - Hash-based detection (MD5 or SHA-256)
   - Three-way merge for manual resolution

4. **ZIP Creation** — Package vault for export
   - Use Python `zipfile` module
   - Include metadata file
   - Exclude Obsidian config

5. **Idempotency** — Track sync state
   - Save sync checkpoints
   - Compare file hashes
   - Skip unnecessary writes

## Running the Tests

### Run all sync tests:
```bash
pytest services/worker/tests/test_sync.py -v
```

### Run specific test class:
```bash
pytest services/worker/tests/test_sync.py::TestZipExport -v
```

### Run with coverage:
```bash
pytest --cov=services/worker --cov-report=term-missing services/worker/tests/test_sync.py
```

### Run async tests only:
```bash
pytest -m asyncio services/worker/tests/test_sync.py -v
```

## Coverage Goals

- **Total tests:** 33 tests covering sync operations
- **Target coverage:** 80%+ of sync module
- **Critical paths:** 100% coverage (file ops, conflict detection, export)

## Dependencies

Tests are **blocked by Task #1** (Obsidian sync implementation).

Once sync service is implemented:
1. Replace test `pass` statements with actual assertions
2. Verify mocks work with real implementation
3. Run tests and achieve 80%+ coverage

## Key Principles

1. **No Real Obsidian** — Don't connect to actual Obsidian vaults
2. **No Real APIs** — Mock all remote calls with patches
3. **Real Files** — Use actual file I/O with temp directories
4. **Deterministic** — Same test input = same result every run
5. **Fast** — All tests complete in <2 seconds
6. **Isolated** — Each test is independent
7. **Clear Failures** — Assertion errors clearly indicate what broke
