#!/usr/bin/env bash
set -euo pipefail
# Lightweight deterministic hook.
# Do not fail the session for missing files.
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
if [ -d "$PROJECT_DIR/vault" ]; then
  find "$PROJECT_DIR/vault" -maxdepth 2 -type f -name '*.md' | head -n 5 >/dev/null || true
fi
exit 0
