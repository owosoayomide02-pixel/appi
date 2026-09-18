# Start Appi on this Windows laptop as a desktop app (no extra consoles).
#
#   powershell -ExecutionPolicy Bypass -File .\scripts\preview-windows.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "services\api"))) {
  $Root = Resolve-Path (Join-Path $PSScriptRoot "..")
}

$envFile = Join-Path $Root ".env"
if (-not (Test-Path $envFile)) {
  Write-Host "No .env yet — running setup first..."
  & powershell -ExecutionPolicy Bypass -File (Join-Path $Root "scripts\setup.ps1")
}

$agent = Join-Path $Root "apps\device-agent"
$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
$pyw = Join-Path (Split-Path $py) "pythonw.exe"
if (-not (Test-Path $pyw)) { $pyw = $py }

Set-Location $agent

Write-Host "Installing tray extras if needed..."
& $py -m pip install --quiet pystray pillow

Write-Host "Creating Desktop and Start Menu shortcuts..."
& $py -m app.main install

Write-Host "Starting Appi. Use the Desktop Appi icon next time — no PowerShell needed."
Write-Host "Operator: http://localhost:3000/app"
Write-Host "Devices:  http://localhost:3000/device"
if ($pyw -like "*pythonw.exe") {
  Start-Process -FilePath $pyw -ArgumentList "-m app.launcher" -WorkingDirectory $agent -WindowStyle Hidden
} else {
  & $py -m app.launcher
}
