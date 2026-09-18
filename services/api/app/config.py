from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_files() -> tuple[str, ...]:
    """Prefer the monorepo root `.env`, then local fallbacks."""
    here = Path(__file__).resolve()
    root = here.parents[3]  # …/APPI-0.1.0/.env
    package = here.parents[2]  # …/services/api
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

    database_url: str = "sqlite+aiosqlite:///./appi.db"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    # Accept Next.js-style names from the same root .env
    next_public_supabase_url: str = ""
    next_public_supabase_anon_key: str = ""

    ai_provider: str = "heuristic"
    ai_api_key: str = ""
    ai_base_url: str = ""
    ai_model: str = ""
    openai_api_key: str = ""

    web_push_vapid_public_key: str = ""
    web_push_vapid_private_key: str = ""

    @model_validator(mode="after")
    def _alias_public_supabase(self) -> "Settings":
        if not (self.supabase_url or "").strip() and (self.next_public_supabase_url or "").strip():
            self.supabase_url = self.next_public_supabase_url.strip()
        if not (self.supabase_anon_key or "").strip() and (self.next_public_supabase_anon_key or "").strip():
            self.supabase_anon_key = self.next_public_supabase_anon_key.strip()
        return self

    @property
    def resolved_ai_key(self) -> str:
        return (self.ai_api_key or self.openai_api_key or "").strip()

    @property
    def resolved_ai_provider(self) -> str:
        name = (self.ai_provider or "heuristic").strip().lower()
        key = self.resolved_ai_key
        if not key:
            return "heuristic"
        if name in {"", "heuristic"}:
            if (self.ai_base_url or "").strip():
                return "openai_compatible"
            if self.openai_api_key:
                return "openai"
            return "heuristic"
        return name or "heuristic"

    github_client_id: str = ""
    github_client_secret: str = ""
    github_oauth_redirect: str = "http://127.0.0.1:8000/api/v1/connections/github/oauth/callback"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_oauth_redirect: str = "http://127.0.0.1:8000/api/v1/connections/gmail/oauth/callback"
    google_calendar_oauth_redirect: str = (
        "http://127.0.0.1:8000/api/v1/connections/google_calendar/oauth/callback"
    )

    jwt_secret: str = "change-me-to-a-long-random-string"
    jwt_expire_minutes: int = 60 * 24 * 7
    encryption_key: str = ""

    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    app_url: str = "http://localhost:3000"
    next_public_app_url: str = ""
    next_public_api_url: str = "http://127.0.0.1:8000"

    runtime_version: str = "0.3.0"
    rate_limit_per_minute: int = 120

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def public_app_url(self) -> str:
        return (self.app_url or self.next_public_app_url or "http://localhost:3000").rstrip("/")

    @property
    def public_api_url(self) -> str:
        return (self.next_public_api_url or f"http://{self.api_host}:{self.api_port}").rstrip("/")


settings = Settings()
