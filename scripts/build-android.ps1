# Build the Android placeholder APK into dist\android\
# Requires Android Studio (JDK + Android SDK). This laptop had Flutter but no SDK/Java.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Project = Join-Path $Root "apps\runtimes\android\kotlin"
$OutDir = Join-Path $Root "dist\android"

$sdk = $env:ANDROID_HOME
if (-not $sdk) { $sdk = $env:ANDROID_SDK_ROOT }
if (-not $sdk) {
  $guess = Join-Path $env:LOCALAPPDATA "Android\Sdk"
  if (Test-Path $guess) { $sdk = $guess }
}

$java = $null
if ($env:JAVA_HOME -and (Test-Path (Join-Path $env:JAVA_HOME "bin\java.exe"))) {
  $java = Join-Path $env:JAVA_HOME "bin\java.exe"
} elseif (Get-Command java -ErrorAction SilentlyContinue) {
  $java = (Get-Command java).Source
}

if (-not $java -or -not $sdk) {
  Write-Host "Cannot build an APK on this machine yet."
  Write-Host "Install Android Studio (it includes a JDK and the Android SDK), then rerun:"
  Write-Host "  powershell -ExecutionPolicy Bypass -File .\scripts\build-android.ps1"
  Write-Host "The APK is a placeholder runtime (foreground notification + honest status)."
  Write-Host "It does not open files, Chrome, or the Windows assistant. Those stay Planned."
  exit 2
}

$local = Join-Path $Project "local.properties"
$sdkEscaped = $sdk -replace '\\', '\\'
Set-Content -Path $local -Value "sdk.dir=$($sdk -replace '\\', '/')" -Encoding ASCII

Set-Location $Project
if (-not (Test-Path (Join-Path $Project "gradle\wrapper\gradle-wrapper.jar"))) {
  Write-Host "Gradle wrapper JAR is missing. Open the kotlin folder in Android Studio once to generate it, or install Gradle and run: gradle wrapper"
  exit 3
}

& .\gradlew.bat assembleDebug --no-daemon
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$apk = Join-Path $Project "app\build\outputs\apk\debug\app-debug.apk"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
Copy-Item $apk (Join-Path $OutDir "appi-android-placeholder-debug.apk") -Force
Write-Host "APK: $(Join-Path $OutDir 'appi-android-placeholder-debug.apk')"
Write-Host "This APK is a placeholder. Pairing a full Android agent is not available in this milestone."
