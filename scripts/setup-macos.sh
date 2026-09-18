#!/usr/bin/env bash
# Install the Appi desktop runtime on macOS (files, terminal, browser).
# Native TCC / App Intents / say-Appi wake word are not implemented yet.
# Run this file on a Mac, not on Windows.

set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This setup must be run on macOS. On Windows use scripts/preview-windows.ps1"
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT="$ROOT/apps/device-agent"
PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Install Python 3.11+ first (python3 not found). python.org or: brew install python"
  exit 3
fi

echo "Installing Appi device-agent dependencies..."
"$PYTHON" -m pip install --user -e "$AGENT"
"$PYTHON" -m pip install --user httpx websockets pydantic-settings playwright

PLIST_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$PLIST_DIR"
PLIST="$PLIST_DIR/dev.appi.runtime.plist"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>dev.appi.runtime</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON</string>
    <string>-m</string>
    <string>app.main</string>
    <string>serve</string>
    <string>--no-voice</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$AGENT</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$HOME/Library/Logs/appi-runtime.log</string>
  <key>StandardErrorPath</key>
  <string>$HOME/Library/Logs/appi-runtime.log</string>
</dict>
</plist>
EOF

echo "Wrote $PLIST"
launchctl unload "$PLIST" >/dev/null 2>&1 || true
launchctl load "$PLIST"
echo "LaunchAgent loaded: dev.appi.runtime"

(cd "$AGENT" && "$PYTHON" -m app.main autostart on) || true

echo
echo "macOS setup is ready. Native microphone / Accessibility / App Intents are not wired."
echo "Voice (say Appi) is Windows-only until a Mac speech backend exists."
echo "Pair from the dashboard, then:"
echo "  cd $AGENT"
echo "  $PYTHON -m app.main pair --code 123456"
echo "What works after pairing: files in approved folders, terminal, Playwright browser, app launch via PATH."
echo "What does not work yet: wake word, TCC-gated Apple APIs, contacts, payments, controlling other apps."
