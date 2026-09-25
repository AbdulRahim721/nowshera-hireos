# The browser frontend is served by server.mjs. Keep one predictable launcher
# so http://127.0.0.1:8000/ does not point at a different backend.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
Write-Host 'Starting Nowshera HireOS at http://127.0.0.1:8000/' -ForegroundColor Cyan
node .\server.mjs

