"""iOS runtime placeholder. Does not access Apple APIs."""

from __future__ import annotations

CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"

IOS_CAPABILITIES = {
    "filesystem": False,
    "terminal": False,
    "browser": False,
    "desktop_ui": False,
    "notifications": False,
    "contacts": False,
    "calendar": False,
    "microphone": False,
    "camera": False,
    "location": False,
    "phone_calls": False,
    "payments": False,
}


def execute(tool: str, _input: dict) -> dict:
    return {
        "success": False,
        "platform": "ios",
        "result": None,
        "verification": None,
        "error": f"{CAPABILITY_UNAVAILABLE}: iOS native runtime is not implemented",
        "error_code": CAPABILITY_UNAVAILABLE,
    }


if __name__ == "__main__":
    print("Appi iOS runtime is a placeholder. App Intents / Shortcuts are not wired in this milestone.")
    print("Capabilities:", IOS_CAPABILITIES)
