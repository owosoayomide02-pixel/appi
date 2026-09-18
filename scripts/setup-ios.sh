#!/usr/bin/env bash
# Build the iPhone placeholder app (simulator). Requires Xcode on a Mac.
# This is not a phone assistant. iOS cannot grant control of other apps.

set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "iPhone builds need a Mac with Xcode."
  echo "Copy this repo to a Mac, open Xcode, then run:"
  echo "  bash scripts/setup-ios.sh"
  echo "The app is a placeholder: it cannot open files, Safari, or other iPhone apps."
  exit 2
fi

if ! command -v xcodebuild >/dev/null 2>&1; then
  echo "Install Xcode from the App Store, then run: xcode-select --install"
  exit 3
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="$ROOT/apps/runtimes/ios/AppiIOS/AppiIOS.xcodeproj"
OUT="$ROOT/dist/ios"

if [[ ! -d "$PROJECT" ]]; then
  echo "Missing Xcode project at $PROJECT"
  exit 4
fi

mkdir -p "$OUT"
echo "Building Appi iOS placeholder for the iPhone simulator..."
xcodebuild \
  -project "$PROJECT" \
  -scheme AppiIOS \
  -sdk iphonesimulator \
  -configuration Debug \
  -derivedDataPath "$OUT/DerivedData" \
  CODE_SIGNING_ALLOWED=NO \
  build

APP="$(find "$OUT/DerivedData" -name 'AppiIOS.app' -type d | head -n 1)"
if [[ -z "$APP" ]]; then
  echo "xcodebuild finished but AppiIOS.app was not found."
  exit 5
fi

cp -R "$APP" "$OUT/AppiIOS.app"
echo "iPhone simulator app: $OUT/AppiIOS.app"
echo "Install on Simulator: xcrun simctl install booted \"$OUT/AppiIOS.app\""
echo "A signed .ipa for a physical iPhone needs an Apple Developer account and Xcode Organizer."
echo "This app does not act as Siri and cannot control other iOS apps (OS Restricted)."
