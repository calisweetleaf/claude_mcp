# Claude MCP Server - HTTP/SSE Mode Launcher
# PowerShell script for Windows users

param(
 [string]$Host = "0.0.0.0",
 [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerScript = Join-Path $ScriptDir "mcp_server.py"

# Check if server script exists
if (-not (Test-Path $ServerScript)) {
 Write-Error "Error: mcp_server.py not found in $ScriptDir"
 exit 1
}

# Display information
Write-Host "Claude MCP Server - HTTP/SSE Mode" -ForegroundColor Green
Write-Host "=" * 40
Write-Host "Starting server on $Host`:$Port" -ForegroundColor Yellow
Write-Host ""
Write-Host "Integration Instructions:" -ForegroundColor Cyan
Write-Host "1. Open Claude Desktop"
Write-Host "2. Go to Settings > Integrations"
Write-Host "3. Click 'Add more' or 'Custom Integration'"
Write-Host "4. Enter URL: http://$Host`:$Port/mcp/sse" -ForegroundColor Yellow
Write-Host "5. Save and restart Claude Desktop"
Write-Host ""
Write-Host "Available endpoints:" -ForegroundColor Cyan
Write-Host "  • Server info: http://$Host`:$Port/"
Write-Host "  • Health check: http://$Host`:$Port/health"
Write-Host "  • Tools list: http://$Host`:$Port/mcp/tools"
Write-Host "  • SSE endpoint: http://$Host`:$Port/mcp/sse" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Red
Write-Host "-" * 40

try {
 # Set environment variables
 $env:MCP_HOST = $Host
 $env:MCP_PORT = $Port
    
 # Start the server
 & python $ServerScript --http --host $Host --port $Port
}
catch {
 Write-Error "Server error: $_"
 exit 1
}
finally {
 Write-Host "`nServer stopped" -ForegroundColor Red
}
