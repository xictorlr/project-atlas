#!/usr/bin/env bash
# Atlas Edge Setup — Phase 0.5
# Downloads all dependencies into .local/ for fully offline operation.
# Idempotent: safe to run multiple times.
#
# Usage: bash scripts/setup.sh
#
# What it does:
#   1. Creates .local/ directory structure
#   2. Checks Ollama is installed
#   3. Pulls Ollama models into .local/ollama/
#   4. Creates MLX model directories (models download on first use)
#   5. Installs JS dependencies (pnpm)
#   6. Installs Python dependencies (uv sync for api + worker)
#   7. Pulls Docker images (pgvector, redis)
#   8. Runs verify-offline.sh
#
# After setup: all data lives in .local/ — no ~/.ollama, no ~/.cache writes.
set -euo pipefail

# ---------------------------------------------------------------------------
# Paths — all absolute, derived from script location
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ATLAS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCAL_DIR="$ATLAS_ROOT/.local"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
step() {
    echo ""
    echo "[$1/$TOTAL_STEPS] $2"
    echo "----------------------------------------------------------------------"
}

ok()   { echo "  [OK] $*"; }
warn() { echo "  [WARN] $*"; }
fail() { echo "  [FAIL] $*" >&2; }

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
TOTAL_STEPS=7
echo ""
echo "======================================================================"
echo "  Atlas Edge Setup"
echo "======================================================================"
echo "  Project root : $ATLAS_ROOT"
echo "  Local storage: $LOCAL_DIR"
echo ""

# ---------------------------------------------------------------------------
# Step 1 — Create .local/ directory structure
# ---------------------------------------------------------------------------
step 1 "Creating local directory structure"

mkdir -p \
    "$LOCAL_DIR/ollama" \
    "$LOCAL_DIR/mlx/whisper" \
    "$LOCAL_DIR/mlx/vlm" \
    "$LOCAL_DIR/mlx/audio" \
    "$LOCAL_DIR/data/postgres" \
    "$LOCAL_DIR/data/redis" \
    "$LOCAL_DIR/uploads" \
    "$LOCAL_DIR/inbox" \
    "$LOCAL_DIR/embeddings" \
    "$LOCAL_DIR/tmp"

ok "All .local/ directories created"

# ---------------------------------------------------------------------------
# Step 2 — Check Ollama is installed
# ---------------------------------------------------------------------------
step 2 "Checking Ollama installation"

if ! command -v ollama &>/dev/null; then
    fail "Ollama not found. Please install it first:"
    echo ""
    echo "    Mac (Homebrew):  brew install ollama"
    echo "    Mac (direct):    https://ollama.com/download"
    echo "    Linux:           curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
    exit 1
fi

ok "Ollama found: $(ollama --version 2>/dev/null || echo 'version unknown')"

# ---------------------------------------------------------------------------
# Step 3 — Pull Ollama models into .local/ollama/
# ---------------------------------------------------------------------------
step 3 "Pulling Ollama models into .local/ollama/"

# Point Ollama at project-local storage — no writes to ~/.ollama
export OLLAMA_MODELS="$LOCAL_DIR/ollama"

# Start Ollama if not already running
OLLAMA_STARTED=false
if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "  Ollama is not running — starting it now..."
    OLLAMA_MODELS="$LOCAL_DIR/ollama" ollama serve >/dev/null 2>&1 &
    OLLAMA_PID=$!
    OLLAMA_STARTED=true

    # Wait up to 15 s for Ollama to become ready
    WAIT=0
    until curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; do
        sleep 1
        WAIT=$((WAIT + 1))
        if [ "$WAIT" -ge 15 ]; then
            fail "Ollama did not start within 15 seconds. Check for port conflicts."
            exit 1
        fi
    done
    ok "Ollama started (PID $OLLAMA_PID)"
else
    ok "Ollama already running"
fi

# Pull models — ollama pull is idempotent (skips if already present)
echo "  Pulling gemma4:27b  (~18 GB) — primary synthesis model..."
OLLAMA_MODELS="$LOCAL_DIR/ollama" ollama pull gemma4:27b

echo "  Pulling gemma4:12b  (~8 GB)  — lightweight synthesis..."
OLLAMA_MODELS="$LOCAL_DIR/ollama" ollama pull gemma4:12b

echo "  Pulling nomic-embed-text (~274 MB) — search embeddings..."
OLLAMA_MODELS="$LOCAL_DIR/ollama" ollama pull nomic-embed-text

ok "All Ollama models pulled"

# If we started Ollama, leave it running (start.sh will manage it).
# Do not kill it here — the user may want to keep using it.

# ---------------------------------------------------------------------------
# Step 4 — MLX model directories (models download on first use)
# ---------------------------------------------------------------------------
step 4 "Preparing MLX model directories"

# lightning-whisper-mlx and mlx-vlm download their weights on first use.
# We set HF_HOME so they download into .local/mlx/ instead of ~/.cache/
# The actual download happens when the worker first runs inference.
export HF_HOME="$LOCAL_DIR/mlx"

# Confirm Python 3.12+ is available for the note below
if command -v python3 &>/dev/null; then
    PY_VER="$(python3 --version 2>&1)"
    ok "Python available: $PY_VER"
    echo "  NOTE: MLX models (Whisper large-v3 ~3 GB, Gemma 4 Vision ~8 GB)"
    echo "        will download automatically on first inference call."
    echo "        HF_HOME is set to .local/mlx/ in scripts/start.sh"
    echo "        so all weights stay inside the project directory."
else
    warn "python3 not found in PATH. MLX inference will be unavailable."
fi

ok "MLX directories ready at $LOCAL_DIR/mlx/"

# ---------------------------------------------------------------------------
# Step 5 — Install JavaScript dependencies
# ---------------------------------------------------------------------------
step 5 "Installing JavaScript dependencies (pnpm)"

if ! command -v pnpm &>/dev/null; then
    fail "pnpm not found. Install via: npm install -g pnpm"
    exit 1
fi

cd "$ATLAS_ROOT"
pnpm install --frozen-lockfile
ok "JS dependencies installed"

# ---------------------------------------------------------------------------
# Step 6 — Install Python dependencies (uv sync)
# ---------------------------------------------------------------------------
step 6 "Installing Python dependencies (uv)"

if ! command -v uv &>/dev/null; then
    fail "uv not found. Install via: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "  Installing services/api..."
cd "$ATLAS_ROOT/services/api"
uv sync --extra dev

echo "  Installing services/worker..."
cd "$ATLAS_ROOT/services/worker"
uv sync --extra dev

ok "Python dependencies installed"

# ---------------------------------------------------------------------------
# Step 7 — Pull Docker images
# ---------------------------------------------------------------------------
step 7 "Pulling Docker images"

if ! command -v docker &>/dev/null; then
    warn "docker not found — skipping image pull."
    warn "Install Docker Desktop from https://www.docker.com/products/docker-desktop/"
    warn "Then re-run: bash scripts/setup.sh"
else
    echo "  Pulling pgvector/pgvector:pg16 ..."
    docker pull pgvector/pgvector:pg16

    echo "  Pulling redis:7-alpine ..."
    docker pull redis:7-alpine

    ok "Docker images pulled"
fi

# ---------------------------------------------------------------------------
# Done — run verify
# ---------------------------------------------------------------------------
echo ""
echo "======================================================================"
echo "  Setup complete. Running verification..."
echo "======================================================================"
echo ""

bash "$SCRIPT_DIR/verify-offline.sh"
