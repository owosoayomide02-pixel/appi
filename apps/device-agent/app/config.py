from pathlib import Path
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_files() -> tuple[str, ...]:
    """Prefer the monorepo root `.env`, then local fallbacks."""
    here = Path(__file__).resolve()
    root = here.parents[3]  # …/APPI-0.1.0/.env
    package = here.parents[2]  # …/apps/device-agent
    cwd = Path.cwd()
    ordered = [root / ".env", package / ".env", cwd / ".env"]
    found = [str(p) for p in ordered if p.is_file()]
    return tuple(found) if found else (str(root / ".env"),)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    device_agent_api_url: str = "http://127.0.0.1:8000"
    device_name: str = ""
    runtime_version: str = "0.3.0"

    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # Website / operator (same keys as root .env)
    app_url: str = "http://localhost:3000"
    next_public_app_url: str = ""
    next_public_api_url: str = ""

    @property
    def public_app_url(self) -> str:
        return (self.app_url or self.next_public_app_url or "http://localhost:3000").rstrip("/")

    @property
    def api_base_url(self) -> str:
        """Brain URL used for HTTP + WebSocket (DEVICE_AGENT_API_URL)."""
        return (
            self.device_agent_api_url
            or self.next_public_api_url
            or f"http://{self.api_host}:{self.api_port}"
        ).rstrip("/")

    @property
    def dashboard_url(self) -> str:
        """Operator UI opened by the desktop window / tray."""
        return f"{self.public_app_url}/app"

    @property
    def device_page_url(self) -> str:
        return f"{self.public_app_url}/device"

    @property
    def web_port(self) -> int:
        parsed = urlparse(self.public_app_url)
        if parsed.port:
            return parsed.port
        return 443 if parsed.scheme == "https" else 3000

    @property
    def resolved_api_host(self) -> str:
        parsed = urlparse(self.api_base_url)
        return parsed.hostname or self.api_host

    @property
    def resolved_api_port(self) -> int:
        parsed = urlparse(self.api_base_url)
        if parsed.port:
            return parsed.port
        if parsed.scheme == "https":
            return 443
        return self.api_port


settings = Settings()
