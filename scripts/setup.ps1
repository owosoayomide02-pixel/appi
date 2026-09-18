# One-time local setup for APPI (Windows).
# Creates .env, installs Python packages, and npm installs the website.
#
#   powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1

param(
  [switch]$SkipWeb,
  [switch]$SkipPython,
  [switch]$ForceEnv
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "APPI setup"
Write-Host "Root: $Root"

$envExample = Join-Path $Root ".env.example"
$envFile = Join-Path $Root ".env"
if (-not (Test-Path $envExample)) {
  throw ".env.example is missing at $envExample"
}

if ((-not (Test-Path $envFile)) -or $ForceEnv) {
  if ((Test-Path $envFile) -and $ForceEnv) {
    Copy-Item $envFile "$envFile.bak" -Force
    Write-Host "Backed up existing .env to .env.bak"
  }
  $bytes = New-Object byte[] 48
  [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
  $jwt = [Convert]::ToBase64String($bytes)
  $bytes2 = New-Object byte[] 48
  [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes2)
  $enc = [Convert]::ToBase64String($bytes2)

  $template = Get-Content $envExample -Raw
  $template = $template -replace "(?m)^JWT_SECRET=.*$", "JWT_SECRET=$jwt"
  $template = $template -replace "(?m)^ENCRYPTION_KEY=.*$", "ENCRYPTION_KEY=$enc"
  $template = $template -replace "(?m)^JWT_SECRET=change-me-to-a-long-random-string$", "JWT_SECRET=$jwt"
  $template = $template -replace "(?m)^ENCRYPTION_KEY=change-me-to-another-long-random-passphrase$", "ENCRYPTION_KEY=$enc"
  Set-Content -Path $envFile -Value $template -Encoding utf8
  Write-Host "Wrote .env (local secrets generated)."
} else {
  Write-Host ".env already exists (use -ForceEnv to regenerate)."
}

# Next.js only auto-loads .env from apps/web. Mirror the public vars there
# (next.config.ts also loads the repo-root .env for NEXT_PUBLIC_*).
$webEnv = Join-Path $Root "apps\web\.env.local"
$appUrl = "http://localhost:3000"
$apiUrl = "http://127.0.0.1:8000"
if (Test-Path $envFile) {
  $m = Select-String -Path $envFile -Pattern '^\s*APP_URL\s*=\s*(.+)$' | Select-Object -First 1
  if ($m) { $appUrl = $m.Matches[0].Groups[1].Value.Trim() }
  $m = Select-String -Path $envFile -Pattern '^\s*NEXT_PUBLIC_APP_URL\s*=\s*(.+)$' | Select-Object -First 1
  if ($m) { $appUrl = $m.Matches[0].Groups[1].Value.Trim() }
  $m = Select-String -Path $envFile -Pattern '^\s*NEXT_PUBLIC_API_URL\s*=\s*(.+)$' | Select-Object -First 1
  if ($m) { $apiUrl = $m.Matches[0].Groups[1].Value.Trim() }
}
@"
NEXT_PUBLIC_APP_URL=$appUrl
NEXT_PUBLIC_API_URL=$apiUrl
"@ | Set-Content -Path $webEnv -Encoding utf8
Write-Host "Wrote apps\web\.env.local (mirrors root .env public URLs)"

if (-not $SkipPython) {
  $py = Join-Path $Root ".venv\Scripts\python.exe"
  if (-not (Test-Path $py)) {
    Write-Host "Creating .venv..."
    python -m venv (Join-Path $Root ".venv")
  }
  & $py -m pip install --upgrade pip
  & $py -m pip install -e "$(Join-Path $Root 'services\api')[dev]"
  & $py -m pip install -e "$(Join-Path $Root 'apps\device-agent')[dev]"
  Write-Host "Python packages installed."
}

if (-not $SkipWeb) {
  Push-Location (Join-Path $Root "apps\web")
  npm install
  Pop-Location
  Write-Host "Website dependencies installed."
}

Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Edit .env if you want an AI key (optional)."
Write-Host "  2. Desktop app:  powershell -ExecutionPolicy Bypass -File .\scripts\preview-windows.ps1"
Write-Host "  3. Or consoles:  .\scripts\dev.ps1 -Api   then   .\scripts\dev.ps1 -Web"
Write-Host "  4. Open http://localhost:3000  (site) or http://localhost:3000/app  (operator)"
Write-Host "  5. Windows exe:  powershell -ExecutionPolicy Bypass -File .\scripts\build-windows.ps1"
