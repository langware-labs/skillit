#!/bin/sh
# Skillit — one-liner installer for macOS / Linux
# Usage: curl -LsSf https://raw.githubusercontent.com/langware-labs/skillit/main/get-skillit.sh | sh
set -e

REPO="langware-labs/skillit"
PLUGIN="skillit"
MARKETPLACE="flowpad-ai"

# ---------- helpers ----------
info()  { printf '\033[1;34m[skillit]\033[0m %s\n' "$*"; }
ok()    { printf '\033[1;32m[skillit]\033[0m %s\n' "$*"; }
warn()  { printf '\033[1;33m[skillit]\033[0m %s\n' "$*"; }
err()   { printf '\033[1;31m[skillit]\033[0m %s\n' "$*" >&2; }

# ---------- detect OS ----------
OS="$(uname -s)"
case "$OS" in
  Darwin) info "Detected macOS" ;;
  Linux)  info "Detected Linux" ;;
  *)      warn "Unsupported OS: $OS — continuing anyway" ;;
esac

# ---------- check claude CLI ----------
if ! command -v claude >/dev/null 2>&1; then
  err "Claude Code CLI not found."
  echo ""
  echo "  Install it first:"
  echo "    npm install -g @anthropic-ai/claude-code"
  echo ""
  echo "  More info: https://docs.anthropic.com/en/docs/claude-code"
  exit 1
fi
info "Found claude CLI: $(command -v claude)"

# ---------- check uv ----------
if ! command -v uv >/dev/null 2>&1; then
  warn "uv not found. skillit uses uv to manage its Python dependencies."
  echo ""
  echo "  Install uv:"
  echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"
  echo "  or:"
  echo "    pip install uv"
  echo ""
  echo "  More info: https://docs.astral.sh/uv/"
  exit 1
fi
info "Found uv: $(command -v uv)"

# ---------- add marketplace & install ----------
info "Adding marketplace ${REPO} ..."
claude plugin marketplace remove "$MARKETPLACE" 2>/dev/null || true
claude plugin marketplace add "$REPO"

info "Installing ${PLUGIN}@${MARKETPLACE} ..."
claude plugin install "${PLUGIN}@${MARKETPLACE}" --scope user

# ---------- done ----------
echo ""
ok "skillit installed successfully!"
echo ""
echo "  Test it:      claude -p \"skillit test\""
echo "  Uninstall:    claude plugin uninstall ${PLUGIN}@${MARKETPLACE}"
echo ""
