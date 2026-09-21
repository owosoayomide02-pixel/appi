#!/usr/bin/env bash
# Install the Appi desktop runtime on Linux (files, terminal, browser).
# Safe to download and run alone — clones the agent from GitHub if needed.
# Voice wake-word is Windows SAPI today — this setup starts with --no-voice.

set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This setup must be run on Linux. On Windows download Appi-windows.zip from the site."
  exit 2
fi

REPO="${APPI_GITHUB_REPO:-owosoayomide02-pixel/appi}"
BRANCH="${APPI_BRANCH:-main}"
INSTALL_ROOT="${APPI_HOME:-$HOME/.appi}"

resolve_agent() {
  if [[ -f "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/apps/device-agent/pyproject.toml" ]]; then
    echo "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/apps/device-agent"
    return
  fi
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
  echo "Install Python 3.11+ first (python3 not found)."
  exit 3
fi

AGENT="$(resolve_agent)"
echo "Using agent at: $AGENT"

echo "Installing Appi device-agent dependencies..."
"$PYTHON" -m pip install --user -e "$AGENT"
"$PYTHON" -m pip install --user httpx websockets pydantic-settings playwright

UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
mkdir -p "$UNIT_DIR"
UNIT="$UNIT_DIR/appi-runtime.service"
cat > "$UNIT" <<EOF
[Unit]
Description=Appi background runtime
After=network.target

[Service]
Type=simple
WorkingDirectory=$AGENT
ExecStart=$PYTHON -m app.main serve --no-voice
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF

echo "Wrote $UNIT"

if command -v systemctl >/dev/null 2>&1; then
  systemctl --user daemon-reload
  systemctl --user enable --now appi-runtime.service
  echo "systemd user service enabled: appi-runtime.service"
else
  echo "systemctl not available. Starting a login autostart entry instead."
  (cd "$AGENT" && "$PYTHON" -m app.main autostart on)
fi

echo
echo "Linux setup is ready."
echo "Pair from https://appi-project01.netlify.app/device then run:"
echo "  cd $AGENT"
echo "  $PYTHON -m app.main pair --code YOUR_CODE"
echo "What works after pairing: files in approved folders, terminal, Playwright browser."
echo "What does not work yet: wake word, clipboard (Windows-only this milestone), contacts, payments."
