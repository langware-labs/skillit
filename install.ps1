# ============================================================================
# Skillit Plugin Installer for Windows
# Dynamic installation script for Claude Code plugin
# Automatically reads plugin.json and creates marketplace
# ============================================================================

$ErrorActionPreference = "Stop"

$PluginDir = $PSScriptRoot
$ParentDir = Split-Path -Parent $PluginDir
$PluginJson = Join-Path $PluginDir ".claude-plugin\plugin.json"

# Check if plugin.json exists
if (-not (Test-Path $PluginJson)) {
    Write-Error "Error: plugin.json not found at $PluginJson"
    exit 1
}

# Read plugin.json
$PluginData = Get-Content $PluginJson -Raw | ConvertFrom-Json

$PluginName = $PluginData.name
$PluginVersion = $PluginData.version
$PluginDescription = $PluginData.description
$PluginAuthor = if ($PluginData.author.name) { $PluginData.author.name } else { "local" }

if (-not $PluginName) {
    Write-Error "Error: Plugin name not found in plugin.json"
    exit 1
}

$MarketplaceName = "local-dev"
$MarketplaceDir = Join-Path $ParentDir ".claude-plugin"
$MarketplaceFile = Join-Path $MarketplaceDir "marketplace.json"

Write-Host "Installing plugin: $PluginName v$PluginVersion"
Write-Host "Description: $PluginDescription"
Write-Host "Plugin directory: $PluginDir"
Write-Host ""

# Check if claude CLI is available
if (-not (Get-Command "claude" -ErrorAction SilentlyContinue)) {
    Write-Error "Error: Claude Code CLI not found in PATH."
    Write-Host "Please install Claude Code first: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
}

# Generate marketplace.json dynamically from plugin.json
Write-Host "Creating marketplace.json..."
if (-not (Test-Path $MarketplaceDir)) {
    New-Item -ItemType Directory -Path $MarketplaceDir -Force | Out-Null
}

$NewPlugin = @{
    name = $PluginName
    source = "./$PluginName"
    description = $PluginDescription
    version = $PluginVersion
}

# If marketplace already exists, preserve other plugins
if (Test-Path $MarketplaceFile) {
    $ExistingMarketplace = Get-Content $MarketplaceFile -Raw | ConvertFrom-Json
    $ExistingPlugins = @($ExistingMarketplace.plugins | Where-Object { $_.name -ne $PluginName })
    $AllPlugins = @($ExistingPlugins) + @($NewPlugin)
} else {
    $AllPlugins = @($NewPlugin)
}

$Marketplace = @{
    name = $MarketplaceName
    description = "Local development plugins"
    owner = @{
        name = $PluginAuthor
    }
    plugins = $AllPlugins
}

$JsonContent = $Marketplace | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($MarketplaceFile, $JsonContent, [System.Text.UTF8Encoding]::new($false))
Write-Host "Marketplace updated at: $MarketplaceFile"

# Add marketplace if not already added
Write-Host ""
Write-Host "Adding marketplace..."
$MarketplaceList = claude plugin marketplace list 2>$null
if ($MarketplaceList -match $MarketplaceName) {
    Write-Host "Marketplace '$MarketplaceName' already registered, updating..."
    claude plugin marketplace update $MarketplaceName 2>$null
} else {
    Push-Location $ParentDir
    try {
        claude plugin marketplace add "./"
    } finally {
        Pop-Location
    }
}

# Install the plugin at user level
Write-Host ""
Write-Host "Installing plugin..."
claude plugin install "$PluginName@$MarketplaceName" --scope user

$InstallPath = Join-Path $env:USERPROFILE ".claude\plugins\cache\$MarketplaceName\$PluginName\$PluginVersion"

# Resolve $CLAUDE_PLUGIN_ROOT in hooks.json to absolute path (Claude Code doesn't expand it on Windows)
$HooksFile = Join-Path $InstallPath "hooks\hooks.json"
if (Test-Path $HooksFile) {
    $HooksContent = Get-Content $HooksFile -Raw
    $ResolvedPath = $InstallPath.Replace('\', '/')
    $HooksContent = $HooksContent.Replace('${CLAUDE_PLUGIN_ROOT}', $ResolvedPath)
    $HooksContent = $HooksContent.Replace('$CLAUDE_PLUGIN_ROOT', $ResolvedPath)
    $HooksContent = $HooksContent.Replace('%CLAUDE_PLUGIN_ROOT%', $ResolvedPath)
    [System.IO.File]::WriteAllText($HooksFile, $HooksContent, [System.Text.UTF8Encoding]::new($false))
    Write-Host "Patched hooks.json with resolved paths: $ResolvedPath"
}

# Clean up log file from installation directory
$LogFile = Join-Path $InstallPath "skill.log"

if (Test-Path $LogFile) {
    Write-Host ""
    Write-Host "Cleaning up log file..."
    Remove-Item $LogFile -Force
    Write-Host "Deleted: $LogFile"
}

Write-Host ""
Write-Host "============================================"
Write-Host "Installation complete!"
Write-Host "============================================"
Write-Host ""
Write-Host "Test with: claude -p `"$PluginName test`""
Write-Host "Uninstall with: .\uninstall.ps1"
Write-Host ""
