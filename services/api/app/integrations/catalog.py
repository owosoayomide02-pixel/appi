"""Connector catalog. Status is never faked as connected."""

from __future__ import annotations

from typing import Any

# Preferred order: Official API / OAuth → OS integration → browser → manual handoff.
CONNECTORS: list[dict[str, Any]] = [
    {"id": "github", "name": "GitHub", "category": "developer", "oauth": True, "status": "not_connected"},
    {"id": "supabase", "name": "Supabase", "category": "developer", "oauth": False, "status": "not_connected"},
    {"id": "vercel", "name": "Vercel", "category": "cloud", "oauth": True, "status": "not_connected"},
    {"id": "cloudflare", "name": "Cloudflare", "category": "cloud", "oauth": True, "status": "not_connected"},
    {"id": "google", "name": "Google", "category": "productivity", "oauth": True, "status": "not_connected"},
    {"id": "gmail", "name": "Gmail", "category": "productivity", "oauth": True, "status": "not_connected"},
    {"id": "google_calendar", "name": "Google Calendar", "category": "productivity", "oauth": True, "status": "not_connected"},
    {"id": "google_contacts", "name": "Google Contacts", "category": "productivity", "oauth": True, "status": "not_connected"},
    {"id": "microsoft", "name": "Microsoft", "category": "productivity", "oauth": True, "status": "not_connected"},
    {"id": "meta", "name": "Meta", "category": "social", "oauth": True, "status": "not_connected"},
    {"id": "instagram", "name": "Instagram", "category": "social", "oauth": True, "status": "not_connected"},
    {"id": "facebook", "name": "Facebook", "category": "social", "oauth": True, "status": "not_connected"},
    {"id": "whatsapp", "name": "WhatsApp", "category": "communication", "oauth": True, "status": "unsupported"},
    {"id": "x", "name": "X", "category": "social", "oauth": True, "status": "not_connected"},
    {"id": "tiktok", "name": "TikTok", "category": "social", "oauth": True, "status": "not_connected"},
    {"id": "twilio", "name": "Twilio", "category": "communication", "oauth": False, "status": "not_connected"},
    {"id": "paystack", "name": "Paystack", "category": "payments", "oauth": True, "status": "not_connected"},
    {"id": "stripe", "name": "Stripe", "category": "payments", "oauth": True, "status": "not_connected"},
    {"id": "open_banking", "name": "Open banking", "category": "finance", "oauth": True, "status": "unsupported"},
    {"id": "ecommerce", "name": "E-commerce", "category": "shopping", "oauth": True, "status": "not_connected"},
]

CATEGORIES = [
    "developer",
    "cloud",
    "communication",
    "social",
    "productivity",
    "payments",
    "finance",
    "shopping",
]


def connector_meta(provider: str) -> dict[str, Any] | None:
    for item in CONNECTORS:
        if item["id"] == provider:
            return item
    return None
