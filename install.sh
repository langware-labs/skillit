#!/bin/bash
# ============================================================================
# Skillit Plugin Installer
# Cross-platform installation script for Claude Code plugin
# Uses the official CLI marketplace approach
# ============================================================================

set -e

PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_NAME="skillit"
PARENT_DIR="$(dirname "$PLUGIN_DIR")"
MARKETPLACE_DIR="$PARENT_DIR/.claude-plugin"
MARKETPLACE_FILE="$MARKETPLACE_DIR/marketplace.json"
MARKETPLACE_NAME="local-dev"

echo "Installing $PLUGIN_NAME plugin..."
echo "Plugin directory: $PLUGIN_DIR"

# Check if claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "Error: Claude Code CLI not found in PATH."
    echo "Please install Claude Code first: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
fi

# Create marketplace.json if it doesn't exist
if [[ ! -f "$MARKETPLACE_FILE" ]]; then
    echo "Creating marketplace.json..."
    mkdir -p "$MARKETPLACE_DIR"
    cat > "$MARKETPLACE_FILE" << EOF
{
  "name": "$MARKETPLACE_NAME",
  "description": "Local development plugins",
  "owner": {
    "name": "local"
  },
  "plugins": [
    {
      "name": "$PLUGIN_NAME",
      "source": "./$PLUGIN_NAME",
      "description": "Appends text to prompts based on keyword mappings",
      "version": "1.0.0"
    }
  ]
}
EOF
    echo "Created marketplace at: $MARKETPLACE_FILE"
else
    echo "Marketplace already exists at: $MARKETPLACE_FILE"
    # Check if plugin is already in marketplace
    if ! grep -q "\"name\": \"$PLUGIN_NAME\"" "$MARKETPLACE_FILE"; then
        echo "Warning: Plugin '$PLUGIN_NAME' not found in marketplace.json"
        echo "Please add it manually or delete $MARKETPLACE_FILE and re-run this script."
    fi
fi

# Add marketplace if not already added
echo "Adding marketplace..."
if claude plugin marketplace list 2>/dev/null | grep -q "$MARKETPLACE_NAME"; then
    echo "Marketplace '$MARKETPLACE_NAME' already registered, updating..."
    claude plugin marketplace update "$MARKETPLACE_NAME" || true
else
    claude plugin marketplace add "$PARENT_DIR"
fi

# Install the plugin at user level
echo "Installing plugin..."
claude plugin install "$PLUGIN_NAME@$MARKETPLACE_NAME" --scope user

echo ""
echo "Installation complete!"
echo ""
echo "Test with: claude -p \"skillit test\""
echo "Uninstall with: ./uninstall.sh"
