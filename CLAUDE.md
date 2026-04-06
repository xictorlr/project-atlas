# Project Atlas repository memory

## Mission
"El Consultor" — an edge-first knowledge compiler for consultants. Record meetings, upload documents, and Atlas compiles everything into a searchable Markdown vault with meeting minutes, summaries, action items, and client-ready reports. All inference runs locally via Ollama + MLX. Zero data leaves the machine.

## Product stance
- Build a consultant's knowledge companion, not a generic chat-over-docs toy.
- Edge-first: all inference runs on-device via Ollama (LLMs) + lightning-whisper-mlx (STT) + mlx-vlm (OCR). No cloud APIs.
- Treat the Markdown vault as a first-class product artifact, not an export side effect.
- Preserve provenance, citations, backlinks, and file stability so the vault stays useful in Obsidian.
- Prefer deterministic pipelines for ingest, compilation, indexing, and publishing; use LLM judgment where synthesis is the point.
- Default to reversible changes, append-only logs, and idempotent jobs.
- Self-contained: all models, data, and uploads live in `.local/` inside the project directory.

## Core stack assumption
- Monorepo with pnpm for JavaScript workspaces and uv for Python services.
- apps/web: Next.js App Router, TypeScript, Tailwind, shadcn/ui.
- services/api: FastAPI for domain APIs and auth-protected orchestration endpoints.
- services/worker: Python job runners for ingest, compilation, indexing, export, and health checks.
- Inference: Ollama 0.19+ (MLX backend) for LLMs and embeddings, lightning-whisper-mlx for speech-to-text, mlx-vlm for vision/OCR.
- PostgreSQL with pgvector for relational state + vector embeddings, Redis for queues and caching.
- Markdown vault on disk is a product asset and must remain portable.
- Apple Silicon first (M1+), with CPU fallbacks for Linux.

## Architecture principles
- Source of truth for user-authored and model-authored knowledge is the vault plus relational metadata, never hidden chat state.
- Every generated artifact must record source coverage, generation time, model, and confidence notes.
- Separate raw source storage, compiled Markdown, derived indexes, and published UI caches.
- Sequential model loading: only one large model in memory at a time. Unload before loading next.
- InferenceRouter is the single entry point for all ML inference. No direct imports of model libraries.
- Keep vendor adapters thin so DeerFlow, Hermes, and MiroFish can be swapped or disabled independently. All three run locally against Ollama + vault RAG.
- Treat MiroFish as optional and isolated because simulation is a premium workflow requiring user confirmation.

## Development workflow
- Explore first, then plan, then implement.
- Before editing, read the closest relevant rule file under .claude/rules.
- Use skills for big workflows instead of embedding giant instructions in chat.
- Make small, reviewable commits and keep generated code consistent with surrounding style.
- Run relevant tests and linters before claiming a change is complete.
- Update docs, prompts, migrations, and schemas together when behavior changes.

## Non-negotiable behaviors
- Never silently change stable vault paths or slugs without a migration plan.
- Never invent citations or provenance fields.
- Never destroy user edits in the vault; merge, annotate, or create review tasks instead.
- Never expose secrets from local files, environment variables, or private vault content.
- Never wire premium or dangerous workflows directly to one-click actions without confirmation and audit trails.

## Repository map
- apps/web: end-user interface, dashboard, reader, editor shells, admin pages.
- services/api: authentication, workspace APIs, vault APIs, job APIs, publication APIs.
- services/worker: ingestion, compiler, search indexing, health checks, exports.
- packages/shared: shared types, schemas, utilities, prompts, adapters.
- vault/: sample or local development knowledge vault.
- docs/: long-form specifications and playbooks.
- .claude/rules/: modular always-on or path-scoped instructions.
- .claude/skills/: reusable workflows invoked on demand.
- .claude/agents/: specialized subagents.

## Preferred implementation sequence
1. Define domain models and repository layout.
2. Build source ingest and raw storage.
3. Build the Markdown compiler and vault synchronization.
4. Build search, citations, and answer assembly.
5. Build the web UI and workspace permissions.
6. Add Obsidian sync and export flows.
7. Add DeerFlow and Hermes adapters.
8. Add MiroFish as an isolated optional module.
9. Add health checks, evals, billing, and operations.

## Quality gates
- Strong typing on TypeScript and Python boundaries.
- Schema validation for all API payloads and job payloads.
- Snapshot or fixture tests for Markdown compiler output.
- E2E coverage for ingest, compile, search, answer, publish, and vault sync.
- Security review for any feature that reads local files, executes code, or reaches third-party services.

## Response style when working in this repo
- Be direct, concrete, and implementation-first.
- Call out assumptions before coding around them.
- Prefer diffs, acceptance criteria, and file-level plans over vague prose.
- When uncertain, inspect the codebase or docs instead of guessing.
- Keep root memory concise; move deep guidance into rules, skills, or docs.

## Read these next depending on task
- Product and scope: .claude/rules/00-product-and-scope.md
- Monorepo and architecture: .claude/rules/10-architecture-and-boundaries.md
- Frontend work: .claude/rules/20-frontend-nextjs.md
- Backend and jobs: .claude/rules/30-backend-and-jobs.md
- Vault and Obsidian: .claude/rules/40-vault-and-obsidian.md
- Search and answers: .claude/rules/50-search-and-answering.md
- Security and privacy: .claude/rules/60-security-and-privacy.md
- Testing and docs: .claude/rules/70-testing-and-docs.md
- Integrations and licensing: .claude/rules/80-integrations-and-licensing.md

## Suggested skills
- /plan-product [scope]
- /design-architecture [scope]
- /build-ingest [scope]
- /compile-vault [scope]
- /build-search [scope]
- /build-web-ui [scope]
- /integrate-obsidian [scope]
- /wire-deerflow [scope]
- /wire-hermes [scope]
- /wire-mirofish [scope]
- /author-evals [scope]
- /run-health-checks [scope]
- /secure-release [scope]

## Definition of done
- Code builds.
- Tests relevant to the change pass.
- Docs and prompts are updated.
- Data migrations are safe and reversible.
- Vault impact has been reviewed.
- Risks and follow-up tasks are explicitly listed.


<claude-recall-context>
# Recent Activity

<!-- This section is auto-generated by claude-recall. Edit content outside the tags. -->

*No recent activity*
</claude-recall-context>