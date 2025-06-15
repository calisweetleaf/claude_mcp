# Automatically activate the .venv for this Claude MCP server codebase
$venvPath = Join-Path $PSScriptRoot ".venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (Test-Path $activateScript) {
 Write-Host "Activating Claude MCP .venv..."
 & $activateScript
 if ($env:VIRTUAL_ENV) {
  Write-Host "✅ .venv activated: $env:VIRTUAL_ENV"
 }
 else {
  Write-Warning ".venv activation script ran, but VIRTUAL_ENV not set."
 }
}
else {
 Write-Warning ".venv not found at $venvPath. Please run 'python -m venv .venv' to create it."
}
