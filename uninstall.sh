#!/bin/bash
# ============================================================================
# Skillit Plugin Uninstaller
# Dynamically removes the plugin from Claude Code
# ============================================================================

set -e

PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_JSON="$PLUGIN_DIR/.claude-plugin/plugin.json"

# Check if plugin.json exists
if [[ ! -f "$PLUGIN_JSON" ]]; then
    echo "Error: plugin.json not found at $PLUGIN_JSON"
    exit 1
fi

# Extract plugin name dynamically
PLUGIN_NAME=$(python3 -c "import json; print(json.load(open('$PLUGIN_JSON')).get('name', ''))")

if [[ -z "$PLUGIN_NAME" ]]; then
    echo "Error: Plugin name not found in plugin.json"
    exit 1
fi

MARKETPLACE_NAME="local-dev"
CACHE_DIR="$HOME/.claude/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME"

echo "Uninstalling plugin: $PLUGIN_NAME"
echo ""

# Check if claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "Error: Claude Code CLI not found in PATH."
    exit 1
fi

# Uninstall via CLI (removes from installed_plugins.json)
if claude plugin uninstall "$PLUGIN_NAME@$MARKETPLACE_NAME" 2>/dev/null; then
    echo "Plugin uninstalled from Claude Code."
fi

# Clean up the cache directory (CLI bug: doesn't clean cache for local-dev marketplaces)
if [ -d "$CACHE_DIR" ]; then
    rm -rf "$CACHE_DIR"
    echo "Plugin cache removed."
fi

echo ""
echo "============================================"
echo "Uninstallation complete!"
echo "============================================"
echo ""
echo "To reinstall: ./install.sh"
echo ""
