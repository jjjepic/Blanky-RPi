#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_BLANKY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BLANKY_DIR="${BLANKY_DIR:-$DEFAULT_BLANKY_DIR}"
BLANKY_MAIN="${BLANKY_MAIN:-main.py}"
ENV_FILE="${BLANKY_ENV_FILE:-$HOME/.blanky/openai.env}"

cd "$BLANKY_DIR"

if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$ENV_FILE"
    set +a
fi

if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "OPENAI_API_KEY is missing. Blanky will start with Online features unavailable."
fi

if [ -f "venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    . "venv/bin/activate"
fi

exec python "$BLANKY_MAIN"
