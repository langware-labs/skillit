# Skillit — one-liner installer for Windows
# Usage: powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/langware-labs/skillit/main/get-skillit.ps1 | iex"
$ErrorActionPreference = "Stop"

$Repo        = "langware-labs/skillit"
$Plugin      = "skillit"
$Marketplace = "flowpad-ai"

# ---------- helpers ----------
function Info  { param($Msg) Write-Host "[skillit] $Msg" -ForegroundColor Cyan }
function Ok    { param($Msg) Write-Host "[skillit] $Msg" -ForegroundColor Green }
function Warn  { param($Msg) Write-Host "[skillit] $Msg" -ForegroundColor Yellow }
function Err   { param($Msg) Write-Host "[skillit] $Msg" -ForegroundColor Red }

# ---------- check claude CLI ----------
if (-not (Get-Command "claude" -ErrorAction SilentlyContinue)) {
    Err "Claude Code CLI not found."
    Write-Host ""
    Write-Host "  Install it first:"
    Write-Host "    npm install -g @anthropic-ai/claude-code"
    Write-Host ""
    Write-Host "  More info: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
}
Info "Found claude CLI: $((Get-Command claude).Source)"

# ---------- check uv ----------
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Warn "uv not found. skillit uses uv to manage its Python dependencies."
    Write-Host ""
    Write-Host "  Install uv:"
    Write-Host "    powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
    Write-Host "  or:"
    Write-Host "    pip install uv"
    Write-Host ""
    Write-Host "  More info: https://docs.astral.sh/uv/"
    exit 1
}
Info "Found uv: $((Get-Command uv).Source)"

# ---------- add marketplace & install ----------
Info "Adding marketplace $Repo ..."
claude plugin marketplace remove $Marketplace 2>$null
claude plugin marketplace add $Repo

Info "Installing ${Plugin}@${Marketplace} ..."
claude plugin install "${Plugin}@${Marketplace}" --scope user

# ---------- done ----------
Write-Host ""
Ok "skillit installed successfully!"
Write-Host ""
Write-Host "  Test it:      claude -p `"skillit test`""
Write-Host "  Uninstall:    claude plugin uninstall ${Plugin}@${Marketplace}"
Write-Host ""
