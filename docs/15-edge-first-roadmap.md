# Edge-First Roadmap: MLX + Ollama Hybrid

> Decision date: 2026-04-06
> Last updated: 2026-04-06
> Status: PROPOSED
> Supersedes: None (extends existing architecture)

## Executive Summary

Pivot Atlas from cloud-dependent LLM stubs to a fully **edge-first** architecture using a **hybrid MLX + Ollama** runtime. Each pipeline stage uses the optimal local backend: `lightning-whisper-mlx` for transcription, `mlx-vlm` for OCR/vision, Ollama 0.19+ (MLX backend) for LLM synthesis, and Ollama for embeddings. Zero data leaves the machine. Future: `mlx-audio` + Kokoro for text-to-speech.

## Design Principles

1. **Edge-only by default** — all inference runs locally; no cloud API keys required
2. **Best backend per task** — Ollama for LLMs + embeddings, MLX-native libs for STT + OCR + TTS
3. **Model-agnostic** — Gemma 4, Qwen 3.5, Llama, Mistral, DeepSeek swappable via config
4. **Additive, not destructive** — existing deterministic pipeline stays; LLM enhances it
5. **Graceful degradation** — if inference is down, deterministic extractors still work
6. **Project-centric UX** — user creates a project, adds sources (audio/PDF/image/text), gets a compiled knowledge vault
7. **Self-contained** — all downloads (models, deps, data) live inside the project directory; nothing scattered across `~/.ollama`, `~/.cache`, or system paths
8. **Apple Silicon first** — MLX gives 30-93% faster inference on Mac M-series vs pure llama.cpp

---

## Self-Contained Storage Layout

Everything lives inside the project directory. Nothing goes to `~/.ollama`, `~/.cache/huggingface`, or system paths.

```
knowledge-compiler-claude-kit/
├── .local/                          # ALL runtime assets (gitignored)
│   ├── ollama/                      # Ollama LLM + embedding storage (OLLAMA_MODELS)
│   │   └── manifests/
│   │   └── blobs/                   # Model weights (~7-18 GB per model)
│   ├── mlx/                         # MLX-native model cache
│   │   ├── whisper/                 # lightning-whisper-mlx models
│   │   │   └── large-v3/           # ~3 GB, MLX-quantized
│   │   ├── vlm/                    # mlx-vlm vision models
│   │   │   └── gemma4-vision/      # ~8 GB, for OCR/whiteboard
│   │   └── audio/                  # mlx-audio models (future)
│   │       └── kokoro/             # ~82 MB, TTS
│   ├── data/
│   │   ├── postgres/                # PostgreSQL data dir
│   │   └── redis/                   # Redis RDB + AOF
│   ├── uploads/                     # Raw uploaded files (audio, PDF, text)
│   ├── inbox/                       # Mobile sync drop folder (Phase 7 ready)
│   ├── embeddings/                  # DuckDB portable export (pgvector is primary in PostgreSQL)
│   └── tmp/                         # Temp files for extraction (auto-cleaned)
├── vault/                           # Compiled Markdown vault (the product)
├── node_modules/                    # JS deps (pnpm)
├── services/api/.venv/              # Python API deps (uv)
├── services/worker/.venv/           # Python worker deps (uv)
└── ...
```

### Environment variables that enforce this

```env
# All paths relative to project root
ATLAS_ROOT=/Volumes/DiscoDeDesarrollo/knowledge-compiler-claude-kit

# Ollama models (LLMs + embeddings) — stay in project
OLLAMA_MODELS=${ATLAS_ROOT}/.local/ollama

# MLX models (Whisper, Vision, TTS) — stay in project
ATLAS_MLX_DIR=${ATLAS_ROOT}/.local/mlx
HF_HOME=${ATLAS_ROOT}/.local/mlx    # HuggingFace cache → project-local

# PostgreSQL data — stay in project
PGDATA=${ATLAS_ROOT}/.local/data/postgres

# Redis persistence — stay in project
REDIS_DATA=${ATLAS_ROOT}/.local/data/redis

# File uploads — stay in project
ATLAS_UPLOAD_DIR=${ATLAS_ROOT}/.local/uploads

# Embeddings DB — stay in project
ATLAS_EMBEDDINGS_DIR=${ATLAS_ROOT}/.local/embeddings

# Temp extraction workspace — stay in project
ATLAS_TMP_DIR=${ATLAS_ROOT}/.local/tmp
```

### .gitignore additions

```gitignore
# Local runtime assets — all downloads, models, data
.local/
```

### Why this matters

1. **Portable**: Move the project folder → everything comes with it
2. **Deletable**: `rm -rf .local/` reclaims all disk space, no orphaned files
3. **Multi-project**: Two Atlas instances don't share or conflict on models
4. **Auditable**: `du -sh .local/*` shows exactly what's using disk space
5. **Offline**: After first setup, zero network needed — everything is local

---

## Hardware Requirements

### Sequential Pipeline = Bigger Models

The pipeline loads one model at a time and frees RAM before loading the next.
This means peak memory = the **largest single model**, not the sum of all models.

```
Step 1: Load Whisper large-v3 (~3 GB) → transcribe → FREE RAM
Step 2: Load mlx-vlm Gemma vision (~8 GB) → OCR     → FREE RAM
Step 3: Load Gemma 4 27B (~18 GB)     → synthesize  → FREE RAM
Step 4: Load nomic-embed (~274 MB)    → index       → FREE RAM
```

Peak usage: **~18 GB** (the biggest single model), not ~23 GB (all combined).

| Hardware | Peak RAM | Can Run |
|----------|----------|---------|
| Mac M1 16GB | 16 GB usable | Gemma 4 12B (Q4), Whisper large, all embeddings |
| Mac M2/M3 32GB | 32 GB usable | Gemma 4 27B (Q4), Qwen3.5 27B, everything |
| Mac M4 Pro 48GB+ | 48 GB usable | 70B models quantized, no limits |
| PC RTX 4090 24GB | 24 GB VRAM | Gemma 4 27B (Q4), fast CUDA inference |

**MVP target**: Mac with 16GB+ unified memory. Recommended: 32GB for best model quality.

---

## Primary Use Case: The Consultant

A consultant manages multiple client projects. Each project accumulates meetings, documents, emails, and notes. Atlas compiles all of this into a structured, searchable knowledge vault with generated outputs.

### Daily Workflow

```
Morning: Consultant prepares for client meeting
  └── Opens Atlas → searches project vault for context
  └── Reviews auto-generated project status report

During meeting: Records audio on phone/laptop
  └── Takes quick typed notes in real time (optional)

After meeting:
  └── Uploads meeting audio (.m4a, .mp3)
  └── Uploads any new documents shared (.pdf, .docx, .xlsx)
  └── Uploads photos of whiteboard (.jpg, .png)
  └── Atlas pipeline runs automatically:
      1. Whisper transcribes audio with timestamps
      2. OCR extracts text from whiteboard photos
      3. pdfplumber + Gemma 4 vision extract from PDFs
      4. LLM extracts entities, decisions, action items
      5. LLM generates meeting minutes (Markdown)
      6. LLM cross-references with existing project knowledge
      7. Vault updates: new notes, updated entities, fresh indexes
      8. Search index rebuilt with embeddings

Next day:
  └── Opens project → sees compiled meeting minutes
  └── Searches "what did we decide about the API migration?"
  └── Generates client-facing status report from vault
  └── Exports deliverable as PDF or slides
```

### What Atlas Generates (Markdown Outputs)

Every output is a Markdown file in the vault with YAML frontmatter, wikilinks, and provenance tracking.

#### Per-Source Outputs (automatic on ingest)

| Output | Description | Trigger |
|--------|-------------|---------|
| **Transcript** | Timestamped meeting transcript | Audio upload |
| **Meeting Minutes** | Structured: attendees, agenda, discussion, decisions, action items | Audio + context |
| **Source Summary** | 3-5 paragraph executive summary of any document | Any source |
| **Entity Profiles** | Person/company/project cards with cross-references | Any source |
| **Reference List** | Extracted citations and bibliography | Academic/technical docs |
| **OCR Text** | Clean text extracted from images/scans | Image upload |
| **Key Quotes** | Notable passages with source attribution | Any source |

#### Cross-Source Outputs (automatic on compile)

| Output | Description | Trigger |
|--------|-------------|---------|
| **Concept Articles** | Synthesized wiki articles from multiple sources | 2+ sources on same topic |
| **Decision Log** | Chronological list of all decisions across meetings | Multiple meeting transcripts |
| **Action Item Tracker** | All action items with owner, deadline, status | Multiple meetings |
| **Stakeholder Map** | Who is involved, their role, key interactions | Entity extraction |
| **Timeline** | Chronological events and milestones | Date extraction across sources |
| **Contradiction Report** | Conflicting information across sources | Cross-source analysis |
| **Coverage Report** | What topics are well-documented vs gaps | Vault health check |

#### On-Demand Outputs (user requests via UI)

| Output | Description | Format |
|--------|-------------|--------|
| **Project Status Report** | Executive summary of current project state | Markdown → PDF |
| **Client Brief** | Polished 1-2 page summary for client delivery | Markdown → PDF |
| **Weekly Digest** | What happened this week across all sources | Markdown |
| **Risk Register** | Identified risks with likelihood/impact/mitigation | Markdown table |
| **RACI Matrix** | Responsibility assignment from meeting context | Markdown table |
| **Comparison Table** | Side-by-side comparison of options discussed | Markdown table |
| **Follow-up Email Draft** | Post-meeting email with action items | Markdown |
| **Proposal Section** | Draft section for a proposal based on vault knowledge | Markdown |
| **Slide Outline** | Structured outline for a presentation | Markdown headings |
| **FAQ Document** | Questions and answers from project knowledge | Markdown |

### Vault Structure for a Consultant Project

```
vault/
├── sources/
│   ├── meeting-2026-04-06-kickoff.md          # Transcript + minutes
│   ├── meeting-2026-04-10-sprint-review.md     # Transcript + minutes
│   ├── proposal-v2-final.md                    # PDF summary
│   ├── competitor-analysis-q1.md               # PDF summary
│   └── whiteboard-architecture-draft.md        # OCR + interpretation
├── entities/
│   ├── john-smith.md                           # Client CTO profile
│   ├── acme-corp.md                            # Client company
│   ├── api-migration-project.md                # Project entity
│   └── vendor-x.md                             # Mentioned vendor
├── concepts/
│   ├── api-migration-strategy.md               # Synthesized from 3 meetings + 2 docs
│   ├── budget-constraints.md                   # Cross-referenced from meetings
│   └── technical-debt-assessment.md            # From code review docs
├── outputs/
│   ├── decision-log.md                         # All decisions chronologically
│   ├── action-items.md                         # Active action items
│   ├── weekly-digest-2026-w15.md               # Auto-generated
│   ├── status-report-2026-04.md                # On-demand
│   └── client-brief-api-migration.md           # On-demand
├── timelines/
│   └── project-timeline.md                     # Extracted milestones
├── indexes/
│   ├── sources-index.md
│   ├── entities-index.md
│   ├── meetings-index.md                       # NEW: chronological meeting list
│   └── tags-index.md
└── meta/
    ├── frontmatter-schema.md
    └── project-config.md                       # Model preferences, output settings
```

---

## Model Catalog

### Pipeline Stages and Recommended Models

Since models load sequentially, pick the best model per stage regardless of combined size.

#### Stage 1: Transcription (Audio → Text) — lightning-whisper-mlx

**Target requirement**: 20-minute meeting audios, transcribed perfectly in two scenarios:
- **English audio → Spanish transcript** (client meetings in EN, notes in ES)
- **Spanish audio → Spanish transcript** (internal meetings in ES)

| Model | Size | 20-min audio on M2 | Quality | Multi-lang | Notes |
|-------|------|-------------------|---------|------------|-------|
| **lightning-whisper-mlx large-v3** | 3 GB | **~24 seconds** | Best | 99 languages, auto-detect | **Recommended.** Handles EN/ES natively. |
| lightning-whisper-mlx distil-large-v3 | 1.5 GB | ~15 seconds | Very good | Same coverage | Faster but slightly lower quality on accented speech |
| lightning-whisper-mlx medium | 1.5 GB | ~12 seconds | Good | Same coverage | Fallback for 8GB machines |

> `lightning-whisper-mlx` is **10x faster** than whisper.cpp and **4x faster** than mlx-whisper on Apple Silicon. Native MLX, zero-copy memory.

**Language handling**:

```python
# Transcription with language control
async def transcribe(self, audio_path: Path, language: str | None = None,
                     task: str = "transcribe") -> TranscribeResult:
    """
    task="transcribe" → output in same language as audio (ES→ES, EN→EN)
    task="translate"  → output always in English (ES→EN, FR→EN)
    
    For EN→ES: transcribe first (EN→EN), then translate text via LLM in Stage 3.
    For ES→ES: transcribe with language="es" for best accuracy.
    """
```

**EN→ES workflow** (the tricky one):
1. Whisper transcribes EN audio → EN text (highest accuracy)
2. LLM (Gemma 4 / Qwen 3) translates EN text → ES text in Stage 3
3. Both versions stored in vault note (original EN + translated ES)

This is more accurate than asking Whisper to translate directly, because:
- Whisper's built-in translation (EN only output) loses nuance
- LLM translation preserves context, domain terminology, and formatting
- You keep the original EN transcript as evidence

**Benchmark for 20-min audio**:
```
large-v3 on Mac M2 Pro:
  20 min audio = 1,200 seconds of audio
  50x realtime = 1,200 / 50 = ~24 seconds to transcribe
  
  With translation via LLM (Gemma 4 27B):
  ~2,000 words transcript → ~30 seconds to translate
  
  Total: ~54 seconds for full EN→ES pipeline
```

#### Stage 2: OCR/Vision (Images/Scans → Text) — mlx-vlm

| Model | Size | What it does | Notes |
|-------|------|-------------|-------|
| **Gemma 4 12B vision (MLX)** | ~8 GB | Multimodal — read documents, whiteboards, tables, handwriting | Via mlx-vlm. Best balance of quality and size. **Recommended.** |
| Qwen-VL (MLX) | ~8 GB | Strong document understanding, multilingual | Alternative for multi-language projects |
| Gemma 4 4B vision (MLX) | ~2.5 GB | Lighter vision model | For 16GB machines |

> `mlx-vlm` provides native MLX inference for 50+ vision-language models. Handles OCR, whiteboard interpretation, table extraction, and document understanding through image-to-text prompting. Replaces the need for dedicated OCR models like Qianfan-OCR or Tesseract.

> **Qianfan-OCR** (https://huggingface.co/baidu/Qianfan-OCR) remains a viable alternative for pure document OCR if you prefer a specialized model. Can run via HuggingFace transformers with weights cached in `.local/mlx/ocr/`.

#### Stage 3: Synthesis (Text → Knowledge)

This is the core reasoning stage: summaries, entities, concepts, reports.

| Model | Size (Q4) | Context | Strengths | Best For |
|-------|-----------|---------|-----------|----------|
| **Gemma 4 27B** | ~18 GB | 128K | Frontier quality, multimodal, structured output | Primary synthesis (32GB+ RAM) |
| **Gemma 4 12B** | ~8 GB | 128K | Strong reasoning, efficient | Primary synthesis (16GB RAM) |
| **Qwen3.5 27B Claude-Distilled** | ~18 GB | 128K | Claude Opus reasoning distilled into local model | Deep analysis, complex reasoning |
| **Qwen 2.5 32B** | ~20 GB | 128K | Excellent JSON output, multilingual | Structured extraction, multi-language projects |
| **Qwen 3 30B (A3B MoE)** | ~18 GB | 128K | MoE = fast inference, 100+ languages | High throughput, polyglot projects |
| **DeepSeek R1 32B** | ~20 GB | 128K | Chain-of-thought reasoning | Complex analysis, risk assessment |
| **Phi 4 14B** | ~9 GB | 16K | Microsoft, strong reasoning per param | Budget machines, quick extraction |
| **Command-R 35B** | ~21 GB | 128K | Built-in tool use, RAG-optimized | Report generation with citations |
| **Llama 3.1 8B** | ~5 GB | 128K | Meta, solid baseline | Minimum viable, fast |
| Gemma 4 4B | ~2.5 GB | 32K | Tiny, surprisingly capable | Ultra-light extraction |

> **Qwen3.5 27B Claude-Distilled** (https://huggingface.co/Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled) — a Qwen 3.5 27B fine-tuned on Claude Opus 4.6 reasoning traces. Potentially the best local model for deep analysis tasks like contradiction detection, risk assessment, and synthesis. Worth benchmarking against Gemma 4 27B.

#### Stage 4: Embeddings (Text → Vectors for Search)

| Model | Size | Dimensions | Notes |
|-------|------|-----------|-------|
| **nomic-embed-text** | 274 MB | 768 | Best general-purpose. **Recommended.** |
| bge-m3 | 568 MB | 1024 | Best for multilingual projects |
| mxbai-embed-large | 670 MB | 1024 | Highest quality, larger |
| all-minilm | 46 MB | 384 | Ultra-light fallback |

#### Stage 5: Translation (optional)

| Model | Size | Notes |
|-------|------|-------|
| **translategemma** | ~2 GB | Google's translation model, in Ollama |
| qwen2.5 or qwen3 | varies | Strong multi-language without dedicated model |

#### Stage 6: Text-to-Speech (future) — mlx-audio

| Model | Size | Latency | Notes |
|-------|------|---------|-------|
| **Kokoro** | 82 MB | sub-200ms | Multiple voices, natural prosody. **Recommended.** |

> `mlx-audio` provides Kokoro TTS natively on MLX with sub-200ms latency. Use cases: read meeting summaries aloud, generate audio briefings for commute, accessibility.

### Recommended Model Profiles

Pre-configured model sets based on hardware:

```yaml
# .local/model-profile.yaml

profiles:
  light:  # 16GB RAM Mac
    transcription:
      backend: lightning-whisper-mlx
      model: distil-large-v3          # 1.5 GB, ~80x realtime
    ocr:
      backend: mlx-vlm
      model: gemma-4-4b-vision        # 2.5 GB
    synthesis:
      backend: ollama
      model: gemma4:12b               # 8 GB
    embeddings:
      backend: ollama
      model: nomic-embed-text         # 274 MB
    tts: null                          # disabled on light
    peak_ram: "~8 GB"

  standard:  # 32GB RAM Mac (RECOMMENDED)
    transcription:
      backend: lightning-whisper-mlx
      model: large-v3                  # 3 GB, ~50x realtime
    ocr:
      backend: mlx-vlm
      model: gemma-4-12b-vision        # 8 GB
    synthesis:
      backend: ollama
      model: gemma4:27b                # 18 GB
    embeddings:
      backend: ollama
      model: nomic-embed-text          # 274 MB
    tts:
      backend: mlx-audio
      model: kokoro                    # 82 MB
    peak_ram: "~18 GB"

  reasoning:  # 32GB+ RAM, complex analysis (MiroFish, contradictions)
    transcription:
      backend: lightning-whisper-mlx
      model: large-v3
    ocr:
      backend: mlx-vlm
      model: gemma-4-12b-vision
    synthesis:
      backend: ollama
      model: qwen3.5-27b-claude-distilled  # Deep reasoning
    embeddings:
      backend: ollama
      model: bge-m3                    # Multilingual embeddings
    tts:
      backend: mlx-audio
      model: kokoro
    peak_ram: "~18 GB"

  polyglot:  # Multi-language projects
    transcription:
      backend: lightning-whisper-mlx
      model: large-v3                  # Whisper is already multilingual
    ocr:
      backend: mlx-vlm
      model: qwen-vl                   # Strong multilingual vision
    synthesis:
      backend: ollama
      model: qwen3:30b-a3b             # 100+ languages, MoE = fast
    embeddings:
      backend: ollama
      model: bge-m3                    # Best multilingual embeddings
    translation:
      backend: ollama
      model: translategemma
    tts:
      backend: mlx-audio
      model: kokoro
    peak_ram: "~18 GB"

  maximum:  # 64GB+ RAM, no compromises
    transcription:
      backend: lightning-whisper-mlx
      model: large-v3
    ocr:
      backend: mlx-vlm
      model: gemma-4-27b-vision
    synthesis:
      backend: ollama
      model: qwen2.5:72b              # Maximum quality
    embeddings:
      backend: ollama
      model: mxbai-embed-large
    tts:
      backend: mlx-audio
      model: kokoro
    peak_ram: "~45 GB"
```

---

## Architecture: Before vs After

### Before (current)
```
PDF/HTML/Text → pdfplumber/BS4 (deterministic) → Chunks → Heuristic entities → Vault
                                                            ↓
                                              TF-IDF search → Evidence packs
```

### After (proposed)
```
┌──────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│  Create Project → Upload Audio/PDF/Image/Text → Monitor Pipeline │
│  Browse Vault → Search → Generate Reports → Export               │
└────────────┬─────────────────────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────────────────────┐
│                        API (FastAPI)                              │
│  /projects  /sources  /jobs  /vault  /search  /outputs  /models  │
└────────────┬─────────────────────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────────────────────┐
│                  Worker Pipeline (arq + Redis)                    │
│                  Models load sequentially — one at a time         │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  STAGE 1: EXTRACT (load Whisper → free → load OCR → free)│    │
│  │  Audio    → lightning-whisper-mlx → transcript + timestamps│    │
│  │  Images   → mlx-vlm (Gemma vision) → text + layout      │    │
│  │  PDF      → pdfplumber     → text + metadata             │    │
│  │  HTML     → BS4            → text + metadata             │    │
│  │  Text     → direct         → passthrough                 │    │
│  └──────────────────────┬──────────────────────────────────┘    │
│                          │ raw text + metadata                   │
│  ┌──────────────────────▼──────────────────────────────────┐    │
│  │  STAGE 2: COMPILE (load Gemma/Qwen → hold for all tasks)│    │
│  │  Source notes     → deterministic Markdown generation     │    │
│  │  Entity extraction→ LLM-powered (persons, orgs, projects)│    │
│  │  Meeting minutes  → structured from transcript + context  │    │
│  │  Summaries        → executive summary per source          │    │
│  │  References       → bibliography extraction               │    │
│  │  Action items     → owner + deadline + status             │    │
│  │  Decisions        → cross-referenced decision log         │    │
│  │  Concepts         → cross-source synthesis                │    │
│  │  Timelines        → date extraction + sequencing          │    │
│  │  Contradictions   → conflict detection across sources     │    │
│  └──────────────────────┬──────────────────────────────────┘    │
│                          │ compiled vault notes                   │
│  ┌──────────────────────▼──────────────────────────────────┐    │
│  │  STAGE 3: INDEX (load embedding model)                    │    │
│  │  TF-IDF index     → lexical search                       │    │
│  │  Vector embeddings → semantic search (DuckDB)             │    │
│  │  Backlink verification → broken link detection            │    │
│  │  Coverage report   → what's well-documented vs gaps       │    │
│  └──────────────────────┬──────────────────────────────────┘    │
│                          │                                       │
│  ┌──────────────────────▼──────────────────────────────────┐    │
│  │  STAGE 4: GENERATE (on-demand, load synthesis model)      │    │
│  │  Status reports  → project overview from vault state       │    │
│  │  Client briefs   → polished 1-2 page summaries            │    │
│  │  Weekly digests  → what happened this week                 │    │
│  │  Follow-up emails→ post-meeting with action items          │    │
│  │  Risk registers  → identified risks with mitigation        │    │
│  │  RACI matrices   → responsibility assignment               │    │
│  │  Comparison tables→ side-by-side option analysis           │    │
│  │  Proposal drafts → sections from vault knowledge           │    │
│  │  FAQ documents   → Q&A from project knowledge              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Inference Router (shared)                                │    │
│  │  load_model() → run() → unload() → load_next()           │    │
│  │  Routes each task to the optimal local backend            │    │
│  └────┬──────────────┬──────────────┬──────────────┬───────┘    │
│       │              │              │              │             │
└───────┼──────────────┼──────────────┼──────────────┼─────────────┘
        │              │              │              │
   ┌────▼─────┐  ┌─────▼──────┐  ┌───▼────┐  ┌─────▼──────┐
   │ Ollama   │  │ lightning-  │  │ mlx-   │  │ mlx-audio  │
   │ 0.19+   │  │ whisper-mlx │  │ vlm    │  │ (future)   │
   │ (MLX    │  │            │  │        │  │            │
   │ backend)│  │ 10x faster │  │ Vision │  │ Kokoro TTS │
   │         │  │ than cpp   │  │ OCR    │  │ sub-200ms  │
   │ LLMs:   │  │            │  │        │  │            │
   │ Gemma 4 │  │ large-v3   │  │ Gemma  │  │ 82M params │
   │ Qwen3.5 │  │ medium     │  │ 4 vis  │  │            │
   │ DeepSeek│  │            │  │ Qwen-VL│  │            │
   │ Embed:  │  │            │  │        │  │            │
   │ nomic   │  │            │  │        │  │            │
   │ bge-m3  │  │            │  │        │  │            │
   └─────────┘  └────────────┘  └────────┘  └────────────┘
   .local/       .local/mlx/    .local/mlx/  .local/mlx/
   ollama/       whisper/        vlm/         audio/
```

### Why this hybrid architecture

| Decision | Rationale |
|----------|-----------|
| Ollama for LLMs | Best model management UX (`ollama pull`), 0.19+ uses MLX backend = near-native speed |
| lightning-whisper-mlx for STT | 10x faster than whisper.cpp on Mac, Ollama doesn't support Whisper |
| mlx-vlm for OCR | Native MLX vision models, handles whiteboard photos + document scans + tables |
| mlx-audio for TTS (future) | Kokoro TTS with sub-200ms latency, same MLX ecosystem |
| All Apple Silicon optimized | Zero-copy unified memory, Metal GPU acceleration across all backends |

---

## Phase 0: Foundation — Inference Router + Backends

**Goal**: Establish the inference abstraction that routes each task to the optimal local backend.
**Estimated effort**: 4-5 days
**Risk**: Low — additive, no existing code changes

### 0.1 Inference Router (the core abstraction)

**New file**: `services/worker/src/atlas_worker/inference/__init__.py`
**New file**: `services/worker/src/atlas_worker/inference/router.py`
**New file**: `services/worker/src/atlas_worker/inference/models.py`
**New file**: `services/worker/src/atlas_worker/inference/health.py`

```python
# router.py — Single entry point for all inference
class InferenceRouter:
    """Routes inference requests to the optimal local backend.
    
    - LLM generation/chat → Ollama 0.19+ (MLX backend)
    - Embeddings           → Ollama
    - Speech-to-text       → lightning-whisper-mlx
    - Vision/OCR           → mlx-vlm
    - Text-to-speech       → mlx-audio + Kokoro (future)
    
    All models stored in .local/ — nothing leaves the project directory.
    Models load sequentially: load → run → unload → load next.
    """

    def __init__(self, config: WorkerConfig):
        self.ollama = OllamaClient(config.ollama_base_url, config.ollama_timeout_s)
        self.whisper = WhisperMLXBackend(config.mlx_dir / "whisper")
        self.vlm = VisionMLXBackend(config.mlx_dir / "vlm")
        # self.tts = AudioMLXBackend(config.mlx_dir / "audio")  # future

    # LLM operations (via Ollama)
    async def generate(self, prompt: str, model: str | None = None, **kwargs) -> GenerateResult
    async def chat(self, messages: list[Message], model: str | None = None) -> ChatResult
    async def embed(self, text: str, model: str | None = None) -> list[float]

    # STT operations (via lightning-whisper-mlx)
    async def transcribe(self, audio_path: Path, language: str | None = None) -> TranscribeResult

    # Vision operations (via mlx-vlm)
    async def ocr(self, image_path: Path, prompt: str = "Extract all text") -> VisionResult

    # Model management
    async def list_models(self) -> dict[str, list[ModelInfo]]  # grouped by backend
    async def health(self) -> InferenceHealth
    async def unload_all(self) -> None


# models.py — Shared data contracts
@dataclass(frozen=True)
class GenerateResult:
    text: str
    model: str
    backend: str  # "ollama", "mlx-vlm", etc.
    tokens_used: int
    duration_ms: int

@dataclass(frozen=True)
class TranscribeResult:
    text: str
    language: str
    duration_seconds: float
    segments: list[TranscriptSegment]
    confidence: float
    model: str
    backend: str  # "lightning-whisper-mlx"

@dataclass(frozen=True)
class VisionResult:
    text: str
    model: str
    backend: str  # "mlx-vlm"
    has_tables: bool
    confidence: float

@dataclass(frozen=True)
class InferenceHealth:
    ollama: OllamaHealth
    whisper: BackendHealth
    vlm: BackendHealth
    overall_status: str  # "healthy", "degraded", "unavailable"
    apple_silicon: bool
    unified_memory_gb: float
```

### 0.1b Backend implementations

**New file**: `services/worker/src/atlas_worker/inference/backends/ollama.py`

```python
class OllamaClient:
    """Async HTTP client for Ollama API at localhost:11434.
    Ollama 0.19+ uses MLX backend on Mac = near-native speed."""

    async def generate(self, model: str, prompt: str, **kwargs) -> GenerateResult
    async def chat(self, model: str, messages: list[Message]) -> ChatResult
    async def embed(self, model: str, text: str) -> list[float]
    async def list_models(self) -> list[ModelInfo]
    async def pull_model(self, model: str) -> AsyncIterator[PullProgress]
    async def health(self) -> OllamaHealth
```

**New file**: `services/worker/src/atlas_worker/inference/backends/whisper_mlx.py`

```python
class WhisperMLXBackend:
    """lightning-whisper-mlx backend for speech-to-text.
    10x faster than whisper.cpp on Apple Silicon.
    Models cached in .local/mlx/whisper/."""

    def __init__(self, model_dir: Path, model_size: str = "large-v3"):
        self.model_dir = model_dir
        self.model_size = model_size

    async def transcribe(self, audio_path: Path, language: str | None = None) -> TranscribeResult
    def is_available(self) -> bool
```

**New file**: `services/worker/src/atlas_worker/inference/backends/vision_mlx.py`

```python
class VisionMLXBackend:
    """mlx-vlm backend for OCR and image understanding.
    Handles: documents, whiteboards, screenshots, tables, handwriting.
    Models cached in .local/mlx/vlm/."""

    def __init__(self, model_dir: Path, model: str = "gemma-4-12b-vision"):
        self.model_dir = model_dir
        self.model = model

    async def process(self, image_path: Path, prompt: str) -> VisionResult
    def is_available(self) -> bool
```

### 0.2 Configuration

**Modified file**: `services/worker/src/atlas_worker/config.py`
**Modified file**: `services/api/src/atlas_api/config.py`

```python
class WorkerConfig:
    # ... existing fields ...

    # Project root
    atlas_root: Path = Path(".")
    mlx_dir: Path = atlas_root / ".local" / "mlx"

    # Ollama (LLMs + embeddings)
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout_s: int = 120
    ollama_default_model: str = "gemma4:27b"
    ollama_embedding_model: str = "nomic-embed-text"

    # Whisper (STT via lightning-whisper-mlx)
    whisper_model_size: str = "large-v3"

    # Vision (OCR via mlx-vlm)
    vlm_model: str = "gemma-4-12b-vision"
    enable_vision_extraction: bool = True

    # Model profile (overrides individual settings)
    model_profile: str = "standard"  # light, standard, reasoning, polyglot, maximum

    # Feature flags
    enable_llm_synthesis: bool = True
    enable_audio_ingest: bool = True
    enable_tts: bool = False  # future
```

### 0.3 Health check endpoint

**Modified file**: `services/api/src/atlas_api/routes/health.py`

New endpoint: `GET /api/v1/inference/health`
```json
{
  "ollama_running": true,
  "ollama_version": "0.6.2",
  "models_available": ["gemma3:12b", "nomic-embed-text"],
  "models_required": ["gemma3:12b"],
  "models_missing": [],
  "gpu_available": true,
  "memory_free_gb": 8.2,
  "status": "healthy"
}
```

### 0.4 Docker Compose update

**Modified file**: `docker-compose.yml`

All volumes bind to `.local/` — no Docker named volumes, no data outside the project.

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16     # PostgreSQL 16 + pgvector extension
    ports:
      - "5432:5432"
    volumes:
      - ./.local/data/postgres:/var/lib/postgresql/data  # project-local
    environment:
      POSTGRES_DB: atlas
      POSTGRES_USER: atlas
      POSTGRES_PASSWORD: atlas_dev
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U atlas"]
      interval: 5s
      retries: 5

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - ./.local/data/redis:/data  # project-local
    command: redis-server --appendonly yes

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ./.local/ollama:/root/.ollama  # project-local, NOT ~/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    # Mac users: run Ollama natively with OLLAMA_MODELS=.local/ollama
    # Linux users: use this container
    profiles:
      - linux  # only starts with --profile linux

  adminer:
    image: adminer
    ports:
      - "8080:8080"
    profiles:
      - debug
```

**Note for Mac users** (primary target): Ollama runs natively, not in Docker. Set:
```bash
export OLLAMA_MODELS=$(pwd)/.local/ollama
ollama serve
```
This makes Ollama store models inside the project instead of `~/.ollama/`.

### 0.5 Tests

**New file**: `services/worker/tests/test_inference_client.py`
- Mock Ollama HTTP responses
- Test generate, embed, health
- Test timeout handling
- Test model-not-found error

### 0.6 .env.example update

```env
# Project root (all .local/ paths derive from this)
ATLAS_ROOT=.

# Local storage (all inside project directory)
OLLAMA_MODELS=${ATLAS_ROOT}/.local/ollama
ATLAS_MLX_DIR=${ATLAS_ROOT}/.local/mlx
HF_HOME=${ATLAS_ROOT}/.local/mlx
ATLAS_UPLOAD_DIR=${ATLAS_ROOT}/.local/uploads
ATLAS_EMBEDDINGS_DIR=${ATLAS_ROOT}/.local/embeddings
ATLAS_TMP_DIR=${ATLAS_ROOT}/.local/tmp

# Inference — Ollama (LLMs + embeddings)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=gemma4:27b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Inference — MLX (STT + Vision + TTS)
WHISPER_MODEL_SIZE=large-v3
VLM_MODEL=gemma-4-12b-vision
ENABLE_TTS=false

# Model profile (overrides individual model settings)
# Options: light, standard, reasoning, polyglot, maximum
MODEL_PROFILE=standard

# Feature flags
ENABLE_LLM_SYNTHESIS=true
ENABLE_AUDIO_INGEST=true
ENABLE_VISION_EXTRACTION=true

# Database (local Docker, data in .local/)
DATABASE_URL=postgresql+asyncpg://atlas:atlas_dev@localhost:5432/atlas
REDIS_URL=redis://localhost:6379/0

# Adapters (all local, backed by Ollama)
ENABLE_DEERFLOW=true
ENABLE_HERMES=true
ENABLE_MIROFISH=false
DEERFLOW_MODEL=gemma4:27b
HERMES_MODEL=gemma4:12b
MIROFISH_MODEL=qwen3.5-27b-claude-distilled
```

### Acceptance criteria — Phase 0
- [ ] `OllamaClient` can connect to Ollama, generate text, list models
- [ ] Health endpoint returns model availability and GPU status
- [ ] Client handles Ollama-down gracefully (returns OllamaHealth.running=false)
- [ ] Config reads from env vars with sensible defaults
- [ ] 5+ unit tests passing with mocked HTTP
- [ ] No existing tests broken

---

## Phase 0.5: Offline Setup Script

**Goal**: One command that downloads everything needed, all into `.local/`. After this, the project works without internet forever.
**Estimated effort**: 2 days
**Depends on**: Phase 0
**Risk**: Low — scripting only, no architecture changes

### 0.5.1 Setup script

**New file**: `scripts/setup.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

ATLAS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCAL_DIR="$ATLAS_ROOT/.local"

echo "=== Atlas Edge Setup ==="
echo "Project root: $ATLAS_ROOT"
echo "Local storage: $LOCAL_DIR"
echo ""

# 1. Create directory structure
echo "[1/8] Creating local directories..."
mkdir -p "$LOCAL_DIR"/{ollama,mlx/whisper,mlx/vlm,mlx/audio,data/postgres,data/redis,uploads,embeddings,tmp}

# 2. Check Ollama installed
echo "[2/7] Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "ERROR: Ollama not found. Install from https://ollama.com"
    echo "  Mac:   brew install ollama"
    echo "  Linux: curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

# 3. Pull Ollama models (LLMs + embeddings) into project-local storage
echo "[3/8] Pulling Ollama models into .local/ollama/ ..."
export OLLAMA_MODELS="$LOCAL_DIR/ollama"

# Start Ollama if not running
if ! curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  Starting Ollama..."
    ollama serve &
    OLLAMA_PID=$!
    sleep 3
fi

echo "  Pulling gemma4:27b (~18 GB) — primary synthesis model..."
ollama pull gemma4:27b

echo "  Pulling gemma4:12b (~8 GB) — lightweight synthesis..."
ollama pull gemma4:12b

echo "  Pulling nomic-embed-text (~274 MB) — search embeddings..."
ollama pull nomic-embed-text

# 4. Download MLX models (Whisper + Vision) into project-local cache
echo "[4/8] Downloading MLX models into .local/mlx/ ..."
export HF_HOME="$LOCAL_DIR/mlx"

echo "  Downloading lightning-whisper-mlx large-v3 (~3 GB)..."
python3 -c "
import os
os.environ['HF_HOME'] = '$LOCAL_DIR/mlx'
from lightning_whisper_mlx import LightningWhisperMLX
whisper = LightningWhisperMLX(model='large-v3', batch_size=12, quant=None)
print('  Whisper MLX model cached.')
"

echo "  Downloading mlx-vlm Gemma 4 vision (~8 GB)..."
python3 -c "
import os
os.environ['HF_HOME'] = '$LOCAL_DIR/mlx'
from mlx_vlm import load
model, processor = load('mlx-community/gemma-4-12b-vision-4bit')
print('  Vision MLX model cached.')
"

# 5. Install JavaScript dependencies
echo "[5/8] Installing JS dependencies..."
cd "$ATLAS_ROOT" && pnpm install --frozen-lockfile

# 6. Install Python dependencies
echo "[6/8] Installing Python dependencies..."
cd "$ATLAS_ROOT/services/api" && uv sync
cd "$ATLAS_ROOT/services/worker" && uv sync

# 7. Pull Docker images (if Docker available)
echo "[7/8] Pulling Docker images..."
if command -v docker &> /dev/null; then
    docker pull pgvector/pgvector:pg16
    docker pull redis:7
else
    echo "  Docker not found, skipping. Install from https://docker.com"
fi

# 8. Verify everything
echo "[8/8] Verifying setup..."
bash "$ATLAS_ROOT/scripts/verify-offline.sh"

# Summary
echo ""
echo "=== Setup Complete ==="
echo ""
du -sh "$LOCAL_DIR"/* 2>/dev/null | sort -rh
echo ""
echo "Total local storage:"
du -sh "$LOCAL_DIR"
echo ""
echo "Backends installed:"
echo "  Ollama 0.19+ (MLX) — LLMs + embeddings"
echo "  lightning-whisper-mlx — speech-to-text (10x faster than whisper.cpp)"
echo "  mlx-vlm — OCR + vision understanding"
echo ""
echo "To start Atlas:"
echo "  1. export OLLAMA_MODELS=$LOCAL_DIR/ollama"
echo "  2. export HF_HOME=$LOCAL_DIR/mlx"
echo "  3. ollama serve"
echo "  4. docker compose up -d postgres redis"
echo "  5. pnpm dev"
echo ""
echo "No internet required from this point forward."
```

### 0.5.2 Verification script

**New file**: `scripts/verify-offline.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

ATLAS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCAL_DIR="$ATLAS_ROOT/.local"
ERRORS=0

echo "=== Atlas Offline Verification ==="
echo ""

# Check directories exist
for dir in ollama mlx/whisper mlx/vlm data/postgres data/redis uploads embeddings tmp; do
    if [ -d "$LOCAL_DIR/$dir" ]; then
        echo "[OK] .local/$dir exists ($(du -sh "$LOCAL_DIR/$dir" 2>/dev/null | cut -f1))"
    else
        echo "[FAIL] .local/$dir missing"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check Ollama models present in local dir
export OLLAMA_MODELS="$LOCAL_DIR/ollama"
echo ""
echo "Ollama models (in .local/ollama/):"
if ollama list 2>/dev/null | grep -q "gemma3"; then
    echo "[OK] gemma3:12b found"
else
    echo "[FAIL] gemma3:12b missing"
    ERRORS=$((ERRORS + 1))
fi

if ollama list 2>/dev/null | grep -q "nomic-embed"; then
    echo "[OK] nomic-embed-text found"
else
    echo "[FAIL] nomic-embed-text missing"
    ERRORS=$((ERRORS + 1))
fi

# Check MLX Whisper model
echo ""
echo "MLX models (in .local/mlx/):"
if [ -d "$LOCAL_DIR/mlx/whisper" ] && [ "$(ls -A "$LOCAL_DIR/mlx/whisper" 2>/dev/null)" ]; then
    echo "[OK] Whisper MLX model cached in .local/mlx/whisper/ ($(du -sh "$LOCAL_DIR/mlx/whisper" 2>/dev/null | cut -f1))"
else
    echo "[FAIL] Whisper MLX model not found in .local/mlx/whisper/"
    ERRORS=$((ERRORS + 1))
fi

if [ -d "$LOCAL_DIR/mlx/vlm" ] && [ "$(ls -A "$LOCAL_DIR/mlx/vlm" 2>/dev/null)" ]; then
    echo "[OK] Vision MLX model cached in .local/mlx/vlm/ ($(du -sh "$LOCAL_DIR/mlx/vlm" 2>/dev/null | cut -f1))"
else
    echo "[FAIL] Vision MLX model not found in .local/mlx/vlm/"
    ERRORS=$((ERRORS + 1))
fi

# Check JS deps
echo ""
if [ -d "$ATLAS_ROOT/node_modules" ]; then
    echo "[OK] node_modules present"
else
    echo "[FAIL] node_modules missing — run pnpm install"
    ERRORS=$((ERRORS + 1))
fi

# Check Python deps
for svc in api worker; do
    if [ -d "$ATLAS_ROOT/services/$svc/.venv" ]; then
        echo "[OK] services/$svc/.venv present"
    else
        echo "[FAIL] services/$svc/.venv missing — run uv sync"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check Docker images
echo ""
if command -v docker &> /dev/null; then
    for img in pgvector/pgvector:pg16 redis:7; do
        if docker image inspect "$img" &> /dev/null; then
            echo "[OK] Docker image $img cached"
        else
            echo "[FAIL] Docker image $img not cached"
            ERRORS=$((ERRORS + 1))
        fi
    done
else
    echo "[WARN] Docker not available — cannot verify images"
fi

# Summary
echo ""
echo "========================"
if [ $ERRORS -eq 0 ]; then
    echo "ALL CHECKS PASSED — Atlas can run fully offline."
else
    echo "$ERRORS CHECK(S) FAILED — run scripts/setup.sh to fix."
fi
echo ""
echo "Disk usage:"
du -sh "$LOCAL_DIR" 2>/dev/null
```

### 0.5.3 .gitignore update

**Modified file**: `.gitignore`

```gitignore
# Local runtime assets — models, data, uploads, cache
# Everything downloaded by scripts/setup.sh lives here
.local/
```

### 0.5.4 Launcher script (convenience)

**New file**: `scripts/start.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

ATLAS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export OLLAMA_MODELS="$ATLAS_ROOT/.local/ollama"
export HF_HOME="$ATLAS_ROOT/.local/mlx"
export ATLAS_MLX_DIR="$ATLAS_ROOT/.local/mlx"
export ATLAS_UPLOAD_DIR="$ATLAS_ROOT/.local/uploads"
export ATLAS_EMBEDDINGS_DIR="$ATLAS_ROOT/.local/embeddings"
export ATLAS_TMP_DIR="$ATLAS_ROOT/.local/tmp"

echo "Starting Atlas (edge mode — MLX + Ollama hybrid)..."
echo "Ollama models: $OLLAMA_MODELS"
echo "MLX models:    $ATLAS_MLX_DIR"

# Start Ollama if not running
if ! curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Starting Ollama..."
    ollama serve &
    sleep 2
fi

# Start infra
docker compose up -d postgres redis

# Wait for postgres
echo "Waiting for PostgreSQL..."
until docker compose exec -T postgres pg_isready -U atlas > /dev/null 2>&1; do
    sleep 1
done

# Start services
echo "Starting API + Worker + Web..."
pnpm dev
```

### Acceptance criteria — Phase 0.5
- [ ] `scripts/setup.sh` downloads everything into `.local/`
- [ ] `scripts/verify-offline.sh` passes with zero errors
- [ ] Disconnect WiFi → `scripts/start.sh` → full pipeline works
- [ ] `du -sh .local/` shows total disk usage (~12-15 GB with all models)
- [ ] `rm -rf .local/` cleans everything; re-run `setup.sh` to restore
- [ ] `.gitignore` excludes `.local/`
- [ ] No files written to `~/.ollama`, `~/.cache`, or any path outside project

---

## Phase 1: Audio Ingestion via Whisper

**Goal**: Users can upload audio files and get them transcribed locally.
**Estimated effort**: 4-5 days
**Depends on**: Phase 0
**Risk**: Medium — new file type, new extractor, new job type

### 1.1 Audio extractor

**New file**: `services/worker/src/atlas_worker/extractors/audio.py`

```python
@dataclass(frozen=True)
class AudioResult:
    text: str
    language: str
    duration_seconds: float
    segments: list[TranscriptSegment]  # timestamped chunks
    confidence: float

@dataclass(frozen=True)
class TranscriptSegment:
    start: float   # seconds
    end: float     # seconds
    text: str
    confidence: float

async def extract_audio(
    raw: bytes,
    filename: str,
    client: OllamaClient,
    model: str = "whisper-large-v3",
) -> AudioResult:
    """
    Strategy:
    1. Save bytes to temp file (Whisper needs file path)
    2. Call lightning-whisper-mlx for transcription
    3. Parse segments with timestamps
    4. Return structured transcript
    """
```

**Decision**: Use `lightning-whisper-mlx` — native MLX, 10x faster than whisper.cpp on Apple Silicon.

| Option | Speed (Mac M2) | Pros | Cons |
|--------|---------------|------|------|
| **A: lightning-whisper-mlx** | 50x realtime | Fastest on Mac, MLX-native, zero-copy memory | Mac-only |
| B: mlx-whisper | 2x faster than cpp | Good MLX integration | Slower than lightning |
| C: faster-whisper | 10x realtime | Cross-platform (CTranslate2) | Not MLX-optimized |
| D: whisper.cpp | 5x realtime | Portable C++ | Slowest on Mac |

**Recommendation**: Option A (`lightning-whisper-mlx`). If cross-platform support is needed later, add `faster-whisper` as fallback for Linux.

The transcription backend is already implemented in Phase 0 as `WhisperMLXBackend` inside the Inference Router. Phase 1 adds the audio extractor that uses it:

```python
# extractors/audio.py
async def extract_audio(
    raw: bytes,
    filename: str,
    router: InferenceRouter,
) -> AudioResult:
    # 1. Save bytes to temp file in .local/tmp/
    # 2. Call router.transcribe(audio_path)
    # 3. Parse segments with timestamps
    # 4. Return structured transcript
```

### 1.2 Image/OCR extractor

**New file**: `services/worker/src/atlas_worker/extractors/ocr.py`

```python
@dataclass(frozen=True)
class OcrResult:
    text: str
    layout_blocks: list[LayoutBlock]  # paragraphs, tables, headings with positions
    language: str
    confidence: float
    has_tables: bool
    has_handwriting: bool

@dataclass(frozen=True)
class LayoutBlock:
    text: str
    block_type: str  # paragraph, table, heading, list, handwriting
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float

async def extract_ocr(
    raw: bytes,
    filename: str,
    model_dir: Path,  # .local/ocr/
) -> OcrResult:
    """
    Uses mlx-vlm (Gemma 4 vision) for document understanding.
    Handles: printed text, tables, forms, handwritten notes, whiteboard photos.
    Falls back to Tesseract if mlx-vlm model not available.
    
    Model cached in .local/mlx/vlm/ — downloaded once by setup.sh.
    """
```

**New file**: `services/worker/src/atlas_worker/inference/ocr_engine.py`

```python
class OcrEngine:
    """Abstraction over OCR backends.
    
    Primary: mlx-vlm with Gemma 4 vision (cached in .local/mlx/vlm/)
    Fallback: Tesseract (system-installed, no ML)
    """

    def __init__(self, model_dir: Path):
        self.model_dir = model_dir  # .local/ocr/

    async def extract(self, image_path: Path) -> OcrResult
    def is_available(self) -> bool
```

### 1.3 Source kind extension

**Modified file**: `packages/shared/src/types/enums.ts`
```typescript
export const SourceKind = {
  Article: "article",
  Pdf: "pdf",
  Repository: "repository",
  ImageSet: "image_set",
  Dataset: "dataset",
  Transcript: "transcript",
  WebClip: "web_clip",
  Audio: "audio",        // NEW
  Video: "video",        // NEW (future: extract audio track → Whisper)
  Image: "image",        // NEW (whiteboard photos, scans, screenshots)
} as const;
```

**Modified file**: `services/api/src/atlas_api/models/enums.py`
```python
class SourceKind(StrEnum):
    # ... existing ...
    audio = "audio"
    video = "video"
    image = "image"
```

### 1.3 Ingest job update

**Modified file**: `services/worker/src/atlas_worker/jobs/ingest.py`

Add audio + image dispatch to the extractor router:
```python
async def ingest_source(ctx, source_id: str, workspace_id: str):
    # ... existing load + read ...

    match source.kind:
        case SourceKind.pdf:
            result = extract_pdf(raw)
        case SourceKind.article | SourceKind.web_clip:
            result = extract_html(raw)
        case SourceKind.audio:                          # NEW
            result = await extract_audio(raw, source.filename, ctx["transcriber"])
        case SourceKind.image:                          # NEW
            result = await extract_ocr(raw, source.filename, ctx["ocr_engine"])
        case _:
            result = extract_text(raw)

    # ... existing chunk + hash + persist ...
```

### 1.4 Upload endpoint update

**Modified file**: `services/api/src/atlas_api/routes/sources.py`

Accept new MIME types:
- Audio: `audio/mpeg`, `audio/wav`, `audio/m4a`, `audio/ogg`, `audio/webm`
- Images: `image/jpeg`, `image/png`, `image/webp`, `image/tiff`

Auto-detect `SourceKind.audio` or `SourceKind.image` from MIME type.

File size limits (configurable):
- Audio: 500MB (a 2-hour podcast at 128kbps is ~115MB)
- Images: 50MB per image
- PDF: 100MB

### 1.5 Frontend: audio upload

**Modified file**: `apps/web/components/sources/upload-form.tsx`

- Accept audio files in file picker (`.mp3, .wav, .m4a, .ogg, .webm`)
- Show audio player preview after selection
- Display transcription progress (job status polling)
- Show transcript in source detail view with timestamps

### 1.6 Vault: transcript source notes

**Modified file**: `services/worker/src/atlas_worker/compiler/source_notes.py`

Audio sources generate notes with:
```yaml
---
title: "Interview with Dr. Smith"
type: source
source_kind: audio
provenance:
  duration_seconds: 3847
  transcription_model: "whisper-large-v3"
  transcription_confidence: 0.94
  language: "en"
tags:
  - source/audio
  - status/transcribed
---

## Transcript

[00:00:00] Welcome to today's discussion about...
[00:01:23] The key finding was that...
```

### 1.7 Dependencies

**Modified file**: `services/worker/pyproject.toml`
```toml
[project.dependencies]
# ... existing ...
lightning-whisper-mlx = ">=0.4.0"   # STT — 10x faster than whisper.cpp on Mac
mlx-vlm = ">=0.5.0"                 # Vision/OCR — native MLX
mlx = ">=0.22.0"                    # Apple MLX framework
httpx = ">=0.27.0"                  # Async HTTP client for Ollama API
pgvector = ">=0.3.0"               # pgvector SQLAlchemy bindings
python-docx = ">=1.1.0"            # Word .docx extraction
openpyxl = ">=3.1.0"               # Excel .xlsx extraction
python-pptx = ">=0.6.0"            # PowerPoint .pptx extraction
# mlx-audio = ">=0.2.0"            # TTS — Kokoro (future, Phase 6+)
```

### 1.8 Tests

**New file**: `services/worker/tests/test_audio_extractor.py`
- Test with short WAV fixture (5 seconds of speech)
- Test language detection
- Test segment timestamp parsing
- Test fallback when Whisper model not available

**New file**: `services/worker/tests/fixtures/sample.wav`
- 5-second speech sample for testing

### Acceptance criteria — Phase 1
- [ ] Upload MP3/WAV/M4A from frontend
- [ ] Audio transcribed locally via lightning-whisper-mlx
- [ ] Transcript stored as source with timestamps in vault
- [ ] Transcription confidence tracked in provenance
- [ ] Source detail page shows audio player + transcript
- [ ] 5+ tests covering audio extraction
- [ ] Graceful error when Whisper model missing

---

## Phase 2: LLM-Enhanced Compilation

**Goal**: Wire Ollama into the compiler for summaries, entity extraction, and concept synthesis.
**Estimated effort**: 5-7 days
**Depends on**: Phase 0
**Risk**: Medium — replaces heuristic entity extraction with LLM; needs eval framework

### 2.1 Prompt library

**New file**: `services/worker/src/atlas_worker/inference/prompts.py`

```python
SYSTEM_PROMPT = """You are a knowledge compiler. You extract structured information
from source documents. You NEVER invent facts. You ALWAYS cite the source text.
Output valid JSON only."""

ENTITY_EXTRACTION_PROMPT = """Extract all named entities from the following text.
For each entity, provide:
- name: The canonical name
- kind: One of [person, company, project, paper, dataset, product]
- aliases: Alternative names or abbreviations
- description: One sentence describing this entity based on the text
- evidence: The exact quote from the text that mentions this entity

Text:
{text}

Respond as JSON array:"""

SUMMARY_PROMPT = """Summarize the following source document in 3-5 paragraphs.
Focus on key findings, arguments, and conclusions.
Cite specific claims with [source] markers.

Text:
{text}

Summary:"""

CONCEPT_SYNTHESIS_PROMPT = """Given these excerpts from {n_sources} different sources
about "{topic}", synthesize a concept article that:
1. Defines the concept
2. Lists key perspectives from each source
3. Notes disagreements or tensions
4. Provides a balanced synthesis

Sources:
{sources_text}

Concept article:"""

REFERENCE_EXTRACTION_PROMPT = """Extract all references, citations, and bibliographic
entries from the following text. For each reference, provide:
- title: The referenced work's title
- authors: List of authors
- year: Publication year if available
- type: One of [paper, book, article, report, website, other]
- context: How this reference is used in the source text

Text:
{text}

Respond as JSON array:"""
```

### 2.2 LLM-powered entity extraction

**Modified file**: `services/worker/src/atlas_worker/compiler/entity_extraction.py`

```python
async def extract_entities_llm(
    text: str,
    client: OllamaClient,
    model: str,
) -> list[ExtractedEntity]:
    """
    Replace heuristic capitalized-word extraction with LLM.
    Falls back to heuristic if Ollama unavailable.
    """
    result = await client.generate(
        model=model,
        prompt=ENTITY_EXTRACTION_PROMPT.format(text=text),
        system=SYSTEM_PROMPT,
        temperature=0.0,  # deterministic
    )
    entities = parse_entity_json(result.text)
    return entities


async def extract_entities(
    text: str,
    client: OllamaClient | None = None,
    model: str | None = None,
) -> list[ExtractedEntity]:
    """Dispatch: LLM if available, heuristic fallback"""
    if client and model:
        try:
            return await extract_entities_llm(text, client, model)
        except OllamaError:
            logger.warning("LLM entity extraction failed, falling back to heuristic")
    return extract_entities_heuristic(text)  # existing code, renamed
```

### 2.3 Summary generator

**New file**: `services/worker/src/atlas_worker/compiler/summarizer.py`

```python
@dataclass(frozen=True)
class Summary:
    text: str
    word_count: int
    model: str
    generation_time_ms: int
    confidence_notes: str

async def summarize_source(
    text: str,
    client: OllamaClient,
    model: str,
    max_length: int = 1000,
) -> Summary:
    """Generate a structured summary of a source document."""
```

### 2.3b Meeting minutes generator

**New file**: `services/worker/src/atlas_worker/compiler/meeting_minutes.py`

```python
@dataclass(frozen=True)
class MeetingMinutes:
    title: str
    date: str
    attendees: list[str]
    agenda_items: list[str]
    discussion_points: list[DiscussionPoint]
    decisions: list[Decision]
    action_items: list[ActionItem]
    next_steps: str
    model: str

@dataclass(frozen=True)
class Decision:
    description: str
    made_by: str | None
    context: str
    timestamp: str | None  # from transcript

@dataclass(frozen=True)
class ActionItem:
    description: str
    owner: str | None
    deadline: str | None
    priority: str  # high, medium, low
    status: str  # open, in_progress, done
    source_quote: str  # exact transcript quote

async def generate_meeting_minutes(
    transcript: str,
    existing_entities: list[str],  # known people/projects for context
    client: OllamaClient,
    model: str,
) -> MeetingMinutes:
    """
    Generate structured meeting minutes from a transcript.
    Cross-references with known entities to resolve names.
    Extracts decisions and action items with owners.
    """
```

### 2.3c Decision and action item tracker

**New file**: `services/worker/src/atlas_worker/compiler/tracker.py`

```python
async def rebuild_decision_log(
    vault_path: Path,
    client: OllamaClient,
    model: str,
) -> DecisionLog:
    """
    Scan all meeting minutes in vault, extract decisions,
    deduplicate, and generate a chronological decision log.
    Output: vault/outputs/decision-log.md
    """

async def rebuild_action_items(
    vault_path: Path,
    client: OllamaClient,
    model: str,
) -> ActionItemTracker:
    """
    Scan all meeting minutes, extract action items,
    track status across meetings (mentioned again = still open),
    generate tracker.
    Output: vault/outputs/action-items.md
    """
```

### 2.4 Reference extractor

**New file**: `services/worker/src/atlas_worker/compiler/reference_extractor.py`

```python
@dataclass(frozen=True)
class ExtractedReference:
    title: str
    authors: list[str]
    year: int | None
    ref_type: str  # paper, book, article, report, website, other
    context: str   # how it's used in the source

async def extract_references(
    text: str,
    client: OllamaClient,
    model: str,
) -> list[ExtractedReference]:
    """Extract bibliographic references from source text using LLM."""
```

### 2.5 Concept synthesizer

**New file**: `services/worker/src/atlas_worker/compiler/concept_synthesizer.py`

```python
@dataclass(frozen=True)
class SynthesizedConcept:
    title: str
    slug: str
    body: str  # Markdown
    source_ids: list[str]
    entity_refs: list[str]
    model: str
    confidence: float

async def synthesize_concepts(
    sources: list[SourceWithChunks],
    entities: list[ExtractedEntity],
    client: OllamaClient,
    model: str,
) -> list[SynthesizedConcept]:
    """
    Cross-source concept synthesis:
    1. Cluster entities and topics across sources
    2. For each cluster, gather relevant chunks
    3. Ask LLM to synthesize a concept article
    4. Generate wikilinks to source notes and entity notes
    """
```

### 2.6 Updated compile job

**Modified file**: `services/worker/src/atlas_worker/jobs/compile.py`

```python
async def compile_vault(ctx, workspace_id: str):
    client = ctx.get("ollama")  # None if Ollama unavailable
    model = ctx.get("default_model")

    sources = await _query_ingested_sources(workspace_id)

    # Step 1: Source notes (existing, deterministic)
    for source in sources:
        generate_source_note(source, vault_path)

    # Step 2: Summaries (LLM)
    if client:
        for source in sources:
            summary = await summarize_source(source.text, client, model)
            append_summary_to_note(source.slug, summary, vault_path)

    # Step 3: Meeting minutes (LLM, audio sources only)
    if client:
        for source in sources:
            if source.kind == SourceKind.audio:
                minutes = await generate_meeting_minutes(
                    source.text, known_entities, client, model)
                write_meeting_minutes_note(source.slug, minutes, vault_path)

    # Step 4: Entities (enhanced with LLM)
    for source in sources:
        entities = await extract_entities(source.text, client, model)
        generate_entity_notes(entities, vault_path)

    # Step 5: References (LLM)
    if client:
        for source in sources:
            refs = await extract_references(source.text, client, model)
            generate_reference_section(source.slug, refs, vault_path)

    # Step 6: Concepts (LLM, cross-source)
    if client:
        concepts = await synthesize_concepts(sources, all_entities, client, model)
        for concept in concepts:
            write_concept_note(concept, vault_path)

    # Step 7: Cross-source trackers (LLM)
    if client:
        await rebuild_decision_log(vault_path, client, model)
        await rebuild_action_items(vault_path, client, model)
        await rebuild_timeline(vault_path, client, model)
        await detect_contradictions(vault_path, client, model)

    # Step 8: Indexes + Backlinks (deterministic)
    rebuild_indexes(vault_path)
    verify_backlinks(vault_path)
    generate_coverage_report(vault_path)
```

### 2.7 Vault note enhancements

Source notes now include:
```markdown
---
title: "Research Paper on AI Safety"
type: source
# ... existing frontmatter ...
summary_model: "gemma3:12b"
summary_generated_at: "2026-04-06T14:30:00Z"
references_extracted: 12
---

## Summary

[LLM-generated summary with [source] citations]

## Key Entities

- [[entities/anthropic]] — AI safety company, referenced 14 times
- [[entities/claude]] — Large language model by Anthropic

## References

1. Amodei et al. (2023) "Constitutional AI" — cited as foundational approach
2. ...

## Source Text

[Original extracted text]
```

### 2.8 Evals

**Modified file**: `services/api/src/atlas_api/evals/compiler_eval.py`

New eval cases:
- Entity extraction precision/recall vs golden set
- Summary faithfulness (no hallucinated claims)
- Reference extraction completeness
- Concept article source coverage

### Acceptance criteria — Phase 2
- [ ] Entity extraction uses LLM when Ollama available, heuristic otherwise
- [ ] Each source note includes an LLM-generated summary
- [ ] References extracted and linked in source notes
- [ ] Cross-source concept synthesis produces concept notes in `vault/concepts/`
- [ ] All LLM-generated content records model, timestamp, confidence
- [ ] Eval framework measures extraction quality
- [ ] Compile job works without Ollama (graceful degradation)

---

## Phase 3: Project-Centric UX

**Goal**: Redesign the frontend around a project lifecycle: create, populate over time, compile, search, generate outputs. The consultant lives inside a project for weeks/months, continuously adding sources.
**Estimated effort**: 6-8 days
**Depends on**: Phase 1 + Phase 2
**Risk**: Low — mostly frontend, minimal backend changes

### 3.1 Project = Workspace (rename in UI)

The existing `Workspace` model maps 1:1 to "Project". No schema change needed — just UI terminology.

### 3.1b Project lifecycle

A project is NOT a one-shot upload. It's a living workspace the consultant uses throughout an engagement:

```
Week 1:  Create project → upload initial docs (proposals, contracts)
         First compile → vault has initial entities + summaries

Week 2:  Record meeting #1 → upload audio + whiteboard photos
         Upload competitor analysis PDF
         Re-compile → vault grows with meeting minutes, new entities

Week 3:  Record meeting #2 → upload audio
         Add handwritten notes (photo) + Excel data
         Generate weekly digest
         DeerFlow: "Research competitor pricing from vault"

Week 4:  Record meeting #3 → upload audio
         Generate status report for client
         MiroFish: "What if budget cuts by 15%?"
         Hermes: surfaces context from prior sessions

Week 8:  Generate final project brief
         Export vault as ZIP for Obsidian archive
         Project marked as "completed"
```

### 3.1c Supported file formats

| Format | Extension | Extractor | Notes |
|--------|-----------|-----------|-------|
| Audio | `.mp3, .wav, .m4a, .ogg, .webm` | lightning-whisper-mlx | Meetings, interviews, memos |
| PDF | `.pdf` | pdfplumber + optional Gemma vision | Reports, contracts, papers |
| Images | `.jpg, .jpeg, .png, .webp, .tiff` | mlx-vlm (Gemma 4 vision) | Whiteboards, scans, screenshots |
| Word | `.docx` | python-docx → text extraction | Proposals, meeting notes |
| Excel | `.xlsx, .csv` | openpyxl / pandas → text + tables | Budgets, timelines, data |
| PowerPoint | `.pptx` | python-pptx → text + slide structure | Presentations, pitch decks |
| Markdown | `.md` | direct passthrough | Personal notes, existing wiki |
| Plain text | `.txt` | direct passthrough | Quick notes, logs |
| HTML | `.html, .htm` | BeautifulSoup4 | Saved web pages |

**New dependencies** for Office formats:
```toml
python-docx = ">=1.1.0"     # Word .docx extraction
openpyxl = ">=3.1.0"        # Excel .xlsx extraction
python-pptx = ">=0.6.0"     # PowerPoint .pptx extraction
```

**New extractors** needed:
```
services/worker/src/atlas_worker/extractors/docx.py
services/worker/src/atlas_worker/extractors/xlsx.py
services/worker/src/atlas_worker/extractors/pptx.py
```

### 3.2 New routes

| Route | Purpose |
|-------|---------|
| `/` | Landing → redirect to `/projects` |
| `/projects` | Project list (grid view, cards with stats) |
| `/projects/new` | Create project wizard |
| `/projects/[id]` | Project dashboard (sources, vault, search, outputs, tools in tabs) |
| `/projects/[id]/sources` | Source management (add any time, not just at creation) |
| `/projects/[id]/sources/upload` | Multimodal upload (audio + PDF + Office + images + text) |
| `/projects/[id]/vault` | Vault browser |
| `/projects/[id]/vault/[slug]` | Note reader/editor |
| `/projects/[id]/search` | Search within project |
| `/projects/[id]/outputs` | Generated reports, briefs, digests |
| `/projects/[id]/tools` | DeerFlow research, Hermes context, MiroFish simulation |
| `/projects/[id]/settings` | Project config, model selection, export |

### 3.2b Adapter tools page

**New page**: `apps/web/app/projects/[id]/tools/page.tsx`

```
┌─────────────────────────────────────────────────────────┐
│  Project Tools                                           │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  DeerFlow — Research                                 │ │
│  │  Ask a research question grounded in your vault.     │ │
│  │                                                       │ │
│  │  [What do we know about competitor pricing?    ] [Go] │ │
│  │                                                       │ │
│  │  Recent queries:                                      │ │
│  │  • "Summarize all budget discussions" — 3 min ago    │ │
│  │  • "Who owns the API migration?" — yesterday         │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  MiroFish — Simulation                               │ │
│  │  Run what-if scenarios against project knowledge.     │ │
│  │                                                       │ │
│  │  [What if we delay launch by 4 weeks?         ] [Go] │ │
│  │  ⚠ Requires confirmation before running               │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Hermes — Session Memory                             │ │
│  │  Context from your previous work sessions.            │ │
│  │                                                       │ │
│  │  Last session (2h ago): You were reviewing the Q1    │ │
│  │  budget gap and had 3 open action items.              │ │
│  │  [Resume context] [Clear]                             │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Create project wizard

```
Step 1: Name + Description
  ├── Project name (required)
  ├── Client / engagement (optional)
  ├── Description (optional)
  ├── Language: [Spanish ▼] (default output language)
  └── Tags (optional)

Step 2: Add Initial Sources (drag & drop zone — optional, can add later)
  ├── Audio files (.mp3, .wav, .m4a)
  ├── PDF documents
  ├── Office files (.docx, .xlsx, .pptx)
  ├── Images (.jpg, .png — whiteboards, scans)
  ├── Markdown / text files
  └── Batch upload supported

Step 3: Configure (optional, advanced)
  ├── Model profile: [standard ▼] (light, standard, reasoning, polyglot)
  ├── Enable DeerFlow research: ☑
  ├── Enable Hermes session memory: ☑
  ├── Enable MiroFish simulation: ☐ (off by default)
  └── Vault export path (for Obsidian sync)

Step 4: Review + Start
  ├── Show source count by type
  ├── Estimated processing time
  └── "Create Project" button
      → Creates workspace
      → If sources added, triggers ingest + compile
      → If no sources, opens empty project dashboard
```

### 3.4 Project dashboard

```
┌──────────────────────────────────────────────────────────┐
│  Project: "Acme Corp — API Migration"         [Settings] │
│  Client: Acme Corp | Created: Apr 6 | 18 sources        │
├──────────┬────────┬────────┬─────────┬────────┬─────────┤
│ Sources  │ Vault  │ Search │ Outputs │ Tools  │ Activity│
├──────────┴────────┴────────┴─────────┴────────┴─────────┤
│                                                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ 5 PDFs   │ │ 4 Audio  │ │ 3 Office │ │ 6 Images │   │
│  │ Ready    │ │ 3 Done   │ │ Ready    │ │ Ready    │   │
│  │          │ │ 1 Running│ │          │ │          │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                           │
│  [+ Add Sources]  ← always available, not just at creation│
│                                                           │
│  Pipeline Status:                                         │
│  ████████████░░░░░░░░  62% — Compiling entities           │
│                                                           │
│  Quick Actions:                                           │
│  [Generate Status Report] [Weekly Digest] [Ask DeerFlow]  │
│                                                           │
│  Recent Activity:                                         │
│  • 14:30 — Transcribed "meeting-apr-10.m4a" (EN→ES)     │
│  • 14:28 — Extracted 23 entities from "paper.pdf"│
│  • 14:25 — Ingested 3 new sources                │
└───────────────────────────────────────────────────┘
```

### 3.5 Inference status bar

**New component**: `apps/web/components/inference-status.tsx`

Persistent status bar showing:
- Ollama connection status (green/red dot)
- Current model loaded
- GPU memory usage
- Active inference jobs

### 3.6 Frontend components

| Component | File | Purpose |
|-----------|------|---------|
| `ProjectCard` | `components/projects/project-card.tsx` | Project grid item with stats |
| `ProjectWizard` | `components/projects/project-wizard.tsx` | Multi-step creation flow |
| `MultiUploader` | `components/sources/multi-uploader.tsx` | Drag-drop for mixed file types |
| `AudioPlayer` | `components/sources/audio-player.tsx` | Inline audio playback with transcript |
| `PipelineProgress` | `components/jobs/pipeline-progress.tsx` | Multi-stage progress visualization |
| `InferenceStatus` | `components/inference-status.tsx` | Ollama health indicator |
| `ModelSelector` | `components/settings/model-selector.tsx` | Dropdown with available Ollama models |

### Acceptance criteria — Phase 3
- [ ] Create project from wizard with name + sources
- [ ] Drag-drop upload of mixed audio + PDF + text files
- [ ] Project dashboard shows pipeline progress in real time
- [ ] Vault browser scoped to project
- [ ] Inference status visible at all times
- [ ] Model selector works with available Ollama models
- [ ] Responsive layout for desktop + tablet

---

## Phase 3.5: On-Demand Output Generation

**Goal**: Users can request generated reports, briefs, and documents from their project vault.
**Estimated effort**: 4-5 days
**Depends on**: Phase 2 + Phase 3
**Risk**: Medium — LLM generation quality varies, needs good prompts

### 3.5.1 Output job type

**New file**: `services/worker/src/atlas_worker/jobs/generate_output.py`

```python
class OutputKind(StrEnum):
    status_report = "status_report"
    client_brief = "client_brief"
    weekly_digest = "weekly_digest"
    risk_register = "risk_register"
    raci_matrix = "raci_matrix"
    comparison_table = "comparison_table"
    followup_email = "followup_email"
    proposal_section = "proposal_section"
    slide_outline = "slide_outline"
    faq_document = "faq_document"
    custom = "custom"  # user provides their own prompt

async def generate_output(ctx, workspace_id: str, output_kind: str, params: dict):
    """
    1. Load relevant vault notes (search by relevance to params)
    2. Build context from source summaries, entities, decisions
    3. Load synthesis model
    4. Generate Markdown document
    5. Write to vault/outputs/{kind}-{date}.md
    6. Return path to generated file
    """
```

### 3.5.2 Output templates (prompts)

**New file**: `services/worker/src/atlas_worker/inference/output_prompts.py`

Each output type has a structured prompt template:

```python
OUTPUT_PROMPTS = {
    "status_report": """Generate a project status report based on the following
project knowledge. Include:
# Project Status Report — {date}
## Executive Summary (2-3 sentences)
## Progress Since Last Report
## Key Decisions Made
## Open Action Items (table: item | owner | deadline | status)
## Risks and Blockers (table: risk | likelihood | impact | mitigation)
## Next Steps
## Appendix: Sources Consulted

Project knowledge:
{context}
""",

    "client_brief": """Generate a polished 1-2 page client-facing brief.
Tone: professional, concise, no internal jargon.
Include: key findings, recommendations, next steps.
Do NOT include: internal discussions, pricing, team dynamics.

Project knowledge:
{context}
""",

    "weekly_digest": """Generate a weekly digest for the week of {week_start}.
Include only events, decisions, and action items from this time period.
Format as a scannable email-style summary.

This week's activity:
{context}
""",

    "followup_email": """Draft a follow-up email based on the most recent meeting.
Tone: {tone}  # professional, casual, executive
Include: summary of discussion, agreed action items with owners, next meeting date.

Meeting context:
{context}
""",

    "custom": """{user_prompt}

Available project knowledge:
{context}
""",
}
```

### 3.5.3 API endpoint

**New file**: `services/api/src/atlas_api/routes/outputs.py`

```python
@router.post("/api/v1/projects/{project_id}/outputs/generate")
async def generate_output(
    project_id: str,
    body: GenerateOutputRequest,  # output_kind, params, custom_prompt
    db: AsyncSession,
):
    """Enqueue an output generation job. Returns job_id for polling."""

@router.get("/api/v1/projects/{project_id}/outputs")
async def list_outputs(project_id: str, db: AsyncSession):
    """List all generated outputs for a project."""

@router.get("/api/v1/projects/{project_id}/outputs/{slug}")
async def get_output(project_id: str, slug: str):
    """Read a generated output (Markdown content)."""

@router.delete("/api/v1/projects/{project_id}/outputs/{slug}")
async def delete_output(project_id: str, slug: str):
    """Delete a generated output from vault."""
```

### 3.5.4 Frontend: output generation UI

**New component**: `apps/web/components/outputs/output-generator.tsx`

```
┌─────────────────────────────────────────────────┐
│  Generate Output                                 │
│                                                   │
│  Type: [Status Report ▼]                         │
│                                                   │
│  Scope:                                          │
│  ☑ All sources  ○ Selected sources only          │
│  ☑ Include meeting minutes                       │
│  ☑ Include action items                          │
│  ☐ Include raw transcripts                       │
│                                                   │
│  Additional instructions (optional):             │
│  ┌───────────────────────────────────────────┐   │
│  │ Focus on the API migration timeline and   │   │
│  │ budget implications...                     │   │
│  └───────────────────────────────────────────┘   │
│                                                   │
│  Model: [gemma4:27b ▼]                           │
│                                                   │
│  [Generate]                                       │
│  ████████████████░░░░ 78% — Writing risk section  │
└───────────────────────────────────────────────────┘
```

**New page**: `apps/web/app/projects/[id]/outputs/page.tsx`
- Grid of generated outputs with type icon, date, preview
- Click to read full Markdown
- Copy as Markdown / Export as PDF buttons
- Re-generate with different parameters

### 3.5.5 Vault output structure

Generated outputs go to `vault/outputs/` with full provenance:

```markdown
---
title: "Project Status Report — April 2026"
type: output
output_kind: status_report
workspace_id: ws_abc123
generated_at: "2026-04-10T15:30:00Z"
model: "gemma4:27b"
generation_time_ms: 12450
sources_consulted: 8
notes_referenced:
  - sources/meeting-2026-04-06-kickoff
  - sources/meeting-2026-04-10-sprint-review
  - entities/acme-corp
  - outputs/action-items
tags:
  - output/status_report
  - status/generated
---

# Project Status Report — April 2026

## Executive Summary

The API migration project is on track for the Q2 deadline...

## Key Decisions Made

| Date | Decision | Made By | Context |
|------|----------|---------|---------|
| 2026-04-06 | Use GraphQL over REST | [[entities/john-smith]] | [[sources/meeting-2026-04-06-kickoff]] |
| 2026-04-10 | Defer auth migration to Phase 2 | Team consensus | [[sources/meeting-2026-04-10-sprint-review]] |

...
```

### Acceptance criteria — Phase 3.5
- [ ] Users can request any of the 10+ output types from the UI
- [ ] Custom prompt allows free-form generation grounded in vault knowledge
- [ ] Generated outputs saved to `vault/outputs/` with full provenance
- [ ] Outputs contain wikilinks back to source notes and entities
- [ ] Model and generation metadata recorded in frontmatter
- [ ] Output list page shows all generated documents
- [ ] Re-generation creates new version, doesn't overwrite

---

## Phase 4: RAG — Project Knowledge Accumulation via Embeddings

**Goal**: As the consultant adds sources over weeks/months, the project accumulates vectorized knowledge. Every new source enriches the search index. DeerFlow, MiroFish, and output generation all use RAG (Retrieval-Augmented Generation) to ground their responses in vault knowledge.
**Estimated effort**: 5-6 days
**Depends on**: Phase 0
**Risk**: Medium — new search path, needs careful fallback

### Why RAG is essential for the consultant workflow

Without RAG, the LLM can only process what fits in its context window (~128K tokens). A consultant project after 8 weeks might have:
- 12 meeting transcripts (~60K words)
- 20 PDF documents (~100K words)
- 50+ vault notes (~30K words)

That's ~190K words — way beyond any context window. RAG solves this:

```
User asks: "What did we decide about the API migration timeline?"

WITHOUT RAG:
  → LLM sees only current context → hallucinates or says "I don't know"

WITH RAG:
  → Embed the question
  → Search vault vectors → find top 10 relevant passages
  → Passages from meeting-apr-06.md, meeting-apr-10.md, decision-log.md
  → LLM synthesizes answer grounded in REAL vault content with citations
```

This is what makes DeerFlow, MiroFish, and output generation actually useful — they search the project's accumulated knowledge before generating.

### 4.1 Embedding pipeline

**New file**: `services/worker/src/atlas_worker/search/embedder.py`

```python
async def embed_vault_notes(
    vault_path: Path,
    client: OllamaClient,
    model: str = "nomic-embed-text",
) -> list[NoteEmbedding]:
    """
    For each vault note:
    1. Read frontmatter + body
    2. Chunk into ~512 token passages
    3. Embed each chunk via Ollama
    4. Store embedding in SQLite/DuckDB alongside note slug + chunk offset
    """
```

### 4.2 Vector database: pgvector (PostgreSQL)

**Why pgvector and not a separate vector DB:**

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **pgvector (PostgreSQL extension)** | Already have Postgres, no new service, SQL joins with metadata, ACID transactions, mature | Slightly slower than purpose-built at >1M vectors | **Winner** — simplest, reuses existing infra |
| DuckDB vss | In-process, portable file | Separate from main DB, no joins with metadata | Use for portable export only |
| ChromaDB | Python-native, easy API | Another service/dependency, separate from metadata | Overkill for edge |
| Qdrant / Milvus | High performance | Separate server, heavy, cloud-oriented | Wrong fit for edge |
| LanceDB | Embedded, fast, Rust | Young ecosystem, another dependency | Watch for future |

**Decision**: pgvector as primary vector store. All embeddings live in PostgreSQL alongside source metadata, job records, and workspace data. One database to backup, migrate, and reason about.

#### Schema

**New migration**: `services/api/alembic/versions/001_add_pgvector.py`

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Embeddings table
CREATE TABLE note_embeddings (
    id              BIGSERIAL PRIMARY KEY,
    workspace_id    TEXT NOT NULL REFERENCES workspaces(id),
    note_slug       TEXT NOT NULL,
    note_title      TEXT,
    chunk_idx       INT NOT NULL,
    chunk_text      TEXT NOT NULL,           -- the passage that was embedded
    content_hash    TEXT NOT NULL,           -- SHA-256 of chunk for change detection
    embedding       vector(768) NOT NULL,   -- nomic-embed-text = 768 dims
    model           TEXT NOT NULL DEFAULT 'nomic-embed-text',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE(workspace_id, note_slug, chunk_idx)
);

-- HNSW index for fast approximate nearest neighbor search
-- ef_construction=128, m=16 are good defaults for <100K vectors
CREATE INDEX idx_embeddings_hnsw ON note_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 128);

-- Partial index for workspace-scoped queries
CREATE INDEX idx_embeddings_workspace ON note_embeddings(workspace_id);

-- For incremental updates: find chunks that changed
CREATE INDEX idx_embeddings_hash ON note_embeddings(workspace_id, note_slug, content_hash);
```

#### SQLAlchemy model

**New file**: `services/api/src/atlas_api/schemas/embedding.py`

```python
from pgvector.sqlalchemy import Vector

class NoteEmbeddingRow(Base):
    __tablename__ = "note_embeddings"

    id = Column(BigInteger, primary_key=True)
    workspace_id = Column(Text, ForeignKey("workspaces.id"), nullable=False)
    note_slug = Column(Text, nullable=False)
    note_title = Column(Text)
    chunk_idx = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    content_hash = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=False)  # pgvector type
    model = Column(Text, nullable=False, default="nomic-embed-text")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("workspace_id", "note_slug", "chunk_idx"),
    )
```

#### Vector store implementation

**New file**: `services/worker/src/atlas_worker/search/vector_store.py`

```python
class PgVectorStore:
    """pgvector-backed vector store. 
    
    All embeddings in PostgreSQL alongside metadata.
    Supports: HNSW approximate search, exact search, filtered search.
    """

    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def upsert(self, workspace_id: str, note_slug: str, 
                     chunks: list[TextChunk], embeddings: list[list[float]],
                     model: str = "nomic-embed-text") -> int:
        """Upsert embeddings for a note. Returns count of chunks updated."""

    async def search(self, workspace_id: str, query_embedding: list[float],
                     limit: int = 20, min_score: float = 0.3) -> list[VectorSearchResult]:
        """
        Cosine similarity search scoped to workspace.
        Uses HNSW index for ~5ms query time on <100K vectors.
        """
        # SQL: SELECT *, 1 - (embedding <=> :query) AS score
        #      FROM note_embeddings
        #      WHERE workspace_id = :ws
        #      ORDER BY embedding <=> :query
        #      LIMIT :limit

    async def search_with_metadata(self, workspace_id: str, 
                                    query_embedding: list[float],
                                    note_types: list[str] | None = None,
                                    date_from: datetime | None = None,
                                    limit: int = 20) -> list[VectorSearchResult]:
        """
        Filtered search: combine vector similarity with metadata filters.
        Example: "search meetings from last week only"
        
        This is where pgvector shines — JOIN with sources/notes tables
        in a single SQL query. Impossible with a separate vector DB.
        """

    async def delete_note(self, workspace_id: str, note_slug: str) -> int:
        """Remove all embeddings for a deleted note."""

    async def stats(self, workspace_id: str) -> VectorStoreStats:
        """Return embedding count, unique notes, total size, last updated."""
```

### 4.3 Incremental indexing (key for long-lived projects)

The project grows over weeks. Re-embedding the entire vault on every new source would be wasteful:

```python
class IncrementalEmbedder:
    """Only embed new or changed vault notes.
    
    Uses content_hash to detect changes.
    A 20-min meeting transcript (~5000 words, ~10 chunks) embeds in ~2 seconds.
    """

    def __init__(self, vector_store: PgVectorStore, router: InferenceRouter):
        self.store = vector_store
        self.router = router

    async def sync(self, workspace_id: str, vault_path: Path) -> EmbedSyncResult:
        """
        1. Scan vault notes, compute content_hash per chunk
        2. Query DB for existing hashes
        3. Embed only new/changed chunks via router.embed()
        4. Delete orphaned embeddings (note removed from vault)
        5. Return stats: added, updated, deleted, unchanged
        """

    async def embed_single_note(self, workspace_id: str, note_path: Path) -> int:
        """
        Fast path: embed just one new note after ingest.
        Called directly by compile job when a new source is added.
        Returns number of chunks embedded.
        """

@dataclass(frozen=True)
class EmbedSyncResult:
    chunks_added: int
    chunks_updated: int  
    chunks_deleted: int
    chunks_unchanged: int
    total_chunks: int
    duration_ms: int
```

### 4.3b Portable export (DuckDB snapshot)

For Obsidian portability or offline backup, export pgvector data to a DuckDB file:

```python
async def export_embeddings_to_duckdb(
    workspace_id: str, 
    session: AsyncSession,
    output_path: Path,  # .local/embeddings/{workspace_id}.duckdb
) -> Path:
    """
    Export all embeddings from pgvector to a portable DuckDB file.
    Use case: share project with someone who doesn't run PostgreSQL.
    Included in ZIP export (Phase 6).
    """
```

### 4.4 RAG pipeline (used by DeerFlow, MiroFish, output generation)

**New file**: `services/worker/src/atlas_worker/search/rag.py`

```python
class RAGPipeline:
    """Retrieval-Augmented Generation grounded in project vault.
    
    Used by:
    - DeerFlow research queries
    - MiroFish simulation context
    - Output generation (status reports, briefs, etc.)
    - Search answer synthesis
    """

    def __init__(self, vector_store: LocalVectorStore, router: InferenceRouter):
        self.vector_store = vector_store
        self.router = router

    async def query(
        self,
        question: str,
        workspace_id: str,
        max_context_tokens: int = 8000,
        mode: str = "hybrid",
    ) -> RAGResult:
        """
        1. Embed the question
        2. Hybrid search: lexical + semantic
        3. Re-rank results by relevance
        4. Build context from top passages (fit within max_context_tokens)
        5. Generate answer via LLM with citation markers
        6. Return answer + sources consulted
        """

    async def gather_context(
        self,
        topic: str,
        workspace_id: str,
        max_tokens: int = 16000,
    ) -> list[ContextPassage]:
        """
        Gather relevant vault passages for a topic.
        Used by output generation to build grounding context.
        Does NOT generate an answer — just retrieves passages.
        """

@dataclass(frozen=True)
class RAGResult:
    answer: str
    sources: list[SourceCitation]  # which vault notes were used
    confidence: float
    model: str
    search_mode: str  # lexical, semantic, hybrid

@dataclass(frozen=True)
class SourceCitation:
    note_slug: str
    note_title: str
    passage: str      # exact text chunk used
    relevance: float  # 0-1
```

### 4.5 Hybrid search

**Modified file**: `services/api/src/atlas_api/search/query.py`

```python
async def execute_search(query: str, workspace_id: str, mode: str = "hybrid"):
    match mode:
        case "lexical":
            return lexical_search(query, workspace_id)  # existing TF-IDF
        case "semantic":
            return semantic_search(query, workspace_id)  # new embeddings
        case "hybrid":
            lexical = lexical_search(query, workspace_id)
            semantic = semantic_search(query, workspace_id)
            return reciprocal_rank_fusion(lexical, semantic)
```

### 4.6 Dependencies

```toml
# services/api/pyproject.toml
pgvector = ">=0.3.0"        # SQLAlchemy integration for pgvector
duckdb = ">=1.0.0"          # Portable export only

# services/worker/pyproject.toml
pgvector = ">=0.3.0"
```

Docker image change:
```yaml
# docker-compose.yml
postgres:
  image: pgvector/pgvector:pg16   # replaces plain postgres:16
```

### 4.7 Migration

**New file**: `services/api/alembic/versions/001_add_pgvector.py`

Run on first startup or via `alembic upgrade head`. Idempotent (`CREATE EXTENSION IF NOT EXISTS`).

### Acceptance criteria — Phase 4
- [ ] pgvector extension active in PostgreSQL
- [ ] `note_embeddings` table with HNSW index created
- [ ] Vault notes embedded on compile/index
- [ ] **Incremental**: adding 1 source re-embeds only that source (~2 sec for 20-min transcript)
- [ ] Semantic search via pgvector returns results in <50ms for <100K vectors
- [ ] Hybrid mode combines lexical (TF-IDF) + semantic (pgvector)
- [ ] **Filtered search**: "search only meetings from last week" works via SQL JOIN
- [ ] RAG pipeline provides grounded answers with citations
- [ ] DeerFlow, MiroFish, and output generation use RAG for context
- [ ] Fallback to lexical-only when embeddings unavailable
- [ ] DuckDB export for portable vault sharing
- [ ] Re-indexing is idempotent
- [ ] Project with 50+ notes returns relevant results in <2 seconds

---

## Phase 5: Model Management UI

**Goal**: Users can browse, pull, and switch Ollama models from the frontend.
**Estimated effort**: 2-3 days
**Depends on**: Phase 0 + Phase 3

### 5.1 API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/models` | List available models |
| POST | `/api/v1/models/pull` | Pull new model from Ollama registry |
| DELETE | `/api/v1/models/{name}` | Delete model |
| GET | `/api/v1/models/status` | GPU/memory status |
| PUT | `/api/v1/projects/{id}/model` | Set project default model |

### 5.2 Frontend

**New page**: `/settings/models`

```
┌───────────────────────────────────────────┐
│  Model Manager                             │
│                                            │
│  Installed Models:                         │
│  ┌──────────────┬────────┬──────────────┐ │
│  │ gemma3:12b   │ 7.4 GB │ ✓ Default    │ │
│  │ nomic-embed  │ 274 MB │ Embeddings   │ │
│  │ whisper-lg   │ 2.9 GB │ Transcription│ │
│  └──────────────┴────────┴──────────────┘ │
│                                            │
│  GPU Memory: ████████░░░░ 8.2/16 GB       │
│                                            │
│  Pull New Model: [gemma3:27b    ] [Pull]   │
│  ████████████████░░░░ 78% — 14.2/18.3 GB  │
└───────────────────────────────────────────┘
```

### Acceptance criteria — Phase 5
- [ ] List installed models with size and purpose
- [ ] Pull new models with progress indicator
- [ ] Set default model per project
- [ ] Show GPU/memory usage in real time
- [ ] Prevent pulling models that won't fit in memory

---

## Phase 6: Polish and Production Hardening

**Goal**: Make it reliable for daily use.
**Estimated effort**: 5-7 days
**Depends on**: All previous phases

### 6.1 Error handling
- Ollama timeout → retry with exponential backoff (max 3)
- Model OOM → auto-switch to smaller quantization
- Audio too long → chunk into 30-min segments, transcribe sequentially
- Concurrent inference → queue with max parallelism based on available memory

### 6.2 Progress tracking
- WebSocket or SSE for real-time pipeline updates
- Per-source progress: ingesting → transcribing → extracting → compiling
- Estimated time remaining based on source size and model speed

### 6.3 Export
- Export project as ZIP (vault + metadata + embeddings DB)
- Open in Obsidian button (configure vault path)
- Export as static site (future)

### 6.4 Onboarding
- First-run setup wizard: check Ollama installed → pull required models → create first project
- Hardware compatibility check
- Model recommendations based on available RAM

### Acceptance criteria — Phase 6
- [ ] No unhandled errors in normal workflows
- [ ] Real-time progress for all long-running jobs
- [ ] ZIP export produces valid Obsidian vault
- [ ] First-run experience guides user through Ollama setup
- [ ] Tested on Mac M1 16GB and M2 32GB

---

## Phase 7: Mobile Companion (FUTURE — not in current scope)

> This phase is **research and design only**. No implementation planned until Phases 0-6 are stable.
> Included here to inform architectural decisions in earlier phases.

**Goal**: A mobile app that captures audio, photos, and quick notes in the field, then syncs to the desktop Atlas instance for full compilation.
**Status**: FUTURE EXPLORATION
**Depends on**: All previous phases stable + mature Google AI Edge SDK

### 7.1 Concept

The consultant's workflow has two environments:

| Environment | Device | What happens | Runtime |
|-------------|--------|-------------|---------|
| **Field** (meetings, site visits) | iPhone / Android | Capture: record audio, photo whiteboard, quick typed notes | Google AI Edge (LiteRT) |
| **Desk** (analysis, reporting) | Mac / PC | Compile: full pipeline, synthesis, search, output generation | MLX + Ollama |

The mobile app is a **capture tool**, not a full compiler. It does lightweight on-device processing and syncs raw + pre-processed data to the desktop.

### 7.2 Mobile capabilities (via Google AI Edge / LiteRT)

| Capability | On-device model | Size | What it does |
|------------|----------------|------|-------------|
| **Quick transcription** | Gemma 4 4B or Whisper small | ~2 GB | Rough transcript while walking out of meeting |
| **Photo → OCR** | Gemma 4 4B vision | ~2 GB | Whiteboard/document text extraction |
| **Audio classification** | FunctionGemma 270M | ~270 MB | "Is this a meeting (multi-speaker) or a memo (monologue)?" |
| **Quick entities** | Gemma 4 4B | ~2 GB | Extract names, companies, dates for preview |
| **Language detection** | Whisper tiny | ~75 MB | Auto-detect EN vs ES before transcription |

> All models run on-device via LiteRT. No internet needed during capture.
> The desktop re-processes everything with higher-quality models (large-v3, Gemma 27B).

### 7.3 Sync protocol

```
Mobile                                    Desktop (Atlas)
┌─────────────────┐                      ┌──────────────────────┐
│ Capture session  │                      │ .local/inbox/        │
│                  │    WiFi local /      │                      │
│ audio.m4a       │──── USB / folder ───►│ audio.m4a            │
│ photo-1.jpg     │     sync / AirDrop   │ photo-1.jpg          │
│ photo-2.jpg     │                      │ photo-2.jpg          │
│ quick-notes.txt │                      │ quick-notes.txt      │
│ session.json    │                      │ session.json         │
│  ├─ timestamp   │                      │  (metadata manifest) │
│  ├─ location    │                      │                      │
│  ├─ language_hint: "en"                │ Atlas auto-detects   │
│  ├─ rough_transcript: "..."            │ new files in inbox   │
│  └─ detected_entities: [...]           │ → triggers ingest    │
└─────────────────┘                      └──────────────────────┘
```

**session.json** — metadata from mobile pre-processing:
```json
{
  "session_id": "ses_20260410_143000",
  "captured_at": "2026-04-10T14:30:00Z",
  "device": "iPhone 15 Pro",
  "files": [
    {"name": "audio.m4a", "type": "audio", "duration_s": 1200, "language_hint": "en"},
    {"name": "photo-1.jpg", "type": "image", "rough_ocr": "Q1 budget: $2.3M..."},
    {"name": "photo-2.jpg", "type": "image", "rough_ocr": "Architecture: API → DB → Cache"},
    {"name": "quick-notes.txt", "type": "text"}
  ],
  "rough_transcript": "John mentioned the API migration timeline...",
  "detected_entities": ["John Smith", "API migration", "Q2 deadline"],
  "classification": "meeting"
}
```

### 7.4 Inbox watcher (desktop side)

**Future file**: `services/worker/src/atlas_worker/sync/inbox_watcher.py`

```python
class InboxWatcher:
    """Watches .local/inbox/ for new capture sessions from mobile.
    
    When a new session.json appears:
    1. Parse manifest
    2. Create source records for each file
    3. Enqueue ingest jobs (full quality: large-v3, Gemma 27B)
    4. Move files from inbox/ to uploads/ after ingestion
    5. The rough_transcript and detected_entities from mobile
       are stored as "mobile_preview" in source metadata —
       the desktop pipeline overwrites with high-quality results.
    """
```

### 7.5 Architectural decisions for earlier phases (informed by Phase 7)

These decisions should be made NOW even though Phase 7 is future:

| Decision | Phase affected | Why |
|----------|---------------|-----|
| Add `.local/inbox/` to directory structure | Phase 0.5 | Ready for mobile sync from day one |
| Use `session.json` manifest format for all batch uploads | Phase 1 | Same format whether files come from UI drag-drop or mobile sync |
| Store `language_hint` in source metadata | Phase 1 | Mobile can pre-detect language; desktop uses it for Whisper `language=` param |
| Keep EN original + ES translation as separate sections in vault notes | Phase 2 | Don't lose the original transcript when translating |
| Make inbox a watchable folder (fsnotify or polling) | Phase 3 | Enables "drop files here" workflow even without mobile app |

### 7.6 Research questions (not blocking)

1. **Google AI Edge SDK maturity**: Is LiteRT stable enough for production mobile apps? What models are pre-optimized?
2. **Sync mechanism**: AirDrop (Mac only), local WiFi API, USB, or folder sync (iCloud/Google Drive with `.local/inbox/` as target)?
3. **Offline capture duration**: How much audio can a phone store and pre-process before syncing? 1 hour? 8 hours?
4. **Battery impact**: Running Gemma 4B + Whisper small on-device during a 1-hour meeting — what's the battery drain?
5. **Cross-platform**: Google AI Edge Gallery supports Android 12+ and iOS 17+. Is there a React Native / Flutter wrapper, or does this need native development?
6. **FunctionGemma for auto-tagging**: Can FunctionGemma 270M auto-classify captures (meeting, lecture, interview, memo) reliably enough to skip user input?

### 7.7 Technology options for mobile app

| Option | Pros | Cons |
|--------|------|------|
| **Google AI Edge Gallery fork** | Already works, Gemma 4 on-device, Apache 2.0 | Java/Kotlin (Android) + Swift (iOS), two codebases |
| **React Native + custom native modules** | Single codebase, JS/TS (same as Atlas web) | LiteRT bindings immature in RN |
| **Flutter + TFLite plugin** | Single codebase, good mobile performance | Dart, different ecosystem from Atlas |
| **PWA with Web LLM** | No app store, same Next.js stack | Limited device access, no background recording |
| **Native iOS + Android** | Best performance, full device access | Two codebases, most effort |

> **Recommendation**: Start with a **PWA** for basic file capture + upload, then build native with Google AI Edge SDK for on-device inference when the use case is validated.

---

## Dependency Graph

```
Phase 0: Inference Router ──► Phase 0.5: Offline Setup ──────────┐
    │                              │                              │
    ├──► Phase 1: Audio + OCR Ingest (EN→ES, ES→ES)              │
    │        │                                                    │
    ├──► Phase 2: LLM Compilation + Minutes + Trackers            │
    │        │                                                    │
    │        ├──► Phase 3: Project UX ◄───────────────────────────┤
    │        │        │                                           │
    │        │        ├──► Phase 3.5: Output Generation            │
    │        │        │                                           │
    ├──► Phase 4: Embeddings Search                               │
    │                 │                                           │
    └──► Phase 5: Model Management ◄──────────────────────────────┘
                      │
                      ▼
              Phase 6: Polish
                      │
                      ▼
        Phase 7: Mobile Companion (FUTURE)
        Google AI Edge / LiteRT
        Capture → Sync → Desktop compiles
```

## Timeline Estimate

| Phase | Duration | Can Parallelize With |
|-------|----------|---------------------|
| Phase 0: Inference Router | 4-5 days | — |
| Phase 0.5: Offline Setup | 2 days | Phase 1 (scripts vs code) |
| Phase 1: Audio + OCR Ingest | 5-6 days | Phase 2, Phase 0.5 |
| Phase 2: LLM Compilation | 6-8 days | Phase 1, Phase 4 |
| Phase 3: Project UX | 5-6 days | Phase 4 (frontend vs backend) |
| Phase 3.5: Output Generation | 4-5 days | Phase 4 (backend vs frontend) |
| Phase 4: Embeddings | 4-5 days | Phase 3, Phase 3.5 |
| Phase 5: Model Management | 2-3 days | Phase 6 |
| Phase 6: Polish | 5-7 days | — |
| Phase 7: Mobile (FUTURE) | TBD | Not in current scope |
| **Total Phases 0-6 (sequential)** | **~38-47 days** | |
| **Total Phases 0-6 (parallelized)** | **~25-29 days** | |

## Files Changed Summary

### New files (~45 files)
```
# Phase 0.5: Setup scripts
scripts/setup.sh
scripts/verify-offline.sh
scripts/start.sh

# Phase 0: Inference Router + Backends
services/worker/src/atlas_worker/inference/__init__.py
services/worker/src/atlas_worker/inference/router.py
services/worker/src/atlas_worker/inference/models.py
services/worker/src/atlas_worker/inference/health.py
services/worker/src/atlas_worker/inference/backends/__init__.py
services/worker/src/atlas_worker/inference/backends/ollama.py
services/worker/src/atlas_worker/inference/backends/whisper_mlx.py
services/worker/src/atlas_worker/inference/backends/vision_mlx.py
services/worker/src/atlas_worker/inference/prompts.py
services/worker/src/atlas_worker/inference/output_prompts.py

# Phase 1: New extractors
services/worker/src/atlas_worker/extractors/audio.py
services/worker/src/atlas_worker/extractors/ocr.py

# Phase 2: New compiler modules
services/worker/src/atlas_worker/compiler/summarizer.py
services/worker/src/atlas_worker/compiler/meeting_minutes.py
services/worker/src/atlas_worker/compiler/tracker.py
services/worker/src/atlas_worker/compiler/reference_extractor.py
services/worker/src/atlas_worker/compiler/concept_synthesizer.py
services/worker/src/atlas_worker/compiler/contradiction_detector.py
services/worker/src/atlas_worker/compiler/timeline_builder.py
services/worker/src/atlas_worker/compiler/coverage_report.py

# Phase 3.5: Output generation
services/worker/src/atlas_worker/jobs/generate_output.py
services/api/src/atlas_api/routes/outputs.py

# Phase 1: Office extractors
services/worker/src/atlas_worker/extractors/docx.py
services/worker/src/atlas_worker/extractors/xlsx.py
services/worker/src/atlas_worker/extractors/pptx.py

# Phase 4: Vector search + RAG
services/worker/src/atlas_worker/search/embedder.py
services/worker/src/atlas_worker/search/vector_store.py
services/worker/src/atlas_worker/search/rag.py
services/api/src/atlas_api/schemas/embedding.py
services/api/alembic/versions/001_add_pgvector.py

# Tests
services/worker/tests/test_inference_client.py
services/worker/tests/test_audio_extractor.py
services/worker/tests/test_ocr_extractor.py
services/worker/tests/test_meeting_minutes.py
services/worker/tests/test_summarizer.py
services/worker/tests/test_output_generation.py
services/worker/tests/fixtures/sample.wav
services/worker/tests/fixtures/sample-whiteboard.png

# Frontend
apps/web/app/projects/page.tsx
apps/web/app/projects/new/page.tsx
apps/web/app/projects/[id]/page.tsx
apps/web/app/projects/[id]/outputs/page.tsx
apps/web/app/projects/[id]/settings/page.tsx
apps/web/app/settings/models/page.tsx
apps/web/components/projects/project-card.tsx
apps/web/components/projects/project-wizard.tsx
apps/web/components/sources/multi-uploader.tsx
apps/web/components/sources/audio-player.tsx
apps/web/components/outputs/output-generator.tsx
apps/web/components/outputs/output-card.tsx
apps/web/components/jobs/pipeline-progress.tsx
apps/web/components/inference-status.tsx
apps/web/components/settings/model-selector.tsx
```

### Modified files (~22 files)
```
# Worker
services/worker/src/atlas_worker/config.py
services/worker/src/atlas_worker/main.py
services/worker/src/atlas_worker/jobs/ingest.py
services/worker/src/atlas_worker/jobs/compile.py
services/worker/src/atlas_worker/compiler/entity_extraction.py
services/worker/src/atlas_worker/extractors/__init__.py
services/worker/pyproject.toml

# API
services/api/src/atlas_api/config.py
services/api/src/atlas_api/routes/health.py
services/api/src/atlas_api/routes/sources.py
services/api/src/atlas_api/models/enums.py
services/api/src/atlas_api/search/query.py
services/api/src/atlas_api/evals/compiler_eval.py
services/api/src/atlas_api/adapters/deerflow.py    # cloud stub → local Ollama
services/api/src/atlas_api/adapters/hermes.py      # cloud stub → local Redis+Ollama
services/api/src/atlas_api/adapters/mirofish.py    # cloud stub → local Ollama

# Shared types
packages/shared/src/types/enums.ts

# Frontend
apps/web/app/layout.tsx
apps/web/app/(dashboard)/layout.tsx
apps/web/lib/api.ts

# Infra
docker-compose.yml
.env.example
.gitignore
```

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| MLX-only = Mac-only | High | Medium | Add `faster-whisper` + `transformers` fallbacks for Linux in Phase 6 |
| lightning-whisper-mlx API breaks | Low | Medium | Pin version; WhisperMLXBackend abstracts away |
| mlx-vlm model quality varies | Medium | Medium | Benchmark Gemma 4 vision vs Qwen-VL for OCR; make configurable |
| 16GB RAM insufficient for 27B models | Medium | High | Sequential pipeline ensures only 1 model loaded; use 12B on light profile |
| LLM hallucinations in entity extraction | Medium | Medium | Always compare with heuristic baseline; confidence scores |
| Audio files too large for temp storage | Low | Medium | Stream-to-disk in .local/tmp/; chunk long audio into 30-min segments |
| DuckDB vector search too slow at scale | Low | Low | Add HNSW index; max ~100K vectors is fine for edge |
| .local/ grows too large (30+ GB) | Medium | Low | Show disk usage in UI; offer model cleanup; profiles control model count |
| Ollama 0.19 MLX backend immature | Medium | Low | Falls back to GGUF; monitor Ollama releases |
| Qwen3.5-Claude-Distilled licensing | Low | High | Verify license before shipping; may need to swap to vanilla Qwen |

## Adapter Localization: DeerFlow, Hermes, MiroFish on Ollama

The existing adapters (services/api/src/atlas_api/adapters/) are designed to be thin and replaceable. In the edge-first pivot, all three must run against local Ollama — zero cloud calls.

### DeerFlow (Research Orchestration)

**Current**: Stub adapter that would call an external DeerFlow API.
**Edge pivot**: DeerFlow orchestrates multi-step research workflows. Locally, this becomes a prompt chain against Ollama.

```python
# adapters/deerflow.py — edge-first implementation
class LocalDeerFlowAdapter:
    """DeerFlow-compatible research orchestrator backed by local Ollama.
    
    Pipeline:
    1. Decompose research question into sub-questions (LLM)
    2. For each sub-question, search vault for relevant notes
    3. Synthesize answer from vault evidence (LLM)
    4. Aggregate sub-answers into final research report (LLM)
    5. Write result to vault/outputs/
    """

    def __init__(self, client: OllamaClient, model: str, vault_path: Path):
        self.client = client
        self.model = model
        self.vault_path = vault_path

    async def submit_task(self, question: str, scope: list[str]) -> DeerFlowTask:
        """Decompose question, search vault, synthesize answer."""

    async def get_result(self, task_id: str) -> DeerFlowResult:
        """Poll for completion, return synthesized research output."""
```

**Use case for consultant**: "Research everything we know about the competitor's pricing strategy" → DeerFlow searches vault across all meetings and documents, synthesizes a report.

### Hermes (Memory Bridge)

**Current**: Stub adapter for external memory/context service.
**Edge pivot**: Hermes becomes a local context manager backed by Redis + vault.

```python
# adapters/hermes.py — edge-first implementation
class LocalHermesAdapter:
    """Hermes-compatible memory bridge backed by Redis + vault.
    
    Functions:
    - Store conversation/session context in Redis (TTL-based)
    - Retrieve relevant past context for current task
    - Cross-reference with vault notes for long-term memory
    - Maintain project-scoped context threads
    """

    def __init__(self, redis: Redis, vault_path: Path, client: OllamaClient):
        self.redis = redis
        self.vault_path = vault_path
        self.client = client  # for context summarization

    async def store_context(self, project_id: str, context: str, ttl: int = 3600)
    async def retrieve_context(self, project_id: str, query: str) -> list[ContextEntry]
    async def summarize_session(self, project_id: str) -> str
    async def clear_context(self, project_id: str)
```

**Use case for consultant**: Hermes remembers what you were working on last session. Open a project → Hermes surfaces "last time you were analyzing the Q1 budget gap and had 3 open action items."

### MiroFish (Simulation Gateway)

**Current**: Stub adapter for external simulation engine.
**Edge pivot**: MiroFish becomes a local scenario simulation engine backed by Ollama.

```python
# adapters/mirofish.py — edge-first implementation
class LocalMiroFishAdapter:
    """MiroFish-compatible simulation gateway backed by local Ollama.
    
    Capabilities:
    - What-if scenario analysis from vault knowledge
    - Stakeholder impact simulation
    - Timeline projection with risk factors
    - Decision tree exploration
    
    All simulation runs are logged to vault/outputs/ for auditability.
    Requires user confirmation before running (premium workflow).
    """

    def __init__(self, client: OllamaClient, model: str, vault_path: Path):
        self.client = client
        self.model = model  # ideally deepseek-r1 or qwen3.5-claude-distilled for reasoning
        self.vault_path = vault_path

    async def run_simulation(self, scenario: SimulationScenario) -> SimulationResult:
        """
        1. Gather relevant vault knowledge for the scenario
        2. Build scenario context with constraints and variables
        3. Run multi-turn reasoning chain (uses chain-of-thought model)
        4. Generate structured outcome report
        5. Write to vault/outputs/simulation-{id}.md
        """

    async def what_if(self, question: str, project_id: str) -> WhatIfResult:
        """Quick what-if: 'What if we delay the migration by 2 months?'"""
```

**Use case for consultant**: "What if the client reduces budget by 20%?" → MiroFish analyzes project scope, timeline, team allocation from vault, generates impact assessment.

### Model Recommendations for Adapters

| Adapter | Best Model | Why |
|---------|-----------|-----|
| DeerFlow | gemma4:27b or qwen2.5:32b | Needs good search + synthesis |
| Hermes | gemma4:12b or phi4:14b | Context summarization is lightweight |
| MiroFish | **qwen3.5-27b-claude-distilled** or deepseek-r1:32b | Needs deep chain-of-thought reasoning |

### Integration in Pipeline

```python
# services/api/src/atlas_api/config.py
class Settings:
    # Adapters — all local, all use project Ollama
    enable_deerflow: bool = True    # was False (disabled when cloud-only)
    enable_hermes: bool = True      # was False
    enable_mirofish: bool = False   # still off by default (premium, needs confirmation)
    
    # Adapter models (can differ from default synthesis model)
    deerflow_model: str = "gemma4:27b"
    hermes_model: str = "gemma4:12b"
    mirofish_model: str = "qwen3.5-27b-claude-distilled"
```

### New API Routes (already scaffolded, now with local backends)

The existing routes at `/api/v1/integrations/deerflow/*`, `/api/v1/integrations/hermes/*`, `/api/v1/integrations/mirofish/*` stay the same — only the adapter implementation changes from cloud stubs to local Ollama backends.

---

## Open Questions

1. **Gemma 4 availability**: Gemma 4 is now in Ollama. Confirm 12B and 27B quantized variants work well.
2. **Video support**: Extract audio track from video (ffmpeg) in Phase 1 or defer?
3. **Multi-language**: Whisper handles multi-language; should the compiler prompts be language-aware? (Qwen 3 supports 100+ languages)
4. **Sequential model loading**: Confirm Ollama unloads models cleanly between pipeline stages. Test memory recovery.
5. **Offline-first frontend**: Should we use service workers for full offline capability?
6. **Disk budget**: `.local/` can grow to 20-30 GB with multiple models. Show disk usage in UI and warn when low?
7. **Symlink option**: For users who already have Ollama models in `~/.ollama`, should `setup.sh` offer to symlink instead of re-downloading?
8. **Vision OCR quality**: Benchmark Gemma 4 vision (mlx-vlm) vs dedicated OCR models for table extraction accuracy. If insufficient, add Qianfan-OCR as optional backend.
9. **Qwen3.5-Claude-Distilled**: Benchmark against Gemma 4 27B for reasoning tasks (MiroFish simulations, contradiction detection). If better, make it the default reasoning model.
10. **Adapter model specialization**: Should each adapter (DeerFlow, Hermes, MiroFish) use a different model optimized for its task, or share one model to simplify?
11. **Meeting detection**: Should Atlas auto-detect that an audio upload is a meeting (multiple speakers) vs a monologue (lecture, dictation) and adjust output accordingly?
