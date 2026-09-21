#!/usr/bin/env bash
# Install the Appi desktop runtime on macOS (files, terminal, browser).
# Safe to download and run alone — clones the agent from GitHub if needed.
# Native TCC / App Intents / say-Appi wake word are not implemented yet.

set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This setup must be run on macOS. On Windows download Appi-windows.zip from the site."
  exit 2
fi

REPO="${APPI_GITHUB_REPO:-owosoayomide02-pixel/appi}"
BRANCH="${APPI_BRANCH:-main}"
INSTALL_ROOT="${APPI_HOME:-$HOME/.appi}"

resolve_agent() {
  # Running from a full checkout: scripts/ -> repo root
  if [[ -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/apps/device-agent/pyproject.toml" ]]; then
    echo "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/apps/device-agent"
    return
  fi
  # Already installed
  if [[ -f "$INSTALL_ROOT/apps/device-agent/pyproject.toml" ]]; then
    echo "$INSTALL_ROOT/apps/device-agent"
    return
  fi
  echo "Downloading Appi source from GitHub ($REPO@$BRANCH)..."
  mkdir -p "$INSTALL_ROOT"
  TMP="$(mktemp -d)"
  curl -fsSL "https://codeload.github.com/${REPO}/tar.gz/${BRANCH}" -o "$TMP/appi.tgz"
  tar -xzf "$TMP/appi.tgz" -C "$TMP"
  SRC="$(find "$TMP" -maxdepth 1 -type d -name '*-*' | head -1)"
  rm -rf "$INSTALL_ROOT/apps" "$INSTALL_ROOT/scripts"
  mkdir -p "$INSTALL_ROOT"
  cp -R "$SRC/apps" "$INSTALL_ROOT/"
  cp -R "$SRC/scripts" "$INSTALL_ROOT/" 2>/dev/null || true
  rm -rf "$TMP"
  echo "$INSTALL_ROOT/apps/device-agent"
}

PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Install Python 3.11+ first (python3 not found). python.org or: brew install python"
  exit 3
fi

AGENT="$(resolve_agent)"
echo "Using agent at: $AGENT"

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
echo "macOS setup is ready."
echo "Pair from https://appi-project01.netlify.app/device then run:"
echo "  cd $AGENT"
echo "  $PYTHON -m app.main pair --code YOUR_CODE"
echo "What works after pairing: files in approved folders, terminal, Playwright browser."
echo "What does not work yet: wake word, TCC-gated Apple APIs, contacts, payments."
