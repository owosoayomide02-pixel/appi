"""Choose official API → OS integration → browser → UI automation → ask.

Never pick UI automation when a safer authenticated connector exists.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.integrations.catalog import CONNECTORS, connector_meta


CONNECTOR_INTENTS: dict[str, list[str]] = {
    "email.send": ["gmail", "google", "microsoft"],
    "email.read": ["gmail", "google", "microsoft"],
    "email.draft": ["gmail", "google", "microsoft"],
    "calendar.create": ["google_calendar", "google", "microsoft"],
    "calendar.read": ["google_calendar", "google", "microsoft"],
    "contacts.search": ["google_contacts", "google", "microsoft"],
    "social.publish": ["instagram", "facebook", "x", "tiktok", "linkedin"],
    "payment.execute": ["paystack", "stripe"],
    "transfer.execute": ["paystack", "stripe", "open_banking"],
    "code.push": ["github"],
    "cloud.manage": ["supabase", "vercel", "cloudflare", "aws"],
}


@dataclass
class ResolvedAction:
    intent: str
    service: str | None
    account: str
    risk: str
    connector_id: str | None
    connector_available: bool
    path: str
    permission: str
    ask_user: bool
    notes: list[str]


def infer_intent(text: str) -> str:
    lowered = text.lower()
    if "instagram" in lowered or "facebook" in lowered or "tiktok" in lowered:
        return "social.publish"
    if "email" in lowered or "gmail" in lowered:
        return "email.send" if any(w in lowered for w in ("send", "mail")) else "email.read"
    if "calendar" in lowered or "meeting" in lowered:
        return "calendar.create" if any(w in lowered for w in ("create", "add", "schedule")) else "calendar.read"
    if "call" in lowered:
        return "call.start"
    if "transfer" in lowered or "pay" in lowered or "₦" in text:
        return "transfer.execute"
    if "github" in lowered:
        return "code.push"
    return "task.generic"


def resolve_action(text: str, *, connected: set[str] | None = None) -> ResolvedAction:
    connected = connected or set()
    intent = infer_intent(text)
    candidates = CONNECTOR_INTENTS.get(intent) or []
    service = None
    lowered = text.lower()
    for item in CONNECTORS:
        if item["id"] in lowered or item["name"].lower() in lowered:
            service = item["id"]
            break
    if not service and candidates:
        service = candidates[0]
    meta = connector_meta(service) if service else None
    connector_id = meta["id"] if meta else None
    connector_available = bool(connector_id and connector_id in connected)
    path = "ask_user"
    notes = [
        "Order: official API connector → OS-native → browser automation → UI automation → ask user.",
    ]
    if connector_id and connector_available:
        path = "official_api"
    elif connector_id:
        path = "ask_user"
        notes.append("CONNECTOR_NOT_CONNECTED")
    elif intent.startswith("call."):
        path = "os_native"
        notes.append("Uses supported device calling intents only. Voice is not authentication.")
    permission = "ASK"
    risk = "high" if intent in {"transfer.execute", "payment.execute", "social.publish", "call.start"} else "medium"
    return ResolvedAction(
        intent=intent,
        service=service,
        account="user-selected account",
        risk=risk,
        connector_id=connector_id,
        connector_available=connector_available,
        path=path,
        permission=permission,
        ask_user=path == "ask_user" or permission == "ASK",
        notes=notes,
    )
