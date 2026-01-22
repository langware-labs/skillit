#!/bin/bash
# ============================================================================
# Skillit Plugin Installer
# Dynamic installation script for Claude Code plugin
# Automatically reads plugin.json and creates marketplace
# ============================================================================

set -e

PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
PARENT_DIR="$(dirname "$PLUGIN_DIR")"
PLUGIN_JSON="$PLUGIN_DIR/.claude-plugin/plugin.json"

# Check if plugin.json exists
if [[ ! -f "$PLUGIN_JSON" ]]; then
    echo "Error: plugin.json not found at $PLUGIN_JSON"
    exit 1
fi

# Extract plugin metadata dynamically using python
read_plugin_json() {
    python3 -c "
import json, sys
with open('$PLUGIN_JSON') as f:
    data = json.load(f)
    print(data.get('$1', ''))
"
}

PLUGIN_NAME=$(read_plugin_json "name")
PLUGIN_VERSION=$(read_plugin_json "version")
PLUGIN_DESCRIPTION=$(read_plugin_json "description")
PLUGIN_AUTHOR=$(python3 -c "import json; data=json.load(open('$PLUGIN_JSON')); print(data.get('author', {}).get('name', 'local'))")

if [[ -z "$PLUGIN_NAME" ]]; then
    echo "Error: Plugin name not found in plugin.json"
    exit 1
fi

MARKETPLACE_NAME="local-dev"
MARKETPLACE_DIR="$PARENT_DIR/.claude-plugin"
MARKETPLACE_FILE="$MARKETPLACE_DIR/marketplace.json"

echo "Installing plugin: $PLUGIN_NAME v$PLUGIN_VERSION"
echo "Description: $PLUGIN_DESCRIPTION"
echo "Plugin directory: $PLUGIN_DIR"
echo ""

# Check if claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "Error: Claude Code CLI not found in PATH."
    echo "Please install Claude Code first: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
fi

# Generate marketplace.json dynamically from plugin.json
echo "Creating marketplace.json..."
mkdir -p "$MARKETPLACE_DIR"

python3 << EOF
import json

marketplace = {
    "name": "$MARKETPLACE_NAME",
    "description": "Local development plugins",
    "owner": {
        "name": "$PLUGIN_AUTHOR"
    },
    "plugins": [
        {
            "name": "$PLUGIN_NAME",
            "source": "./$PLUGIN_NAME",
            "description": "$PLUGIN_DESCRIPTION",
            "version": "$PLUGIN_VERSION"
        }
    ]
}

# If marketplace already exists, preserve other plugins
try:
    with open("$MARKETPLACE_FILE", 'r') as f:
        existing = json.load(f)
        # Remove this plugin if it exists
        existing_plugins = [p for p in existing.get('plugins', []) if p.get('name') != "$PLUGIN_NAME"]
        # Add our plugin
        existing_plugins.append(marketplace['plugins'][0])
        marketplace['plugins'] = existing_plugins
except FileNotFoundError:
    pass

with open("$MARKETPLACE_FILE", 'w') as f:
    json.dump(marketplace, f, indent=2)

print(f"Marketplace updated at: $MARKETPLACE_FILE")
EOF

# Add marketplace if not already added
echo ""
echo "Adding marketplace..."
if claude plugin marketplace list 2>/dev/null | grep -q "$MARKETPLACE_NAME"; then
    echo "Marketplace '$MARKETPLACE_NAME' already registered, updating..."
    claude plugin marketplace update "$MARKETPLACE_NAME" || true
else
    claude plugin marketplace add "$PARENT_DIR"
fi

# Install the plugin at user level
echo ""
echo "Installing plugin..."
claude plugin install "$PLUGIN_NAME@$MARKETPLACE_NAME" --scope user

# Clean up log file from installation directory
INSTALL_PATH="$HOME/.claude/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$PLUGIN_VERSION"
LOG_FILE="$INSTALL_PATH/skill.log"

if [[ -f "$LOG_FILE" ]]; then
    echo ""
    echo "Cleaning up log file..."
    rm -f "$LOG_FILE"
    echo "Deleted: $LOG_FILE"
fi

echo ""
echo "============================================"
echo "Installation complete!"
echo "============================================"
echo ""
echo "Test with: claude -p \"$PLUGIN_NAME test\""
echo "Uninstall with: ./uninstall.sh"
echo ""
