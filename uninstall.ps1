# ============================================================================
# Skillit Plugin Uninstaller for Windows
# Dynamically removes the plugin from Claude Code
# ============================================================================

$ErrorActionPreference = "Stop"

$PluginDir = $PSScriptRoot
$PluginJson = Join-Path $PluginDir ".claude-plugin\plugin.json"

# Check if plugin.json exists
if (-not (Test-Path $PluginJson)) {
    Write-Error "Error: plugin.json not found at $PluginJson"
    exit 1
}

# Read plugin.json
$PluginData = Get-Content $PluginJson -Raw | ConvertFrom-Json
$PluginName = $PluginData.name

if (-not $PluginName) {
    Write-Error "Error: Plugin name not found in plugin.json"
    exit 1
}

$MarketplaceName = "local-dev"
$CacheDir = Join-Path $env:USERPROFILE ".claude\plugins\cache\$MarketplaceName\$PluginName"

Write-Host "Uninstalling plugin: $PluginName"
Write-Host ""

# Check if claude CLI is available
if (-not (Get-Command "claude" -ErrorAction SilentlyContinue)) {
    Write-Error "Error: Claude Code CLI not found in PATH."
    exit 1
}

# Uninstall via CLI (removes from installed_plugins.json)
try {
    claude plugin uninstall "$PluginName@$MarketplaceName" 2>$null
    Write-Host "Plugin uninstalled from Claude Code."
} catch {
    # Ignore errors if plugin wasn't installed
}

# Clean up the cache directory (CLI bug: doesn't clean cache for local-dev marketplaces)
if (Test-Path $CacheDir) {
    Remove-Item $CacheDir -Recurse -Force
    Write-Host "Plugin cache removed."
}

Write-Host ""
Write-Host "============================================"
Write-Host "Uninstallation complete!"
Write-Host "============================================"
Write-Host ""
Write-Host "To reinstall: .\install.ps1"
Write-Host ""
