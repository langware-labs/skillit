#!/bin/bash
# Skillit Plugin Uninstaller
set -e

cd "$(dirname "$0")"

PLUGIN_NAME=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['name'])")
MARKETPLACE_NAME=$(python3 -c "import json; print(json.load(open('.claude-plugin/marketplace.json'))['name'])")
CACHE_DIR="$HOME/.claude/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME"

echo "Uninstalling $PLUGIN_NAME@$MARKETPLACE_NAME..."

# Check if claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "Error: Claude Code CLI not found."
    exit 1
fi

# Uninstall plugin
claude plugin uninstall "$PLUGIN_NAME@$MARKETPLACE_NAME" 2>/dev/null || true

# Remove marketplace registration
claude plugin marketplace remove "$MARKETPLACE_NAME" 2>/dev/null || true

# Clean up cache
rm -rf "$CACHE_DIR" 2>/dev/null || true

echo "Done! To reinstall: ./install.sh"
