from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_unix_and_ios_setup_scripts_exist():
    for name in ("setup-linux.sh", "setup-macos.sh", "setup-ios.sh"):
        path = ROOT / "scripts" / name
        text = path.read_text(encoding="utf-8")
        assert text.startswith("#!/usr/bin/env bash")
        assert "set -euo pipefail" in text
    linux = (ROOT / "scripts" / "setup-linux.sh").read_text(encoding="utf-8")
    assert "serve --no-voice" in linux
    assert "systemctl --user" in linux
    macos = (ROOT / "scripts" / "setup-macos.sh").read_text(encoding="utf-8")
    assert "LaunchAgents" in macos
    ios = (ROOT / "scripts" / "setup-ios.sh").read_text(encoding="utf-8")
    assert "xcodebuild" in ios
    assert "OS Restricted" in ios
    project = ROOT / "apps" / "runtimes" / "ios" / "AppiIOS" / "AppiIOS.xcodeproj" / "project.pbxproj"
    assert project.is_file()
    assert "dev.appi.ios" in project.read_text(encoding="utf-8")
    assert "PBXNativeTarget" in project.read_text(encoding="utf-8")
    vbs = ROOT / "scripts" / "Start Appi.vbs"
    assert vbs.is_file()
    assert "app.launcher" in vbs.read_text(encoding="utf-8")
