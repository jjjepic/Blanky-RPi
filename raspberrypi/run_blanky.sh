#!/usr/bin/env bash
set -euo pipefail

BLANKY_DIR="${BLANKY_DIR:-/home/jorge/Blanky15}"
BLANKY_MAIN="${BLANKY_MAIN:-main15.py}"
ENV_FILE="${BLANKY_ENV_FILE:-$HOME/.blanky/openai.env}"

cd "$BLANKY_DIR"

if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$ENV_FILE"
    set +a
fi

if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "OPENAI_API_KEY is missing. Add it to $ENV_FILE"
    if command -v zenity >/dev/null 2>&1; then
        zenity --error --title="Blanky" --text="OPENAI_API_KEY is missing. Add it to $ENV_FILE"
    fi
    exit 1
fi

if [ -f "venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    . "venv/bin/activate"
fi

exec python "$BLANKY_MAIN"
