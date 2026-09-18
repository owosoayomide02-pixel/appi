"""Official API connectors. Never fake a connected provider."""

from __future__ import annotations

from typing import Any

CONNECTOR_NOT_CONNECTED = "CONNECTOR_NOT_CONNECTED"


class ConnectorAdapter:
    id = "base"
    name = "Base"

    async def status(self) -> str:
        return "not_connected"

    async def execute(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "success": False,
            "error_code": CONNECTOR_NOT_CONNECTED,
            "error": f"{CONNECTOR_NOT_CONNECTED}: {self.id} is not connected",
            "action": action,
        }


class GmailAdapter(ConnectorAdapter):
    """Stub adapter. Live Gmail OAuth and tools live in app.integrations.gmail."""

    id = "gmail"
    name = "Gmail"


class GoogleCalendarAdapter(ConnectorAdapter):
    """Stub adapter. Live Calendar OAuth and tools live in app.integrations.google_calendar."""

    id = "google_calendar"
    name = "Google Calendar"


class GoogleContactsAdapter(ConnectorAdapter):
    id = "google_contacts"
    name = "Google Contacts"


class GitHubAdapter(ConnectorAdapter):
    id = "github"
    name = "GitHub"


class SupabaseAdapter(ConnectorAdapter):
    id = "supabase"
    name = "Supabase"


ADAPTERS = {
    adapter.id: adapter
    for adapter in (
        GmailAdapter(),
        GoogleCalendarAdapter(),
        GoogleContactsAdapter(),
        GitHubAdapter(),
        SupabaseAdapter(),
    )
}
