# Build the Windows assistant into dist\windows\Appi\
# Output: Appi.exe + README.txt (pair to the website operator at /app)
#
#   powershell -ExecutionPolicy Bypass -File .\scripts\build-windows.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

Write-Host "Installing PyInstaller extras..."
& $py -m pip install --quiet pyinstaller pystray pillow pywebview

$dist = Join-Path $Root "dist\windows"
$work = Join-Path $dist "work"
New-Item -ItemType Directory -Force -Path $dist | Out-Null

& $py -m PyInstaller --noconfirm --clean --distpath $dist --workpath $work (Join-Path $Root "packaging\windows\appi.spec")

$out = Join-Path $dist "Appi"
$exe = Join-Path $out "Appi.exe"
if (-not (Test-Path $exe)) {
  throw "Appi.exe was not produced at $exe"
}

$readmeSrc = Join-Path $Root "packaging\windows\README.txt"
Copy-Item $readmeSrc (Join-Path $out "README.txt") -Force

$envSrc = Join-Path $Root "packaging\windows\dotenv.production"
Copy-Item $envSrc (Join-Path $out ".env") -Force

# Zip for distribution
$zip = Join-Path $dist "Appi-windows.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
# Zip the Appi folder itself so unzip yields Appi\Appi.exe (clear path)
Compress-Archive -Path $out -DestinationPath $zip -Force

Write-Host ""
Write-Host "Windows assistant: $exe"
Write-Host "Zip package:       $zip"
Write-Host ""
Write-Host "Install / pair:"
Write-Host "  1. Unzip anywhere (not as Administrator)."
Write-Host "  2. Double-click Appi.exe - desktop window opens (no CMD)."
Write-Host "  3. Pair with a code from https://appi-project01.netlify.app/device"
Write-Host "  4. Or:  .\Appi.exe pair --code 123456"
Write-Host "  Operator UI: https://appi-project01.netlify.app/app"
Write-Host "  Autostart:   .\Appi.exe autostart on"
