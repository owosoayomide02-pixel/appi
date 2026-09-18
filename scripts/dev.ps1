# Developer consoles for APPI.
# Prefer scripts\preview-windows.ps1 for the normal desktop app.
#
#   .\scripts\dev.ps1 -Api
#   .\scripts\dev.ps1 -Web
#   .\scripts\dev.ps1 -Agent
#   .\scripts\dev.ps1 -All

param(
  [switch]$Api,
  [switch]$Web,
  [switch]$Agent,
  [switch]$All
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env"
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

function Get-DotEnvValue([string]$Path, [string]$Key, [string]$Default) {
  if (-not (Test-Path $Path)) { return $Default }
  $line = Get-Content $Path -ErrorAction SilentlyContinue |
    Where-Object { $_ -match ("^\s*" + [regex]::Escape($Key) + "\s*=") } |
    Select-Object -First 1
  if (-not $line) { return $Default }
  $value = ($line -split "=", 2)[1].Trim()
  if (-not $value) { return $Default }
  return $value
}

if (-not (Test-Path $envFile)) {
  Write-Host "No .env found. Run: powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1"
  exit 1
}

$apiHost = Get-DotEnvValue $envFile "API_HOST" "127.0.0.1"
$apiPort = Get-DotEnvValue $envFile "API_PORT" "8000"
$appUrl = Get-DotEnvValue $envFile "APP_URL" "http://localhost:3000"

if ($All) {
  $Api = $true
  $Web = $true
  $Agent = $true
}

$started = $false

if ($Api) {
  $started = $true
  Write-Host "API → http://${apiHost}:${apiPort}  (from .env)"
  $args = "-m uvicorn app.main:app --reload --host $apiHost --port $apiPort"
  Start-Process -FilePath $py -ArgumentList $args -WorkingDirectory (Join-Path $root "services\api")
}

if ($Web) {
  $started = $true
  Write-Host "Web → $appUrl  (operator: /app)"
  Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory (Join-Path $root "apps\web")
}

if ($Agent) {
  $started = $true
  Write-Host "Device agent (serve) → brain at $(Get-DotEnvValue $envFile 'DEVICE_AGENT_API_URL' 'http://127.0.0.1:8000')"
  Start-Process -FilePath $py -ArgumentList "-m app.main serve" -WorkingDirectory (Join-Path $root "apps\device-agent")
}

if (-not $started) {
  Write-Host "Usage:"
  Write-Host "  .\scripts\dev.ps1 -Api"
  Write-Host "  .\scripts\dev.ps1 -Web"
  Write-Host "  .\scripts\dev.ps1 -Agent"
  Write-Host "  .\scripts\dev.ps1 -All"
  Write-Host ""
  Write-Host "Env file: $envFile"
  Write-Host "Desktop app (no consoles): .\scripts\preview-windows.ps1"
}
