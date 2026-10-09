from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_linux_systemd_user_unit_exists():
    unit = (ROOT / "apps" / "runtimes" / "linux" / "appi-runtime.service").read_text(encoding="utf-8")
    assert "app.main serve" in unit
    assert "[Service]" in unit


def test_macos_launch_agent_exists():
    plist = (ROOT / "apps" / "runtimes" / "macos" / "dev.appi.runtime.plist").read_text(encoding="utf-8")
    assert "dev.appi.runtime" in plist
    assert "serve" in plist


def test_android_foreground_service_declares_notification():
    manifest = (ROOT / "apps" / "runtimes" / "android" / "kotlin" / "app" / "src" / "main" / "AndroidManifest.xml").read_text(encoding="utf-8")
    service = (ROOT / "apps" / "runtimes" / "android" / "kotlin" / "app" / "src" / "main" / "kotlin" / "dev" / "appi" / "runtime" / "AppiForegroundService.kt").read_text(encoding="utf-8")
    assert "FOREGROUND_SERVICE" in manifest
    assert "startForeground" in service
    assert "class AppiForegroundService" in service
    assert "class AccessibilityService" not in service
