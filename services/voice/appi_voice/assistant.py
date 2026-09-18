"""Local assistant phrases. Voice is still an input method, not a Guardian bypass."""

from __future__ import annotations

import json
import re
from datetime import datetime


def display_name(raw: str | None) -> str:
    name = (raw or "").strip()
    if not name:
        return "there"
    return name.split()[0]


def greeting(name: str | None = None) -> str:
    first = display_name(name)
    hour = datetime.now().hour
    if hour < 12:
        hello = "Good morning"
    elif hour < 17:
        hello = "Good afternoon"
    else:
        hello = "Good evening"
    return f"{hello} {first}. How are you? What can I do for you?"


def follow_up(name: str | None = None) -> str:
    return f"What else can I do for you, {display_name(name)}?"


def sanitize_heard(text: str | None) -> str:
    raw = (text or "").strip()
    if not raw:
        return ""
    if raw.startswith("{") and '"text"' in raw:
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                return str(payload.get("text") or "").strip()
        except json.JSONDecodeError:
            return ""
    return raw


def local_reply(text: str, name: str | None = None) -> str | None:
    """Answer small-talk on-device. Returns None when the cloud brain should handle it."""
    first = display_name(name)
    lowered = re.sub(r"[^a-z0-9\s']", " ", (text or "").lower())
    lowered = " ".join(lowered.split())
    if not lowered:
        return None
    if any(token in lowered for token in ("never mind", "nothing", "cancel", "stop", "goodbye", "good bye", "that's all", "thats all")):
        return f"Okay {first}. Call me when you need me."
    if any(token in lowered for token in ("how are you", "how's it going", "hows it going", "i'm fine", "im fine", "i am fine")):
        return f"I'm here and ready, {first}. What can I do for you?"
    if lowered in {"hello", "hi", "hey", "hey appi", "hello appi", "hi appi"}:
        return greeting(first)
    if any(token in lowered for token in ("what can you do", "what do you do", "help", "what can you help")):
        return (
            f"{first}, on this Windows PC I can open apps installed on this laptop, "
            "work with files in your approved folders, run commands in the terminal, and use the browser. "
            "Say open, then the app name. I can also write a post, copy it, and log into sites "
            "using the password stored only on this PC — never in the chat. "
            "You still handle MFA, banks, and money. What do you need?"
        )
    if "thank" in lowered:
        return f"You're welcome, {first}."
    return None
