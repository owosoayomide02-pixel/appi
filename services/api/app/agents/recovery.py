from __future__ import annotations

MAX_RETRIES = 2
MAX_REPLANS = 2


def classify_error(message: str) -> str:
    text = (message or "").lower()
    if any(token in text for token in ("timeout", "timed out", "temporarily")):
        return "retry"
    if any(token in text for token in ("not found", "enoent", "module not found", "failed", "error")):
        return "replan"
    if any(token in text for token in ("denied", "forbidden", "kill switch", "blocked")):
        return "stop"
    return "replan"
