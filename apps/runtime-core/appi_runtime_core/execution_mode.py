"""Execution modes and idle policy for the background runtime."""

from __future__ import annotations

from enum import Enum


class ExecutionMode(str, Enum):
    BACKGROUND_SAFE = "BACKGROUND_SAFE"
    FOREGROUND_REQUIRED = "FOREGROUND_REQUIRED"
    USER_ATTENTION_REQUIRED = "USER_ATTENTION_REQUIRED"


FOREGROUND_TOOLS = {
    "browser.open_browser",
    "browser.open_url",
    "browser.navigate",
    "browser.click",
    "browser.type",
    "desktop.launch_app",
    "app.launch",
    "app.focus",
    "desktop.interact",
    "social.draft",
    "access.prepare",
    "access.login",
}

ATTENTION_TOOLS = {
    "payment.execute",
    "payment.prepare",
    "files.delete_file",
    "filesystem.delete",
    "calling.start",
    "social.publish",
    "app.uninstall",
    "system.shutdown",
    "system.restart",
}


def mode_for_tool(tool: str) -> ExecutionMode:
    if tool in ATTENTION_TOOLS or tool.endswith(".execute"):
        return ExecutionMode.USER_ATTENTION_REQUIRED
    if tool in FOREGROUND_TOOLS or tool.startswith("browser.") or tool.startswith("desktop."):
        return ExecutionMode.FOREGROUND_REQUIRED
    return ExecutionMode.BACKGROUND_SAFE
