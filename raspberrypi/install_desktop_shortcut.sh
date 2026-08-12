#!/usr/bin/env bash
set -euo pipefail

BLANKY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BLANKY_MAIN="${BLANKY_MAIN:-main15.py}"
DESKTOP_DIR="$HOME/Desktop"
APP_DIR="$HOME/.local/share/applications"
ENV_DIR="$HOME/.blanky"
ENV_FILE="$ENV_DIR/openai.env"
DESKTOP_FILE="$DESKTOP_DIR/Blanky.desktop"
APP_FILE="$APP_DIR/Blanky.desktop"
RUNNER="$BLANKY_DIR/raspberrypi/run_blanky.sh"
ICON="$BLANKY_DIR/assets/blanky_logo_light.png"

mkdir -p "$DESKTOP_DIR" "$APP_DIR" "$ENV_DIR"
chmod +x "$RUNNER"

if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<'EOF'
# Paste your OpenAI API key below. Keep this file private.
OPENAI_API_KEY=""
EOF
    chmod 600 "$ENV_FILE"
fi

cat > "$APP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Blanky
Comment=Blanky industrial voice assistant
Exec=env BLANKY_DIR=$BLANKY_DIR BLANKY_MAIN=$BLANKY_MAIN $RUNNER
Icon=$ICON
Path=$BLANKY_DIR
Terminal=false
Categories=Utility;
StartupNotify=true
EOF

cp "$APP_FILE" "$DESKTOP_FILE"
chmod +x "$APP_FILE" "$DESKTOP_FILE"

echo "Blanky shortcut installed:"
echo "  $DESKTOP_FILE"
echo "Private API key file:"
echo "  $ENV_FILE"
