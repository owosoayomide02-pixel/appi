"""Prepare posts and logins. Appi never types passwords or taps Post."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.desktop import apps as desktop_apps
from app.desktop import clipboard as desktop_clipboard

COMPOSE: dict[str, dict[str, str]] = {
    "instagram": {"url": "https://www.instagram.com/", "app": "instagram", "label": "Instagram"},
    "facebook": {"url": "https://www.facebook.com/", "app": "facebook", "label": "Facebook"},
    "x": {"url": "https://x.com/compose/post", "app": "x", "label": "X"},
    "twitter": {"url": "https://x.com/compose/post", "app": "twitter", "label": "X"},
    "linkedin": {"url": "https://www.linkedin.com/feed/", "app": "linkedin", "label": "LinkedIn"},
    "tiktok": {"url": "https://www.tiktok.com/tiktokstudio/upload", "app": "tiktok", "label": "TikTok"},
    "whatsapp": {"url": "https://web.whatsapp.com/", "app": "whatsapp", "label": "WhatsApp"},
    "threads": {"url": "https://www.threads.net/", "app": "threads", "label": "Threads"},
}

LOGIN: dict[str, dict[str, str]] = {
    "gmail": {"url": "https://accounts.google.com/", "label": "Google"},
    "google": {"url": "https://accounts.google.com/", "label": "Google"},
    "github": {"url": "https://github.com/login", "label": "GitHub"},
    "instagram": {"url": "https://www.instagram.com/accounts/login/", "label": "Instagram"},
    "facebook": {"url": "https://www.facebook.com/login/", "label": "Facebook"},
    "x": {"url": "https://x.com/login", "label": "X"},
    "twitter": {"url": "https://x.com/login", "label": "X"},
    "linkedin": {"url": "https://www.linkedin.com/login", "label": "LinkedIn"},
    "whatsapp": {"url": "https://web.whatsapp.com/", "label": "WhatsApp"},
}


def _err(code: str, message: str) -> dict[str, Any]:
    return {"success": False, "error": message, "error_code": code, "verification_required": True}


def _ok(data: dict[str, Any]) -> dict[str, Any]:
    return {"success": True, "data": data, "verification_required": True}


def normalize_platform(raw: str | None) -> str:
    text = (raw or "").strip().lower()
    if text in {"twitter", "tweet", "x"}:
        return "x"
    if text in COMPOSE:
        return text
    return text


def draft_post(payload: dict[str, Any]) -> dict[str, Any]:
    text = str(payload.get("text") or payload.get("body") or payload.get("content") or payload.get("post") or "").strip()
    if not text:
        return _err("ACTION_FAILED", "No post text to draft")
    platform = normalize_platform(payload.get("platform") or payload.get("service") or payload.get("app") or "")
    clip = desktop_clipboard.write(text)
    if not clip.get("success"):
        return clip

    opened: dict[str, Any] = {"launched": False}
    target = COMPOSE.get(platform)
    if target:
        opened = desktop_apps.launch({"app": target["app"], "url": target["url"]})
    else:
        note_path = _write_local_draft(text)
        opened = desktop_apps.launch({"app": "notepad", "url": str(note_path)})
        opened["data"] = {**(opened.get("data") or {}), "draft_file": str(note_path)}

    label = (target or {}).get("label") or "your notes"
    return _ok(
        {
            "drafted": True,
            "published": False,
            "platform": platform or "local",
            "text": text,
            "clipboard": True,
            "opened": bool((opened.get("data") or {}).get("launched") or opened.get("success")),
            "open_result": opened.get("data") or {},
            "next_step": f"Paste into {label} and send it yourself. Appi did not publish and will not type your password.",
        }
    )


def prepare_access(payload: dict[str, Any]) -> dict[str, Any]:
    service = normalize_platform(payload.get("service") or payload.get("app") or payload.get("platform") or "")
    target = LOGIN.get(service) or COMPOSE.get(service)
    if not target:
        return _err(
            "ACTION_FAILED",
            "Say which site to open (Gmail, GitHub, Instagram, Facebook, X, LinkedIn). Appi will not type your password.",
        )
    opened = desktop_apps.launch({"app": service, "url": target["url"]})
    if not opened.get("success"):
        return opened
    return _ok(
        {
            "opened": True,
            "published": False,
            "typed_password": False,
            "service": service,
            "url": target["url"],
            "next_step": f"Sign into {target.get('label') or service} yourself. Appi does not store or type passwords, MFA, or Face ID.",
        }
    )


def _write_local_draft(text: str) -> Path:
    folder = Path.home() / "Appi" / "drafts"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    path = folder / f"post-{stamp}.txt"
    path.write_text(text, encoding="utf-8")
    return path


def extract_platform(goal: str) -> str:
    lowered = f" {goal.lower()} "
    mapping = (
        ("instagram", "instagram"),
        ("facebook", "facebook"),
        ("tiktok", "tiktok"),
        ("linkedin", "linkedin"),
        ("whatsapp", "whatsapp"),
        ("threads", "threads"),
        ("twitter", "x"),
        ("tweet", "x"),
        (" on x ", "x"),
        ("x.com", "x"),
    )
    for token, platform in mapping:
        if token in lowered:
            return platform
    return ""


def extract_post_text(goal: str) -> str:
    raw = re.sub(r"^\[voice\]\s*", "", goal.strip(), flags=re.I)
    match = re.search(
        r"(?:saying|that says|that reads|caption(?:ed)?|about|:\s+)(.+)$",
        raw,
        re.I | re.S,
    )
    if match:
        return match.group(1).strip().strip('"').strip()
    cleaned = re.sub(
        r"^(?:appi[,:\s]*)?(?:please\s+)?(?:write|draft|create|make|post|publish|share|tweet)\s+"
        r"(?:an?\s+)?(?:instagram\s+|facebook\s+|tiktok\s+|linkedin\s+|twitter\s+|x\s+|whatsapp\s+)?"
        r"(?:post|tweet|caption|update|status)?\s*(?:for me\s*)?",
        "",
        raw,
        flags=re.I,
    ).strip()
    return cleaned or raw
