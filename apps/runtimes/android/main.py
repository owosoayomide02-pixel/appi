"""Android runtime placeholder. Does not access Android APIs."""

from __future__ import annotations

CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"

ANDROID_CAPABILITIES = {
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
        "platform": "android",
        "result": None,
        "verification": None,
        "error": f"{CAPABILITY_UNAVAILABLE}: Android native runtime is not implemented",
        "error_code": CAPABILITY_UNAVAILABLE,
    }


if __name__ == "__main__":
    print("Appi Android runtime is a placeholder. Pairing a real Android agent is not available in this milestone.")
    print("Capabilities:", ANDROID_CAPABILITIES)
