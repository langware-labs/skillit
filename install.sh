#!/bin/bash
# Skillit Plugin Installer
set -e

cd "$(dirname "$0")"

PLUGIN_NAME=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['name'])")
PLUGIN_VERSION=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])")
MARKETPLACE_NAME=$(python3 -c "import json; print(json.load(open('.claude-plugin/marketplace.json'))['name'])")

echo "Installing $PLUGIN_NAME@$MARKETPLACE_NAME v$PLUGIN_VERSION..."

# Check if claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "Error: Claude Code CLI not found."
    exit 1
fi

# Uninstall existing version first (for clean reinstall)
claude plugin uninstall "$PLUGIN_NAME@$MARKETPLACE_NAME" 2>/dev/null || true

# Remove and re-add marketplace to ensure it points to local directory
claude plugin marketplace remove "$MARKETPLACE_NAME" 2>/dev/null || true
claude plugin marketplace add ./

# Install from local marketplace
claude plugin install "$PLUGIN_NAME@$MARKETPLACE_NAME" --scope user

# Clean up log file
LOG_FILE="$HOME/.claude/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$PLUGIN_VERSION/skill.log"
rm -f "$LOG_FILE" 2>/dev/null || true

echo "Done! Test with: claude -p \"$PLUGIN_NAME test\""
