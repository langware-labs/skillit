#!/bin/bash
# ============================================================================
# Skillit Plugin Uninstaller
# Removes the plugin from Claude Code
# ============================================================================

set -e

PLUGIN_NAME="skillit"
MARKETPLACE_NAME="local-dev"

echo "Uninstalling $PLUGIN_NAME plugin..."

# Check if claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "Error: Claude Code CLI not found in PATH."
    exit 1
fi

# Uninstall the plugin
if claude plugin list 2>/dev/null | grep -q "$PLUGIN_NAME@$MARKETPLACE_NAME"; then
    claude plugin uninstall "$PLUGIN_NAME@$MARKETPLACE_NAME"
    echo "Plugin uninstalled successfully."
else
    echo "Plugin '$PLUGIN_NAME@$MARKETPLACE_NAME' is not installed."
fi

echo ""
echo "Uninstallation complete!"
echo ""
echo "Note: The marketplace '$MARKETPLACE_NAME' is still registered."
echo "To remove it: claude plugin marketplace remove $MARKETPLACE_NAME"
