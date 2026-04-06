#!/usr/bin/env bash
# Atlas Edge Launcher — Phase 0.5
# Starts all services with environment variables pointing to .local/.
#
# Usage: bash scripts/start.sh
#
# What it does:
#   1. Sets all env vars pointing to .local/
#   2. Starts Ollama if not running (OLLAMA_MODELS → .local/ollama/)
#   3. Starts Docker compose (postgres + redis)
#   4. Waits for PostgreSQL to be ready
#   5. Starts pnpm dev (Next.js + FastAPI + worker)
#
# Prerequisites: run scripts/setup.sh first.
set -euo pipefail

# ---------------------------------------------------------------------------
# Paths — all absolute, derived from script location
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ATLAS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCAL_DIR="$ATLAS_ROOT/.local"

# ---------------------------------------------------------------------------
# Environment — all local assets in .local/, nothing in ~/.cache or ~/.ollama
# ---------------------------------------------------------------------------

# Ollama: LLM + embedding models
export OLLAMA_MODELS="$LOCAL_DIR/ollama"
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_DEFAULT_MODEL="${OLLAMA_DEFAULT_MODEL:-gemma4:26b}"
export OLLAMA_EMBEDDING_MODEL="${OLLAMA_EMBEDDING_MODEL:-nomic-embed-text}"

# MLX: Whisper + Vision model caches (HF_HOME redirects HuggingFace downloads)
export HF_HOME="$LOCAL_DIR/mlx"
export ATLAS_MLX_DIR="$LOCAL_DIR/mlx"

# Atlas storage paths
export ATLAS_UPLOAD_DIR="$LOCAL_DIR/uploads"
export ATLAS_EMBEDDINGS_DIR="$LOCAL_DIR/embeddings"
export ATLAS_TMP_DIR="$LOCAL_DIR/tmp"

# Load .env if present (overrides defaults above without overriding already-set vars)
if [ -f "$ATLAS_ROOT/.env" ]; then
    set -a
    source "$ATLAS_ROOT/.env"
    set +a
fi

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
ok()   { echo "  [OK] $*"; }
info() { echo "  [-] $*"; }

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
echo ""
echo "======================================================================"
echo "  Atlas Edge — Starting"
echo "======================================================================"
echo "  Project root   : $ATLAS_ROOT"
echo "  Ollama models  : $OLLAMA_MODELS"
echo "  MLX models     : $ATLAS_MLX_DIR"
echo "  Uploads        : $ATLAS_UPLOAD_DIR"
echo ""

# ---------------------------------------------------------------------------
# Step 1 — Sanity check: .local/ exists
# ---------------------------------------------------------------------------
if [ ! -d "$LOCAL_DIR" ]; then
    echo "  ERROR: .local/ directory not found."
    echo "  Run setup first: bash scripts/setup.sh"
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 2 — Start Ollama if not running
# ---------------------------------------------------------------------------
info "Checking Ollama..."

if ! command -v ollama &>/dev/null; then
    echo "  ERROR: ollama not found in PATH."
    echo "  Install from https://ollama.com, then re-run."
    exit 1
fi

if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    ok "Ollama already running"
else
    info "Starting Ollama (models in .local/ollama/)..."
    OLLAMA_MODELS="$LOCAL_DIR/ollama" ollama serve >/dev/null 2>&1 &
    OLLAMA_BG_PID=$!

    WAIT=0
    until curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; do
        sleep 1
        WAIT=$((WAIT + 1))
        if [ "$WAIT" -ge 20 ]; then
            echo "  ERROR: Ollama did not start within 20 seconds."
            echo "  Check for port 11434 conflicts or run 'ollama serve' manually."
            exit 1
        fi
    done
    ok "Ollama started (PID $OLLAMA_BG_PID)"
fi

# ---------------------------------------------------------------------------
# Step 3 — Start Docker infra (postgres + redis)
# ---------------------------------------------------------------------------
info "Starting Docker services (postgres + redis)..."

if ! command -v docker &>/dev/null; then
    echo "  ERROR: docker not found in PATH."
    echo "  Install Docker Desktop from https://www.docker.com/products/docker-desktop/"
    exit 1
fi

cd "$ATLAS_ROOT"
docker compose up -d postgres redis

ok "Docker services started"

# ---------------------------------------------------------------------------
# Step 4 — Wait for PostgreSQL to be ready
# ---------------------------------------------------------------------------
info "Waiting for PostgreSQL to accept connections..."

WAIT=0
until docker compose exec -T postgres pg_isready \
        -U "${POSTGRES_USER:-atlas}" \
        -d "${POSTGRES_DB:-atlas_dev}" >/dev/null 2>&1; do
    sleep 1
    WAIT=$((WAIT + 1))
    if [ "$WAIT" -ge 30 ]; then
        echo "  ERROR: PostgreSQL did not become ready within 30 seconds."
        echo "  Check: docker compose logs postgres"
        exit 1
    fi
done

ok "PostgreSQL is ready"

# ---------------------------------------------------------------------------
# Step 5 — Start all services via pnpm dev
# ---------------------------------------------------------------------------
echo ""
echo "======================================================================"
echo "  Atlas is starting"
echo "======================================================================"
echo ""
echo "  Web UI  :  http://localhost:3000"
echo "  API     :  http://localhost:8000"
echo "  API docs:  http://localhost:8000/docs"
echo "  Ollama  :  http://localhost:11434"
echo ""
echo "  Press Ctrl+C to stop all services."
echo ""

cd "$ATLAS_ROOT"
pnpm dev
