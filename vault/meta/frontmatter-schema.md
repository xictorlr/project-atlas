---
title: "Frontmatter Schema Reference"
slug: frontmatter-schema
type: meta
created: "2026-04-05T00:00:00Z"
updated: "2026-04-05T00:00:00Z"
---

# Frontmatter Schema Reference

Canonical YAML frontmatter fields for each note type in this vault.
All generated notes must conform to this schema. Fields marked **required** must be present and non-null.
Fields marked *optional* may be omitted or null when not applicable.

---

## Common fields (all note types)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | required | Human-readable note title. Used as the Obsidian display name. |
| `slug` | string | required | URL-safe, lowercase, hyphen-separated identifier. Must be stable once set. |
| `type` | enum | required | One of: `source`, `entity`, `concept`, `index`, `timeline`, `meta`. |
| `created` | ISO 8601 datetime | required | When this note was first generated. Set once; never updated. |
| `updated` | ISO 8601 datetime | required | When this note was last modified by the compiler or a user. |
| `workspace_id` | string | required | Owning workspace identifier (`ws_…`). Enables multi-tenant filtering. |
| `tags` | string[] | required | Namespaced tag list. Use `type/subtype` format (e.g., `source/article`). |
| `aliases` | string[] | optional | Alternative titles Obsidian should resolve as wikilinks. |

---

## Source notes (`type: source`)

Stored under `vault/sources/`. One note per ingested source artifact.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_id` | string | required | Stable source identifier (`src_…`) from the relational store. |
| `provenance.url` | string | optional | Original URL if web-sourced. |
| `provenance.retrieved_at` | ISO 8601 datetime | optional | When the source was fetched. |
| `provenance.ingested_by` | string | required | Worker component that performed ingest (e.g., `worker/ingest-v1`). |
| `provenance.ingest_job_id` | string | required | Job identifier for the ingest run (`job_…`). |
| `provenance.content_hash` | string | required | SHA-256 of the raw content, prefixed `sha256:`. Used for dedup. |
| `provenance.mime_type` | string | required | MIME type of the original artifact (e.g., `text/html`, `application/pdf`). |
| `provenance.char_count` | integer | required | Character count of normalized text after extraction. |
| `author` | string | optional | Attributed author from source metadata. |
| `published_at` | date (YYYY-MM-DD) | optional | Publication date from source metadata. |
| `language` | ISO 639-1 code | optional | Primary language of the source (e.g., `en`). |
| `entities` | string[] | optional | Wikilink slugs of entity notes referenced by this source. |
| `concepts` | string[] | optional | Wikilink slugs of concept notes referenced by this source. |
| `confidence` | float 0–1 | optional | Compiler confidence in the extracted summary. Null if not generated. |
| `model` | string | optional | Model ID used for note generation (e.g., `claude-sonnet-4-6`). |
| `generation_notes` | string | optional | Free-text notes from the compiler about quality or gaps. |

---

## Entity notes (`type: entity`)

Stored under `vault/entities/`. One note per tracked real-world entity.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_kind` | enum | required | One of: `person`, `company`, `project`, `paper`, `dataset`, `product`, `place`, `event`. |
| `provenance.source_ids` | string[] | required | Source identifiers (`src_…`) that mention this entity. |
| `provenance.compiled_by` | string | required | Worker component that generated this note (e.g., `worker/compiler-v1`). |
| `provenance.compile_job_id` | string | required | Job identifier for the compile run. |
| `provenance.model` | string | required | Model ID used during synthesis. |
| `provenance.generated_at` | ISO 8601 datetime | required | When this version of the note was synthesized. |
| `provenance.confidence` | float 0–1 | required | Compiler confidence in entity synthesis. |
| `sources` | wikilink[] | required | Wikilinks to source notes that ground this entity profile. |
| `concepts` | wikilink[] | optional | Wikilinks to concept notes this entity relates to. |

---

## Concept notes (`type: concept`)

Stored under `vault/concepts/`. One note per synthesized abstract topic.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provenance.source_ids` | string[] | required | Source identifiers used in synthesis. |
| `provenance.compiled_by` | string | required | Worker component (e.g., `worker/compiler-v1`). |
| `provenance.compile_job_id` | string | required | Job identifier. |
| `provenance.model` | string | required | Model ID used. |
| `provenance.generated_at` | ISO 8601 datetime | required | Generation timestamp. |
| `provenance.confidence` | float 0–1 | required | Synthesis confidence. |
| `sources` | wikilink[] | required | Grounding source notes. |
| `entities` | wikilink[] | optional | Entity notes related to this concept. |
| `related_concepts` | wikilink[] | optional | Sibling concept notes. |

---

## Index notes (`type: index`)

Stored under `vault/indexes/`. Auto-generated by the compiler; do not hand-edit.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `index_kind` | enum | required | One of: `sources`, `entities`, `concepts`, `tags`, `timeline`. |
| `generated_at` | ISO 8601 datetime | required | When the index was last rebuilt. |
| `generated_by` | string | required | Worker component that generated this index. |
| `entry_count` | integer | required | Number of entries in the index at generation time. |

---

## Timeline notes (`type: timeline`)

Stored under `vault/timelines/`. Auto-generated from entity and source notes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timeline_kind` | enum | required | One of: `entity`, `topic`, `workspace`. |
| `subject_slug` | string | required | Slug of the entity or concept this timeline is for. |
| `generated_at` | ISO 8601 datetime | required | When this timeline was last rebuilt. |
| `generated_by` | string | required | Worker component. |
| `sources` | wikilink[] | required | Source notes that contributed events. |

---

## Slug rules

- Lowercase ASCII, digits, and hyphens only.
- Max 80 characters.
- No leading or trailing hyphens.
- Must be unique within its folder (`sources/`, `entities/`, `concepts/`, etc.).
- Set once at creation; never changed after the note is published. Rename creates a redirect stub.

## Tag namespace conventions

| Prefix | Examples | Used for |
|--------|----------|----------|
| `source/` | `source/article`, `source/pdf`, `source/repo` | Source note kind |
| `entity/` | `entity/person`, `entity/company` | Entity kind |
| `concept/` | `concept/technology`, `concept/policy` | Concept domain |
| `status/` | `status/draft`, `status/reviewed`, `status/stale` | Review state |
| `workspace/` | `workspace/acme-corp` | Workspace scope |

## Invariants enforced by the compiler

1. `slug` matches the filename (e.g., `sample-source.md` has `slug: sample-source`).
2. `content_hash` changes if and only if the raw source content changes.
3. `created` is never updated after first write.
4. `source_id` and `workspace_id` are never changed after assignment.
5. Any note with `type: index` or `type: timeline` must not be hand-edited; compiler overwrites on rebuild.
