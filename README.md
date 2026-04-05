# Project Atlas

A knowledge compiler that turns raw sources into a living Markdown vault, searchable answers, and reusable outputs.

Atlas ingests documents (text, HTML, PDF), extracts structured knowledge, compiles it into an Obsidian-compatible Markdown vault with full provenance, and provides search with citation-backed evidence packs.

## Architecture

```
apps/web          Next.js 15 + React 19 + Tailwind + shadcn/ui
services/api      FastAPI + SQLAlchemy + Alembic + Pydantic v2
services/worker   arq job queue (ingest, compile, health checks)
packages/shared   TypeScript domain types (branded IDs, enums)
vault/            Obsidian-compatible Markdown knowledge base
```

**Infrastructure:** PostgreSQL 16, Redis 7, Docker Compose

## Quick Start

### Prerequisites

- Node.js 20+, pnpm 9+
- Python 3.12+, [uv](https://docs.astral.sh/uv/)
- Docker & Docker Compose

### 1. Start infrastructure

```bash
docker compose up -d
```

### 2. Install dependencies

```bash
# JavaScript packages
pnpm install

# Python services
cd services/api && uv sync && cd ../..
cd services/worker && uv sync && cd ../..
```

### 3. Run database migrations

```bash
cd services/api
uv run alembic upgrade head
```

### 4. Start services

```bash
# API server (port 8000)
cd services/api && uv run uvicorn atlas_api.main:app --reload

# Worker
cd services/worker && uv run python -m atlas_worker.main

# Web UI (port 3000)
pnpm --filter @atlas/web dev
```

### 5. Run tests

```bash
# All JavaScript tests (shared + web)
pnpm test

# API tests
cd services/api && uv run pytest tests/

# Worker tests
cd services/worker && uv run pytest tests/
```

## Features

### Source Ingestion
Upload text, HTML, or PDF files. The ingest pipeline extracts content, chunks it, computes SHA-256 hashes, and stores manifests for deduplication.

### Vault Compiler
Generates Obsidian-compatible Markdown notes from ingested sources:
- **Source notes** with full YAML frontmatter and provenance
- **Entity extraction** (heuristic NER: proper nouns, @mentions, URLs, emails)
- **Index generation** (sources, entities, tags)
- **Backlink verification** across `[[wikilinks]]`
- **Conflict detection** that preserves user edits

### Search & Evidence
- TF-IDF lexical search over vault notes
- Evidence pack assembly with citation-backed passages
- Footnote-style Markdown citations

### Web Dashboard
- Sources management (upload, list, detail view)
- Vault browser (Markdown reader with wikilink rendering)
- Search interface with evidence panel
- Jobs monitor with auto-refresh and recompile action

### Integration Adapters
All adapters follow a Protocol pattern and are feature-flagged via environment variables:

| Adapter | Purpose | Env var |
|---------|---------|---------|
| DeerFlow | Research orchestration | `ATLAS_DEERFLOW_ENABLED` |
| Hermes | Cross-session memory bridge | `ATLAS_HERMES_ENABLED` |
| MiroFish | Scenario simulation (isolated) | `ATLAS_MIROFISH_ENABLED` |

### Health & Observability
- Vault integrity checks (broken links, missing frontmatter, stale/orphan/duplicate notes)
- Source health monitoring
- Search quality eval framework (precision@k, recall@k, MRR)
- Compiler eval framework
- Liveness (`/health`) and readiness (`/health/ready`) probes

## Project Structure

```
.
├── apps/
│   └── web/                    # Next.js 15 frontend
│       ├── app/(dashboard)/    # Dashboard routes
│       └── components/         # UI components (shadcn/ui)
├── services/
│   ├── api/                    # FastAPI backend
│   │   ├── src/atlas_api/
│   │   │   ├── adapters/       # DeerFlow, Hermes, MiroFish
│   │   │   ├── evals/          # Search & compiler eval framework
│   │   │   ├── models/         # Pydantic v2 domain models
│   │   │   ├── routes/         # API endpoints
│   │   │   ├── schemas/        # SQLAlchemy ORM models
│   │   │   └── search/         # TF-IDF indexer, query, evidence
│   │   ├── alembic/            # Database migrations
│   │   └── tests/
│   └── worker/                 # arq job queue
│       ├── src/atlas_worker/
│       │   ├── compiler/       # Vault compiler pipeline
│       │   ├── extractors/     # Text, HTML, PDF extractors
│       │   ├── health/         # Vault & source health checks
│       │   ├── jobs/           # Ingest & compile jobs
│       │   └── sync/           # Obsidian sync & export
│       └── tests/
├── packages/
│   └── shared/                 # TypeScript domain types
├── vault/                      # Sample Obsidian vault
├── docker-compose.yml          # PostgreSQL 16 + Redis 7
└── turbo.json                  # Monorepo task runner
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness probe |
| GET | `/health/ready` | Readiness probe (DB check) |
| POST | `/workspaces` | Create workspace |
| GET | `/workspaces` | List workspaces |
| GET | `/sources` | List sources |
| POST | `/sources` | Create source metadata |
| POST | `/sources/{id}/upload` | Upload file + enqueue ingest |
| GET | `/jobs` | List jobs |
| GET | `/search?q=&limit=` | Search vault notes |
| POST | `/search/reindex` | Rebuild search index |
| POST | `/evidence` | Build evidence pack |
| GET | `/vault/notes` | List vault notes |
| GET | `/vault/notes/{slug}` | Read vault note |
| GET | `/vault/graph` | Wikilink graph |
| POST | `/export` | Export vault as ZIP |

## Test Coverage

**373 tests passing** across all packages:

| Package | Tests | Coverage |
|---------|-------|----------|
| `services/api` | 162 passed, 53 skipped | Search, vault, adapters, evals, health |
| `services/worker` | 130 passed, 24 skipped | Extractors, compiler, ingest, sync, health |
| `apps/web` | 72 passed | Components, pages |
| `packages/shared` | 9 passed | Branded ID type guards |

## Design Principles

- **Vault-first**: The Markdown vault is a first-class product artifact, not an export side effect
- **Provenance**: Every generated artifact records source coverage, generation time, and confidence
- **Deterministic pipelines**: Ingest, compilation, and indexing are deterministic; LLM judgment is used only where synthesis is the point
- **Immutable data**: Frozen Pydantic models, readonly TypeScript interfaces
- **Replaceable adapters**: Protocol-based adapters behind feature flags
- **Idempotent jobs**: All jobs are retry-safe with deduplication

## Claude Code Kit

This repository also serves as a production-grade Claude Code instruction set. It includes:

- `CLAUDE.md` — concise project memory loaded every session
- `.claude/rules/` — modular instructions (9 domain rule files), some path-gated
- `.claude/skills/` — long-form workflows for repeatable tasks (14 skills)
- `.claude/agents/` — specialized subagents (8 agents: research, architecture, UI, backend, data, QA, security, Obsidian)
- `docs/` — detailed design references, product specs, and implementation playbooks

The entire codebase was generated from these instructions using Claude Code agent teams.

## License

Private repository.
