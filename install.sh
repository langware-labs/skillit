#!/bin/bash
# Skillit Plugin Installer
set -e

USE_SYMLINK=$( [ "$1" = "--symlink" ] || [ "$1" = "-s" ] && echo true || echo false )

cd "$(dirname "$0")"
SOURCE_DIR="$(pwd)"

PLUGIN_NAME=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['name'])")
PLUGIN_VERSION=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])")
MARKETPLACE_NAME=$(python3 -c "import json; print(json.load(open('.claude-plugin/marketplace.json'))['name'])")

echo "Installing $PLUGIN_NAME@$MARKETPLACE_NAME v$PLUGIN_VERSION$( [ "$USE_SYMLINK" = true ] && echo " (symlink)" )..."

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

CACHE_DIR="$HOME/.claude/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$PLUGIN_VERSION"

# Replace cache copy with content symlinks if requested, otherwise clean up log file
if [ "$USE_SYMLINK" = true ] && [ -d "$CACHE_DIR" ]; then
    # Keep cache as a real directory (Claude Code replaces top-level symlinks),
    # but symlink each item inside it back to the source
    rm -rf "$CACHE_DIR"
    mkdir -p "$CACHE_DIR"
    for item in "$SOURCE_DIR"/* "$SOURCE_DIR"/.[!.]*; do
        [ -e "$item" ] || [ -L "$item" ] && ln -s "$item" "$CACHE_DIR/"
    done
    echo "Created content symlinks: $CACHE_DIR/* -> $SOURCE_DIR/*"
elif [ "$USE_SYMLINK" = false ]; then
    rm -f "$CACHE_DIR/skill.log" 2>/dev/null || true
fi

echo "Done! Test with: claude -p \"$PLUGIN_NAME test\""
