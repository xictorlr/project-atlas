#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LOG_DIR="$PROJECT_DIR/.claude/logs"
mkdir -p "$LOG_DIR"
DATE_STAMP="$(date +%Y%m%d-%H%M%S)"
echo "session_end $DATE_STAMP" >> "$LOG_DIR/session-events.log"
exit 0
