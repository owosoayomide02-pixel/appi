"""Future integration surface. V0.1 reports Not connected — no fake OAuth."""

from abc import ABC, abstractmethod


class Connector(ABC):
    provider: str
    oauth: bool = True

    @abstractmethod
    def status(self) -> str:
        return "not_connected"


class FutureConnector(Connector):
    def __init__(self, provider: str) -> None:
        self.provider = provider

    def status(self) -> str:
        return "not_connected"


FUTURE_MODULES = {
    "social": FutureConnector("social"),
    "email": FutureConnector("email"),
    "calendar": FutureConnector("calendar"),
    "calls": FutureConnector("calls"),
    "payments": FutureConnector("payments"),
    "shopping": FutureConnector("shopping"),
    "mobile": FutureConnector("mobile"),
    "desktop_ui": FutureConnector("desktop_ui"),
    "cloud": FutureConnector("cloud"),
    "voice": FutureConnector("voice"),
    "github": FutureConnector("github"),
    "supabase": FutureConnector("supabase"),
    "google": FutureConnector("google"),
    "microsoft": FutureConnector("microsoft"),
    "vercel": FutureConnector("vercel"),
    "cloudflare": FutureConnector("cloudflare"),
}
