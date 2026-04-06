#!/usr/bin/env bash
# Atlas Offline Verification — Phase 0.5
# Checks every component needed for fully offline operation.
# Prints PASS/FAIL per item and a summary with disk usage.
#
# Usage: bash scripts/verify-offline.sh
#
# Exit code: 0 if all checks pass, 1 if any check fails.
set -euo pipefail

# ---------------------------------------------------------------------------
# Paths — all absolute, derived from script location
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ATLAS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCAL_DIR="$ATLAS_ROOT/.local"

# Point Ollama at project-local storage for model list check
export OLLAMA_MODELS="$LOCAL_DIR/ollama"

# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------
PASS=0
FAIL=0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
check_pass() {
    local label="$1"
    local detail="${2:-}"
    printf "  [PASS] %-52s %s\n" "$label" "$detail"
    PASS=$((PASS + 1))
}

check_fail() {
    local label="$1"
    local detail="${2:-}"
    printf "  [FAIL] %-52s %s\n" "$label" "$detail"
    FAIL=$((FAIL + 1))
}

dir_size() {
    # Returns human-readable size of a directory, or "0B" if empty/missing
    du -sh "$1" 2>/dev/null | cut -f1 || echo "0B"
}

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
echo ""
echo "======================================================================"
echo "  Atlas Offline Verification"
echo "======================================================================"
echo "  Project root : $ATLAS_ROOT"
echo "  Local storage: $LOCAL_DIR"
echo ""

# ---------------------------------------------------------------------------
# Section 1 — .local/ directory structure
# ---------------------------------------------------------------------------
echo "--- Directory structure ---"

REQUIRED_DIRS=(
    "ollama"
    "mlx/whisper"
    "mlx/vlm"
    "mlx/audio"
    "data/postgres"
    "data/redis"
    "uploads"
    "inbox"
    "embeddings"
    "tmp"
)

for rel_dir in "${REQUIRED_DIRS[@]}"; do
    full_path="$LOCAL_DIR/$rel_dir"
    if [ -d "$full_path" ]; then
        check_pass ".local/$rel_dir" "($(dir_size "$full_path"))"
    else
        check_fail ".local/$rel_dir" "directory missing"
    fi
done

# ---------------------------------------------------------------------------
# Section 2 — Ollama models
# ---------------------------------------------------------------------------
echo ""
echo "--- Ollama models (OLLAMA_MODELS=$LOCAL_DIR/ollama) ---"

REQUIRED_OLLAMA_MODELS=(
    "gemma4:26b"
    "gemma4"
    "nomic-embed-text"
)

if ! command -v ollama &>/dev/null; then
    check_fail "ollama binary" "not found in PATH"
else
    check_pass "ollama binary" "($(ollama --version 2>/dev/null | head -1 || echo 'version unknown'))"

    # Ollama must be running to list models
    if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "  [WARN] Ollama is not running — starting temporarily for model check..."
        OLLAMA_MODELS="$LOCAL_DIR/ollama" ollama serve >/dev/null 2>&1 &
        OLLAMA_TEMP_PID=$!
        WAIT=0
        until curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; do
            sleep 1
            WAIT=$((WAIT + 1))
            if [ "$WAIT" -ge 15 ]; then
                echo "  [WARN] Ollama did not start within 15 s — skipping model checks"
                kill "$OLLAMA_TEMP_PID" 2>/dev/null || true
                OLLAMA_TEMP_PID=""
                break
            fi
        done
    fi

    if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        OLLAMA_LIST="$(OLLAMA_MODELS="$LOCAL_DIR/ollama" ollama list 2>/dev/null || echo "")"
        for model in "${REQUIRED_OLLAMA_MODELS[@]}"; do
            # Match model name prefix (e.g. "gemma4:26b" in list output)
            if echo "$OLLAMA_LIST" | grep -qF "$model"; then
                check_pass "ollama: $model"
            else
                check_fail "ollama: $model" "not in OLLAMA_MODELS dir — run setup.sh"
            fi
        done
    else
        for model in "${REQUIRED_OLLAMA_MODELS[@]}"; do
            check_fail "ollama: $model" "cannot verify (Ollama not running)"
        done
    fi

    # Clean up temp Ollama process if we started one
    if [ -n "${OLLAMA_TEMP_PID:-}" ]; then
        kill "$OLLAMA_TEMP_PID" 2>/dev/null || true
    fi
fi

# ---------------------------------------------------------------------------
# Section 3 — MLX model caches
# ---------------------------------------------------------------------------
echo ""
echo "--- MLX model caches (.local/mlx/) ---"

# Whisper: populated after first audio inference
if [ -d "$LOCAL_DIR/mlx/whisper" ] && [ -n "$(ls -A "$LOCAL_DIR/mlx/whisper" 2>/dev/null)" ]; then
    check_pass "mlx/whisper (lightning-whisper-mlx)" "($(dir_size "$LOCAL_DIR/mlx/whisper"))"
else
    # Not a hard failure at setup time — downloads on first use
    printf "  [NOTE] %-52s %s\n" "mlx/whisper" "empty (downloads on first audio ingest)"
fi

# VLM: populated after first vision inference
if [ -d "$LOCAL_DIR/mlx/vlm" ] && [ -n "$(ls -A "$LOCAL_DIR/mlx/vlm" 2>/dev/null)" ]; then
    check_pass "mlx/vlm (mlx-vlm vision)" "($(dir_size "$LOCAL_DIR/mlx/vlm"))"
else
    printf "  [NOTE] %-52s %s\n" "mlx/vlm" "empty (downloads on first vision ingest)"
fi

# ---------------------------------------------------------------------------
# Section 4 — JavaScript dependencies
# ---------------------------------------------------------------------------
echo ""
echo "--- JavaScript dependencies ---"

if [ -d "$ATLAS_ROOT/node_modules" ]; then
    check_pass "node_modules" "($(dir_size "$ATLAS_ROOT/node_modules"))"
else
    check_fail "node_modules" "missing — run: pnpm install --frozen-lockfile"
fi

# ---------------------------------------------------------------------------
# Section 5 — Python virtual environments
# ---------------------------------------------------------------------------
echo ""
echo "--- Python virtual environments ---"

for svc in api worker; do
    venv_path="$ATLAS_ROOT/services/$svc/.venv"
    if [ -d "$venv_path" ]; then
        check_pass "services/$svc/.venv" "($(dir_size "$venv_path"))"
    else
        check_fail "services/$svc/.venv" "missing — run: cd services/$svc && uv sync"
    fi
done

# ---------------------------------------------------------------------------
# Section 6 — Docker images
# ---------------------------------------------------------------------------
echo ""
echo "--- Docker images ---"

REQUIRED_IMAGES=(
    "pgvector/pgvector:pg16"
    "redis:7-alpine"
)

if ! command -v docker &>/dev/null; then
    for img in "${REQUIRED_IMAGES[@]}"; do
        check_fail "docker: $img" "docker not found in PATH"
    done
else
    for img in "${REQUIRED_IMAGES[@]}"; do
        if docker image inspect "$img" >/dev/null 2>&1; then
            check_pass "docker: $img"
        else
            check_fail "docker: $img" "not cached — run: docker pull $img"
        fi
    done
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "======================================================================"
echo "  Summary"
echo "======================================================================"

TOTAL_LOCAL_SIZE="$(dir_size "$LOCAL_DIR")"
echo "  Total .local/ disk usage: $TOTAL_LOCAL_SIZE"
echo "  Checks passed: $PASS"
echo "  Checks failed: $FAIL"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo "  RESULT: PASS — Atlas is ready for offline operation."
    echo "  Start with: bash scripts/start.sh"
    echo ""
    exit 0
else
    echo "  RESULT: FAIL — $FAIL check(s) need attention."
    echo "  Fix the issues above, then re-run: bash scripts/verify-offline.sh"
    echo ""
    exit 1
fi
