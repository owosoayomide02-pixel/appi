from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _env_files() -> tuple[str, ...]:
    """Prefer monorepo root `.env` locally; on Docker/Render rely on process env."""
    here = Path(__file__).resolve()
    candidates: list[Path] = [Path.cwd() / ".env"]
    # Safe walk — Docker layout is /app/app/config.py (shallow), local is deeper.
    for parent in list(here.parents)[:6]:
        candidates.append(parent / ".env")
    found: list[str] = []
    seen: set[str] = set()
    for path in candidates:
        try:
            resolved = str(path.resolve())
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if path.is_file():
            found.append(resolved)
    return tuple(found)


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
    next_public_supabase_publishable_key: str = ""

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
        publishable = (self.next_public_supabase_publishable_key or "").strip()
        if not (self.supabase_anon_key or "").strip():
            if (self.next_public_supabase_anon_key or "").strip():
                self.supabase_anon_key = self.next_public_supabase_anon_key.strip()
            elif publishable:
                self.supabase_anon_key = publishable
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
    github_auth_oauth_redirect: str = "http://127.0.0.1:8000/api/v1/auth/oauth/github/callback"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_oauth_redirect: str = "http://127.0.0.1:8000/api/v1/connections/gmail/oauth/callback"
    google_auth_oauth_redirect: str = "http://127.0.0.1:8000/api/v1/auth/oauth/google/callback"
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

    # Public installers — set in root `.env` (DOWNLOAD_* / GITHUB_REPO)
    github_repo: str = ""
    download_windows_url: str = ""
    download_macos_url: str = ""
    download_linux_url: str = ""
    next_public_download_windows_url: str = ""
    next_public_download_macos_url: str = ""
    next_public_download_linux_url: str = ""
    next_public_github_repo: str = ""

    @model_validator(mode="after")
    def _resolve_download_urls(self) -> "Settings":
        """Prefer explicit DOWNLOAD_* from `.env`; only invent URLs if GITHUB_REPO is set."""
        repo = (self.next_public_github_repo or self.github_repo or "").strip()
        self.github_repo = repo
        release = f"https://github.com/{repo}/releases/latest/download" if repo else ""
        raw = f"https://raw.githubusercontent.com/{repo}/main" if repo else ""
        self.download_windows_url = (
            self.download_windows_url
            or self.next_public_download_windows_url
            or (f"{release}/Appi-windows.zip" if release else "")
        ).strip()
        self.download_macos_url = (
            self.download_macos_url
            or self.next_public_download_macos_url
            or (f"{raw}/scripts/setup-macos.sh" if raw else "")
        ).strip()
        self.download_linux_url = (
            self.download_linux_url
            or self.next_public_download_linux_url
            or (f"{raw}/scripts/setup-linux.sh" if raw else "")
        ).strip()
        return self

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
