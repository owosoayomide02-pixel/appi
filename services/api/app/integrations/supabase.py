"""Official Supabase REST connector. Keys never go to the model."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import settings

_CACHE: tuple[float, bool] | None = None
_CACHE_TTL = 60.0


def normalize_supabase_url(url: str) -> str:
    raw = (url or "").strip().rstrip("/")
    for suffix in ("/rest/v1", "/auth/v1", "/storage/v1"):
        if raw.lower().endswith(suffix):
            raw = raw[: -len(suffix)]
            break
    return raw.rstrip("/")


def supabase_configured() -> bool:
    url = normalize_supabase_url(settings.supabase_url)
    key = (settings.supabase_anon_key or settings.supabase_service_role_key or "").strip()
    return bool(url.startswith("https://") and key)


def _anon_or_service() -> str:
    return (settings.supabase_anon_key or settings.supabase_service_role_key or "").strip()


async def ping_supabase() -> bool:
    global _CACHE
    if not supabase_configured():
        return False
    now = time.monotonic()
    if _CACHE and now - _CACHE[0] < _CACHE_TTL:
        return _CACHE[1]
    base = normalize_supabase_url(settings.supabase_url)
    key = _anon_or_service()
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"}
    ok = False
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            # Root OpenAPI is often disabled for the anon key; a missing table 404 means the key is valid.
            response = await client.get(f"{base}/rest/v1/appi_connection_probe", headers=headers)
            ok = response.status_code in {200, 206, 404, 406}
    except Exception:
        ok = False
    _CACHE = (now, ok)
    return ok


def supabase_status() -> dict[str, Any]:
    return {
        "supabase_configured": supabase_configured(),
    }
