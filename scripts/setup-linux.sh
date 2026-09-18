#!/usr/bin/env bash
# Install the Appi desktop runtime on Linux (files, terminal, browser).
# Voice wake-word is Windows SAPI today — this setup starts with --no-voice.
# Run this file on a Linux machine, not on Windows.

set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This setup must be run on Linux. On Windows use scripts/preview-windows.ps1"
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT="$ROOT/apps/device-agent"
PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Install Python 3.11+ first (python3 not found)."
  exit 3
fi

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
echo "Linux setup is ready. This is the shared Python agent, not yet verified on this host."
echo "Voice (say Appi) is Windows-only until Linux STT/TTS is implemented."
echo "Pair from the dashboard, then:"
echo "  cd $AGENT"
echo "  $PYTHON -m app.main pair --code 123456"
echo "What works after pairing: files in approved folders, terminal, Playwright browser, app launch if the binary exists."
echo "What does not work yet: wake word, clipboard (Windows-only this milestone), contacts, payments."
