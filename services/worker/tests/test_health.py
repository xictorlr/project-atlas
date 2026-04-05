"""Unit tests for the worker health check package.

Tests vault_health.check_vault and source_health.check_sources using
temporary vault directories and synthetic source records.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas_worker.health.models import HealthReport, IssueSeverity
from atlas_worker.health.source_health import check_sources
from atlas_worker.health.vault_health import check_vault


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _write_note(directory: Path, filename: str, content: str) -> Path:
    path = directory / filename
    path.write_text(content, encoding="utf-8")
    return path


VALID_SOURCE_NOTE = """\
---
title: "Sample Source"
slug: sample-source
type: source
created: "2026-04-01T00:00:00Z"
updated: "2026-04-01T00:00:00Z"
workspace_id: ws_test
tags:
  - source/article
source_id: src_001
provenance:
  ingested_by: worker/ingest-v1
  ingest_job_id: job_001
  content_hash: sha256:abc123
  mime_type: text/html
  char_count: 500
---

This is the body of the note. It links to [[entities/some-entity]].
"""

VALID_ENTITY_NOTE = """\
---
title: "Some Entity"
slug: some-entity
type: entity
created: "2026-04-01T00:00:00Z"
updated: "2026-04-01T00:00:00Z"
workspace_id: ws_test
tags:
  - entity/company
entity_kind: company
provenance:
  source_ids:
    - src_001
  compiled_by: worker/compiler-v1
  compile_job_id: job_002
  model: claude-sonnet-4-6
  generated_at: "2026-04-01T00:00:00Z"
  confidence: 0.9
sources:
  - "[[sources/sample-source]]"
---

Some Entity is a notable company mentioned in source documents.
"""


# ── vault_health tests ────────────────────────────────────────────────────────


class TestCheckVaultMissingDir:
    def test_returns_error_when_vault_dir_missing(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent_workspace"
        report = check_vault(missing)

        assert not report.healthy
        assert any(i.code == "vault_dir_missing" for i in report.issues)


class TestCheckVaultHealthyNotes:
    def test_no_issues_for_valid_notes(self, tmp_path: Path) -> None:
        vault = tmp_path / "ws_test"
        sources_dir = vault / "sources"
        entities_dir = vault / "entities"
        sources_dir.mkdir(parents=True)
        entities_dir.mkdir(parents=True)

        _write_note(sources_dir, "sample-source.md", VALID_SOURCE_NOTE)
        _write_note(entities_dir, "some-entity.md", VALID_ENTITY_NOTE)

        report = check_vault(vault)

        broken = [i for i in report.issues if i.code == "broken_wikilink"]
        missing_fm = [i for i in report.issues if i.code == "missing_frontmatter"]
        assert not broken, f"Unexpected broken links: {broken}"
        assert not missing_fm, f"Unexpected missing frontmatter: {missing_fm}"


class TestCheckVaultBrokenLink:
    def test_detects_broken_wikilink(self, tmp_path: Path) -> None:
        vault = tmp_path / "ws_broken"
        sources_dir = vault / "sources"
        sources_dir.mkdir(parents=True)

        _write_note(sources_dir, "lone-note.md", """\
---
title: "Lone Note"
slug: lone-note
type: source
created: "2026-04-01T00:00:00Z"
updated: "2026-04-01T00:00:00Z"
workspace_id: ws_broken
tags: [source/article]
source_id: src_x
provenance:
  ingested_by: worker/ingest-v1
  ingest_job_id: job_x
  content_hash: sha256:aaa
  mime_type: text/html
  char_count: 100
---

Links to a [[does-not-exist]] note.
""")

        report = check_vault(vault)
        broken = [i for i in report.issues if i.code == "broken_wikilink"]
        assert len(broken) == 1
        assert broken[0].severity == IssueSeverity.ERROR


class TestCheckVaultMissingFrontmatter:
    def test_detects_missing_required_fields(self, tmp_path: Path) -> None:
        vault = tmp_path / "ws_missing_fm"
        vault.mkdir(parents=True)

        _write_note(vault, "bare-note.md", "# No frontmatter here\n\nJust body text.\n")

        report = check_vault(vault)
        missing = [i for i in report.issues if i.code == "missing_frontmatter"]
        # All common required fields should be reported
        assert len(missing) >= 5


class TestCheckVaultEmptyNote:
    def test_detects_empty_body(self, tmp_path: Path) -> None:
        vault = tmp_path / "ws_empty"
        vault.mkdir(parents=True)

        _write_note(vault, "empty-body.md", """\
---
title: "Empty"
slug: empty
type: concept
created: "2026-04-01T00:00:00Z"
updated: "2026-04-01T00:00:00Z"
workspace_id: ws_empty
tags: [concept/technology]
provenance:
  source_ids: [src_1]
  compiled_by: worker/compiler-v1
  compile_job_id: job_1
  model: claude-sonnet-4-6
  generated_at: "2026-04-01T00:00:00Z"
  confidence: 0.8
sources: []
---
""")

        report = check_vault(vault)
        empty = [i for i in report.issues if i.code == "empty_note"]
        assert len(empty) == 1
        assert empty[0].severity == IssueSeverity.WARNING


class TestCheckVaultDuplicateSlug:
    def test_detects_duplicate_slugs(self, tmp_path: Path) -> None:
        vault = tmp_path / "ws_dupe"
        a_dir = vault / "sources"
        b_dir = vault / "entities"
        a_dir.mkdir(parents=True)
        b_dir.mkdir(parents=True)

        shared_fm = """\
---
title: "Duplicate"
slug: my-slug
type: {note_type}
created: "2026-04-01T00:00:00Z"
updated: "2026-04-01T00:00:00Z"
workspace_id: ws_dupe
tags: []
{extras}
---
Body here.
"""
        _write_note(
            a_dir,
            "note-a.md",
            shared_fm.format(
                note_type="source",
                extras="source_id: src_a\nprovenance:\n  ingested_by: w\n  ingest_job_id: j\n  content_hash: sha256:x\n  mime_type: text/html\n  char_count: 10",
            ),
        )
        _write_note(
            b_dir,
            "note-b.md",
            shared_fm.format(
                note_type="entity",
                extras="entity_kind: company\nprovenance:\n  source_ids: []\n  compiled_by: w\n  compile_job_id: j\n  model: m\n  generated_at: 2026-04-01T00:00:00Z\n  confidence: 0.5\nsources: []",
            ),
        )

        report = check_vault(vault)
        dupes = [i for i in report.issues if i.code == "duplicate_slug"]
        assert len(dupes) >= 1


class TestCheckVaultStats:
    def test_stats_populated(self, tmp_path: Path) -> None:
        vault = tmp_path / "ws_stats"
        vault.mkdir(parents=True)
        _write_note(vault, "note.md", "# Just a note\n\nBody.\n")

        report = check_vault(vault)
        assert "notes_scanned" in report.stats
        assert report.stats["notes_scanned"] == 1


# ── source_health tests ───────────────────────────────────────────────────────


class _FakeSource:
    def __init__(
        self,
        id: str,
        workspace_id: str = "ws_test",
        status: str = "ready",
        vault_note_path: str | None = None,
        manifest: dict | None = None,
    ) -> None:
        self.id = id
        self.workspace_id = workspace_id
        self.status = status
        self.vault_note_path = vault_note_path
        self.manifest = manifest


class TestCheckSourcesHealthy:
    def test_no_issues_for_healthy_sources(self, tmp_path: Path) -> None:
        vault = tmp_path / "vault"
        sources_dir = vault / "sources"
        sources_dir.mkdir(parents=True)
        (sources_dir / "src_001.md").write_text("# Note\n\nBody.\n")

        src = _FakeSource(
            id="src_001",
            status="ready",
            vault_note_path="sources/src_001.md",
            manifest={"key": "value"},
        )
        report = check_sources([src], vault)
        assert report.healthy
        assert report.warning_count == 0


class TestCheckSourcesFailed:
    def test_detects_failed_source(self, tmp_path: Path) -> None:
        src = _FakeSource(id="src_bad", status="failed", manifest={"key": "val"})
        report = check_sources([src], tmp_path / "vault")

        errors = [i for i in report.issues if i.code == "source_failed"]
        assert len(errors) == 1
        assert errors[0].severity == IssueSeverity.ERROR


class TestCheckSourcesNoVaultNote:
    def test_detects_missing_vault_note_path(self, tmp_path: Path) -> None:
        src = _FakeSource(id="src_nopath", vault_note_path=None, manifest={"k": "v"})
        report = check_sources([src], tmp_path / "vault")

        issues = [i for i in report.issues if i.code == "source_no_vault_note"]
        assert len(issues) == 1


class TestCheckSourcesNoManifest:
    def test_detects_missing_manifest(self, tmp_path: Path) -> None:
        src = _FakeSource(id="src_noman", manifest=None)
        report = check_sources([src], tmp_path / "vault")

        issues = [i for i in report.issues if i.code == "source_no_manifest"]
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.WARNING


class TestCheckSourcesEmpty:
    def test_empty_source_list_healthy(self, tmp_path: Path) -> None:
        report = check_sources([], tmp_path / "vault")
        assert report.healthy
        assert report.stats["sources_checked"] == 0
