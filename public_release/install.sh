#!/usr/bin/env bash
set -e
echo "⚡ Installing Axiom Autonomous Engine (axiom-ai)..."

TARGET_DIR="/usr/local/bin"
if [ ! -w "$TARGET_DIR" ]; then
    SUDO="sudo"
else
    SUDO=""
fi

LATEST_URL="https://github.com/xstr3ss/axiom-ai/releases/latest/download/axiom"

echo "📥 Fetching binary from: $LATEST_URL"
$SUDO curl -fsSL "$LATEST_URL" -o "$TARGET_DIR/axiom"
$SUDO chmod +x "$TARGET_DIR/axiom"

echo ""
echo "✅ Axiom installed successfully!"
echo "🚀 Type 'axiom' to begin."
