"""Canonical capability catalog. Capabilities and permissions are separate."""

from __future__ import annotations

from typing import Any

CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"

# Fine-grained capabilities. A device may support a capability while Appi still lacks permission.
CAPABILITIES: dict[str, dict[str, Any]] = {
    "filesystem.read": {"group": "filesystem", "risk": "low", "implemented_on": ["windows", "linux", "macos"]},
    "filesystem.write": {"group": "filesystem", "risk": "medium", "implemented_on": ["windows", "linux", "macos"]},
    "filesystem.delete": {"group": "filesystem", "risk": "high", "implemented_on": ["windows", "linux", "macos"]},
    "terminal.execute": {"group": "terminal", "risk": "medium", "implemented_on": ["windows", "linux", "macos"]},
    "process.start": {"group": "terminal", "risk": "medium", "implemented_on": ["windows", "linux", "macos"]},
    "process.stop": {"group": "terminal", "risk": "medium", "implemented_on": ["windows", "linux", "macos"]},
    "browser.navigate": {"group": "browser", "risk": "medium", "implemented_on": ["windows", "linux", "macos"]},
    "browser.click": {"group": "browser", "risk": "medium", "implemented_on": ["windows", "linux", "macos"]},
    "browser.type": {"group": "browser", "risk": "medium", "implemented_on": ["windows", "linux", "macos"]},
    "browser.read": {"group": "browser", "risk": "low", "implemented_on": ["windows", "linux", "macos"]},
    "browser.download": {"group": "browser", "risk": "medium", "implemented_on": ["windows", "linux", "macos"]},
    "browser.upload": {"group": "browser", "risk": "medium", "implemented_on": ["windows", "linux", "macos"]},
    "desktop.launch_app": {"group": "desktop_ui", "risk": "medium", "implemented_on": ["windows"]},
    "desktop.inspect_ui": {"group": "desktop_ui", "risk": "medium", "implemented_on": []},
    "desktop.interact": {"group": "desktop_ui", "risk": "medium", "implemented_on": []},
    "clipboard.read": {"group": "desktop_ui", "risk": "medium", "implemented_on": ["windows"]},
    "clipboard.write": {"group": "desktop_ui", "risk": "medium", "implemented_on": ["windows"]},
    "system.info": {"group": "system", "risk": "low", "implemented_on": ["windows"]},
    "notification.send": {"group": "notifications", "risk": "low", "implemented_on": []},
    "contacts.read": {"group": "contacts", "risk": "high", "implemented_on": []},
    "calendar.read": {"group": "calendar", "risk": "medium", "implemented_on": []},
    "calendar.write": {"group": "calendar", "risk": "medium", "implemented_on": []},
    "messaging.send": {"group": "messaging", "risk": "high", "implemented_on": []},
    "calling.start": {"group": "phone_calls", "risk": "high", "implemented_on": []},
    "location.read": {"group": "location", "risk": "high", "implemented_on": []},
    "camera.capture": {"group": "camera", "risk": "high", "implemented_on": []},
    "microphone.record": {"group": "microphone", "risk": "high", "implemented_on": []},
    "payment.prepare": {"group": "payments", "risk": "medium", "implemented_on": []},
    "payment.execute": {"group": "payments", "risk": "high", "implemented_on": []},
    "social.draft": {"group": "social", "risk": "low", "implemented_on": ["windows"]},
    "social.publish": {"group": "social", "risk": "high", "implemented_on": []},
    "social.message": {"group": "social", "risk": "high", "implemented_on": []},
    "github.read": {"group": "cloud", "risk": "low", "implemented_on": []},
    "email.read": {"group": "cloud", "risk": "low", "implemented_on": []},
    "email.send": {"group": "cloud", "risk": "high", "implemented_on": []},
    "cloud.manage": {"group": "cloud", "risk": "high", "implemented_on": []},
    "database.manage": {"group": "database", "risk": "high", "implemented_on": []},
}

GROUP_FLAGS = (
    "filesystem",
    "terminal",
    "browser",
    "desktop_ui",
    "notifications",
    "microphone",
    "camera",
    "contacts",
    "calendar",
    "phone_calls",
    "payments",
    "messaging",
    "location",
    "social",
    "cloud",
    "database",
    "system",
)

# Existing V0.1 tool names keep working and map onto the capability registry.
TOOL_TO_CAPABILITY: dict[str, str] = {
    "files.list_directory": "filesystem.read",
    "files.read_file": "filesystem.read",
    "files.write_file": "filesystem.write",
    "files.create_file": "filesystem.write",
    "files.rename_file": "filesystem.write",
    "files.move_file": "filesystem.write",
    "files.copy_file": "filesystem.write",
    "files.delete_file": "filesystem.delete",
    "files.delete": "filesystem.delete",
    "files.search": "filesystem.read",
    "filesystem.read": "filesystem.read",
    "filesystem.write": "filesystem.write",
    "filesystem.delete": "filesystem.delete",
    "terminal.run_command": "terminal.execute",
    "terminal.execute": "terminal.execute",
    "terminal.start_process": "process.start",
    "terminal.stop_process": "process.stop",
    "terminal.get_process_status": "process.start",
    "process.start": "process.start",
    "process.stop": "process.stop",
    "browser.open_browser": "browser.navigate",
    "browser.open_url": "browser.navigate",
    "browser.navigate": "browser.navigate",
    "browser.click": "browser.click",
    "browser.type": "browser.type",
    "browser.read_page": "browser.read",
    "browser.read": "browser.read",
    "browser.screenshot": "browser.read",
    "browser.select": "browser.click",
    "browser.scroll": "browser.read",
    "browser.upload_file": "browser.upload",
    "browser.download_file": "browser.download",
    "browser.search": "browser.navigate",
    "project.detect_framework": "filesystem.read",
    "project.inspect_package_json": "filesystem.read",
    "project.inspect_git_status": "filesystem.read",
    "project.detect_errors": "filesystem.read",
    "project.run_tests": "terminal.execute",
    "project.run_build": "terminal.execute",
    "social.draft": "social.draft",
    "social.publish": "social.publish",
    "social.delete": "social.publish",
    "social.message": "social.message",
    "payment.prepare": "payment.prepare",
    "payment.execute": "payment.execute",
    "transfer.prepare": "payment.prepare",
    "transfer.execute": "payment.execute",
    "messaging.send": "messaging.send",
    "calling.start": "calling.start",
    "contacts.read": "contacts.read",
    "calendar.read": "calendar.read",
    "calendar.write": "calendar.write",
    "calendar.create": "calendar.write",
    "desktop.launch_app": "desktop.launch_app",
    "app.launch": "desktop.launch_app",
    "access.prepare": "desktop.launch_app",
    "access.login": "browser.navigate",
    "system.info": "system.info",
    "clipboard.read": "clipboard.read",
    "clipboard.write": "clipboard.write",
    "notification.send": "notification.send",
    "cloud.manage": "cloud.manage",
    "database.manage": "database.manage",
    "github.user": "github.read",
    "github.repos": "github.read",
    "email.read": "email.read",
    "email.search": "email.read",
    "email.draft": "email.send",
    "email.send": "email.send",
    "gmail.profile": "email.read",
}


def capability_for_tool(tool: str) -> str:
    if tool in TOOL_TO_CAPABILITY:
        return TOOL_TO_CAPABILITY[tool]
    if tool in CAPABILITIES:
        return tool
    group = tool.split(".")[0] if "." in tool else tool
    if group == "files":
        return "filesystem.read"
    if group in CAPABILITIES:
        return group
    return tool


def group_for_capability(capability: str) -> str:
    meta = CAPABILITIES.get(capability) or {}
    if meta.get("group"):
        return str(meta["group"])
    if "." in capability:
        return capability.split(".", 1)[0]
    return capability


def capability_implemented(capability: str, platform: str) -> bool:
    meta = CAPABILITIES.get(capability)
    if not meta:
        return False
    return platform.lower() in {p.lower() for p in meta.get("implemented_on") or []}


def device_has_capability(capabilities: dict[str, Any] | None, capability: str) -> bool:
    caps = capabilities or {}
    if capability in caps and caps[capability] is False:
        return False
    if caps.get(capability) is True:
        return True
    group = group_for_capability(capability)
    if group in caps:
        return bool(caps[group])
    return False


def sanitize_reported_capabilities(platform: str, reported: dict[str, Any] | None) -> dict[str, bool]:
    """Merge a runtime report with the catalog. Unimplemented flags cannot be turned on."""
    merged = default_capabilities(platform)
    if reported:
        for key, value in reported.items():
            merged[str(key)] = bool(value)
    honest = default_capabilities(platform)
    for key, allowed in honest.items():
        if not allowed:
            merged[key] = False
    return merged


def default_capabilities(platform: str) -> dict[str, bool]:
    platform = platform.lower()
    flags = {flag: False for flag in GROUP_FLAGS}
    fine = {name: False for name in CAPABILITIES}
    if platform in {"windows", "linux", "macos"}:
        flags.update({"filesystem": True, "terminal": True, "browser": True})
        for name, meta in CAPABILITIES.items():
            if platform in meta.get("implemented_on", []):
                fine[name] = True
        if platform == "windows":
            flags["desktop_ui"] = True
            flags["system"] = True
    merged = {**flags, **fine}
    return merged


def coarse_from_fine(capabilities: dict[str, bool]) -> dict[str, bool]:
    return {flag: bool(capabilities.get(flag)) for flag in GROUP_FLAGS}
