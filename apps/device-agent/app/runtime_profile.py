"""Honest capability profile for the desktop Python runtime."""

from __future__ import annotations

import sys

from app.config import settings

RUNTIME_VERSION = (settings.runtime_version or "0.3.0").strip()


def detect_platform() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("linux"):
        return "linux"
    return sys.platform


def os_label(platform: str) -> str:
    return {
        "windows": "Windows",
        "macos": "macOS",
        "linux": "Linux",
        "android": "Android",
        "ios": "iOS",
    }.get(platform, platform)


def desktop_capabilities(platform: str) -> dict[str, bool]:
    # Files, terminal, Playwright, Windows app launch / clipboard / system.info.
    # Desktop UI automation, OS notifications, contacts, payments, etc. are not.
    implemented = {
        "filesystem": True,
        "filesystem.read": True,
        "filesystem.write": True,
        "filesystem.delete": True,
        "terminal": True,
        "terminal.execute": True,
        "process.start": True,
        "process.stop": True,
        "browser": True,
        "browser.navigate": True,
        "browser.click": True,
        "browser.type": True,
        "browser.read": True,
        "browser.download": True,
        "browser.upload": True,
        "desktop_ui": platform == "windows",
        "desktop.launch_app": platform == "windows",
        "app.launch": platform == "windows",
        "system.info": platform == "windows",
        "desktop.inspect_ui": False,
        "desktop.interact": False,
        "clipboard.read": platform == "windows",
        "clipboard.write": platform == "windows",
        "notifications": False,
        "notification.send": False,
        "contacts": False,
        "contacts.read": False,
        "calendar": False,
        "calendar.read": False,
        "calendar.write": False,
        "phone_calls": False,
        "calling.start": False,
        "payments": False,
        "payment.prepare": False,
        "payment.execute": False,
        "messaging": False,
        "messaging.send": False,
        "location": False,
        "location.read": False,
        "camera": False,
        "camera.capture": False,
        "microphone": False,
        "microphone.record": False,
        "social": False,
        "social.draft": platform == "windows",
        "social.publish": False,
        "social.message": False,
        "cloud": False,
        "cloud.manage": False,
        "database.manage": False,
    }
    if platform not in {"windows", "linux", "macos"}:
        return {key: False for key in implemented}
    return implemented
