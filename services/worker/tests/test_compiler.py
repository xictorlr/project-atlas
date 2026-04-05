"""Tests for the vault compiler pipeline (tasks #6–#9).

Coverage:
  - slug generation (source_notes.make_slug)
  - vault_writer: create, update, skip, conflict detection
  - source_notes.generate_source_note: create and idempotent update
  - entity_extraction.extract_entities: heuristic patterns
  - entity_extraction.extract_and_generate: note creation + source patching
  - backlinks.verify_all: valid and broken link detection
  - index_generator.rebuild_indexes: produces three index files
  - compile_vault orchestrator: end-to-end with fixture data
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from atlas_worker.compiler.entity_extraction import extract_and_generate, extract_entities
from atlas_worker.compiler.index_generator import rebuild_indexes
from atlas_worker.compiler.backlinks import verify_all
from atlas_worker.compiler.source_notes import (
    SourceProvenance,
    SourceRecord,
    generate_source_note,
    make_slug,
)
from atlas_worker.compiler.vault_writer import (
    parse_frontmatter,
    render_frontmatter,
    write_note,
)
from atlas_worker.jobs.compile import compile_vault


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    return tmp_path / "vault"


def _make_provenance(**kwargs) -> SourceProvenance:
    defaults = {
        "ingest_job_id": "job_test001",
        "content_hash": "sha256:" + hashlib.sha256(b"test").hexdigest(),
        "mime_type": "text/html",
        "char_count": 42,
        "ingested_by": "worker/ingest-v1",
        "url": "https://example.com/article",
        "retrieved_at": "2026-04-05T00:00:00Z",
    }
    defaults.update(kwargs)
    return SourceProvenance(**defaults)


def _make_record(**kwargs) -> SourceRecord:
    defaults = {
        "source_id": "src_test001",
        "workspace_id": "ws_test001",
        "title": "Acme Corp Annual Report 2025",
        "extracted_text": (
            "Acme Corp published its Annual Report 2025. "
            "CEO John Smith announced record profits. "
            "The Acme Platform now serves 10 million users. "
            "Contact: info@acme.com or visit https://acme.com."
        ),
        "provenance": _make_provenance(),
        "tags": [],
        "author": "Jane Doe",
        "published_at": "2025-12-31",
        "language": "en",
    }
    defaults.update(kwargs)
    return SourceRecord(**defaults)


def _source_note_path(vault_root: Path, record: SourceRecord) -> Path:
    slug = make_slug(record.title)
    return vault_root / record.workspace_id / "sources" / f"{slug}.md"


# ---------------------------------------------------------------------------
# Slug tests
# ---------------------------------------------------------------------------


class TestMakeSlug:
    def test_basic_title(self):
        assert make_slug("Hello World") == "hello-world"

    def test_special_chars_stripped(self):
        assert make_slug("Hello, World! (2025)") == "hello-world-2025"

    def test_max_length(self):
        long = "word " * 30
        result = make_slug(long)
        assert len(result) <= 80

    def test_no_leading_trailing_hyphens(self):
        result = make_slug("  ---hello--- ")
        assert not result.startswith("-")
        assert not result.endswith("-")

    def test_empty_string(self):
        assert make_slug("") == ""

    def test_deterministic(self):
        title = "OpenAI Research Lab 2025"
        assert make_slug(title) == make_slug(title)


# ---------------------------------------------------------------------------
# vault_writer tests
# ---------------------------------------------------------------------------


class TestWriteNote:
    def test_creates_new_note(self, tmp_path: Path):
        path = tmp_path / "notes" / "test.md"
        fm = {
            "title": "Test",
            "slug": "test",
            "type": "source",
            "created": "2026-01-01T00:00:00Z",
            "updated": "2026-01-01T00:00:00Z",
        }
        result = write_note(path, fm, "# Test\nBody here.\n")
        assert result.action == "created"
        assert path.exists()
        assert "title: Test" in path.read_text()

    def test_creates_parent_dirs(self, tmp_path: Path):
        path = tmp_path / "a" / "b" / "c" / "note.md"
        write_note(path, {"title": "X", "slug": "x", "created": "t", "updated": "t"}, "body")
        assert path.exists()

    def test_skips_identical_content(self, tmp_path: Path):
        path = tmp_path / "note.md"
        fm = {"title": "T", "slug": "t", "created": "t", "updated": "t"}
        write_note(path, fm, "# T\n")
        result = write_note(path, fm, "# T\n")
        assert result.action == "skipped"

    def test_preserves_created_field(self, tmp_path: Path):
        path = tmp_path / "note.md"
        fm1 = {
            "title": "T",
            "slug": "t",
            "created": "2026-01-01T00:00:00Z",
            "updated": "2026-01-01T00:00:00Z",
        }
        write_note(path, fm1, "body\n")
        fm2 = {
            "title": "T",
            "slug": "t",
            "created": "2099-01-01T00:00:00Z",
            "updated": "2099-01-01T00:00:00Z",
        }
        write_note(path, fm2, "body\n", generated_section="## Updated\nnew\n")
        raw = path.read_text()
        loaded, _ = parse_frontmatter(raw)
        assert loaded["created"] == "2026-01-01T00:00:00Z"

    def test_replaces_generated_section(self, tmp_path: Path):
        path = tmp_path / "note.md"
        fm = {"title": "T", "slug": "t", "created": "t", "updated": "t"}
        write_note(path, fm, "body\n", generated_section="old content\n")
        result = write_note(path, fm, "body\n", generated_section="new content\n")
        assert result.action == "updated"
        assert "new content" in path.read_text()
        assert "old content" not in path.read_text()

    def test_conflict_when_no_generated_block_and_body_differs(self, tmp_path: Path):
        path = tmp_path / "note.md"
        fm = {"title": "T", "slug": "t", "created": "t", "updated": "t"}
        # Write without generated section.
        path.write_text(render_frontmatter(fm) + "user authored body\n", encoding="utf-8")
        result = write_note(path, fm, "different body\n")
        assert result.action == "conflict"
        assert result.conflict is not None
        # File must not be overwritten.
        assert "user authored body" in path.read_text()


# ---------------------------------------------------------------------------
# source_notes tests
# ---------------------------------------------------------------------------


class TestGenerateSourceNote:
    def test_creates_note(self, vault_root: Path):
        record = _make_record()
        result = generate_source_note(record, vault_root)
        assert result.action == "created"
        assert result.path.exists()
        assert result.slug == make_slug(record.title)

    def test_note_path_structure(self, vault_root: Path):
        record = _make_record()
        result = generate_source_note(record, vault_root)
        expected = vault_root / record.workspace_id / "sources" / f"{result.slug}.md"
        assert result.path == expected

    def test_frontmatter_required_fields(self, vault_root: Path):
        record = _make_record()
        generate_source_note(record, vault_root)
        raw = _source_note_path(vault_root, record).read_text()
        fm, _ = parse_frontmatter(raw)
        assert fm["type"] == "source"
        assert fm["source_id"] == record.source_id
        assert fm["workspace_id"] == record.workspace_id
        assert fm["slug"] == make_slug(record.title)
        assert any("source/" in t for t in fm["tags"])
        assert fm["provenance"]["content_hash"] == record.provenance.content_hash

    def test_body_contains_title_heading(self, vault_root: Path):
        record = _make_record()
        generate_source_note(record, vault_root)
        raw = _source_note_path(vault_root, record).read_text()
        assert f"# {record.title}" in raw

    def test_body_contains_excerpt(self, vault_root: Path):
        record = _make_record()
        generate_source_note(record, vault_root)
        raw = _source_note_path(vault_root, record).read_text()
        assert "atlas:generated" in raw

    def test_idempotent_update(self, vault_root: Path):
        record = _make_record()
        r1 = generate_source_note(record, vault_root)
        assert r1.action == "created"
        r2 = generate_source_note(record, vault_root)
        assert r2.action in ("updated", "skipped")

    def test_slug_matches_filename(self, vault_root: Path):
        record = _make_record()
        result = generate_source_note(record, vault_root)
        assert result.path.stem == result.slug

    def test_missing_title_raises(self, vault_root: Path):
        record = _make_record(title="")
        with pytest.raises(ValueError, match="title"):
            generate_source_note(record, vault_root)

    def test_missing_source_id_raises(self, vault_root: Path):
        record = _make_record(source_id="")
        with pytest.raises(ValueError, match="source_id"):
            generate_source_note(record, vault_root)

    def test_generates_source_tag_from_mime_type(self, vault_root: Path):
        record = _make_record(provenance=_make_provenance(mime_type="application/pdf"))
        result = generate_source_note(record, vault_root)
        raw = result.path.read_text()
        fm, _ = parse_frontmatter(raw)
        assert "source/pdf" in fm["tags"]

    def test_escapes_frontmatter_title_with_colon(self, vault_root: Path):
        record = _make_record(title="Key: Value Report 2025")
        result = generate_source_note(record, vault_root)
        assert result.path.exists()
        raw = result.path.read_text()
        fm, _ = parse_frontmatter(raw)
        assert "Key" in fm["title"]


# ---------------------------------------------------------------------------
# entity_extraction tests
# ---------------------------------------------------------------------------


class TestExtractEntities:
    def test_extracts_capitalized_phrases(self):
        text = "CEO John Smith announced the results at Acme Corporation."
        entities = extract_entities(text)
        slugs = [e.slug for e in entities]
        assert any("john-smith" in s for s in slugs)

    def test_extracts_email(self):
        text = "Contact us at support@example.com for help."
        entities = extract_entities(text)
        kinds = {e.kind for e in entities}
        assert "email" in kinds

    def test_extracts_url(self):
        text = "Visit https://example.com for more info."
        entities = extract_entities(text)
        kinds = {e.kind for e in entities}
        assert "url" in kinds

    def test_deduplicates_entities(self):
        text = "John Smith said John Smith agreed."
        entities = extract_entities(text)
        names = [e.name for e in entities]
        assert names.count("John Smith") <= 1

    def test_returns_list_for_plain_text(self):
        text = "this is a plain text sentence with no entities."
        entities = extract_entities(text)
        assert isinstance(entities, list)

    def test_no_crash_on_empty_string(self):
        assert extract_entities("") == []

    def test_handles_overlapping_patterns(self):
        text = "Contact John Smith at john@smith.com or https://smith.com."
        entities = extract_entities(text)
        assert len(entities) >= 2


class TestExtractAndGenerate:
    def test_creates_entity_notes(self, vault_root: Path):
        record = _make_record()
        text = "John Smith leads the Global Research Institute."
        result = extract_and_generate(
            record=record,
            note_text=text,
            vault_root=vault_root,
            compile_job_id="job_test002",
        )
        assert isinstance(result.entities, list)
        for note_result in result.note_results:
            assert note_result.path.exists()

    def test_entity_frontmatter_has_source_id(self, vault_root: Path):
        record = _make_record()
        text = "CEO John Smith announced the results."
        result = extract_and_generate(
            record=record,
            note_text=text,
            vault_root=vault_root,
            compile_job_id="job_test003",
        )
        for note_result in result.note_results:
            raw = note_result.path.read_text()
            fm, _ = parse_frontmatter(raw)
            prov = fm.get("provenance") or {}
            assert record.source_id in prov.get("source_ids", [])

    def test_entity_note_type_is_entity(self, vault_root: Path):
        record = _make_record()
        text = "Jane Doe leads the project."
        result = extract_and_generate(
            record=record,
            note_text=text,
            vault_root=vault_root,
            compile_job_id="job_test006",
        )
        for note_result in result.note_results:
            raw = note_result.path.read_text()
            fm, _ = parse_frontmatter(raw)
            assert fm["type"] == "entity"

    def test_patches_source_note_entities(self, vault_root: Path):
        record = _make_record()
        src_result = generate_source_note(record, vault_root)
        text = "John Smith from Global Research Institute wrote the report."
        extraction = extract_and_generate(
            record=record,
            note_text=text,
            vault_root=vault_root,
            compile_job_id="job_test004",
            source_note_path=src_result.path,
        )
        if extraction.entities:
            raw = src_result.path.read_text()
            fm, _ = parse_frontmatter(raw)
            entities_list = fm.get("entities") or []
            assert len(entities_list) > 0

    def test_idempotent_source_id_accumulation(self, vault_root: Path):
        record = _make_record()
        text = "John Smith gave a presentation."
        common_kwargs: dict = dict(
            note_text=text,
            vault_root=vault_root,
            compile_job_id="job_test005",
        )
        extract_and_generate(record=record, **common_kwargs)
        extract_and_generate(record=record, **common_kwargs)
        entities_dir = vault_root / record.workspace_id / "entities"
        if entities_dir.exists():
            for md in entities_dir.glob("*.md"):
                fm, _ = parse_frontmatter(md.read_text())
                prov = fm.get("provenance") or {}
                ids = prov.get("source_ids", [])
                assert ids.count(record.source_id) == 1

    def test_entity_kind_inferred(self, vault_root: Path):
        record = _make_record()
        text = "John Smith works at Acme Corp."
        result = extract_and_generate(
            record=record,
            note_text=text,
            vault_root=vault_root,
            compile_job_id="job_test007",
        )
        for entity in result.entities:
            assert entity.kind in ("person", "company", "project", "url", "email", "unknown")


# ---------------------------------------------------------------------------
# backlinks tests
# ---------------------------------------------------------------------------


class TestBacklinks:
    def test_no_broken_links_on_empty_vault(self, vault_root: Path):
        ws_dir = vault_root / "ws_empty"
        ws_dir.mkdir(parents=True)
        report = verify_all(ws_dir)
        assert report.broken_count == 0
        assert report.notes_scanned == 0

    def test_reports_broken_link(self, vault_root: Path):
        ws_dir = vault_root / "ws_broken"
        ws_dir.mkdir(parents=True)
        note = ws_dir / "note.md"
        note.write_text("# Note\n[[entities/nonexistent-entity]]\n", encoding="utf-8")
        report = verify_all(ws_dir)
        assert report.broken_count == 1
        assert "entities/nonexistent-entity" in report.broken_links[0].raw_target

    def test_valid_link_counted(self, vault_root: Path):
        ws_dir = vault_root / "ws_valid"
        (ws_dir / "sources").mkdir(parents=True)
        (ws_dir / "entities").mkdir(parents=True)
        source = ws_dir / "sources" / "my-source.md"
        source.write_text("# Source\n[[entities/my-entity]]\n", encoding="utf-8")
        entity = ws_dir / "entities" / "my-entity.md"
        entity.write_text("# Entity\n", encoding="utf-8")
        report = verify_all(ws_dir)
        assert report.valid_links >= 1
        assert report.broken_count == 0

    def test_nonexistent_dir_returns_empty_report(self, vault_root: Path):
        ws_dir = vault_root / "ws_does_not_exist"
        report = verify_all(ws_dir)
        assert report.broken_count == 0

    def test_link_with_display_text_resolved(self, vault_root: Path):
        ws_dir = vault_root / "ws_display"
        (ws_dir / "entities").mkdir(parents=True)
        note = ws_dir / "note.md"
        note.write_text("# Note\n[[entities/my-entity|My Entity]]\n", encoding="utf-8")
        entity = ws_dir / "entities" / "my-entity.md"
        entity.write_text("# Entity\n", encoding="utf-8")
        report = verify_all(ws_dir)
        assert report.valid_links >= 1

    def test_multiple_links_in_one_note(self, vault_root: Path):
        ws_dir = vault_root / "ws_multi"
        (ws_dir / "entities").mkdir(parents=True)
        note = ws_dir / "note.md"
        note.write_text(
            "# Note\n[[entities/exists]]\n[[entities/missing]]\n",
            encoding="utf-8",
        )
        (ws_dir / "entities" / "exists.md").write_text("# Exists\n", encoding="utf-8")
        report = verify_all(ws_dir)
        assert report.valid_links >= 1
        assert report.broken_count >= 1


# ---------------------------------------------------------------------------
# index_generator tests
# ---------------------------------------------------------------------------


class TestRebuildIndexes:
    def test_creates_three_index_files(self, vault_root: Path):
        record = _make_record()
        generate_source_note(record, vault_root)
        ws_dir = vault_root / record.workspace_id
        result = rebuild_indexes(ws_dir)
        assert result.sources_index_path.exists()
        assert result.entities_index_path.exists()
        assert result.tags_index_path.exists()

    def test_sources_index_contains_table(self, vault_root: Path):
        record = _make_record()
        generate_source_note(record, vault_root)
        ws_dir = vault_root / record.workspace_id
        rebuild_indexes(ws_dir)
        content = (ws_dir / "indexes" / "sources-index.md").read_text()
        assert "| Title |" in content
        assert make_slug(record.title) in content

    def test_index_frontmatter_type(self, vault_root: Path):
        record = _make_record()
        generate_source_note(record, vault_root)
        ws_dir = vault_root / record.workspace_id
        rebuild_indexes(ws_dir)
        raw = (ws_dir / "indexes" / "sources-index.md").read_text()
        fm, _ = parse_frontmatter(raw)
        assert fm["type"] == "index"
        assert fm["index_kind"] == "sources"

    def test_sources_index_lists_all_sources(self, vault_root: Path):
        record1 = _make_record(source_id="src_a", title="Alpha Report")
        record2 = _make_record(source_id="src_b", title="Beta Report")
        generate_source_note(record1, vault_root)
        generate_source_note(record2, vault_root)
        ws_dir = vault_root / record1.workspace_id
        result = rebuild_indexes(ws_dir)
        assert result.source_count == 2

    def test_idempotent_rebuild(self, vault_root: Path):
        record = _make_record()
        generate_source_note(record, vault_root)
        ws_dir = vault_root / record.workspace_id
        r1 = rebuild_indexes(ws_dir)
        r2 = rebuild_indexes(ws_dir)
        assert r1.source_count == r2.source_count

    def test_empty_workspace_produces_empty_tables(self, vault_root: Path):
        ws_dir = vault_root / "ws_empty2"
        ws_dir.mkdir(parents=True)
        result = rebuild_indexes(ws_dir)
        assert result.source_count == 0
        assert result.entity_count == 0

    def test_entity_index_updated_after_extraction(self, vault_root: Path):
        record = _make_record()
        generate_source_note(record, vault_root)
        text = "John Smith gave a keynote."
        extract_and_generate(
            record=record,
            note_text=text,
            vault_root=vault_root,
            compile_job_id="job_idx_test",
        )
        ws_dir = vault_root / record.workspace_id
        result = rebuild_indexes(ws_dir)
        if result.entity_count > 0:
            content = (ws_dir / "indexes" / "entities-index.md").read_text()
            assert "| Name |" in content


# ---------------------------------------------------------------------------
# compile_vault orchestrator tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestCompileVaultJob:
    @pytest.mark.asyncio
    async def test_compile_with_fixture_sources(self, vault_root: Path):
        record = _make_record()
        ctx = {"vault_root": vault_root, "db": None}
        result = await compile_vault(
            ctx,
            workspace_id=record.workspace_id,
            sources=[record],
            job_id="job_compile_test001",
        )
        assert result["job"] == "compile_vault"
        assert result["workspace_id"] == record.workspace_id
        assert result["status"] in ("ok", "partial")
        assert result["notes_created"] == 1

    @pytest.mark.asyncio
    async def test_compile_is_idempotent(self, vault_root: Path):
        record = _make_record()
        ctx = {"vault_root": vault_root, "db": None}
        r1 = await compile_vault(ctx, workspace_id=record.workspace_id, sources=[record])
        r2 = await compile_vault(ctx, workspace_id=record.workspace_id, sources=[record])
        assert r1["notes_created"] == 1
        assert r2["notes_created"] == 0
        assert r2["notes_updated"] + r2["notes_skipped"] >= 1

    @pytest.mark.asyncio
    async def test_compile_produces_index_files(self, vault_root: Path):
        record = _make_record()
        ctx = {"vault_root": vault_root, "db": None}
        await compile_vault(ctx, workspace_id=record.workspace_id, sources=[record])
        ws_dir = vault_root / record.workspace_id
        assert (ws_dir / "indexes" / "sources-index.md").exists()
        assert (ws_dir / "indexes" / "entities-index.md").exists()

    @pytest.mark.asyncio
    async def test_compile_returns_timing(self, vault_root: Path):
        record = _make_record()
        ctx = {"vault_root": vault_root, "db": None}
        result = await compile_vault(ctx, workspace_id=record.workspace_id, sources=[record])
        assert isinstance(result["total_time_ms"], int)
        assert result["total_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_compile_empty_sources(self, vault_root: Path):
        ctx = {"vault_root": vault_root, "db": None}
        result = await compile_vault(ctx, workspace_id="ws_empty", sources=[])
        assert result["notes_created"] == 0
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_compile_counts_generated_notes(self, vault_root: Path):
        records = [
            _make_record(source_id="src_a", title="Alpha Report"),
            _make_record(source_id="src_b", title="Beta Analysis"),
        ]
        ctx = {"vault_root": vault_root, "db": None}
        result = await compile_vault(
            ctx, workspace_id="ws_test001", sources=records, job_id="job_multi"
        )
        assert result["notes_created"] == 2

    @pytest.mark.asyncio
    async def test_compile_includes_vault_path_in_index(self, vault_root: Path):
        record = _make_record()
        ctx = {"vault_root": vault_root, "db": None}
        await compile_vault(ctx, workspace_id=record.workspace_id, sources=[record])
        index_path = vault_root / record.workspace_id / "indexes" / "sources-index.md"
        assert index_path.exists()
