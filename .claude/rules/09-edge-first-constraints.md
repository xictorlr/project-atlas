# Edge-first constraints

All inference runs locally. No data leaves the machine. No cloud API keys required.

## How to use this rule

Read this file before adding any inference, model, or external API call.
This rule takes precedence over any rule that implies cloud connectivity.

## Invariants

- All LLM inference MUST go through the InferenceRouter, never direct API calls to OpenAI/Anthropic/etc.
- The InferenceRouter dispatches to: Ollama (LLMs + embeddings), lightning-whisper-mlx (STT), mlx-vlm (vision/OCR).
- All model weights MUST be stored in `.local/` inside the project directory.
- OLLAMA_MODELS MUST point to `.local/ollama/`, never `~/.ollama/`.
- HF_HOME MUST point to `.local/mlx/`, never `~/.cache/huggingface/`.
- No code may import `openai`, `anthropic`, or any cloud LLM SDK.
- No code may make HTTP calls to external inference APIs (api.openai.com, api.anthropic.com, etc.).
- Sequential model loading: only one large model in memory at a time. Unload before loading next.
- The application MUST work with zero internet after `scripts/setup.sh` has run once.
- PostgreSQL with pgvector is the vector database. No external vector DB services (Pinecone, Weaviate, etc.).

## Graceful degradation

- If Ollama is not running: deterministic extractors (pdfplumber, BS4, python-docx) still work. LLM synthesis is skipped.
- If MLX backends unavailable (e.g., Linux): fall back to CPU-based alternatives and log a warning.
- Never crash because a model is missing. Return a clear error and continue.

## Model profiles

Support hardware-aware model selection via `MODEL_PROFILE` env var:
- `light`: 16GB RAM — smaller models (gemma4, distil-large-v3)
- `standard`: 32GB RAM — full models (gemma4:26b, large-v3) — **default**
- `reasoning`: 32GB+ — deep reasoning model for MiroFish/analysis
- `polyglot`: multi-language focus (qwen3, bge-m3, translategemma)
- `maximum`: 64GB+ — largest models available

## Reference

See `docs/15-edge-first-roadmap.md` for the full architecture and model catalog.
